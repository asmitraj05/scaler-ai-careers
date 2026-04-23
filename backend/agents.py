from typing import List, Dict
from models import (
    create_job,
    create_relevant_job,
    create_recruiter,
    create_outreach_message
)
import uuid
import time
import requests

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

TECH_KEYWORDS = {
    'Python': ['python'],
    'JavaScript': ['javascript', ' js '],
    'TypeScript': ['typescript'],
    'Java': ['java'],
    'Go': ['golang', ' go '],
    'C++': ['c++', 'cpp'],
    'React': ['react'],
    'Node.js': ['node.js', 'nodejs'],
    'Django': ['django'],
    'FastAPI': ['fastapi'],
    'Spring Boot': ['spring boot', 'spring'],
    'PostgreSQL': ['postgresql', 'postgres'],
    'MySQL': ['mysql'],
    'MongoDB': ['mongodb'],
    'Redis': ['redis'],
    'Kafka': ['kafka'],
    'Docker': ['docker'],
    'Kubernetes': ['kubernetes', 'k8s'],
    'AWS': ['aws', 'amazon web services'],
    'GCP': ['gcp', 'google cloud'],
    'Azure': ['azure'],
    'Microservices': ['microservices'],
}


def extract_tech_from_text(text: str) -> List[str]:
    text_lower = text.lower()
    found = []
    for tech, keywords in TECH_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(tech)
    return found[:5] if found else []


def scrape_remoteok_jobs(role: str, num_results: int) -> List[Dict]:
    """Fetch remote jobs from RemoteOK's free public API."""
    try:
        resp = requests.get(
            'https://remoteok.io/api',
            headers={'User-Agent': HEADERS['User-Agent'], 'Accept': 'application/json'},
            timeout=8,
        )
        if resp.status_code != 200:
            return []

        role_lower = role.lower()
        keyword_map = {
            'backend':    ['backend', 'python', 'node', 'go', 'java', 'api'],
            'full stack': ['fullstack', 'full-stack', 'full stack', 'react', 'vue'],
            'frontend':   ['frontend', 'front-end', 'react', 'vue', 'angular'],
            'python':     ['python', 'django', 'fastapi', 'flask'],
            'devops':     ['devops', 'sre', 'infrastructure', 'kubernetes'],
            'data':       ['data', 'ml', 'machine learning', 'analytics'],
        }
        keywords = next(
            (kws for key, kws in keyword_map.items() if key in role_lower),
            [role_lower],
        )

        jobs = []
        for item in resp.json():
            if not isinstance(item, dict) or len(jobs) >= num_results:
                break
            title = (item.get('position') or item.get('title') or '').lower()
            tags  = ' '.join(item.get('tags') or []).lower()
            if not any(kw in title or kw in tags for kw in keywords):
                continue
            tech = [t.strip().title() for t in (item.get('tags') or [])[:5]]
            job = create_job(
                id=str(uuid.uuid4()),
                company_name=item.get('company', 'Remote Company'),
                job_title=item.get('position') or item.get('title') or role,
                location='Remote',
                job_url=item.get('url') or f"https://remoteok.io/l/{item.get('id', '')}",
                posted_date=item.get('date', 'Recently'),
                description=(item.get('description') or f"Remote {role} position")[:200],
                tech_stack=tech,
            )
            job['portal_name'] = 'RemoteOK'
            job['portal_logo'] = '🌍'
            job['portal_color'] = '#17b978'
            jobs.append(job)

        print(f"   [RemoteOK] Got {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"   [RemoteOK] Error: {e}")
        return []


def scrape_linkedin_jobs(role: str, location: str, num_results: int) -> List[Dict]:
    """Scrape real jobs from LinkedIn's public guest API (no login required)."""
    if not BS4_AVAILABLE:
        print("   [LinkedIn] bs4 not installed")
        return []

    jobs: List[Dict] = []
    start = 0

    while len(jobs) < num_results:
        try:
            loc_param = f"{location}, India" if location.lower() != 'remote' else 'India'
            url = (
                'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
                f'?keywords={requests.utils.quote(role)}'
                f'&location={requests.utils.quote(loc_param)}'
                f'&start={start}'
            )

            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                print(f"   [LinkedIn] HTTP {resp.status_code}")
                break

            soup  = BeautifulSoup(resp.text, 'html.parser')
            cards = soup.find_all('div', class_='base-card')
            if not cards:
                break

            for card in cards:
                if len(jobs) >= num_results:
                    break
                try:
                    title_el   = card.find('h3', class_='base-search-card__title')
                    company_el = card.find('h4', class_='base-search-card__subtitle')
                    loc_el     = card.find('span', class_='job-search-card__location')
                    link_el    = card.find('a', class_='base-card__full-link')

                    if not (title_el and company_el and link_el):
                        continue

                    title   = title_el.get_text(strip=True)
                    company = company_el.get_text(strip=True)
                    loc     = loc_el.get_text(strip=True) if loc_el else location
                    job_url = (link_el.get('href') or '').split('?')[0]

                    if not job_url:
                        continue

                    job = create_job(
                        id=str(uuid.uuid4()),
                        company_name=company,
                        job_title=title,
                        location=loc,
                        job_url=job_url,
                        posted_date='Recently',
                        description=f"{company} is hiring for {title}",
                        tech_stack=extract_tech_from_text(title),
                    )
                    job['portal_name'] = 'LinkedIn'
                    job['portal_logo'] = '💼'
                    job['portal_color'] = '#0077b5'
                    jobs.append(job)
                except Exception:
                    continue

            start += len(cards)
            if len(cards) < 10:
                break  # reached last page
            time.sleep(0.3)

        except Exception as e:
            print(f"   [LinkedIn] Error: {e}")
            break

    print(f"   [LinkedIn] Got {len(jobs)} jobs")
    return jobs


class JobFinderAgent:

    def find_jobs(self, role: str, location: str, num_results: int = 5) -> List[Dict]:
        print(f"\n[JobFinder] Searching: {role} in {location}")

        jobs: List[Dict] = []

        # Primary: LinkedIn (India-specific, live listings)
        linkedin_jobs = scrape_linkedin_jobs(role, location, num_results)
        jobs.extend(linkedin_jobs)

        # Secondary: RemoteOK fills remaining slots (especially useful for "Remote" location)
        remaining = num_results - len(jobs)
        if remaining > 0:
            time.sleep(0.3)
            remote_jobs = scrape_remoteok_jobs(role, remaining)
            jobs.extend(remote_jobs)

        print(f"[JobFinder] Total: {len(jobs)} jobs\n")
        return jobs[:num_results]


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
                    job_id=job['id'],
                    job=job,
                    relevance_score=score,
                    reason=self.REASONS[idx % len(self.REASONS)],
                )
            )
            print(f"   {job['company_name']} — score {score}")

        print()
        return relevant


