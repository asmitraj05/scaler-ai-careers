import sys
import os
import sqlite3
import json
import hashlib
from datetime import datetime
from threading import Thread
import time
import uuid
# Add vendor directory to path for dependencies
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vendor'))

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from orchestrator import CareersSalesOrchestrator
from agents import fetch_linkedin_job_description
from linkedin_utils import generate_linkedin_search_url
from linkedin_auth import (
    get_linkedin_auth_url,
    exchange_auth_code_for_token,
    get_linkedin_profile,
    store_linkedin_auth,
    get_linkedin_connections,
    sync_outreach_with_linkedin,
    get_user_outreach_with_linkedin_status,
    extract_linkedin_id_from_url
)
import database
from indeed_fetcher import fetch_indeed_jobs

app = Flask(__name__)
CORS(app)

# Initialize orchestrator
orchestrator = CareersSalesOrchestrator()

# In-memory storage for messages
messages_db = {}

# Database configuration
DB_FILE = os.path.join(os.path.dirname(__file__), 'jobs_cache.db')

def _linkedin_date_to_iso(posted_datetime: str, posted_date: str) -> str:
    """Convert LinkedIn posted_datetime (ISO) or posted_date ('N days ago') to YYYY-MM-DD."""
    if posted_datetime:
        try:
            raw = posted_datetime.replace('Z', '+00:00')
            return datetime.fromisoformat(raw).strftime('%Y-%m-%d')
        except Exception:
            pass
    # Fallback: parse "X days ago" / "X weeks ago"
    if posted_date:
        try:
            import re
            from datetime import timedelta
            n = int(re.search(r'\d+', posted_date).group())
            if 'week' in posted_date:
                n *= 7
            elif 'month' in posted_date:
                n *= 30
            return (datetime.now() - timedelta(days=n)).strftime('%Y-%m-%d')
        except Exception:
            pass
    return datetime.now().strftime('%Y-%m-%d')


def save_orchestrator_results(role: str, location: str, results: list):
    """
    Persist orchestrator output (message objects with embedded jobs)
    into the unified jobs table.
    One DB row per result; raw_data = full message object (frontend-ready).
    """
    inserted = updated = 0
    for item in results:
        job = item.get('job') or {}
        job_url = job.get('job_url') or item.get('job_url') or ''
        if not job_url:
            continue

        external_id = database.make_external_id(job_url)
        source      = (job.get('portal_name') or 'LinkedIn').lower()

        date_iso = _linkedin_date_to_iso(
            job.get('posted_datetime', ''),
            job.get('posted_date', '')
        )

        unified = {
            'external_id':         external_id,
            'source':              source,
            'title':               job.get('job_title') or item.get('job_title', ''),
            'company_name':        job.get('company_name') or item.get('company_name', ''),
            'location':            job.get('location', ''),
            'job_url':             job_url,
            'apply_url':           None,
            'role_query':          role,
            'location_query':      location,
            'date_published':      date_iso,
            'description':         job.get('description', ''),
            'is_remote':           False,
            'job_type':            None,
            'experience_level':    None,
            'salary':              None,
            'company_rating':      None,
            'tech_stack':          job.get('tech_stack') or [],
            'relevance_score':     item.get('relevance_score', 0.85),
            'reason':              item.get('reason', ''),
            'recruiter_name':      item.get('recruiter_name', ''),
            'recruiter_email':     item.get('recruiter_email', ''),
            'recruiter_title':     None,
            'recruiter_linkedin_url': None,
            'subject_line':        item.get('subject_line', ''),
            'message_body':        item.get('message_body', ''),
            'portal_name':         job.get('portal_name', 'LinkedIn'),
            'portal_logo':         job.get('portal_logo', ''),
            'portal_color':        job.get('portal_color', ''),
            'raw_data':            item,
        }

        _, action = database.upsert_job(unified)
        if action == 'inserted':
            inserted += 1
        else:
            updated += 1

    print(f"[DB] Orchestrator results saved — inserted: {inserted}, updated: {updated}")


