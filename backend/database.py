"""
Persistent SQLite database — single source of truth for all job data.
Unified schema for LinkedIn, Indeed, and future sources.
"""

import sqlite3
import uuid
import json
import hashlib
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), 'jobs_cache.db')


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # safe concurrent writes
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_jobs_table():
    """
    Create the unified jobs table and supporting tables.
    Runs on every startup — safe to call multiple times (IF NOT EXISTS).
    Never wipes data.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ── Unified jobs table ─────────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id                  TEXT PRIMARY KEY,

            -- Deduplication key: external platform ID + source
            external_id         TEXT NOT NULL,
            source              TEXT NOT NULL,   -- 'linkedin' | 'indeed' | 'remoteok'

            -- Core fields (shared by all sources)
            title               TEXT NOT NULL,
            company_name        TEXT,
            location            TEXT,
            job_url             TEXT,
            apply_url           TEXT,            -- Indeed-specific; NULL for LinkedIn

            -- Search context (used for querying)
            role_query          TEXT,
            location_query      TEXT,

            -- Date: stored as ISO YYYY-MM-DD.
            -- days_since_posted is computed dynamically at query time:
            --   CAST(julianday('now') - julianday(date_published) AS INTEGER)
            date_published      TEXT,

            -- Job details
            description         TEXT,
            is_remote           INTEGER DEFAULT 0,
            job_type            TEXT,
            experience_level    TEXT,

            -- Indeed-specific
            salary              TEXT,
            company_rating      REAL,

            -- Extracted / computed
            tech_stack          TEXT,            -- JSON array
            relevance_score     REAL,
            reason              TEXT,

            -- Recruiter info (populated by recruiter finder pipeline)
            recruiter_name      TEXT,
            recruiter_email     TEXT,
            recruiter_title     TEXT,
            recruiter_linkedin_url TEXT,

            -- Outreach message (populated by message generator)
            subject_line        TEXT,
            message_body        TEXT,

            -- UI rendering
            portal_name         TEXT,
            portal_logo         TEXT,
            portal_color        TEXT,

            -- Full serialised object for zero-transform reads
            raw_data            TEXT,            -- JSON

            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(external_id, source)
        )
    ''')

    # ── Normalised attribute / benefit tables ──────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_attributes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id      TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            attribute   TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_benefits (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id      TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            benefit     TEXT NOT NULL
        )
    ''')

    # ── Indexes ────────────────────────────────────────────────────────────────
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_jobs_role_location
        ON jobs(role_query, location_query)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_jobs_source
        ON jobs(source)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_jobs_date
        ON jobs(date_published)
    ''')
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_dedup
        ON jobs(external_id, source)
    ''')

    conn.commit()
    conn.close()
    print("[DB] Persistent jobs table ready")


# ── Write ──────────────────────────────────────────────────────────────────────

def upsert_job(job_data: dict) -> tuple:
    """
    Insert or update a job record.
    Deduplication key: external_id + source.
    Returns (job_id, action) where action is 'inserted' or 'updated'.
    """
    conn = get_connection()
    cursor = conn.cursor()

    external_id = job_data.get('external_id', '')
    source      = job_data.get('source', 'unknown')

    cursor.execute(
        'SELECT id FROM jobs WHERE external_id = ? AND source = ?',
        (external_id, source)
    )
    row = cursor.fetchone()

    if row:
        job_id = row['id']
        cursor.execute('''
            UPDATE jobs SET
                title               = ?,
                company_name        = ?,
                location            = ?,
                job_url             = ?,
                apply_url           = ?,
                role_query          = ?,
                location_query      = ?,
                date_published      = ?,
                description         = ?,
                is_remote           = ?,
                job_type            = ?,
                experience_level    = ?,
                salary              = ?,
                company_rating      = ?,
                tech_stack          = ?,
                relevance_score     = ?,
                reason              = ?,
                recruiter_name      = ?,
                recruiter_email     = ?,
                recruiter_title     = ?,
                recruiter_linkedin_url = ?,
                subject_line        = ?,
                message_body        = ?,
                portal_name         = ?,
                portal_logo         = ?,
                portal_color        = ?,
                raw_data            = ?,
                updated_at          = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', _values(job_data) + (job_id,))
        action = 'updated'
    else:
        job_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO jobs (
                id, external_id, source,
                title, company_name, location, job_url, apply_url,
                role_query, location_query, date_published,
                description, is_remote, job_type, experience_level,
                salary, company_rating, tech_stack,
                relevance_score, reason,
                recruiter_name, recruiter_email, recruiter_title, recruiter_linkedin_url,
                subject_line, message_body,
                portal_name, portal_logo, portal_color,
                raw_data
            ) VALUES (
                ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?
            )
        ''', (job_id, external_id, source) + _values(job_data))
        action = 'inserted'

    # Attributes
    attrs = job_data.get('attributes') or []
    if attrs:
        cursor.execute('DELETE FROM job_attributes WHERE job_id = ?', (job_id,))
        cursor.executemany(
            'INSERT INTO job_attributes (job_id, attribute) VALUES (?, ?)',
            [(job_id, a) for a in attrs]
        )

    # Benefits
    benefits = job_data.get('benefits') or []
    if benefits:
        cursor.execute('DELETE FROM job_benefits WHERE job_id = ?', (job_id,))
        cursor.executemany(
            'INSERT INTO job_benefits (job_id, benefit) VALUES (?, ?)',
            [(job_id, b) for b in benefits]
        )

    conn.commit()
    conn.close()
    return job_id, action


def _values(d: dict) -> tuple:
    """Return the ordered column values for INSERT/UPDATE (excluding id/external_id/source)."""
    return (
        d.get('title'),
        d.get('company_name'),
        d.get('location'),
        d.get('job_url'),
        d.get('apply_url'),
        d.get('role_query'),
        d.get('location_query'),
        d.get('date_published'),
        d.get('description'),
        int(bool(d.get('is_remote', 0))),
        d.get('job_type'),
        d.get('experience_level'),
        d.get('salary'),
        d.get('company_rating'),
        json.dumps(d.get('tech_stack') or []),
        d.get('relevance_score'),
        d.get('reason'),
        d.get('recruiter_name'),
        d.get('recruiter_email'),
        d.get('recruiter_title'),
        d.get('recruiter_linkedin_url'),
        d.get('subject_line'),
        d.get('message_body'),
        d.get('portal_name'),
        d.get('portal_logo'),
        d.get('portal_color'),
        json.dumps(d.get('raw_data') or {}),
    )


# ── Read ───────────────────────────────────────────────────────────────────────

def get_jobs(role_query: str, location_query: str,
             max_age_days: int = 7, limit: int = 40) -> list:
    """
    Fetch jobs matching role + location from the persistent DB.
    days_since_posted is computed live via julianday arithmetic — no stored value needed.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            j.*,
            CAST(julianday('now') - julianday(j.date_published) AS INTEGER)
                AS days_since_posted,
            GROUP_CONCAT(DISTINCT ja.attribute) AS attributes_csv,
            GROUP_CONCAT(DISTINCT jb.benefit)   AS benefits_csv
        FROM jobs j
        LEFT JOIN job_attributes ja ON ja.job_id = j.id
        LEFT JOIN job_benefits   jb ON jb.job_id = j.id
        WHERE
            j.role_query     LIKE ?
            AND j.location_query LIKE ?
            AND (
                j.date_published IS NULL
                OR CAST(julianday('now') - julianday(j.date_published) AS INTEGER) <= ?
            )
        GROUP BY j.id
        ORDER BY j.relevance_score DESC, j.date_published DESC
        LIMIT ?
    ''', (f'%{role_query}%', f'%{location_query}%', max_age_days, limit))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        job = dict(row)
        job['tech_stack']  = json.loads(job.get('tech_stack')  or '[]')
        job['raw_data']    = json.loads(job.get('raw_data')    or '{}')
        job['attributes']  = job.pop('attributes_csv', '').split(',') if job.get('attributes_csv') else []
        job['benefits']    = job.pop('benefits_csv', '').split(',')   if job.get('benefits_csv')   else []
        results.append(job)

    return results


def count_fresh_jobs(role_query: str, location_query: str, max_age_hours: int = 12) -> int:
    """
    Count jobs fetched within the last N hours.
    Used to decide whether a fresh scrape is needed.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM jobs
        WHERE role_query     LIKE ?
          AND location_query LIKE ?
          AND updated_at > datetime('now', ? || ' hours')
    ''', (f'%{role_query}%', f'%{location_query}%', f'-{max_age_hours}'))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def make_external_id(url_or_key: str) -> str:
    """Stable external ID from a URL or platform key."""
    return hashlib.md5(url_or_key.encode('utf-8')).hexdigest()
