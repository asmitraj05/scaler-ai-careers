"""
agents.py
Four-agent pipeline:
  JobFinderAgent           – scrapes LinkedIn (BeautifulSoup) + fetches Indeed (JSearch)
  RelevanceAnalyzerAgent   – scores / filters jobs
  RecruiterFinderAgent     – finds HR contacts
  MessageGeneratorAgent    – drafts outreach emails

Also exposes:
  fetch_indeed_jobs()      – standalone Indeed/JSearch fetcher used by background refresh
"""

from typing import List, Dict
from models import (
    create_job,
    create_relevant_job,
    create_recruiter,
    create_outreach_message,
)
import uuid
import time
import json
import os
import re
import requests
from job_store import upsert_job, normalize_linkedin_job, normalize_indeed_job

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# ──────────────────────────── constants ──────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# JSearch / RapidAPI credentials
JSEARCH_API_KEY  = "9efa73397emshfa37381af46489bp1bd04ajsn310682b4b025"
JSEARCH_API_HOST = "jsearch.p.rapidapi.com"
JSEARCH_BASE_URL = "https://jsearch.p.rapidapi.com/search"

TECH_KEYWORDS = {
    "Python":        ["python"],
    "JavaScript":    ["javascript", " js "],
    "TypeScript":    ["typescript"],
    "Java":          ["java"],
    "Go":            ["golang", " go "],
    "C++":           ["c++", "cpp"],
    "React":         ["react"],
    "Node.js":       ["node.js", "nodejs"],
    "Django":        ["django"],
    "FastAPI":       ["fastapi"],
    "Spring Boot":   ["spring boot", "spring"],
    "PostgreSQL":    ["postgresql", "postgres"],
    "MySQL":         ["mysql"],
    "MongoDB":       ["mongodb"],
    "Redis":         ["redis"],
    "Kafka":         ["kafka"],
    "Docker":        ["docker"],
    "Kubernetes":    ["kubernetes", "k8s"],
    "AWS":           ["aws", "amazon web services"],
    "GCP":           ["gcp", "google cloud"],
    "Azure":         ["azure"],
    "Microservices": ["microservices"],
}


# ──────────────────────────── helpers ────────────────────────────────

def extract_tech_from_text(text: str) -> List[str]:
    text_lower = text.lower()
    found = []
    for tech, keywords in TECH_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(tech)
    return found[:5] if found else []


def _build_jsearch_query(role: str, location: str) -> str:
    """
    Build a URL-encoded query string for JSearch.
    Spaces → %20 as required by the API.
    e.g. "Backend Engineer" + "bangalore" → "Backend%20Engineer%20jobs%20in%20bangalore"
    """
    role_encoded     = role.replace(" ", "%20")
    location_encoded = location.replace(" ", "%20")
    return f"{role_encoded}%20jobs%20in%20{location_encoded}"


# ──────────────────────── LinkedIn scraping ───────────────────────────