def init_database():
    """Initialize SQLite database for caching"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cached_jobs (
            id TEXT PRIMARY KEY,
            role TEXT NOT NULL,
            location TEXT NOT NULL,
            platform TEXT DEFAULT 'LinkedIn',
            company TEXT,
            job_title TEXT,
            posted_date TEXT,
            experience TEXT,
            recruiter_name TEXT,
            recruiter_email TEXT,
            job_url TEXT,
            relevance_score REAL,
            reason TEXT,
            recruiter_title TEXT,
            message_body TEXT,
            subject_line TEXT,
            tech_stack TEXT,
            full_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_role_location
        ON cached_jobs(role, location)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_created_at
        ON cached_jobs(created_at)
    ''')

    # Create user_linkedin_auth table for storing LinkedIn OAuth tokens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_linkedin_auth (
            id TEXT PRIMARY KEY,
            user_id TEXT UNIQUE,
            linkedin_id TEXT,
            linkedin_name TEXT,
            linkedin_email TEXT,
            linkedin_profile_url TEXT,
            access_token TEXT,
            refresh_token TEXT,
            token_expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create outreach_logs table for CRM tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outreach_logs (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            company_name TEXT NOT NULL,
            job_role TEXT NOT NULL,
            recruiter_name TEXT,
            recruiter_email TEXT,
            recruiter_linkedin_id TEXT,
            linkedin_profile_url TEXT,
            status TEXT DEFAULT 'REQUEST_SENT',
            linkedin_connection_status TEXT,
            last_synced_at TIMESTAMP,
            message_sent BOOLEAN DEFAULT 0,
            message_body TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES user_linkedin_auth(user_id)
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_outreach_status
        ON outreach_logs(status)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_outreach_created_at
        ON outreach_logs(created_at)
    ''')

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully")
    print("[DB] Outreach tracking table ready")

def get_cached_jobs(role: str, location: str) -> dict:
    """Get cached jobs from database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        query = '''
            SELECT full_data FROM cached_jobs
            WHERE role = ? AND location = ?
            AND created_at > datetime('now', '-7 days')
            ORDER BY created_at DESC
            LIMIT 40
        '''

        cursor.execute(query, (role, location))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            jobs = [json.loads(row[0]) for row in rows]
            print(f"[CACHE] HIT: Found {len(jobs)} cached jobs for {role} in {location}")
            return {
                "results": jobs,
                "source": "cache",
                "cached_at": datetime.now().isoformat(),
                "from_cache": True
            }

        print(f"[CACHE] MISS: No cached jobs for {role} in {location}")
        return None

    except Exception as e:
        print(f"[CACHE] Error reading cache: {e}")
        return None

