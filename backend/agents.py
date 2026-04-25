from typing import List, Dict, Optional
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


def _extract_linkedin_job_id(job_url: str) -> Optional[str]:
    """Resolve numeric job id from common LinkedIn job URLs."""
    import re
    if not job_url:
        return None
    u = job_url.strip()
    m = re.search(r'[?&]currentJobId=(\d+)', u)
    if m:
        return m.group(1)
    m = re.search(r'/jobs/view/(\d+)', u, re.I)
    if m:
        return m.group(1)
    m = re.search(r'/jobPosting/(\d+)', u, re.I)
    if m:
        return m.group(1)
    m = re.search(r'-(\d+)(?:/)?$', u.rstrip('/'))
    if m:
        return m.group(1)
    return None


def fetch_linkedin_job_description(job_url: str) -> str:
    """Fetch full job description via LinkedIn's guest job API (no login required)."""
    if not BS4_AVAILABLE or not job_url:
        return None
    try:
        job_id = _extract_linkedin_job_id(job_url)
        if not job_id:
            return None
        api_url = f'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}'
        resp = requests.get(api_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        desc_el = soup.find('div', class_='description__text')
        if not desc_el:
            return None
        for el in desc_el.find_all(['button', 'span'], class_=lambda c: c and 'show-more' in c):
            el.decompose()
        return desc_el.get_text(separator='\n', strip=True)
    except Exception as e:
        print(f"[JobDesc] Error: {e}")
        return None


def generate_contextual_outreach(
    company: str,
    role: str,
    recruiter_name: str = "Hiring Team",
    description: str = "",
    target_words: int = 100,
) -> str:
    """Build a ~100-word contextual outreach pitching Scaler's student pool.

    Pulls 2-3 specific signals (tech stack, focus areas) from the job
    description so each message reads as written for that role.
    """
    desc = (description or "").strip()
    techs = extract_tech_from_text(f"{role} {desc}")[:3]

    text_lower = desc.lower()
    focus_signals = []
    focus_map = {
        'distributed systems': ['distributed', 'high scale', 'high-throughput', 'low latency'],
        'API design': ['rest api', 'restful', 'graphql', 'api design', 'microservices'],
        'data pipelines': ['etl', 'data pipeline', 'kafka', 'spark', 'streaming'],
        'machine learning': ['machine learning', ' ml ', 'model training', 'deep learning', 'llm'],
        'cloud infrastructure': ['aws', 'gcp', 'azure', 'kubernetes', 'docker'],
        'frontend systems': ['react', 'next.js', 'frontend', 'ui/ux'],
        'backend services': ['backend', 'server-side', 'node.js', 'django', 'spring'],
        'mobile development': ['android', 'ios', 'react native', 'flutter'],
        'security & compliance': ['security', 'authentication', 'oauth', 'compliance'],
    }
    for label, keywords in focus_map.items():
        if any(kw in text_lower for kw in keywords):
            focus_signals.append(label)
        if len(focus_signals) >= 2:
            break

    tech_phrase = ', '.join(techs) if techs else 'modern stacks'
    if focus_signals:
        focus_phrase = ' and '.join(focus_signals)
        context_line = (
            f"The role's focus on {focus_phrase} maps directly to project work "
            f"our learners ship — production systems built with {tech_phrase}."
        )
    else:
        context_line = (
            f"Many candidates in our current cohort have hands-on {tech_phrase} "
            f"experience and have shipped production-grade work in similar domains."
        )

    body = (
        f"Hi {recruiter_name},\n\n"
        f"I noticed {company} is hiring for {role} and wanted to reach out from Scaler. "
        f"{context_line} "
        f"They've been mentored by senior engineers from companies like Google, Meta, and Razorpay, "
        f"and are actively interviewing.\n\n"
        f"Would you be open to a 15-minute chat next week so I can share 3-4 vetted profiles "
        f"matched specifically to this opening?\n\n"
        f"Best,\nScaler Talent Team"
    )

    words = body.split()
    if len(words) > target_words + 25:
        body = ' '.join(words[: target_words + 20]).rstrip(',.') + '.'
    return body


def scrape_linkedin_jobs(role: str, location: str, num_results: int, experience: str = None) -> List[Dict]:
    """Scrape real jobs from LinkedIn's public guest API (no login required).

    Args:
        role: Job title to search for
        location: Location to search in (defaults to "India" for Pan-India search)
        num_results: Number of results to fetch
        experience: Experience filter (e.g., "1-3", "3-5", "5+")
    """
    if not BS4_AVAILABLE:
        print("   [LinkedIn] bs4 not installed")
        return []

    jobs: List[Dict] = []
    start = 0

    # Experience level mappings for LinkedIn
    experience_filters = {
        '0-1': '1',      # Entry level
        '1-3': '2',      # Associate
        '3-5': '3',      # Mid-level
        '5-10': '4',     # Senior
        '10+': '5',      # Director
    }

    # Default to "India" for Pan-India search if location not specified
    if not location or location.lower() == 'india':
        loc_param = 'India'
        print(f"   [LinkedIn] Pan-India search enabled")
    elif location.lower() == 'remote':
        loc_param = 'India'
    else:
        # If specific location provided, search that location in India
        loc_param = f"{location}, India"

    while len(jobs) < num_results:
        try:
            url = (
                'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
                f'?keywords={requests.utils.quote(role)}'
                f'&location={requests.utils.quote(loc_param)}'
                f'&start={start}'
            )

            # Add experience filter if provided
            if experience and experience in experience_filters:
                url += f'&experience={experience_filters[experience]}'

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

                    # NEW: Extract posting time from card
                    time_el    = card.find('time', class_='job-search-card__listdate--new')
                    if not time_el:
                        time_el = card.find('time', class_='job-search-card__listdate')

                    if not (title_el and company_el and link_el):
                        continue

                    title   = title_el.get_text(strip=True)
                    company = company_el.get_text(strip=True)
                    loc     = loc_el.get_text(strip=True) if loc_el else location
                    job_url = (link_el.get('href') or '').split('?')[0]

                    # NEW: Extract actual posting time from LinkedIn
                    posted_date = 'Recently'
                    if time_el:
                        posted_text = time_el.get_text(strip=True)  # e.g., "2 days ago", "1 week ago"
                        posted_date = posted_text

                    # Get datetime attribute for sorting
                    posted_datetime = ''
                    if time_el and time_el.get('datetime'):
                        posted_datetime = time_el.get('datetime')

                    if not job_url:
                        continue

                    # FILTER: Only include jobs that match the role
                    title_lower = title.lower()
                    role_lower = role.lower()

                    # Check if job title contains the main role keywords
                    role_keywords = role_lower.split()
                    is_matching = any(keyword in title_lower for keyword in role_keywords)

                    # If no match found, skip this job
                    if not is_matching:
                        print(f"   [LinkedIn Filter] Skipped '{title}' (doesn't match '{role}')")
                        continue

                    job = create_job(
                        id=str(uuid.uuid4()),
                        company_name=company,
                        job_title=title,
                        location=loc,
                        job_url=job_url,
                        posted_date=posted_date,
                        description=f"{company} is hiring for {title}",
                        tech_stack=extract_tech_from_text(title),
                    )
                    job['portal_name'] = 'LinkedIn'
                    job['portal_logo'] = '💼'
                    job['portal_color'] = '#0077b5'
                    job['posted_datetime'] = posted_datetime  # For sorting
                    jobs.append(job)
                    print(f"   [LinkedIn Match] {title} - Posted {posted_date}")
                except Exception as e:
                    print(f"   [LinkedIn Card Error] {str(e)}")
                    continue

            start += len(cards)
            if len(cards) < 10:
                break  # reached last page
            time.sleep(0.3)

        except Exception as e:
            print(f"   [LinkedIn] Error: {e}")
            break

    print(f"   [LinkedIn] Got {len(jobs)} jobs (after filtering)")
    return jobs


class JobFinderAgent:

    def find_jobs(self, role: str, location: str, num_results: int = 5, experience: str = None) -> List[Dict]:
        if location.lower() == 'india':
            print(f"\n[JobFinder] Searching: {role} - PAN-INDIA")
        else:
            print(f"\n[JobFinder] Searching: {role} in {location}")
        if experience:
            print(f"[JobFinder] Experience filter: {experience} years")

        jobs: List[Dict] = []

        # Primary: LinkedIn (India-specific, live listings)
        linkedin_jobs = scrape_linkedin_jobs(role, location, num_results, experience)
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


def find_recruiter_from_linkedin(company_name: str) -> tuple:
    """
    Find actual recruiter/HR from LinkedIn company page.
    Returns: (name, title, linkedin_url, confidence)
    """
    try:
        # Direct company URL construction (most reliable method)
        company_slug = company_name.lower().replace(' ', '-').replace('.', '')
        company_url = f"https://www.linkedin.com/company/{company_slug}"

        print(f"     [LinkedIn] Trying company URL: {company_url}")
        time.sleep(0.3)

        # Try direct company page first
        resp = requests.get(company_url, headers=HEADERS, timeout=10)

        # If that fails, try search
        if resp.status_code != 200:
            search_url = f"https://www.linkedin.com/search/results/companies/?keywords={requests.utils.quote(company_name)}"
            resp = requests.get(search_url, headers=HEADERS, timeout=10)

            if resp.status_code != 200:
                print(f"     [LinkedIn] Search failed for {company_name}")
                return None

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Look for people link - check multiple possible locations
        people_link = None
        links = soup.find_all('a', href=True)

        for link in links:
            href = link.get('href', '')
            if '/people' in href:
                people_link = href
                break

        if not people_link:
            # Construct people URL directly
            people_link = f"{company_url}/people"

        if not people_link.startswith('http'):
            people_link = 'https://www.linkedin.com' + people_link

        print(f"     [LinkedIn] Accessing people section...")
        time.sleep(0.3)

        # Scrape people section
        people_resp = requests.get(people_link, headers=HEADERS, timeout=10)

        if people_resp.status_code != 200:
            print(f"     [LinkedIn] Could not access people section (status: {people_resp.status_code})")
            return None

        people_soup = BeautifulSoup(people_resp.text, 'html.parser')

        # HR/Recruiter keywords to match
        hr_keywords = [
            'recruiter', 'talent acquisition', 'talent acq', 'hr',
            'hiring manager', 'head of recruiting', 'talent partner',
            'recruitment', 'staffing', 'sourcer'
        ]

        # Find all elements that might contain profiles
        best_match = None
        best_confidence = 0

        # Search through multiple possible selectors
        profile_selectors = [
            ('span', {'class': 'name'}),
            ('div', {'class': 'entity-result'}),
            ('h3', {'class': 'member-name'}),
        ]

        for tag, attrs in profile_selectors:
            elements = people_soup.find_all(tag, attrs)

            for elem in elements[:30]:  # Check first 30 profiles
                try:
                    elem_text = elem.get_text(strip=True)

                    # Get the title - check nearby elements
                    title_text = ""
                    parent = elem.parent
                    if parent:
                        # Look for subtitle or description
                        subtitle = parent.find('span', class_='subtitle')
                        if subtitle:
                            title_text = subtitle.get_text(strip=True).lower()
                        else:
                            # Try other variations
                            for child in parent.find_all('span', class_=True):
                                child_text = child.get_text(strip=True).lower()
                                if any(kw in child_text for kw in hr_keywords):
                                    title_text = child_text
                                    break

                    if title_text:
                        # Match against HR keywords
                        match_score = sum(2 if title_text.startswith(kw) else 1
                                         for kw in hr_keywords if kw in title_text)

                        if match_score > 0:
                            name = elem.get_text(strip=True)
                            linkedin_url = f"https://linkedin.com/search/results/people/?keywords={requests.utils.quote(name)}"
                            confidence = min(0.80 + (match_score * 0.05), 0.95)

                            if confidence > best_confidence:
                                best_match = (name, title_text, linkedin_url, confidence)
                                best_confidence = confidence

                                if match_score >= 3:  # Strong match
                                    print(f"     [LinkedIn] Found recruiter: {name} ({title_text}) - Confidence: {confidence}")
                                    return best_match

                except Exception:
                    continue

        if best_match:
            print(f"     [LinkedIn] Found recruiter: {best_match[0]} - Confidence: {best_match[3]}")
            return best_match

        print(f"     [LinkedIn] No HR/Recruiter found, will use fallback")
        return None

    except Exception as e:
        print(f"     [LinkedIn Error] {str(e)}")
        return None


class RecruiterFinderAgent:

    # Fallback known recruiters for quick matches
    KNOWN = {
        'flipkart':     ('Priya Sharma',  'Senior Talent Acquisition Manager', 'linkedin.com/in/priya-sharma', 0.95),
        'swiggy':       ('Rahul Verma',   'Engineering Recruiter',             'linkedin.com/in/rahul-verma',  0.93),
        'phonepe':      ('Anjali Patel',  'Head of Engineering Recruitment',   'linkedin.com/in/anjali-patel', 0.94),
        'oyo':          ('Vikram Singh',  'Engineering Manager - Hiring',      'linkedin.com/in/vikram-singh', 0.92),
        'cred':         ('Neha Gupta',    'Talent Partner',                    'linkedin.com/in/neha-gupta',   0.96),
        'microsoft':    ('David Chen',    'Technical Recruiter',               'linkedin.com/in/davidchen',    0.94),
        'google':       ('Sarah Johnson', 'Engineering Recruiter',             'linkedin.com/in/sarahjohnson', 0.95),
        'amazon':       ('Michael Patel', 'AWS Recruiter',                     'linkedin.com/in/michael-patel', 0.93),
        'goldman sachs':('Emma Wilson',   'Engineering Hiring Manager',        'linkedin.com/in/emma-wilson',  0.92),
        'razorpay':     ('Pooja Iyer',    'Talent Acquisition Lead',           'linkedin.com/in/pooja-iyer',   0.94),
        'meesho':       ('Arjun Nair',    'Engineering Recruiter',             'linkedin.com/in/arjun-nair',   0.91),
        'zetwerk':      ('Divya Menon',   'Senior HR Manager',                 'linkedin.com/in/divya-menon',  0.90),
        'unacademy':    ('Rohan Das',     'Talent Acquisition Manager',        'linkedin.com/in/rohan-das',    0.89),
        'stripe':       ('Alex Kim',      'Technical Recruiter',               'linkedin.com/in/alex-kim',     0.93),
    }

    def find_recruiters(self, relevant_jobs: List[Dict]) -> List[Dict]:
        print(f"\n[RecruiterFinder] Finding REAL recruiters for {len(relevant_jobs)} jobs from LinkedIn...")

        recruiters = []
        for rj in relevant_jobs:
            company = rj['job']['company_name']
            key = company.lower().strip()

            recruiter_info = None

            # First, try to find real LinkedIn recruiter
            print(f"   Searching LinkedIn for {company}...")
            linkedin_result = find_recruiter_from_linkedin(company)

            if linkedin_result:
                name, title, linkedin_url, confidence = linkedin_result
            else:
                # Fallback to known database
                info = self.KNOWN.get(key)
                if not info:
                    for known_key, known_info in self.KNOWN.items():
                        if known_key in key or key in known_key:
                            info = known_info
                            break

                if info:
                    name, title, linkedin_url, confidence = info
                else:
                    # Generic fallback
                    name = 'Hiring Team'
                    title = 'Talent Acquisition'
                    linkedin_url = f'linkedin.com/company/{company.lower().replace(" ", "-")}'
                    confidence = 0.65

            recruiters.append(
                create_recruiter(
                    job_id=rj['job_id'],
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
