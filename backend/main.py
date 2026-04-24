import sys
import os
import sqlite3
import json
from datetime import datetime
from threading import Thread
import time
import uuid
# Add vendor directory to path for dependencies
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vendor'))

from flask import Flask, request, jsonify
from flask_cors import CORS
from orchestrator import CareersSalesOrchestrator
from linkedin_utils import generate_linkedin_search_url

app = Flask(__name__)
CORS(app)

# Initialize orchestrator
orchestrator = CareersSalesOrchestrator()

# In-memory storage for messages
messages_db = {}

# Database configuration
DB_FILE = os.path.join(os.path.dirname(__file__), 'jobs_cache.db')

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

    # Create outreach_logs table for CRM tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outreach_logs (
            id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            job_role TEXT NOT NULL,
            recruiter_name TEXT,
            recruiter_email TEXT,
            linkedin_profile_url TEXT,
            status TEXT DEFAULT 'REQUEST_SENT',
            message_sent BOOLEAN DEFAULT 0,
            message_body TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

        cursor.execute('''
            INSERT INTO outreach_logs
            (id, company_name, job_role, recruiter_name, recruiter_email, linkedin_profile_url, status)
            VALUES (?, ?, ?, ?, ?, ?, 'REQUEST_SENT')
        ''', (outreach_id, company_name, job_role, recruiter_name, recruiter_email, linkedin_url))

        conn.commit()
        conn.close()

        print(f"[OUTREACH] Created log: {company_name} - {job_role}")
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
    """Background thread to refresh cache periodically"""
    major_roles = [
        'Backend Engineer',
        'Frontend Engineer',
        'Full Stack Engineer',
        'Data Science Engineer',
        'DevOps Engineer'
    ]

    locations = ['India', 'Bangalore']

    while True:
        try:
            print("[BACKGROUND] Starting cache refresh job...")
            for role in major_roles:
                for location in locations:
                    try:
                        print(f"[BACKGROUND] Caching {role} in {location}...")
                        result = orchestrator.run_workflow(role, location, num_results=40)
                        if result.get('results'):
                            save_jobs_to_cache(role, location, result['results'])
                        time.sleep(5)
                    except Exception as e:
                        print(f"[BACKGROUND] Error caching {role} in {location}: {e}")

            cleanup_old_jobs()
            print("[BACKGROUND] Cache refresh completed. Sleeping for 4 hours...")
            time.sleep(4 * 60 * 60)

        except Exception as e:
            print(f"[BACKGROUND] Error in cache refresh: {e}")
            time.sleep(60)


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})


@app.route('/workflow/run', methods=['POST'])
def run_workflow():
    data = request.get_json()
    role = data.get('role')
    location = data.get('location', 'India')  # Default to India for Pan-India search
    experience = data.get('experience')  # e.g., "1-3", "3-5", "5+"
    num_results = data.get('num_results', 40)

    if not role:
        return jsonify({"error": "Missing role"}), 400

    # CHECK CACHE FIRST (< 1 second)
    cached = get_cached_jobs(role, location)
    if cached:
        return jsonify(cached)

    # IF NO CACHE, SCRAPE FRESH (2-3 minutes)
    print(f"[API] No cache found. Scraping fresh jobs for {role}...")
    result = orchestrator.run_workflow(role, location, num_results, experience)

    # Save fresh results to cache for next time
    if result.get('results'):
        save_jobs_to_cache(role, location, result['results'])

    # Store messages in memory
    for msg in result.get('results', []):
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


if __name__ == '__main__':
    print("[STARTUP] Flask app starting...")
    print("[STARTUP] Initializing backend caching system...")
    init_database()

    # Start background cache refresh thread as daemon
    cache_thread = Thread(target=background_cache_refresh, daemon=True)
    cache_thread.start()
    print("[STARTUP] Background cache refresh thread started")

    app.run(debug=True, host='0.0.0.0', port=8000)
