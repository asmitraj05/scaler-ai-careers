"""
FastAPI Backend Job Caching System
Fastest & Most Feasible Solution - SQLite + APScheduler
Drop-in replacement for existing /workflow/run endpoint
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DB_FILE = "jobs_cache.db"

def init_database():
    """Initialize SQLite database for caching"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cached_jobs (
            id TEXT PRIMARY KEY,
            role TEXT NOT NULL,
            location TEXT NOT NULL,
            platform TEXT NOT NULL,
            company TEXT,
            job_title TEXT,
            posted_date TEXT,
            experience TEXT,
            recruiter_name TEXT,
            job_url TEXT,
            relevance_score REAL,
            reason TEXT,
            recruiter_title TEXT,
            message_body TEXT,
            tech_stack TEXT,
            full_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_role_location_platform
        ON cached_jobs(role, location, platform)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_created_at
        ON cached_jobs(created_at)
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized")

def get_cached_jobs(role: str, location: str, portals: list = None) -> dict:
    """Get cached jobs from database"""
    if portals is None:
        portals = ['LinkedIn']

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Build query
    placeholders = ','.join('?' * len(portals))
    query = f'''
        SELECT full_data FROM cached_jobs
        WHERE role = ? AND location = ? AND platform IN ({placeholders})
        AND created_at > datetime('now', '-7 days')
        ORDER BY created_at DESC
        LIMIT 40
    '''

    params = [role, location] + portals
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if rows:
        jobs = [json.loads(row[0]) for row in rows]
        logger.info(f"Cache HIT: Found {len(jobs)} jobs for {role} in {location}")
        return {
            "results": jobs,
            "source": "cache",
            "cached_at": datetime.now().isoformat()
        }

    logger.info(f"Cache MISS: No jobs for {role} in {location}")
    return None

def save_jobs_to_cache(role: str, location: str, jobs_data: list):
    """Save jobs to cache"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for job in jobs_data:
        cursor.execute('''
            INSERT OR REPLACE INTO cached_jobs
            (id, role, location, platform, company, job_title, posted_date,
             experience, recruiter_name, job_url, relevance_score, reason,
             recruiter_title, message_body, tech_stack, full_data, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            job.get('id'),
            role,
            location,
            job.get('platform', 'LinkedIn'),
            job.get('company_name'),
            job.get('job_title'),
            job.get('posted_date'),
            job.get('experience'),
            job.get('recruiter_name'),
            job.get('job_url'),
            job.get('relevance_score'),
            job.get('reason'),
            job.get('recruiter_title'),
            job.get('message_body'),
            json.dumps(job.get('tech_stack', [])),
            json.dumps(job)
        ))

    conn.commit()
    conn.close()
    logger.info(f"Saved {len(jobs_data)} jobs to cache for {role}")

def cleanup_old_jobs():
    """Delete jobs older than 7 days"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM cached_jobs
        WHERE created_at < datetime('now', '-7 days')
    ''')

    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    logger.info(f"Cleanup: Deleted {deleted} old jobs")

async def scrape_jobs_for_role(role: str, location: str, portals: list):
    """
    Call your existing scraping function
    Replace this with your actual scraping logic
    """
    # THIS IS WHERE YOUR EXISTING SCRAPING CODE GOES
    # Example:
    # return await your_existing_scrape_function(role, location, portals)

    # For now, returning empty - integrate with your scraper
    return []

def background_job_scheduler():
    """Background job to fetch and cache jobs"""
    major_roles = [
        'Backend Engineer',
        'Frontend Engineer',
        'Full Stack Engineer',
        'Data Science Engineer',
        'DevOps Engineer',
        'System Design Expert',
        'Mobile Developer',
        'Cloud Engineer',
        'Database Engineer',
        'Machine Learning Engineer'
    ]

    locations = ['India', 'Bangalore', 'Delhi', 'Mumbai', 'Hyderabad']
    portals = ['LinkedIn', 'Naukri', 'Indeed']

    logger.info("Starting background job to cache jobs...")

    for role in major_roles:
        for location in locations:
            try:
                # Call your existing scraping function
                # jobs = scrape_jobs_for_role(role, location, portals)
                # if jobs:
                #     save_jobs_to_cache(role, location, jobs)
                logger.info(f"Cached jobs for {role} in {location}")
            except Exception as e:
                logger.error(f"Error caching {role} in {location}: {e}")

    cleanup_old_jobs()
    logger.info("Background caching job completed")

# Modified /workflow/run endpoint with caching
class WorkflowRequest(BaseModel):
    role: str
    location: str
    experience: str = None
    portals: list = ['LinkedIn']
    num_results: int = 40

@app.post('/workflow/run')
async def workflow_run(request: WorkflowRequest):
    """
    Main endpoint - returns cached jobs if available, else scrapes fresh
    """
    try:
        # CHECK CACHE FIRST (< 1 second)
        cached = get_cached_jobs(request.role, request.location, request.portals)
        if cached:
            return cached

        # IF NO CACHE, SCRAPE FRESH (2-3 minutes)
        logger.info(f"No cache found. Scraping fresh jobs for {request.role}...")

        # INTEGRATE YOUR EXISTING SCRAPING LOGIC HERE
        # fresh_jobs = await your_scraping_function(
        #     request.role,
        #     request.location,
        #     request.portals,
        #     request.num_results
        # )

        # For now, returning error - you'll integrate your scraper
        raise HTTPException(status_code=503, detail="Cache empty and scraper not yet integrated")

        # Once scraper is integrated:
        # save_jobs_to_cache(request.role, request.location, fresh_jobs)
        # return {
        #     "results": fresh_jobs,
        #     "source": "fresh",
        #     "fetched_at": datetime.now().isoformat()
        # }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Initialize scheduler
def start_scheduler():
    """Start background job scheduler"""
    scheduler = BackgroundScheduler()

    # Run cache job every 4 hours
    scheduler.add_job(
        background_job_scheduler,
        'interval',
        hours=4,
        id='cache_jobs',
        name='Cache Jobs from LinkedIn',
        replace_existing=True,
        misfire_grace_time=60
    )

    # Also run on startup after 10 seconds
    scheduler.add_job(
        background_job_scheduler,
        'date',
        run_date=datetime.now() + timedelta(seconds=10),
        id='initial_cache',
        name='Initial Cache Load'
    )

    scheduler.start()
    logger.info("Background scheduler started")

# Startup event
@app.on_event("startup")
async def startup():
    init_database()
    start_scheduler()
    logger.info("FastAPI server started with caching enabled")

# Test endpoint to check cache status
@app.get('/cache/status')
async def cache_status():
    """Check cache status and statistics"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM cached_jobs')
    total_jobs = cursor.fetchone()[0]

    cursor.execute('''
        SELECT role, location, COUNT(*) as count
        FROM cached_jobs
        GROUP BY role, location
    ''')
    breakdown = cursor.fetchall()

    cursor.execute('''
        SELECT MAX(created_at) FROM cached_jobs
    ''')
    last_updated = cursor.fetchone()[0]

    conn.close()

    return {
        "total_cached_jobs": total_jobs,
        "last_updated": last_updated,
        "breakdown": [
            {"role": b[0], "location": b[1], "count": b[2]}
            for b in breakdown
        ]
    }

if __name__ == "__main__":
    import uvicorn

    init_database()
    start_scheduler()

    # Run with: uvicorn backend_cache_implementation:app --reload --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
