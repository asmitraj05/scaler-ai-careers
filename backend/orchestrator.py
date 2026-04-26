from typing import Dict, List, Optional
from agents import (
    RelevanceAnalyzerAgent,
    RecruiterFinderAgent,
    MessageGeneratorAgent,
)
from job_store import query_jobs

class CareersSalesOrchestrator:
    """Central controller coordinating all agents"""

    def __init__(self):
        self.relevance_analyzer = RelevanceAnalyzerAgent()
        self.recruiter_finder = RecruiterFinderAgent()
        self.message_generator = MessageGeneratorAgent()
        self.results_cache = {}

    def run_workflow(
        self,
        role: str,
        location: str,
        num_results: int = 100,
        experience: Optional[str] = None,
        portals: Optional[List[str]] = None,
    ) -> Dict:
        """
        Execute the complete workflow:
        Job Finding → Relevance Analysis → Recruiter Finding → Message Generation
        """
        try:
            print(f"[Orchestrator] Starting workflow for: {role} in {location}")
            if experience:
                print(f"[Orchestrator] Experience filter: {experience}")
            if portals:
                print(f"[Orchestrator] Portal filter: {portals}")

            # Step 1: Pull filtered jobs from DB. Experience is intentionally
            # NOT used as a SQL filter — most rows have no experience signal,
            # so any bucket would hide otherwise-matching jobs. We log the
            # selected level for visibility but show all role/portal matches.
            print("[Step 1] Querying DB with filters...")
            jobs = query_jobs(
                role=role,
                portals=portals,
                location=location if location and location.lower() != "india" else None,
                experience=None,
                limit=num_results,
            )
            if not jobs:
                return {
                    "total_jobs_found": 0,
                    "relevant_jobs": 0,
                    "recruiters_found": 0,
                    "messages_generated": 0,
                    "results": [],
                    "error": "No jobs found matching your criteria"
                }
            print(f"[Step 1] Found {len(jobs)} jobs")

            # Step 2: Score relevance
            print("[Step 2] Analyzing relevance...")
            relevant_jobs = self.relevance_analyzer.analyze_relevance(jobs)
            if not relevant_jobs:
                return {
                    "total_jobs_found": len(jobs),
                    "relevant_jobs": 0,
                    "recruiters_found": 0,
                    "messages_generated": 0,
                    "results": [],
                    "error": "No jobs matched relevance criteria"
                }
            print(f"[Step 2] {len(relevant_jobs)} jobs are relevant")

            # Step 3: Find recruiters (every job gets one — fallback to "Hiring Team")
            print("[Step 3] Finding recruiters...")
            recruiters = self.recruiter_finder.find_recruiters(relevant_jobs)
            recruiters_with_email = [r for r in recruiters if r.get("email")]
            print(f"[Step 3] Resolved {len(recruiters_with_email)} recruiter contacts")

            # Step 4: Generate one message per relevant job. We pass ALL relevant
            # jobs through — the message generator now substitutes a placeholder
            # recruiter when one is missing, so no job is silently dropped here.
            print("[Step 4] Generating messages...")
            messages = self.message_generator.generate_messages(
                relevant_jobs, recruiters
            )
            print(f"[Step 4] Generated {len(messages)} messages")

            cache_key = f"{role}_{location}_{experience or ''}_{','.join(portals or [])}"
            self.results_cache[cache_key] = messages

            return {
                "total_jobs_found": len(jobs),
                "relevant_jobs": len(relevant_jobs),
                "recruiters_found": len(recruiters_with_email),
                "messages_generated": len(messages),
                "results": messages,
                "error": None
            }

        except Exception as e:
            print(f"[Orchestrator] Error: {str(e)}")
            return {
                "total_jobs_found": 0,
                "relevant_jobs": 0,
                "recruiters_found": 0,
                "messages_generated": 0,
                "results": [],
                "error": f"Workflow failed: {str(e)}"
            }