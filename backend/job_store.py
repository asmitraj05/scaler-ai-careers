"""
job_store.py
Unified SQLite store for jobs scraped from LinkedIn and fetched from Indeed (JSearch).

Schema mirrors the target PostgreSQL DDL but uses SQLite-compatible types:
  - UUID PRIMARY KEY  → TEXT PRIMARY KEY
  - DECIMAL(10,8)     → REAL
"""

import sqlite3
import os
import uuid as _uuid
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), "jobs.db")


# ─────────────────────────── connection ────────────────────────────

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row          # lets callers do row["column"]
    return conn


# ─────────────────────────── schema ────────────────────────────────

def init_jobs_db():
    """
    Create (or migrate) the unified jobs table.
    Safe to call on every startup — uses IF NOT EXISTS.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        -- Job Basics
        id                  TEXT PRIMARY KEY,
        external_job_id     TEXT,
        title               TEXT,
        description         TEXT,
        employment_type     TEXT,
        experience_level    TEXT,
        source_portal       TEXT,
        apply_link          TEXT,
        posted_at           TEXT,

        -- Company Details
        company_name        TEXT,
        company_logo_url    TEXT,
        company_website_url TEXT,

        -- Location Details
        city                TEXT,
        state               TEXT,
        full_address        TEXT,
        latitude            REAL,
        longitude           REAL,

        -- Recruiter Details
        recruiter_name      TEXT,
        recruiter_role      TEXT,
        recruiter_linkedin  TEXT,

        -- Metadata
        created_at          TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_portal
        ON jobs(source_portal)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_company
        ON jobs(company_name)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_created_at
        ON jobs(created_at)
    """)

    conn.commit()
    conn.close()
    print("[DB] jobs table ready (unified schema)")


# ─────────────────────────── upsert ────────────────────────────────

def upsert_job(job: dict):
    """
    Insert or replace a single normalised job dict into the jobs table.
    The dict must have keys matching the column names above.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO jobs (
        id, external_job_id, title, description,
        employment_type, experience_level, source_portal,
        apply_link, posted_at,
        company_name, company_logo_url, company_website_url,
        city, state, full_address, latitude, longitude,
        recruiter_name, recruiter_role, recruiter_linkedin,
        created_at
    ) VALUES (
        :id, :external_job_id, :title, :description,
        :employment_type, :experience_level, :source_portal,
        :apply_link, :posted_at,
        :company_name, :company_logo_url, :company_website_url,
        :city, :state, :full_address, :latitude, :longitude,
        :recruiter_name, :recruiter_role, :recruiter_linkedin,
        :created_at
    )
    """, {
        "id":                   job.get("id"),
        "external_job_id":      job.get("external_job_id"),
        "title":                job.get("title"),
        "description":          job.get("description"),
        "employment_type":      job.get("employment_type"),
        "experience_level":     job.get("experience_level"),
        "source_portal":        job.get("source_portal"),
        "apply_link":           job.get("apply_link"),
        "posted_at":            job.get("posted_at"),
        "company_name":         job.get("company_name"),
        "company_logo_url":     job.get("company_logo_url"),
        "company_website_url":  job.get("company_website_url"),
        "city":                 job.get("city"),
        "state":                job.get("state"),
        "full_address":         job.get("full_address"),
        "latitude":             job.get("latitude"),
        "longitude":            job.get("longitude"),
        "recruiter_name":       job.get("recruiter_name"),
        "recruiter_role":       job.get("recruiter_role"),
        "recruiter_linkedin":   job.get("recruiter_linkedin"),
        "created_at":           datetime.utcnow().isoformat(),
    })

    conn.commit()
    conn.close()


# ─────────────────────────── normalizers ───────────────────────────

