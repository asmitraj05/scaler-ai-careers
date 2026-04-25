"""
Indeed Scraper API integration (RapidAPI).
Fetches jobs, maps them to the unified schema, and returns
dicts ready for database.upsert_job().
"""

import os
import uuid
import json
import requests
from datetime import datetime, timezone
from database import make_external_id

# ── Config ─────────────────────────────────────────────────────────────────────

RAPIDAPI_KEY  = os.getenv('RAPIDAPI_KEY', '9efa73397emshfa37381af46489bp1bd04ajsn310682b4b025')
INDEED_URL    = 'https://indeed-scraper-api.p.rapidapi.com/api/job'

HEADERS = {
    'Content-Type':    'application/json',
    'x-rapidapi-host': 'indeed-scraper-api.p.rapidapi.com',
    'x-rapidapi-key':  RAPIDAPI_KEY,
}

# ── Tech keyword extractor ─────────────────────────────────────────────────────

_TECH_KEYWORDS = [
    'python', 'java', 'javascript', 'typescript', 'react', 'node', 'angular', 'vue',
    'django', 'flask', 'fastapi', 'spring', 'aws', 'azure', 'gcp', 'docker',
    'kubernetes', 'terraform', 'sql', 'postgresql', 'mysql', 'mongodb', 'redis',
    'kafka', 'spark', 'hadoop', 'tensorflow', 'pytorch', 'scikit', 'go', 'golang',
    'rust', 'scala', 'kotlin', 'swift', 'c++', 'c#', '.net', 'rails', 'laravel',
    'php', 'elasticsearch', 'graphql', 'grpc', 'rabbitmq', 'celery',
]

def _extract_tech(text: str) -> list:
    if not text:
        return []
    lower = text.lower()
    return [kw for kw in _TECH_KEYWORDS if kw in lower][:8]


# ── Date parsing ───────────────────────────────────────────────────────────────

def _parse_date(raw: str) -> str:
    """
    Parse an ISO datetime string (e.g. '2024-01-15T00:00:00Z')
    into YYYY-MM-DD for storage. Returns None on failure.
    """
    if not raw:
        return None
    try:
        raw_clean = raw.replace('Z', '+00:00')
        dt = datetime.fromisoformat(raw_clean)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        pass
    # Try plain date
    try:
        return datetime.strptime(raw[:10], '%Y-%m-%d').strftime('%Y-%m-%d')
    except Exception:
        return None


# ── Generic outreach message for Indeed jobs ───────────────────────────────────

def _default_message(company: str, title: str, role_query: str) -> str:
    return (
        f"Hi,\n\n"
        f"I came across the {title} opening at {company} and I'm very interested. "
        f"My background in {role_query} aligns closely with what you're looking for, "
        f"and I'd love the opportunity to contribute to your team.\n\n"
        f"Would you be open to a quick call to discuss further?\n\n"
        f"Best regards"
    )

def _default_subject(company: str, title: str) -> str:
    return f"Interested in {title} role at {company}"


# ── Main fetch function ────────────────────────────────────────────────────────