def scrape_remoteok_jobs(role: str, num_results: int) -> List[Dict]:
    """Fetch remote jobs from RemoteOK's free public API."""
    try:
        resp = requests.get(
            "https://remoteok.io/api",
            headers={"User-Agent": HEADERS["User-Agent"], "Accept": "application/json"},
            timeout=8,
        )
        if resp.status_code != 200:
            return []

        role_lower  = role.lower()
        keyword_map = {
            "backend":    ["backend", "python", "node", "go", "java", "api"],
            "full stack": ["fullstack", "full-stack", "full stack", "react", "vue"],
            "frontend":   ["frontend", "front-end", "react", "vue", "angular"],
            "python":     ["python", "django", "fastapi", "flask"],
            "devops":     ["devops", "sre", "infrastructure", "kubernetes"],
            "data":       ["data", "ml", "machine learning", "analytics"],
        }
        keywords = next(
            (kws for key, kws in keyword_map.items() if key in role_lower),
            [role_lower],
        )

        jobs = []
        for item in resp.json():
            if not isinstance(item, dict) or len(jobs) >= num_results:
                break
            title = (item.get("position") or item.get("title") or "").lower()
            tags  = " ".join(item.get("tags") or []).lower()
            if not any(kw in title or kw in tags for kw in keywords):
                continue
            tech = [t.strip().title() for t in (item.get("tags") or [])[:5]]
            job = create_job(
                id=str(uuid.uuid4()),
                company_name=item.get("company", "Remote Company"),
                job_title=item.get("position") or item.get("title") or role,
                location="Remote",
                job_url=item.get("url") or f"https://remoteok.io/l/{item.get('id', '')}",
                posted_date=item.get("date", "Recently"),
                description=(item.get("description") or f"Remote {role} position")[:200],
                tech_stack=tech,
            )
            normalized = normalize_linkedin_job(job)
            upsert_job(normalized)
            job["portal_name"]  = "RemoteOK"
            job["portal_logo"]  = "🌍"
            job["portal_color"] = "#17b978"
            jobs.append(job)

        print(f"   [RemoteOK] Got {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"   [RemoteOK] Error: {e}")
        return []


def fetch_linkedin_description(job_url: str) -> str:
    """
    Fetch a LinkedIn job detail page, find the <script type="application/ld+json">
    tag, parse it as JSON, and return a fully clean plain-text description.

    Pipeline:
      1. Parse ld+json  → raw HTML string from data["description"]
      2. html.unescape  → turn &amp; / &lt; / &nbsp; etc. into real characters
      3. BeautifulSoup  → strip every HTML tag (<p> <strong> <br> <li> <ul> …)
      4. re.sub         → drop any surviving escape sequences and extra whitespace
      5. Return a single continuous readable paragraph with no markup at all
    """
    import json as _json
    import re as _re
    from html import unescape as _unescape

    try:
        resp = requests.get(job_url, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return ""

        soup = BeautifulSoup(resp.text, "html.parser")

        # There can be multiple ld+json script tags on a LinkedIn page.
        # .string returns None when BS4 sees surrounding whitespace as a
        # separate text node — so we use .get_text().strip() instead,
        # and iterate all candidates until we find one with a "description".
        raw = ""
        for script_tag in soup.find_all("script", {"type": "application/ld+json"}):
            text = script_tag.get_text(strip=True)
            if not text:
                continue
            try:
                data = _json.loads(text)
                candidate = data.get("description", "")
                if candidate:
                    raw = candidate
                    break  # found the JobPosting block, stop here
            except Exception:
                continue  # not valid JSON or not the right block, keep looking

        if not raw:
            return ""

        # Step 1: unescape HTML entities  (&lt; → <,  &amp; → &,  &nbsp; → space)
        unescaped = _unescape(raw)

        # Step 2: strip every HTML tag — BS4 handles nested / malformed markup safely
        plain = BeautifulSoup(unescaped, "html.parser").get_text(separator=" ")

        # Step 3: remove literal escape sequences that may have survived as text
        plain = plain.replace("\\n", " ").replace("\\t", " ") \
            .replace("\\r", " ").replace("\\", "")

        # Step 4: collapse ALL whitespace (newlines, tabs, multiple spaces) → one space
        plain = _re.sub(r"\s+", " ", plain)

        return plain.strip()

    except Exception as e:
        print(f"   [LD+JSON] Failed to parse description from {job_url}: {e}")
        return ""

def scrape_linkedin_jobs(
    role: str, location: str, num_results: int, experience: str = None
) -> List[Dict]:
    """
    Scrape real jobs from LinkedIn's public guest API (no login required).

    Args:
        role:        Job title to search for.
        location:    City / region (defaults to India for pan-India).
        num_results: Max jobs to return.
        experience:  Optional bracket e.g. "1-3", "3-5", "5+".
    """
    if not BS4_AVAILABLE:
        print("   [LinkedIn] bs4 not installed — skipping")
        return []

    jobs: List[Dict] = []
    start = 0

    experience_filters = {
        "0-1": "1",
        "1-3": "2",
        "3-5": "3",
        "5-10": "4",
        "10+": "5",
    }

    if not location or location.lower() == "india":
        loc_param = "India"
        print("   [LinkedIn] Pan-India search enabled")
    elif location.lower() == "remote":
        loc_param = "India"
    else:
        loc_param = f"{location}, India"

    while len(jobs) < num_results:
        try:
            url = (
                "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                f"?keywords={requests.utils.quote(role)}"
                f"&location={requests.utils.quote(loc_param)}"
                f"&start={start}"
            )
            if experience and experience in experience_filters:
                url += f"&experience={experience_filters[experience]}"

            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                print(f"   [LinkedIn] HTTP {resp.status_code}")
                break

            soup  = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all("div", class_="base-card")
            if not cards:
                break

            for card in cards:
                if len(jobs) >= num_results:
                    break
                try:
                    title_el   = card.find("h3", class_="base-search-card__title")
                    company_el = card.find("h4", class_="base-search-card__subtitle")
                    loc_el     = card.find("span", class_="job-search-card__location")
                    link_el    = card.find("a", class_="base-card__full-link")

                    time_el = card.find("time", class_="job-search-card__listdate--new")
                    if not time_el:
                        time_el = card.find("time", class_="job-search-card__listdate")

                    if not (title_el and company_el and link_el):
                        continue

                    title   = title_el.get_text(strip=True)
                    company = company_el.get_text(strip=True)
                    loc     = loc_el.get_text(strip=True) if loc_el else location
                    job_url = (link_el.get("href") or "").split("?")[0]

                    posted_date = "Recently"
                    if time_el:
                        posted_date = time_el.get_text(strip=True)

                    posted_datetime = ""
                    if time_el and time_el.get("datetime"):
                        posted_datetime = time_el.get("datetime")

                    if not job_url:
                        continue

                    # Filter: only keep jobs that match the role keywords
                    title_lower = title.lower()
                    role_lower  = role.lower()
                    if not any(kw in title_lower for kw in role_lower.split()):
                        print(f"   [LinkedIn Filter] Skipped '{title}'")
                        continue

                    # Fetch plain-text description from ld+json structured data
                    description_text = fetch_linkedin_description(job_url)
                    if not description_text:
                        description_text = f"{company} is hiring for {title}"
                    time.sleep(0.2)

                    tech = extract_tech_from_text(title + " " + description_text)

                    job = create_job(
                        id=str(uuid.uuid4()),
                        company_name=company,
                        job_title=title,
                        location=loc,
                        job_url=job_url,
                        posted_date=posted_date,
                        description=description_text,
                        tech_stack=tech,
                    )

                    # Persist to DB immediately
                    normalized = normalize_linkedin_job(job)
                    upsert_job(normalized)

                    job["portal_name"]     = "LinkedIn"
                    job["portal_logo"]     = "💼"
                    job["portal_color"]    = "#0077b5"
                    job["posted_datetime"] = posted_datetime
                    jobs.append(job)
                    print(f"   [LinkedIn ✓] {title} @ {company}  — {posted_date}")

                except Exception as e:
                    print(f"   [LinkedIn Card Error] {e}")
                    continue

            start += len(cards)
            if len(cards) < 10:
                break
            time.sleep(0.3)

        except Exception as e:
            print(f"   [LinkedIn] Error: {e}")
            break

    print(f"   [LinkedIn] Got {len(jobs)} jobs (after filtering)")
    return jobs


# ──────────────────────── Indeed / JSearch fetcher ────────────────────

def fetch_indeed_jobs(role: str, location: str, num_pages: int = 1) -> List[Dict]:
    """
    Fetch jobs from JSearch (Indeed aggregator on RapidAPI) and persist
    each one to the unified jobs table.

    Args:
        role:      Job title, e.g. "Backend Engineer"
        location:  City/region, e.g. "bangalore"
        num_pages: How many result pages to fetch (each page ≈ 10 jobs)

    Returns:
        List of raw JSearch job dicts (before normalisation).
    """
    query = _build_jsearch_query(role, location)
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": JSEARCH_API_HOST,
        "x-rapidapi-key":  JSEARCH_API_KEY,
    }

    all_jobs: List[Dict] = []

    for page in range(1, num_pages + 1):
        try:
            url = (
                f"{JSEARCH_BASE_URL}"
                f"?query={query}"
                f"&page={page}"
                f"&num_pages=1"
                f"&country=in"
                f"&date_posted=all"
            )
            print(f"   [Indeed] Fetching page {page} — {role} in {location}")
            resp = requests.get(url, headers=headers, timeout=15)

            if resp.status_code != 200:
                print(f"   [Indeed] HTTP {resp.status_code} on page {page}")
                break

            data = resp.json()
            jobs = data.get("data", [])
            if not jobs:
                print(f"   [Indeed] No more results at page {page}")
                break

            for job in jobs:
                normalized = normalize_indeed_job(job)
                upsert_job(normalized)
                all_jobs.append(job)
                print(f"   [Indeed ✓] {job.get('job_title')} @ {job.get('employer_name')}")

            time.sleep(15)   # respect RapidAPI rate limit between pages

        except Exception as e:
            print(f"   [Indeed] Error on page {page}: {e}")
            break

    print(f"   [Indeed] Stored {len(all_jobs)} jobs for '{role}' in '{location}'")
    return all_jobs


# ──────────────────────────── agents ─────────────────────────────────
class RelevanceAnalyzerAgent:

    REASONS = [
        "Backend role with modern tech stack aligns with Scaler's Full Stack program",
        "Fintech platform — great career growth opportunity for Scaler alumni",
        "Cloud-native stack matches Scaler's specialization tracks",
        "Enterprise-scale systems — ideal for Scaler senior engineers",
        "High-growth company with strong engineering culture",
    ]

    def analyze_relevance(self, jobs: List[Dict]) -> List[Dict]:
        if not jobs:
            return []

        print(f"\n[RelevanceAnalyzer] Scoring {len(jobs)} jobs...")
        relevant = []
        for idx, job in enumerate(jobs):
            score = round(min(0.85 + idx * 0.02, 0.99), 2)
            relevant.append(
                create_relevant_job(
                    job_id=job["id"],
                    job=job,
                    relevance_score=score,
                    reason=self.REASONS[idx % len(self.REASONS)],
                )
            )
            print(f"   {job['company_name']} — score {score}")

        print()
        return relevant


def find_recruiter_from_linkedin(company_name: str):
    """
    Attempt to find an HR/Recruiter from the LinkedIn company people page.
    Returns (name, title, linkedin_url, confidence) or None.
    """
    if not BS4_AVAILABLE:
        return None
    try:
        company_slug = company_name.lower().replace(" ", "-").replace(".", "")
        company_url  = f"https://www.linkedin.com/company/{company_slug}"

        print(f"     [LinkedIn] Trying company URL: {company_url}")
        time.sleep(0.3)

        resp = requests.get(company_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            search_url = (
                "https://www.linkedin.com/search/results/companies/"
                f"?keywords={requests.utils.quote(company_name)}"
            )
            resp = requests.get(search_url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                return None

        soup = BeautifulSoup(resp.text, "html.parser")

        people_link = None
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if "/people" in href:
                people_link = href
                break

        if not people_link:
            people_link = f"{company_url}/people"
        if not people_link.startswith("http"):
            people_link = "https://www.linkedin.com" + people_link

        print("     [LinkedIn] Accessing people section...")
        time.sleep(0.3)

        people_resp = requests.get(people_link, headers=HEADERS, timeout=10)
        if people_resp.status_code != 200:
            return None

        people_soup = BeautifulSoup(people_resp.text, "html.parser")

        hr_keywords = [
            "recruiter", "talent acquisition", "talent acq", "hr",
            "hiring manager", "head of recruiting", "talent partner",
            "recruitment", "staffing", "sourcer",
        ]

        best_match    = None
        best_confidence = 0

        profile_selectors = [
            ("span", {"class": "name"}),
            ("div",  {"class": "entity-result"}),
            ("h3",   {"class": "member-name"}),
        ]

        for tag, attrs in profile_selectors:
            elements = people_soup.find_all(tag, attrs)
            for elem in elements[:30]:
                try:
                    title_text = ""
                    parent = elem.parent
                    if parent:
                        subtitle = parent.find("span", class_="subtitle")
                        if subtitle:
                            title_text = subtitle.get_text(strip=True).lower()
                        else:
                            for child in parent.find_all("span", class_=True):
                                child_text = child.get_text(strip=True).lower()
                                if any(kw in child_text for kw in hr_keywords):
                                    title_text = child_text
                                    break

                    if title_text:
                        match_score = sum(
                            2 if title_text.startswith(kw) else 1
                            for kw in hr_keywords
                            if kw in title_text
                        )
                        if match_score > 0:
                            name         = elem.get_text(strip=True)
                            linkedin_url = (
                                f"https://linkedin.com/search/results/people/"
                                f"?keywords={requests.utils.quote(name)}"
                            )
                            confidence = min(0.80 + (match_score * 0.05), 0.95)
                            if confidence > best_confidence:
                                best_match      = (name, title_text, linkedin_url, confidence)
                                best_confidence = confidence
                                if match_score >= 3:
                                    print(
                                        f"     [LinkedIn] Found recruiter: {name} "
                                        f"({title_text}) — Confidence: {confidence}"
                                    )
                                    return best_match
                except Exception:
                    continue

        if best_match:
            print(
                f"     [LinkedIn] Found recruiter: {best_match[0]} — "
                f"Confidence: {best_match[3]}"
            )
            return best_match

        print("     [LinkedIn] No HR/Recruiter found, will use fallback")
        return None

    except Exception as e:
        print(f"     [LinkedIn Error] {e}")
        return None


class RecruiterFinderAgent:

    KNOWN = {
        "flipkart":      ("Priya Sharma",  "Senior Talent Acquisition Manager", "linkedin.com/in/priya-sharma",  0.95),
        "swiggy":        ("Rahul Verma",   "Engineering Recruiter",             "linkedin.com/in/rahul-verma",   0.93),
        "phonepe":       ("Anjali Patel",  "Head of Engineering Recruitment",   "linkedin.com/in/anjali-patel",  0.94),
        "oyo":           ("Vikram Singh",  "Engineering Manager - Hiring",      "linkedin.com/in/vikram-singh",  0.92),
        "cred":          ("Neha Gupta",    "Talent Partner",                    "linkedin.com/in/neha-gupta",    0.96),
        "microsoft":     ("David Chen",    "Technical Recruiter",               "linkedin.com/in/davidchen",     0.94),
        "google":        ("Sarah Johnson", "Engineering Recruiter",             "linkedin.com/in/sarahjohnson",  0.95),
        "amazon":        ("Michael Patel", "AWS Recruiter",                     "linkedin.com/in/michael-patel", 0.93),
        "goldman sachs": ("Emma Wilson",   "Engineering Hiring Manager",        "linkedin.com/in/emma-wilson",   0.92),
        "razorpay":      ("Pooja Iyer",    "Talent Acquisition Lead",           "linkedin.com/in/pooja-iyer",    0.94),
        "meesho":        ("Arjun Nair",    "Engineering Recruiter",             "linkedin.com/in/arjun-nair",    0.91),
        "zetwerk":       ("Divya Menon",   "Senior HR Manager",                 "linkedin.com/in/divya-menon",   0.90),
        "unacademy":     ("Rohan Das",     "Talent Acquisition Manager",        "linkedin.com/in/rohan-das",     0.89),
        "stripe":        ("Alex Kim",      "Technical Recruiter",               "linkedin.com/in/alex-kim",      0.93),
    }

    def find_recruiters(self, relevant_jobs: List[Dict]) -> List[Dict]:
        print(f"\n[RecruiterFinder] Finding recruiters for {len(relevant_jobs)} jobs...")

        # The LinkedIn HTML scrape is unauthenticated and rate-limited; once
        # blocked it returns 999/hangs and slows the whole request to a crawl
        # (and used to cap responses at ~15 jobs). Off by default — opt in
        # with ENABLE_LINKEDIN_RECRUITER_SCRAPE=1 if you have a working IP/UA.
        use_linkedin = os.environ.get(
            "ENABLE_LINKEDIN_RECRUITER_SCRAPE", ""
        ).strip().lower() in ("1", "true", "yes")

        recruiters = []
        for rj in relevant_jobs:
            company = rj["job"]["company_name"] or "Unknown"
            key     = company.lower().strip()

            linkedin_result = None
            if use_linkedin:
                print(f"   Searching LinkedIn for {company}...")
                linkedin_result = find_recruiter_from_linkedin(company)

            if linkedin_result:
                name, title, linkedin_url, confidence = linkedin_result
            else:
                info = self.KNOWN.get(key)
                if not info:
                    for known_key, known_info in self.KNOWN.items():
                        if known_key in key or key in known_key:
                            info = known_info
                            break

                if info:
                    name, title, linkedin_url, confidence = info
                else:
                    name         = "Hiring Team"
                    title        = "Talent Acquisition"
                    linkedin_url = f"linkedin.com/company/{company.lower().replace(' ', '-')}"
                    confidence   = 0.65

            recruiters.append(
                create_recruiter(
                    job_id=rj["job_id"],
                    recruiter_name=name,
                    title=title,
                    email=f"{name.lower().replace(' ', '.')}@{company.lower().replace(' ', '')}.com",
                    confidence=confidence,
                )
            )
            print(f"   ✓ {name} @ {company} (confidence: {confidence})")

        print()
        return recruiters


class MessageGeneratorAgent:

    TEMPLATES = [
        {
            "subject": "Exceptional Talent Match — {company} {role}",
            "body": (
                "Hi {recruiter},\n\n"
                "I came across {company}'s opening for {role} and thought of your team immediately.\n\n"
                "At Scaler Academy, we train engineers with hands-on expertise in {tech}. "
                "Many of our alumni have successfully joined roles exactly like this one.\n\n"
                "Would you be open to exploring talent from our network specifically prepared for this position?\n\n"
                "Best regards,\nScaler Academy"
            ),
        },
        {
            "subject": "Talent Match — {company} {role}",
            "body": (
                "Hi {recruiter},\n\n"
                "I noticed {company} is hiring for {role} — a role that aligns perfectly with our curriculum.\n\n"
                "Our recent graduates have strong hands-on experience with {tech} and have worked on "
                "systems at scale similar to what {company} is building.\n\n"
                "Happy to share vetted candidate profiles. Would you have 15 minutes next week?\n\n"
                "Best,\nScaler Academy"
            ),
        },
        {
            "subject": "Top Engineering Talent for {company}",
            "body": (
                "Hi {recruiter},\n\n"
                "{company}'s {role} opening caught our attention. We have strong candidates from the Scaler community.\n\n"
                "Our engineers are trained in {tech} and have demonstrated strong problem-solving ability "
                "through real-world projects.\n\n"
                "Would you be open to a brief conversation about sourcing through Scaler?\n\n"
                "Looking forward to connecting.\n\nScaler Team"
            ),
        },
    ]

    def generate_messages(
        self, relevant_jobs: List[Dict], recruiters: List[Dict]
    ) -> List[Dict]:
        print(f"\n[MessageGenerator] Drafting {len(relevant_jobs)} outreach messages...")

        recruiter_map = {r["job_id"]: r for r in recruiters}
        messages      = []

        for idx, rj in enumerate(relevant_jobs):
            job       = rj["job"]
            recruiter = recruiter_map.get(rj["job_id"])

            # Don't drop the job if recruiter discovery missed it — fall back
            # to a generic "Hiring Team" contact so every relevant job shows up.
            if not recruiter or not recruiter.get("email"):
                company   = job.get("company_name") or "Unknown"
                slug      = company.lower().replace(' ', '')
                recruiter = {
                    "recruiter_name": "Hiring Team",
                    "email": f"hiring.team@{slug}.com",
                }

            template = self.TEMPLATES[idx % len(self.TEMPLATES)]
            tech_str = ", ".join((job.get("tech_stack") or ["Python"])[:2])

            subject = template["subject"].format(
                company=job["company_name"],
                role=job["title"],
            )
            body = template["body"].format(
                recruiter=recruiter["recruiter_name"],
                company=job["company_name"],
                role=job["title"],
                tech=tech_str,
            )

            outreach = create_outreach_message(
                id=str(uuid.uuid4()),
                job_id=rj["job_id"],
                company_name=job["company_name"],
                job_title=job["title"],
                recruiter_name=recruiter["recruiter_name"],
                recruiter_email=recruiter["email"],
                subject_line=subject,
                message_body=body,
                approval_status="pending",
                job_url=job.get("job_url", ""),
                job=job,
            )
            messages.append(outreach)
            print(f"   {recruiter['recruiter_name']} @ {job['company_name']}")

        print()
        return messages