def save_jobs_to_cache(role: str, location: str, jobs_data: list):
    """Save jobs to cache"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        for job in jobs_data:
            cursor.execute('''
                INSERT OR REPLACE INTO cached_jobs
                (id, role, location, company, job_title, posted_date,
                 experience, recruiter_name, recruiter_email, job_url,
                 relevance_score, reason, recruiter_title, message_body,
                 subject_line, tech_stack, full_data, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                job.get('id'),
                role,
                location,
                job.get('company_name'),
                job.get('job_title'),
                job.get('posted_date'),
                job.get('experience'),
                job.get('recruiter_name'),
                job.get('email'),
                job.get('job_url'),
                job.get('relevance_score'),
                job.get('reason'),
                job.get('recruiter_title'),
                job.get('message_body'),
                job.get('subject_line'),
                json.dumps(job.get('tech_stack', [])),
                json.dumps(job)
            ))

        conn.commit()
        conn.close()
        print(f"[CACHE] Saved {len(jobs_data)} jobs to cache for {role}")

    except Exception as e:
        print(f"[CACHE] Error saving to cache: {e}")

def cleanup_old_jobs():
    """Delete jobs older than 7 days"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM cached_jobs
            WHERE created_at < datetime('now', '-7 days')
        ''')

        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"[CACHE] Cleanup: Deleted {deleted} old jobs")

    except Exception as e:
        print(f"[CACHE] Error during cleanup: {e}")

# ============ OUTREACH TRACKING ============

def create_outreach_log(company_name: str, job_role: str, recruiter_name: str,
                       recruiter_email: str = None, linkedin_url: str = None) -> dict:
    """Create a new outreach log entry"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        outreach_id = str(uuid.uuid4())
        # Extract LinkedIn ID from the recruiter's profile URL
        recruiter_linkedin_id = extract_linkedin_id_from_url(linkedin_url) if linkedin_url else None

        cursor.execute('''
            INSERT INTO outreach_logs
            (id, company_name, job_role, recruiter_name, recruiter_email, recruiter_linkedin_id,
             linkedin_profile_url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'REQUEST_SENT')
        ''', (outreach_id, company_name, job_role, recruiter_name, recruiter_email,
              recruiter_linkedin_id, linkedin_url))

        conn.commit()
        conn.close()

        print(f"[OUTREACH] Created log: {company_name} - {job_role} (LinkedIn ID: {recruiter_linkedin_id})")
        return {
            "id": outreach_id,
            "status": "success",
            "message": "Outreach logged successfully"
        }

    except Exception as e:
        print(f"[OUTREACH] Error creating log: {e}")
        return {"status": "error", "message": str(e)}

def update_outreach_status(outreach_id: str, status: str) -> dict:
    """Update outreach log status"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE outreach_logs
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, outreach_id))

        conn.commit()
        conn.close()

        print(f"[OUTREACH] Updated status to {status} for {outreach_id}")
        return {"status": "success", "message": f"Updated to {status}"}

    except Exception as e:
        print(f"[OUTREACH] Error updating status: {e}")
        return {"status": "error", "message": str(e)}

def get_outreach_logs() -> list:
    """Get all outreach logs"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, company_name, job_role, recruiter_name, recruiter_email,
                   linkedin_profile_url, status, message_sent, created_at, updated_at
            FROM outreach_logs
            ORDER BY created_at DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        logs = []
        for row in rows:
            logs.append({
                "id": row[0],
                "company_name": row[1],
                "job_role": row[2],
                "recruiter_name": row[3],
                "recruiter_email": row[4],
                "linkedin_profile_url": row[5],
                "status": row[6],
                "message_sent": bool(row[7]),
                "created_at": row[8],
                "updated_at": row[9]
            })

        return logs

    except Exception as e:
        print(f"[OUTREACH] Error fetching logs: {e}")
        return []

def get_outreach_stats() -> dict:
    """Get outreach dashboard statistics"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Total requests sent today
        cursor.execute('''
            SELECT COUNT(*) FROM outreach_logs
            WHERE DATE(created_at) = DATE('now')
        ''')
        sent_today = cursor.fetchone()[0]

        # Total connected
        cursor.execute('''
            SELECT COUNT(*) FROM outreach_logs
            WHERE status = 'CONNECTED'
        ''')
        connected = cursor.fetchone()[0]

        # Messages sent
        cursor.execute('''
            SELECT COUNT(*) FROM outreach_logs
            WHERE status = 'MESSAGE_SENT'
        ''')
        messages_sent = cursor.fetchone()[0]

        # Pending (REQUEST_SENT but not connected)
        cursor.execute('''
            SELECT COUNT(*) FROM outreach_logs
            WHERE status = 'REQUEST_SENT'
        ''')
        pending = cursor.fetchone()[0]

        # Total all time
        cursor.execute('''
            SELECT COUNT(*) FROM outreach_logs
        ''')
        total_all_time = cursor.fetchone()[0]

        conn.close()

        return {
            "sent_today": sent_today,
            "connected": connected,
            "messages_sent": messages_sent,
            "pending": pending,
            "total_all_time": total_all_time
        }

    except Exception as e:
        print(f"[OUTREACH] Error getting stats: {e}")
        return {}

def background_cache_refresh():
    """
    Background thread — runs on startup, refreshes every 4 hours.
    For each role × location:
      1. LinkedIn via orchestrator  → persistent DB + legacy cached_jobs
      2. Indeed via RapidAPI        → persistent DB only
    """
    major_roles = [
        'Backend Engineer',
        'Frontend Engineer',
        'Full Stack Engineer',
        'Data Science Engineer',
        'DevOps Engineer',
        'Mobile Developer',
        'Cloud Engineer',
    ]
    locations = ['India', 'Bangalore']

    while True:
        try:
            print("[BACKGROUND] Starting refresh cycle…")
            for role in major_roles:
                for location in locations:
                    # ── LinkedIn via orchestrator ──────────────────────────────
                    try:
                        print(f"[BACKGROUND] LinkedIn: {role} / {location}")
                        result = orchestrator.run_workflow(role, location, num_results=40)
                        if result.get('results'):
                            save_jobs_to_cache(role, location, result['results'])
                            save_orchestrator_results(role, location, result['results'])
                    except Exception as exc:
                        print(f"[BACKGROUND] LinkedIn error ({role}/{location}): {exc}")
                    time.sleep(3)

                    # ── Indeed via RapidAPI ────────────────────────────────────
                    try:
                        print(f"[BACKGROUND] Indeed: {role} / {location}")
                        indeed_jobs = fetch_indeed_jobs(role, location, max_rows=50, from_days=7)
                        ins = upd = 0
                        for job in indeed_jobs:
                            _, action = database.upsert_job(job)
                            if action == 'inserted': ins += 1
                            else: upd += 1
                        print(f"[BACKGROUND] Indeed saved — inserted: {ins}, updated: {upd}")
                    except Exception as exc:
                        print(f"[BACKGROUND] Indeed error ({role}/{location}): {exc}")
                    time.sleep(3)

            cleanup_old_jobs()
            print("[BACKGROUND] Cycle complete. Sleeping 4 hours…")
            time.sleep(4 * 60 * 60)

        except Exception as exc:
            print(f"[BACKGROUND] Unexpected error: {exc}")
            time.sleep(60)


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})


@app.route('/workflow/run', methods=['POST'])
def run_workflow():
    data        = request.get_json()
    role        = data.get('role')
    location    = data.get('location', 'India')
    experience  = data.get('experience')
    num_results = data.get('num_results', 40)

    if not role:
        return jsonify({"error": "Missing role"}), 400

    # ── 1. Try persistent DB first (jobs fetched in last 12 hours) ─────────────
    fresh_count = database.count_fresh_jobs(role, location, max_age_hours=12)
    if fresh_count >= 5:
        db_jobs = database.get_jobs(role, location, max_age_days=7, limit=num_results)
        results = [j['raw_data'] for j in db_jobs if j.get('raw_data')]
        if results:
            print(f"[API] DB hit — {len(results)} jobs for '{role}' in '{location}'")
            for msg in results:
                if isinstance(msg, dict) and msg.get('id'):
                    messages_db[msg['id']] = msg
            return jsonify({
                "results": results,
                "source": "database",
                "from_cache": True,
                "total_jobs_found": len(results),
                "relevant_jobs": len(results),
            })

    # ── 2. Legacy SQLite cache (< 7 days) ─────────────────────────────────────
    cached = get_cached_jobs(role, location)
    if cached:
        print(f"[API] Legacy cache hit for '{role}' in '{location}'")
        for msg in cached.get('results', []):
            if isinstance(msg, dict) and msg.get('id'):
                messages_db[msg['id']] = msg
        return jsonify(cached)

    # ── 3. Fresh scrape via orchestrator ──────────────────────────────────────
    print(f"[API] No data found — running fresh scrape for '{role}' in '{location}'…")
    result = orchestrator.run_workflow(role, location, num_results, experience)

    if result.get('results'):
        # Save to both stores
        save_jobs_to_cache(role, location, result['results'])
        save_orchestrator_results(role, location, result['results'])
        # Cache in memory
        for msg in result['results']:
            if isinstance(msg, dict) and msg.get('id'):
                messages_db[msg['id']] = msg

    return jsonify(result)


@app.route('/messages', methods=['GET'])
def get_all_messages():
    return jsonify(list(messages_db.values()))


@app.route('/messages/<message_id>', methods=['GET'])
def get_message(message_id):
    if message_id not in messages_db:
        return jsonify({"error": "Message not found"}), 404
    return jsonify(messages_db[message_id])


@app.route('/messages/<message_id>', methods=['PUT'])
def update_message(message_id):
    if message_id not in messages_db:
        return jsonify({"error": "Message not found"}), 404

    data = request.get_json()
    msg = messages_db[message_id]

    # Store original if first edit
    if not msg.get('edited_by_user'):
        msg['original_message'] = f"Subject: {msg['subject_line']}\n\n{msg['message_body']}"
        msg['edited_by_user'] = True

    if 'subject_line' in data:
        msg['subject_line'] = data['subject_line']
    if 'message_body' in data:
        msg['message_body'] = data['message_body']

    messages_db[message_id] = msg
    return jsonify(msg)


@app.route('/messages/<message_id>/approve', methods=['POST'])
def approve_message(message_id):
    if message_id not in messages_db:
        return jsonify({"error": "Message not found"}), 404

    msg = messages_db[message_id]
    msg['approval_status'] = 'approved'
    messages_db[message_id] = msg
    return jsonify(msg)


@app.route('/messages/<message_id>/reject', methods=['POST'])
def reject_message(message_id):
    if message_id not in messages_db:
        return jsonify({"error": "Message not found"}), 404

    msg = messages_db[message_id]
    msg['approval_status'] = 'rejected'
    messages_db[message_id] = msg
    return jsonify(msg)


@app.route('/stats', methods=['GET'])
def get_stats():
    all_messages = list(messages_db.values())

    approved = sum(1 for m in all_messages if m.get('approval_status') == 'approved')
    rejected = sum(1 for m in all_messages if m.get('approval_status') == 'rejected')
    pending = sum(1 for m in all_messages if m.get('approval_status') == 'pending')

    return jsonify({
        "total_messages": len(all_messages),
        "approved": approved,
        "pending": pending,
        "rejected": rejected,
        "approval_rate": approved / len(all_messages) if all_messages else 0
    })


@app.route('/job-description', methods=['GET'])
def get_job_description():
    """Fetch actual job description from the job platform URL."""
    job_url = request.args.get('url')
    if not job_url:
        return jsonify({"error": "url parameter required"}), 400
    description = fetch_linkedin_job_description(job_url)
    if description:
        return jsonify({"description": description}), 200
    return jsonify({"description": None}), 200


@app.route('/linkedin/search-url', methods=['POST'])
def generate_linkedin_url():
    """
    Generate a smart LinkedIn People Search URL based on job context

    Request body:
    {
        "company": "Razorpay",
        "job_title": "Senior Backend Engineer",  (optional)
        "location": "Bangalore"  (optional)
    }

    Response:
    {
        "url": "https://www.linkedin.com/search/results/people/?...",
        "keywords": "HR OR Recruiter OR Engineering Manager",
        "company": "Razorpay"
    }
    """
    try:
        data = request.get_json()
        company = data.get('company')
        job_title = data.get('job_title')
        location = data.get('location')

        if not company:
            return jsonify({"error": "Company name is required"}), 400

        # Generate LinkedIn URL
        url = generate_linkedin_search_url(
            company=company,
            job_title=job_title,
            location=location
        )

        # Also return the keywords used for transparency
        from linkedin_utils import get_recruiter_keywords
        keywords = get_recruiter_keywords(job_title)

        return jsonify({
            "url": url,
            "keywords": keywords,
            "company": company,
            "job_title": job_title or "Not specified",
            "location": location or "Not specified"
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to generate URL: {str(e)}"}), 500


# ============ OUTREACH TRACKING ENDPOINTS ============

@app.route('/create-outreach', methods=['POST'])
def create_outreach():
    """Log a new outreach action when user clicks Connect"""
    try:
        data = request.get_json()
        company_name = data.get('company_name')
        job_role = data.get('job_role')
        recruiter_name = data.get('recruiter_name')
        recruiter_email = data.get('recruiter_email')
        linkedin_url = data.get('linkedin_url')

        if not company_name or not job_role:
            return jsonify({"error": "Company name and job role are required"}), 400

        result = create_outreach_log(
            company_name=company_name,
            job_role=job_role,
            recruiter_name=recruiter_name,
            recruiter_email=recruiter_email,
            linkedin_url=linkedin_url
        )

        if result.get('status') == 'success':
            return jsonify({
                "status": "success",
                "outreach_id": result.get('id'),
                "message": "Outreach logged successfully"
            }), 201
        else:
            return jsonify(result), 500

    except Exception as e:
        print(f"[API] Error creating outreach: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/update-outreach-status', methods=['POST'])
def update_status():
    """Update outreach log status"""
    try:
        data = request.get_json()
        outreach_id = data.get('id')
        status = data.get('status')

        if not outreach_id or not status:
            return jsonify({"error": "ID and status are required"}), 400

        if status not in ['REQUEST_SENT', 'CONNECTED', 'MESSAGE_SENT', 'NOT_CONTACTED']:
            return jsonify({"error": "Invalid status"}), 400

        result = update_outreach_status(outreach_id, status)
        return jsonify(result), 200

    except Exception as e:
        print(f"[API] Error updating status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/outreach-dashboard', methods=['GET'])
def get_dashboard():
    """Get all outreach logs for dashboard"""
    try:
        logs = get_outreach_logs()
        stats = get_outreach_stats()

        return jsonify({
            "status": "success",
            "stats": stats,
            "logs": logs
        }), 200

    except Exception as e:
        print(f"[API] Error getting dashboard: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/outreach-stats', methods=['GET'])
def get_stats_endpoint():
    """Get outreach statistics only"""
    try:
        stats = get_outreach_stats()
        return jsonify(stats), 200

    except Exception as e:
        print(f"[API] Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500


# ============ LINKEDIN OAUTH ENDPOINTS ============

@app.route('/auth/linkedin/login', methods=['POST'])
def linkedin_login():
    """Generate LinkedIn OAuth authorization URL"""
    try:
        auth_url = get_linkedin_auth_url()
        print(f"[AUTH] Generated LinkedIn auth URL")
        return jsonify({
            "status": "success",
            "auth_url": auth_url
        }), 200

    except Exception as e:
        print(f"[AUTH] Error generating auth URL: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/auth/linkedin/callback', methods=['GET'])
def linkedin_callback():
    """Handle LinkedIn OAuth callback"""
    try:
        auth_code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        error_description = request.args.get('error_description')

        if error:
            print(f"[AUTH] LinkedIn auth error: {error} - {error_description}")
            return redirect(f'http://localhost:3000?auth_error={error}&error_description={error_description}')

        if not auth_code:
            print("[AUTH] No authorization code received")
            return redirect('http://localhost:3000?auth_error=no_code')

        # Exchange code for access token
        token_data = exchange_auth_code_for_token(auth_code)
        if not token_data:
            print("[AUTH] Failed to exchange auth code for token")
            return redirect('http://localhost:3000?auth_error=token_exchange_failed')

        # Get user's LinkedIn profile
        access_token = token_data.get('access_token')
        linkedin_profile = get_linkedin_profile(access_token)
        if not linkedin_profile:
            print("[AUTH] Failed to fetch LinkedIn profile")
            return redirect('http://localhost:3000?auth_error=profile_fetch_failed')

        # Store LinkedIn auth data in database
        user_id = linkedin_profile.get('id')
        auth_id = store_linkedin_auth(user_id, linkedin_profile, token_data)

        if not auth_id:
            print("[AUTH] Failed to store LinkedIn auth")
            return redirect('http://localhost:3000?auth_error=storage_failed')

        print(f"[AUTH] LinkedIn user {user_id} authenticated successfully")
        # Redirect back to frontend with user_id
        return redirect(f'http://localhost:3000?auth_success=true&user_id={user_id}&name={linkedin_profile.get("localizedFirstName", "")}')

    except Exception as e:
        print(f"[AUTH] Error handling LinkedIn callback: {e}")
        return redirect(f'http://localhost:3000?auth_error=server_error&error_message={str(e)}')


@app.route('/associate-outreach-with-user', methods=['POST'])
def associate_outreach_with_user():
    """Associate recent outreach logs with a LinkedIn user after authentication"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Associate recent outreach logs (last 30 minutes) that don't have a user_id yet
        cursor.execute('''
            UPDATE outreach_logs
            SET user_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id IS NULL
            AND created_at > datetime('now', '-30 minutes')
        ''', (user_id,))

        associated_count = cursor.rowcount
        conn.commit()
        conn.close()

        print(f"[ASSOCIATE] Associated {associated_count} outreach logs with user {user_id}")
        return jsonify({
            "status": "success",
            "associated_count": associated_count,
            "message": f"Associated {associated_count} outreach logs with LinkedIn user"
        }), 200

    except Exception as e:
        print(f"[ASSOCIATE] Error associating outreach: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/sync-linkedin-connections', methods=['POST'])
def sync_connections():
    """Sync outreach logs with real LinkedIn connection status"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        # Perform sync
        success = sync_outreach_with_linkedin(user_id)

        if success:
            print(f"[SYNC] Successfully synced connections for user {user_id}")
            return jsonify({
                "status": "success",
                "message": f"Synced LinkedIn connections for user {user_id}"
            }), 200
        else:
            print(f"[SYNC] Failed to sync connections for user {user_id}")
            return jsonify({
                "status": "error",
                "error": "Failed to sync connections"
            }), 500

    except Exception as e:
        print(f"[SYNC] Error syncing connections: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/outreach-dashboard-with-linkedin', methods=['GET'])
def get_dashboard_with_linkedin():
    """Get all outreach logs with real LinkedIn connection status"""
    try:
        user_id = request.args.get('user_id')

        if not user_id:
            return jsonify({"error": "user_id query parameter is required"}), 400

        # Get logs with real LinkedIn status
        logs = get_user_outreach_with_linkedin_status(user_id)

        # Still get stats for dashboard
        stats = get_outreach_stats()

        return jsonify({
            "status": "success",
            "stats": stats,
            "logs": logs
        }), 200

    except Exception as e:
        print(f"[API] Error getting dashboard with LinkedIn: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("[STARTUP] Flask app starting…")

    # Legacy tables (outreach_logs, user_linkedin_auth, cached_jobs)
    init_database()

    # Persistent unified jobs table (LinkedIn + Indeed)
    database.init_jobs_table()

    # Background refresh — LinkedIn + Indeed every 4 hours
    cache_thread = Thread(target=background_cache_refresh, daemon=True)
    cache_thread.start()
    print("[STARTUP] Background refresh thread started")

    app.run(debug=True, host='0.0.0.0', port=8000)