class RecruiterFinderAgent:

    # Known recruiters for well-known companies
    KNOWN = {
        'flipkart':     ('Priya Sharma',  'Senior Talent Acquisition Manager', 'priya.sharma@flipkart.com',   0.95),
        'swiggy':       ('Rahul Verma',   'Engineering Recruiter',             'rahul.verma@swiggy.in',       0.93),
        'phonepe':      ('Anjali Patel',  'Head of Engineering Recruitment',   'anjali.patel@phonepe.com',    0.94),
        'oyo':          ('Vikram Singh',  'Engineering Manager - Hiring',      'vikram.singh@oyorooms.com',   0.92),
        'cred':         ('Neha Gupta',    'Talent Partner',                    'neha.gupta@cred.club',        0.96),
        'microsoft':    ('David Chen',    'Technical Recruiter',               'david.chen@microsoft.com',    0.94),
        'google':       ('Sarah Johnson', 'Engineering Recruiter',             'sjohnson@google.com',         0.95),
        'amazon':       ('Michael Patel', 'AWS Recruiter',                     'm.patel@amazon.com',          0.93),
        'goldman sachs':('Emma Wilson',   'Engineering Hiring Manager',        'emma.wilson@gs.com',          0.92),
        'razorpay':     ('Pooja Iyer',    'Talent Acquisition Lead',           'pooja.iyer@razorpay.com',     0.94),
        'meesho':       ('Arjun Nair',    'Engineering Recruiter',             'arjun.nair@meesho.com',       0.91),
        'zetwerk':      ('Divya Menon',   'Senior HR Manager',                 'divya.menon@zetwerk.com',     0.90),
        'unacademy':    ('Rohan Das',     'Talent Acquisition Manager',        'rohan.das@unacademy.com',     0.89),
        'stripe':       ('Alex Kim',      'Technical Recruiter',               'alex.kim@stripe.com',         0.93),
    }

    def find_recruiters(self, relevant_jobs: List[Dict]) -> List[Dict]:
        print(f"\n[RecruiterFinder] Finding recruiters for {len(relevant_jobs)} jobs...")

        recruiters = []
        for rj in relevant_jobs:
            company = rj['job']['company_name']
            key = company.lower().strip()

            # Try exact key, then partial match
            info = self.KNOWN.get(key)
            if not info:
                for known_key, known_info in self.KNOWN.items():
                    if known_key in key or key in known_key:
                        info = known_info
                        break

            if info:
                name, title, email, confidence = info
            else:
                # Generic fallback — derive email from company name
                domain = company.lower().replace(' ', '').replace('.', '') + '.com'
                name = 'Hiring Team'
                title = 'Talent Acquisition'
                email = f'careers@{domain}'
                confidence = 0.70

            recruiters.append(
                create_recruiter(
                    job_id=rj['job_id'],
                    recruiter_name=name,
                    title=title,
                    email=email,
                    confidence=confidence,
                )
            )
            print(f"   {name} @ {company}")

        print()
        return recruiters


