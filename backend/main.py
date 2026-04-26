"""
main.py
Flask backend for the Scaler Careers Sales tool.

Background refresh strategy
────────────────────────────
For each (role, location) pair we spin up TWO daemon threads:
  • LinkedIn thread  – scrapes LinkedIn guest API via BeautifulSoup
  • Indeed thread    – hits JSearch/RapidAPI for Indeed jobs

Both threads run once at startup, then sleep 4 hours and repeat.
Jobs land directly in jobs.db via upsert_job() in job_store.py.
"""

import sys
import os
import sqlite3
import json
from datetime import datetime
from threading import Thread
import time
import uuid

# ── vendor path ──────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vendor"))

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS

from job_store import (
    init_jobs_db,
    normalize_indeed_job,
    upsert_job,
    get_all_jobs,
    get_jobs_by_portal,
    count_jobs,
)
from orchestrator import CareersSalesOrchestrator
from linkedin_utils import generate_linkedin_search_url
from agents import scrape_linkedin_jobs, fetch_indeed_jobs

# Optional LinkedIn auth module (may not exist in all deployments)
try:
    from linkedin_auth import (
        get_linkedin_auth_url,
        exchange_auth_code_for_token,
        get_linkedin_profile,
        store_linkedin_auth,
        get_linkedin_connections,
        sync_outreach_with_linkedin,
        get_user_outreach_with_linkedin_status,
        extract_linkedin_id_from_url,
    )
    LINKEDIN_AUTH_AVAILABLE = True
except ImportError:
    LINKEDIN_AUTH_AVAILABLE = False
    print("[STARTUP] linkedin_auth module not found — OAuth endpoints disabled")

# ── app setup ────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

orchestrator = CareersSalesOrchestrator()
messages_db: dict = {}          # in-memory store for outreach messages

DB_FILE = os.path.join(os.path.dirname(__file__), "jobs.db")

# ── roles & locations to pre-warm ────────────────────────────────────
BACKGROUND_ROLES = [
    "Backend Engineer",
    "Frontend Engineer",
    "Full Stack Engineer",
    "Data Science Engineer",
    "DevOps Engineer",
]

REFRESH_INTERVAL_SECONDS = 4 * 60 * 60   # 4 hours


# ════════════════════════════════════════════════════════════════════
#  Outreach log helpers (SQLite outreach_logs table)
# ════════════════════════════════════════════════════════════════════

