# Simple data models (no pydantic dependency)
from typing import Dict, List, Optional

def create_job(
    id: str,
    company_name: str,
    job_title: str,
    location: str,
    job_url: str,
    posted_date: Optional[str] = None,
    description: str = "",
    tech_stack: List[str] = None
) -> Dict:
    return {
        "id": id,
        "company_name": company_name,
        "job_title": job_title,
        "location": location,
        "job_url": job_url,
        "posted_date": posted_date,
        "description": description,
        "tech_stack": tech_stack or []
    }


def create_relevant_job(job_id: str, job: Dict, relevance_score: float, reason: str) -> Dict:
    return {
        "job_id": job_id,
        "job": job,
        "relevance_score": relevance_score,
        "reason": reason
    }


def create_recruiter(
    job_id: str,
    recruiter_name: str,
    title: str,
    email: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    confidence: float = 0.8
) -> Dict:
    return {
        "job_id": job_id,
        "recruiter_name": recruiter_name,
        "title": title,
        "email": email,
        "linkedin_url": linkedin_url,
        "confidence": confidence
    }


def create_outreach_message(
    id: str,
    job_id: str,
    company_name: str,
    job_title: str,
    recruiter_name: str,
    recruiter_email: str,
    subject_line: str,
    message_body: str,
    approval_status: str = "pending",
    edited_by_user: bool = False,
    original_message: Optional[str] = None,
    job_url: Optional[str] = None,
    job: Optional[Dict] = None
) -> Dict:
    return {
        "id": id,
        "job_id": job_id,
        "company_name": company_name,
        "job_title": job_title,
        "recruiter_name": recruiter_name,
        "recruiter_email": recruiter_email,
        "subject_line": subject_line,
        "message_body": message_body,
        "approval_status": approval_status,
        "edited_by_user": edited_by_user,
        "original_message": original_message,
        "job_url": job_url,
        "job": job
    }