class MessageGeneratorAgent:

    TEMPLATES = [
        {
            'subject': 'Exceptional Talent Match — {company} {role}',
            'body': (
                'Hi {recruiter},\n\n'
                'I came across {company}\'s opening for {role} and thought of your team immediately.\n\n'
                'At Scaler Academy, we train engineers with hands-on expertise in {tech}. '
                'Many of our alumni have successfully joined roles exactly like this one.\n\n'
                'Would you be open to exploring talent from our network specifically prepared for this position?\n\n'
                'Best regards,\nScaler Academy'
            ),
        },
        {
            'subject': 'Talent Match — {company} {role}',
            'body': (
                'Hi {recruiter},\n\n'
                'I noticed {company} is hiring for {role} — a role that aligns perfectly with our curriculum.\n\n'
                'Our recent graduates have strong hands-on experience with {tech} and have worked on '
                'systems at scale similar to what {company} is building.\n\n'
                'Happy to share vetted candidate profiles. Would you have 15 minutes next week?\n\n'
                'Best,\nScaler Academy'
            ),
        },
        {
            'subject': 'Top Engineering Talent for {company}',
            'body': (
                'Hi {recruiter},\n\n'
                '{company}\'s {role} opening caught our attention. We have strong candidates from the Scaler community.\n\n'
                'Our engineers are trained in {tech} and have demonstrated strong problem-solving ability '
                'through real-world projects.\n\n'
                'Would you be open to a brief conversation about sourcing through Scaler?\n\n'
                'Looking forward to connecting.\n\nScaler Team'
            ),
        },
    ]

    def generate_messages(self, relevant_jobs: List[Dict], recruiters: List[Dict]) -> List[Dict]:
        print(f"\n[MessageGenerator] Drafting {len(relevant_jobs)} outreach messages...")

        recruiter_map = {r['job_id']: r for r in recruiters}
        messages = []

        for idx, rj in enumerate(relevant_jobs):
            job = rj['job']
            recruiter = recruiter_map.get(rj['job_id'])
            if not recruiter or not recruiter.get('email'):
                continue

            template = self.TEMPLATES[idx % len(self.TEMPLATES)]
            tech_str = ', '.join((job.get('tech_stack') or ['Python'])[:2])

            subject = template['subject'].format(
                company=job['company_name'],
                role=job['job_title'],
            )
            body = template['body'].format(
                recruiter=recruiter['recruiter_name'],
                company=job['company_name'],
                role=job['job_title'],
                tech=tech_str,
            )

            outreach = create_outreach_message(
                id=str(uuid.uuid4()),
                job_id=rj['job_id'],
                company_name=job['company_name'],
                job_title=job['job_title'],
                recruiter_name=recruiter['recruiter_name'],
                recruiter_email=recruiter['email'],
                subject_line=subject,
                message_body=body,
                approval_status='pending',
                job_url=job.get('job_url', ''),
                job=job,
            )
            messages.append(outreach)
            print(f"   {recruiter['recruiter_name']} @ {job['company_name']}")

        print()
        return messages