def fetch_indeed_jobs(role: str, location: str,
                      max_rows: int = 50,
                      from_days: int = 7) -> list:
    """
    Call the Indeed Scraper API and return a list of unified job dicts
    ready for database.upsert_job().
    """
    payload = {
        "scraper": {
            "maxRows": max_rows,
            "query": role,
            "location": location,
            "jobType": "fulltime",
            "radius": "50",
            "sort": "relevance",
            "fromDays": str(from_days),
            "country": "in",
        }
    }

    try:
        print(f"[Indeed] Fetching '{role}' in '{location}' (last {from_days} days)…")
        resp = requests.post(INDEED_URL, headers=HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"[Indeed] API error: {exc}")
        return []

    # ── Normalise response envelope ────────────────────────────────────────────
    raw_jobs: list = []
    if isinstance(data, list):
        raw_jobs = data
    elif isinstance(data, dict):
        raw_jobs = (
            data.get('jobs')
            or data.get('data', {}).get('jobs')
            or data.get('results')
            or []
        )

    print(f"[Indeed] Raw jobs received: {len(raw_jobs)}")

    unified = []
    inserted = updated = skipped = 0

    for raw in raw_jobs:
        job_key = (
            raw.get('jobKey')
            or raw.get('job_key')
            or raw.get('jobId')
            or raw.get('id')
        )
        if not job_key:
            skipped += 1
            continue

        external_id    = make_external_id(f"indeed_{job_key}")
        date_published = _parse_date(
            raw.get('datePublished')
            or raw.get('date_published')
            or raw.get('date')
        )

        company = raw.get('companyName') or raw.get('company_name') or ''
        title   = raw.get('title') or raw.get('job_title') or ''
        desc    = raw.get('descriptionText') or raw.get('description') or ''
        job_url = raw.get('jobUrl') or raw.get('job_url') or ''

        tech_stack = _extract_tech(desc)

        # Attributes & benefits — can be list or comma string
        def _listify(val):
            if not val:
                return []
            if isinstance(val, list):
                return [str(v) for v in val if v]
            return [str(val)]

        attributes = _listify(raw.get('attributes'))
        benefits   = _listify(raw.get('benefits'))

        # ── Frontend-compatible raw_data object ────────────────────────────────
        # Mirrors the outreach message structure the frontend expects.
        inner_job_id = str(uuid.uuid4())
        message_id   = str(uuid.uuid4())

        raw_data = {
            'id':             message_id,
            'job_id':         inner_job_id,
            'company_name':   company,
            'job_title':      title,
            'recruiter_name': 'Hiring Team',
            'recruiter_email': '',
            'subject_line':   _default_subject(company, title),
            'message_body':   _default_message(company, title, role),
            'approval_status': 'pending',
            'edited_by_user': False,
            'original_message': '',
            'job_url':        job_url,
            # ── Embedded job object ──────────────────────────────────────────
            'job': {
                'id':             inner_job_id,
                'company_name':   company,
                'job_title':      title,
                'location':       raw.get('location') or location,
                'job_url':        job_url,
                'apply_url':      raw.get('applyUrl') or raw.get('apply_url') or '',
                'posted_date':    f"{(datetime.now() - datetime.strptime(date_published, '%Y-%m-%d')).days} days ago"
                                  if date_published else 'Recently',
                'posted_datetime': date_published or '',
                'description':    desc,
                'tech_stack':     tech_stack,
                'portal_name':    'Indeed',
                'portal_logo':    '🔵',
                'portal_color':   '#003A9B',
                'relevance_score': 0.80,
                'reason':         f'Matches your {role} search on Indeed',
                'salary':         raw.get('salary') or '',
                'company_rating': raw.get('rating'),
                'is_remote':      bool(raw.get('isRemote') or raw.get('is_remote')),
                'attributes':     attributes,
                'benefits':       benefits,
                'source':         'indeed',
            },
            # Top-level convenience fields (used by some frontend components)
            'company':        company,
            'role':           title,
            'location':       raw.get('location') or location,
            'platform':       'Indeed',
            'jobUrl':         job_url,
            'postedDate':     f"{(datetime.now() - datetime.strptime(date_published, '%Y-%m-%d')).days} days ago"
                              if date_published else 'Recently',
            'experience':     '',
            'relevanceScore': 0.80,
            'reason':         f'Matches your {role} search on Indeed',
            'tech_stack':     tech_stack,
            'recruiter': {
                'name':       'Hiring Team',
                'role':       'Talent Acquisition',
                'email':      '',
                'linkedinUrl': '',
                'confidence': 0.50,
            },
            'salary':         raw.get('salary') or '',
            'isRemote':       bool(raw.get('isRemote') or raw.get('is_remote')),
            'source':         'indeed',
        }

        unified.append({
            'external_id':   external_id,
            'source':        'indeed',
            'title':         title,
            'company_name':  company,
            'location':      raw.get('location') or location,
            'job_url':       job_url,
            'apply_url':     raw.get('applyUrl') or raw.get('apply_url') or '',
            'role_query':    role,
            'location_query': location,
            'date_published': date_published,
            'description':   desc,
            'is_remote':     bool(raw.get('isRemote') or raw.get('is_remote')),
            'job_type':      'fulltime',
            'salary':        raw.get('salary') or '',
            'company_rating': raw.get('rating'),
            'tech_stack':    tech_stack,
            'relevance_score': 0.80,
            'reason':        f'Matches your {role} search on Indeed',
            'recruiter_name': 'Hiring Team',
            'recruiter_email': '',
            'recruiter_title': 'Talent Acquisition',
            'subject_line':  _default_subject(company, title),
            'message_body':  _default_message(company, title, role),
            'portal_name':   'Indeed',
            'portal_logo':   '🔵',
            'portal_color':  '#003A9B',
            'attributes':    attributes,
            'benefits':      benefits,
            'raw_data':      raw_data,
        })

    print(f"[Indeed] Parsed {len(unified)} jobs (skipped {skipped} with no key)")
    return unified