def _ensure_outreach_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outreach_logs (
            id                      TEXT PRIMARY KEY,
            user_id                 TEXT,
            company_name            TEXT NOT NULL,
            job_role                TEXT NOT NULL,
            recruiter_name          TEXT,
            recruiter_email         TEXT,
            recruiter_linkedin_id   TEXT,
            linkedin_profile_url    TEXT,
            status                  TEXT DEFAULT 'REQUEST_SENT',
            linkedin_connection_status TEXT,
            last_synced_at          TEXT,
            message_sent            INTEGER DEFAULT 0,
            message_body            TEXT,
            created_at              TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at              TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_outreach_status
        ON outreach_logs(status)
    """)
    conn.commit()
    conn.close()


def create_outreach_log(
    company_name: str,
    job_role: str,
    recruiter_name: str,
    recruiter_email: str = None,
    linkedin_url: str = None,
) -> dict:
    try:
        conn   = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        outreach_id          = str(uuid.uuid4())
        recruiter_linkedin_id = None
        if linkedin_url and LINKEDIN_AUTH_AVAILABLE:
            recruiter_linkedin_id = extract_linkedin_id_from_url(linkedin_url)

        cursor.execute("""
            INSERT INTO outreach_logs
            (id, company_name, job_role, recruiter_name, recruiter_email,
             recruiter_linkedin_id, linkedin_profile_url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'REQUEST_SENT')
        """, (
            outreach_id, company_name, job_role, recruiter_name,
            recruiter_email, recruiter_linkedin_id, linkedin_url,
        ))

        conn.commit()
        conn.close()
        print(f"[OUTREACH] Created log: {company_name} — {job_role}")
        return {"id": outreach_id, "status": "success", "message": "Outreach logged"}

    except Exception as e:
        print(f"[OUTREACH] Error creating log: {e}")
        return {"status": "error", "message": str(e)}


def update_outreach_status(outreach_id: str, status: str) -> dict:
    try:
        conn   = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE outreach_logs
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, outreach_id))
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Updated to {status}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_outreach_logs() -> list:
    try:
        conn   = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, company_name, job_role, recruiter_name, recruiter_email,
                   linkedin_profile_url, status, message_sent, created_at, updated_at
            FROM outreach_logs
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": r[0], "company_name": r[1], "job_role": r[2],
                "recruiter_name": r[3], "recruiter_email": r[4],
                "linkedin_profile_url": r[5], "status": r[6],
                "message_sent": bool(r[7]), "created_at": r[8], "updated_at": r[9],
            }
            for r in rows
        ]
    except Exception as e:
        print(f"[OUTREACH] Error fetching logs: {e}")
        return []


def get_outreach_stats() -> dict:
    try:
        conn   = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        def _count(query, params=()):
            cursor.execute(query, params)
            return cursor.fetchone()[0]

        stats = {
            "sent_today":    _count("SELECT COUNT(*) FROM outreach_logs WHERE DATE(created_at) = DATE('now')"),
            "connected":     _count("SELECT COUNT(*) FROM outreach_logs WHERE status = 'CONNECTED'"),
            "messages_sent": _count("SELECT COUNT(*) FROM outreach_logs WHERE status = 'MESSAGE_SENT'"),
            "pending":       _count("SELECT COUNT(*) FROM outreach_logs WHERE status = 'REQUEST_SENT'"),
            "total_all_time":_count("SELECT COUNT(*) FROM outreach_logs"),
        }
        conn.close()
        return stats
    except Exception as e:
        print(f"[OUTREACH] Error getting stats: {e}")
        return {}


# ════════════════════════════════════════════════════════════════════
#  Background refresh threads
# ════════════════════════════════════════════════════════════════════

def _role_refresh_worker(role: str, startup_delay: float = 0):
    """
    One daemon thread per role.

    Sequence per cycle:
      1. Scrape LinkedIn  (pan-India, covers all cities)
      2. Wait 15 s
      3. Fetch Indeed     (pan-India, 2 pages)
      4. Sleep 4 h, then repeat

    startup_delay staggers the first run across roles so all threads
    don't hit the APIs at exactly the same second on startup.
    """
    print(f"[BG] Thread started for role '{role}' (startup delay: {startup_delay}s)")

    if startup_delay > 0:
        time.sleep(startup_delay)

    while True:
        # ── LinkedIn ──────────────────────────────────────────────
        try:
            print(f"[BG-LI] Scraping LinkedIn — {role}")
            li_jobs = scrape_linkedin_jobs(role, "India", num_results=40)
            print(f"[BG-LI] Done — {len(li_jobs)} jobs for '{role}'")
        except Exception as e:
            print(f"[BG-LI] Error for '{role}': {e}")

        # Gap between LinkedIn and Indeed to avoid rate-limit bursts
        print(f"[BG] Waiting 15 s before Indeed fetch for '{role}'...")
        time.sleep(15)

        # ── Indeed ───────────────────────────────────────────────
        try:
            print(f"[BG-IN] Fetching Indeed — {role}")
            in_jobs = fetch_indeed_jobs(role, "bangalore", num_pages=1)
            print(f"[BG-IN] Done — {len(in_jobs)} jobs for '{role}'")
        except Exception as e:
            print(f"[BG-IN] Error for '{role}': {e}")

        print(f"[BG] Cycle complete for '{role}'. Sleeping 30 mins...")
        time.sleep(REFRESH_INTERVAL_SECONDS)


def start_background_refresh():
    """
    Spin up exactly ONE thread per role.
    Each thread handles both LinkedIn and Indeed for that role,
    sequentially, with a 15-second gap between platforms.
    Threads are staggered by 20 seconds on startup so they don't
    all fire simultaneously.
    """
    print("[STARTUP] Launching background refresh threads (1 per role)...")

    for idx, role in enumerate(BACKGROUND_ROLES):
        startup_delay = idx * 20   # stagger: role 0 = 0s, role 1 = 20s, etc.
        Thread(
            target=_role_refresh_worker,
            args=(role, startup_delay),
            daemon=True,
            name=f"BG-{role}",
        ).start()

    print(
        f"[STARTUP] {len(BACKGROUND_ROLES)} background threads launched "
        f"(1 per role, staggered by 20 s). "
        f"Each thread: LinkedIn → 15 s gap → Indeed → 30 minutes sleep."
    )


# ════════════════════════════════════════════════════════════════════
#  API endpoints
# ════════════════════════════════════════════════════════════════════

# ── health ──────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "job_counts": count_jobs()})


# ── jobs (DB-backed) ─────────────────────────────────────────────────

@app.route("/jobs", methods=["GET"])
def list_jobs():
    """
    Return jobs stored in the DB.

    Query params:
      portal  – filter by 'LinkedIn' or 'Indeed' (optional)
      limit   – max rows (default 400)
    """
    portal = request.args.get("portal")
    limit  = int(request.args.get("limit", 100))

    if portal:
        jobs = get_jobs_by_portal(portal, limit)
    else:
        jobs = get_all_jobs(limit)

    return jsonify({"count": len(jobs), "jobs": jobs})


@app.route("/jobs/count", methods=["GET"])
def jobs_count():
    return jsonify(count_jobs())


@app.route("/jobs/ingest", methods=["POST"])
def ingest_jobs():
    """
    Accepts a raw JSearch/Indeed API response body and stores jobs.
    Useful for manual ingestion / testing without the background thread.

    Body: { "data": [ <JSearch job objects> ] }
    """
    try:
        data = request.get_json()
        if not data or "data" not in data:
            return jsonify({"error": "Invalid payload — expected { data: [...] }"}), 400

        stored = 0
        for job in data.get("data", []):
            normalized = normalize_indeed_job(job)
            upsert_job(normalized)
            stored += 1

        return jsonify({"status": "success", "stored": stored})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── workflow (orchestrator) ──────────────────────────────────────────

@app.route("/workflow/run", methods=["POST"])
def run_workflow():
    data       = request.get_json()
    role       = data.get("role")
    location   = data.get("location", "India")
    experience = data.get("experience")
    portals    = data.get("portals") or None
    num_results = data.get("num_results", 100)

    if not role:
        return jsonify({"error": "Missing role"}), 400

    result = orchestrator.run_workflow(
        role,
        location,
        num_results,
        experience=experience,
        portals=portals,
    )

    for msg in result.get("results", []):
        messages_db[msg["id"]] = msg

    return jsonify(result)


# ── messages ────────────────────────────────────────────────────────

@app.route("/messages", methods=["GET"])
def get_all_messages():
    return jsonify(list(messages_db.values()))


@app.route("/messages/<message_id>", methods=["GET"])
def get_message(message_id):
    if message_id not in messages_db:
        return jsonify({"error": "Message not found"}), 404
    return jsonify(messages_db[message_id])


@app.route("/messages/<message_id>", methods=["PUT"])
def update_message(message_id):
    if message_id not in messages_db:
        return jsonify({"error": "Message not found"}), 404

    data = request.get_json()
    msg  = messages_db[message_id]

    if not msg.get("edited_by_user"):
        msg["original_message"] = f"Subject: {msg['subject_line']}\n\n{msg['message_body']}"
        msg["edited_by_user"]   = True

    if "subject_line" in data:
        msg["subject_line"] = data["subject_line"]
    if "message_body" in data:
        msg["message_body"] = data["message_body"]

    messages_db[message_id] = msg
    return jsonify(msg)


@app.route("/messages/<message_id>/approve", methods=["POST"])
def approve_message(message_id):
    if message_id not in messages_db:
        return jsonify({"error": "Message not found"}), 404
    messages_db[message_id]["approval_status"] = "approved"
    return jsonify(messages_db[message_id])


@app.route("/messages/<message_id>/reject", methods=["POST"])
def reject_message(message_id):
    if message_id not in messages_db:
        return jsonify({"error": "Message not found"}), 404
    messages_db[message_id]["approval_status"] = "rejected"
    return jsonify(messages_db[message_id])


@app.route("/stats", methods=["GET"])
def get_stats():
    all_messages = list(messages_db.values())
    approved = sum(1 for m in all_messages if m.get("approval_status") == "approved")
    rejected = sum(1 for m in all_messages if m.get("approval_status") == "rejected")
    pending  = sum(1 for m in all_messages if m.get("approval_status") == "pending")
    return jsonify({
        "total_messages": len(all_messages),
        "approved":       approved,
        "pending":        pending,
        "rejected":       rejected,
        "approval_rate":  approved / len(all_messages) if all_messages else 0,
    })


# ── LinkedIn URL generator ───────────────────────────────────────────

@app.route("/linkedin/search-url", methods=["POST"])
def generate_linkedin_url():
    try:
        data      = request.get_json()
        company   = data.get("company")
        job_title = data.get("job_title")
        location  = data.get("location")

        if not company:
            return jsonify({"error": "Company name is required"}), 400

        url = generate_linkedin_search_url(
            company=company, job_title=job_title, location=location
        )
        from linkedin_utils import get_recruiter_keywords
        keywords = get_recruiter_keywords(job_title)

        return jsonify({
            "url":       url,
            "keywords":  keywords,
            "company":   company,
            "job_title": job_title or "Not specified",
            "location":  location  or "Not specified",
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to generate URL: {e}"}), 500


# ── outreach tracking ────────────────────────────────────────────────

@app.route("/create-outreach", methods=["POST"])
def create_outreach():
    try:
        data           = request.get_json()
        company_name   = data.get("company_name")
        job_role       = data.get("job_role")
        recruiter_name = data.get("recruiter_name")
        recruiter_email= data.get("recruiter_email")
        linkedin_url   = data.get("linkedin_url")

        if not company_name or not job_role:
            return jsonify({"error": "company_name and job_role are required"}), 400

        result = create_outreach_log(
            company_name=company_name,
            job_role=job_role,
            recruiter_name=recruiter_name,
            recruiter_email=recruiter_email,
            linkedin_url=linkedin_url,
        )

        if result.get("status") == "success":
            return jsonify({
                "status":      "success",
                "outreach_id": result.get("id"),
                "message":     "Outreach logged successfully",
            }), 201
        return jsonify(result), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/update-outreach-status", methods=["POST"])
def update_status():
    try:
        data        = request.get_json()
        outreach_id = data.get("id")
        status      = data.get("status")

        if not outreach_id or not status:
            return jsonify({"error": "id and status are required"}), 400
        if status not in ["REQUEST_SENT", "CONNECTED", "MESSAGE_SENT", "NOT_CONTACTED"]:
            return jsonify({"error": "Invalid status"}), 400

        return jsonify(update_outreach_status(outreach_id, status)), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/outreach-dashboard", methods=["GET"])
def get_dashboard():
    try:
        return jsonify({
            "status": "success",
            "stats":  get_outreach_stats(),
            "logs":   get_outreach_logs(),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/outreach-stats", methods=["GET"])
def get_stats_endpoint():
    try:
        return jsonify(get_outreach_stats())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── LinkedIn OAuth (only if linkedin_auth module is present) ─────────

if LINKEDIN_AUTH_AVAILABLE:

    @app.route("/auth/linkedin/login", methods=["POST"])
    def linkedin_login():
        try:
            auth_url = get_linkedin_auth_url()
            return jsonify({"status": "success", "auth_url": auth_url})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/auth/linkedin/callback", methods=["GET"])
    def linkedin_callback():
        try:
            auth_code = request.args.get("code")
            error     = request.args.get("error")
            error_desc= request.args.get("error_description")

            if error:
                return redirect(f"http://localhost:3000?auth_error={error}&error_description={error_desc}")
            if not auth_code:
                return redirect("http://localhost:3000?auth_error=no_code")

            token_data = exchange_auth_code_for_token(auth_code)
            if not token_data:
                return redirect("http://localhost:3000?auth_error=token_exchange_failed")

            access_token    = token_data.get("access_token")
            linkedin_profile= get_linkedin_profile(access_token)
            if not linkedin_profile:
                return redirect("http://localhost:3000?auth_error=profile_fetch_failed")

            user_id = linkedin_profile.get("id")
            auth_id = store_linkedin_auth(user_id, linkedin_profile, token_data)
            if not auth_id:
                return redirect("http://localhost:3000?auth_error=storage_failed")

            return redirect(
                f"http://localhost:3000?auth_success=true"
                f"&user_id={user_id}"
                f"&name={linkedin_profile.get('localizedFirstName', '')}"
            )
        except Exception as e:
            return redirect(f"http://localhost:3000?auth_error=server_error&error_message={e}")

    @app.route("/associate-outreach-with-user", methods=["POST"])
    def associate_outreach_with_user():
        try:
            data    = request.get_json()
            user_id = data.get("user_id")
            if not user_id:
                return jsonify({"error": "user_id is required"}), 400

            conn   = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE outreach_logs
                SET user_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id IS NULL
                AND created_at > datetime('now', '-30 minutes')
            """, (user_id,))
            count = cursor.rowcount
            conn.commit()
            conn.close()

            return jsonify({
                "status":           "success",
                "associated_count": count,
                "message":          f"Associated {count} outreach logs",
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/sync-linkedin-connections", methods=["POST"])
    def sync_connections():
        try:
            data    = request.get_json()
            user_id = data.get("user_id")
            if not user_id:
                return jsonify({"error": "user_id is required"}), 400

            success = sync_outreach_with_linkedin(user_id)
            if success:
                return jsonify({"status": "success", "message": f"Synced for {user_id}"})
            return jsonify({"status": "error", "error": "Sync failed"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/outreach-dashboard-with-linkedin", methods=["GET"])
    def get_dashboard_with_linkedin():
        try:
            user_id = request.args.get("user_id")
            if not user_id:
                return jsonify({"error": "user_id query parameter is required"}), 400

            logs  = get_user_outreach_with_linkedin_status(user_id)
            stats = get_outreach_stats()
            return jsonify({"status": "success", "stats": stats, "logs": logs})
        except Exception as e:
            return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════════
#  Entry point
# ════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("[STARTUP] Flask app starting...")

    # 1. Initialise DB schema
    init_jobs_db()
    _ensure_outreach_table()

    # 2. Launch background scrape/fetch threads
    start_background_refresh()

    print("[STARTUP] Server listening on http://0.0.0.0:8000")
    app.run(debug=True, host="0.0.0.0", port=8000, use_reloader=False)
    # use_reloader=False prevents Flask's dev reloader from doubling
    # the background threads in debug mode.