def _stable_linkedin_id(job: dict) -> str:
    """
    Derive a stable UUID from the job URL so the same LinkedIn listing
    always maps to the same primary key, regardless of how many times
    we scrape it.  Falls back to a random UUID only if no URL exists.
    """
    import hashlib
    url = job.get("job_url") or ""
    if url:
        # Deterministic UUID v5 from the URL string
        return str(_uuid.UUID(hashlib.md5(url.encode()).hexdigest()))
    return str(_uuid.uuid4())


def normalize_linkedin_job(job: dict) -> dict:
    """
    Convert a raw LinkedIn-scraped job dict (as produced by agents.py
    create_job / scrape_linkedin_jobs) into the unified schema dict.

    Expected keys:
        id, company_name, job_title, location, job_url,
        posted_date, description, tech_stack,
        portal_name (optional), posted_datetime (optional)
    """
    location_raw = job.get("location") or ""
    parts = [p.strip() for p in location_raw.split(",")]

    city  = parts[0] if len(parts) >= 1 else None
    state = parts[1] if len(parts) >= 2 else None

    return {
        # Stable ID derived from URL — same job URL = same PK every run
        "id":                   _stable_linkedin_id(job),
        "external_job_id":      job.get("job_url"),   # store URL as external ref
        "title":                job.get("job_title"),
        "description":          job.get("description"),
        "employment_type":      None,
        "experience_level":     None,
        "source_portal":        "LinkedIn",
        "apply_link":           job.get("job_url"),
        "posted_at":            job.get("posted_datetime") or job.get("posted_date"),

        "company_name":         job.get("company_name"),
        "company_logo_url":     None,
        "company_website_url":  None,

        "city":                 city,
        "state":                state,
        "full_address":         location_raw,
        "latitude":             None,
        "longitude":            None,

        "recruiter_name":       None,
        "recruiter_role":       None,
        "recruiter_linkedin":   None,
    }


def normalize_indeed_job(job: dict) -> dict:
    """
    Convert a raw JSearch / Indeed API response item into the unified
    schema dict.

    Expected keys (from JSearch):
        job_id, job_title, employer_name, employer_logo,
        employer_website, job_employment_type, job_description,
        job_apply_link, job_posted_at_datetime_utc,
        job_city, job_state, job_location,
        job_latitude, job_longitude

    Primary key strategy:
        We use Indeed's own stable job_id as `id` so re-running never
        creates duplicates — INSERT OR REPLACE on the same PK just
        overwrites the existing row.
    """
    indeed_job_id = job.get("job_id") or str(_uuid.uuid4())
    return {
        # Stable PK = Indeed's own job_id
        "id":                   indeed_job_id,
        "external_job_id":      indeed_job_id,
        "title":                job.get("job_title"),
        "description":          job.get("job_description"),
        "employment_type":      job.get("job_employment_type"),
        "experience_level":     None,
        "source_portal":        "Indeed",
        "apply_link":           job.get("job_apply_link"),
        "posted_at":            job.get("job_posted_at_datetime_utc"),

        "company_name":         job.get("employer_name"),
        "company_logo_url":     job.get("employer_logo"),
        "company_website_url":  job.get("employer_website"),

        "city":                 job.get("job_city"),
        "state":                job.get("job_state"),
        "full_address":         job.get("job_location"),
        "latitude":             job.get("job_latitude"),
        "longitude":            job.get("job_longitude"),

        "recruiter_name":       None,
        "recruiter_role":       None,
        "recruiter_linkedin":   None,
    }


# ─────────────────────────── query helpers ─────────────────────────

def get_all_jobs(limit: int = 200) -> list:
    """Return the most recent jobs from the DB as plain dicts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM jobs
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_jobs_by_portal(portal: str, limit: int = 200) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM jobs
        WHERE source_portal = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (portal, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_jobs() -> dict:
    """Quick row counts per portal — handy for health checks."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT source_portal, COUNT(*) as cnt
        FROM jobs
        GROUP BY source_portal
    """)
    rows = cursor.fetchall()
    conn.close()
    return {r["source_portal"]: r["cnt"] for r in rows}