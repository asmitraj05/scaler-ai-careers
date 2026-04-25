from typing import Dict
from agents import (
    RelevanceAnalyzerAgent,
    RecruiterFinderAgent,
    MessageGeneratorAgent,
)
from job_store import get_all_jobs

class CareersSalesOrchestrator:
    """Central controller coordinating all agents"""

    def __init__(self):
        self.relevance_analyzer = RelevanceAnalyzerAgent()
        self.recruiter_finder = RecruiterFinderAgent()
        self.message_generator = MessageGeneratorAgent()
        self.results_cache = {}

    def run_workflow(self, role: str, location: str, num_results: int = 100, experience: str = None) -> Dict:
        """
        Execute the complete workflow:
        Job Finding → Relevance Analysis → Recruiter Finding → Message Generation

        Args:
            role: Job title to search for
            location: Location to search in
            num_results: Number of results to return
            experience: Experience filter (e.g., "1-3", "3-5", "5+")
        """
        try:
            print(f"[Orchestrator] Starting workflow for: {role} in {location}")
            if experience:
                print(f"[Orchestrator] Experience filter: {experience} years")

            # Step 1: Find jobs
            print("[Step 1] Fetching jobs from DB...")
            jobs = get_all_jobs(num_results)
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

            # Step 2: Analyze relevance
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

            # Step 3: Find recruiters
            print("[Step 3] Finding recruiters...")
            recruiters = self.recruiter_finder.find_recruiters(relevant_jobs)
            recruiters_with_email = [r for r in recruiters if r.get("email")]
            print(f"[Step 3] Found {len(recruiters_with_email)} recruiters")

            # Filter relevant jobs to only those with recruiter info
            relevant_jobs_with_recruiter = [
                rj for rj in relevant_jobs if any(r["job_id"] == rj["job_id"] for r in recruiters_with_email)
            ]

            # Step 4: Generate messages
            print("[Step 4] Generating messages...")
            messages = self.message_generator.generate_messages(
                relevant_jobs_with_recruiter, recruiters_with_email
            )
            print(f"[Step 4] Generated {len(messages)} messages")

            # Store results in cache
            cache_key = role + "_" + location
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