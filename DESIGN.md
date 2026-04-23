# AI-Native Careers Sales Automation System
## Complete System Design Document

---

## 1. Problem Understanding

**Current State (Manual Process):**
- Scaler's careers team manually searches job boards
- Identifies companies hiring for relevant roles
- Finds recruiter/hiring manager contacts
- Manually drafts personalized outreach emails
- No systematic follow-up or tracking

**Pain Points:**
- Time-consuming (hours per day on research)
- Error-prone (inconsistent messaging)
- Non-scalable (can't handle volume)
- No quality control before sending

**Solution Goal:**
Automate 80% of the research and message generation workflow while maintaining human oversight for final approval and personalization.

---

## 2. System Overview

**High-Level Architecture:**
```
User Input (Role, Location) 
    ↓
Orchestrator (Central Controller)
    ├─ Job Finder Agent (Search for openings)
    ├─ Relevance Analyzer Agent (Filter jobs)
    ├─ Recruiter Finder Agent (Identify contacts)
    └─ Message Generator Agent (Create outreach)
    ↓
Results Database
    ↓
Human Review UI (React/Next.js)
    ├─ View generated messages
    ├─ Edit before sending
    ├─ Approve/Reject/Flag
    └─ Track status
```

**Core Principle:** Each agent has ONE responsibility. Outputs are structured data, not arbitrary text.

---

## 3. Agent Design (Detailed)

### Agent 1: Job Finder Agent
**Responsibility:** Find job postings matching criteria

**Inputs:**
- Job role (e.g., "Backend Engineer")
- Location (e.g., "Bangalore")
- Keywords/filters

**Outputs:**
```json
{
  "jobs": [
    {
      "id": "unique_id",
      "company_name": "TechCorp",
      "job_title": "Senior Backend Engineer",
      "location": "Bangalore",
      "job_url": "https://...",
      "posted_date": "2025-04-20",
      "description": "...",
      "tech_stack": ["Python", "PostgreSQL"]
    }
  ]
}
```

**Tools Used:**
- Serper API (Google Search) for job postings
- Ycombinator Jobs, LinkedIn Jobs endpoints, or web scraping

**Implementation:**
```python
def find_jobs(role: str, location: str) -> List[Job]:
    # Call Serper API with structured search
    query = f"{role} jobs {location} site:linkedin.com OR site:glassdoor.com"
    results = serper_api.search(query)
    return parse_results(results)
```

---

### Agent 2: Relevance Analyzer Agent
**Responsibility:** Filter jobs for Scaler's training programs

**Inputs:**
- List of jobs from Job Finder Agent
- Scaler's course catalog (optional)

**Outputs:**
```json
{
  "relevant_jobs": [
    {
      "job_id": "unique_id",
      "relevance_score": 0.95,
      "reason": "Backend role + Python + PostgreSQL align with Scaler's Full Stack course"
    }
  ]
}
```

**Tool Used:**
- Claude API with structured reasoning

**Implementation:**
```python
def analyze_relevance(jobs: List[Job]) -> List[RelevantJob]:
    prompt = f"""
    Analyze these job postings for relevance to Scaler's training programs.
    Score each 0-1 based on alignment with our courses.
    
    Jobs: {json.dumps(jobs)}
    
    Return JSON with: job_id, relevance_score, reason
    """
    response = claude.messages.create(...)
    return parse_relevance(response)
```

---

### Agent 3: Recruiter Finder Agent
**Responsibility:** Identify and extract recruiter/hiring manager contact info

**Inputs:**
- Relevant jobs (from Analyzer)

**Outputs:**
```json
{
  "recruiters": [
    {
      "job_id": "unique_id",
      "recruiter_name": "John Doe",
      "title": "Hiring Manager",
      "email": "john@techcorp.com",
      "linkedin_url": "https://linkedin.com/in/johndoe",
      "confidence": 0.85
    }
  ]
}
```

**Tools Used:**
- Web scraping (company careers pages)
- LinkedIn scraping or API
- Email finder APIs (Hunter, RocketReach)

**Implementation:**
```python
def find_recruiters(jobs: List[RelevantJob]) -> List[Recruiter]:
    recruiters = []
    for job in jobs:
        # Method 1: Scrape company careers page
        company_page = scrape_company_page(job.company_name)
        if company_page:
            recruiter = extract_recruiter_info(company_page)
            recruiters.append(recruiter)
        
        # Method 2: Find via email API
        if not recruiter:
            email = find_email_api(job.company_name, "recruiter")
            recruiters.append(Recruiter(email=email))
    
    return recruiters
```

---

### Agent 4: Message Generator Agent
**Responsibility:** Create personalized, contextual outreach messages

**Inputs:**
- Company info
- Job details
- Recruiter info
- Scaler's positioning

**Outputs:**
```json
{
  "messages": [
    {
      "job_id": "unique_id",
      "recruiter_email": "john@techcorp.com",
      "subject_line": "Scaler's Backend Program - Matching Your Hiring Needs",
      "body": "Hi John,\n\nI noticed TechCorp is hiring...",
      "tone": "professional",
      "personalization_level": "high"
    }
  ]
}
```

**Tool Used:**
- Claude API for contextual generation

**Implementation:**
```python
def generate_message(company: str, job: Job, recruiter: Recruiter) -> Message:
    prompt = f"""
    Generate a professional, personalized outreach email for:
    - Company: {company}
    - Role: {job.title}
    - Recruiter: {recruiter.name}
    - Our pitch: Scaler trains backend engineers for roles like this
    
    Constraints:
    - 200-250 words
    - Professional but friendly tone
    - Mention specific tech stack from job posting
    - Include a clear CTA (call to action)
    - No generic templates
    
    Return JSON: {{"subject": "...", "body": "..."}}
    """
    return claude.messages.create(...)
```

---

## 4. Orchestrator Design

**Role:** Coordinates agents, passes outputs, handles failures

**Pseudo-code:**
```python
class CareersSalesOrchestrator:
    def run_workflow(self, role: str, location: str) -> Results:
        # Step 1: Find jobs
        jobs = self.job_finder.find_jobs(role, location)
        if not jobs:
            return {"error": "No jobs found"}
        
        # Step 2: Analyze relevance
        relevant_jobs = self.relevance_analyzer.analyze(jobs)
        if not relevant_jobs:
            return {"error": "No relevant jobs found"}
        
        # Step 3: Find recruiters
        recruiters = self.recruiter_finder.find(relevant_jobs)
        # Handle partial failures (some jobs without recruiter info)
        recruiters = [r for r in recruiters if r.email or r.linkedin_url]
        
        # Step 4: Generate messages
        messages = self.message_generator.generate(relevant_jobs, recruiters)
        
        # Step 5: Store results
        self.db.save_batch(messages)
        
        return {
            "total_jobs_found": len(jobs),
            "relevant_jobs": len(relevant_jobs),
            "recruiters_found": len(recruiters),
            "messages_generated": len(messages),
            "results": messages
        }
```

**Error Handling:**
- Graceful degradation if one agent fails
- Partial results are still useful
- Logging and retry logic for API failures

---

## 5. Tools & APIs

### Required Integrations:

| Tool | Purpose | Alternative |
|------|---------|-------------|
| Serper API | Job search | Google Jobs API, LinkedIn API |
| Claude API | Reasoning & Generation | OpenAI GPT-4 |
| Hunter.io / RocketReach | Email finding | Manual LinkedIn scraping |
| Web Scraper | Company pages | BeautifulSoup + Selenium |

### Implementation Details:

**Search API (Serper):**
```python
def search_jobs(query: str) -> List[dict]:
    headers = {"X-API-KEY": SERPER_API_KEY}
    response = requests.post("https://google.serper.dev/search", 
        json={"q": query})
    return parse_results(response.json())
```

**Email Finder:**
```python
def find_email(company: str, name: str) -> str:
    # Use Hunter API
    response = requests.get("https://api.hunter.io/v2/email-finder",
        params={"domain": get_domain(company), "full_name": name})
    return response.json()["data"]["email"]
```

---

## 6. UI/UX Design

### Technology: React + TypeScript + Tailwind CSS (with Scaler branding)

### Scaler Brand Colors (from website):
```css
--primary: #1F2937;      /* Dark blue/gray */
--accent: #3B82F6;       /* Bright blue */
--success: #10B981;      /* Green */
--warning: #F59E0B;      /* Amber */
--error: #EF4444;        /* Red */
--background: #F9FAFB;   /* Light gray */
--text-dark: #1F2937;    /* Dark text */
--text-light: #6B7280;   /* Light gray text */
```

### UI Layout:

**Page 1: Input**
```
┌─────────────────────────────────────────┐
│ Scaler Careers AI Assistant             │
├─────────────────────────────────────────┤
│                                         │
│  What role are you hiring for?          │
│  [Backend Engineer ▼]                   │
│                                         │
│  Location (City/Country)                │
│  [Bangalore             ]               │
│                                         │
│  [Run AI Outreach] (Blue button)        │
│                                         │
└─────────────────────────────────────────┘
```

**Page 2: Results & Review**
```
┌─────────────────────────────────────────┐
│ Found 5 relevant opportunities          │
├─────────────────────────────────────────┤
│                                         │
│ [Card 1] TechCorp - Senior Backend Eng  │
│ ├─ Recruiter: John Doe (john@...)       │
│ ├─ Message Preview: "Hi John..."        │
│ ├─ [Edit] [Approve] [Reject]            │
│                                         │
│ [Card 2] StartupXYZ - Backend Engr      │
│ ├─ Recruiter: Jane Smith (jane@...)     │
│ ├─ Message Preview: "Hi Jane..."        │
│ ├─ [Edit] [Approve] [Reject]            │
│                                         │
│ ... more cards ...                      │
│                                         │
│ [Approve All] [Send Approved]           │
└─────────────────────────────────────────┘
```

**Page 3: Edit Message**
```
┌─────────────────────────────────────────┐
│ Edit Outreach Message                   │
├─────────────────────────────────────────┤
│ Company: TechCorp                       │
│ Recruiter: john@techcorp.com            │
│                                         │
│ Subject:                                │
│ [Scaler's Backend Program - Your Needs] │
│                                         │
│ Message Body:                           │
│ ┌─────────────────────────────────────┐ │
│ │ Hi John,                            │ │
│ │                                     │ │
│ │ I noticed TechCorp is hiring for... │ │
│ │                                     │ │
│ │ [Edit here]                         │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Save] [Cancel] [Preview]               │
└─────────────────────────────────────────┘
```

**Page 4: Dashboard (Optional)**
```
┌─────────────────────────────────────────┐
│ Campaign Dashboard                      │
├─────────────────────────────────────────┤
│ Total Outreaches: 45                    │
│ Approved: 32 | Pending: 8 | Rejected: 5│
│ Sent: 28 | Replied: 7 | Conversion: 25%│
│                                         │
│ [Recent Outreaches]                     │
│ TechCorp → John Doe → Sent ✓            │
│ StartupXYZ → Jane Smith → Pending       │
└─────────────────────────────────────────┘
```

---

## 7. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐     │
│  │ Input Form   │→ │ Results     │→ │ Edit & Review  │     │
│  └──────────────┘  └─────────────┘  └────────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │ API Calls
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  Backend (Python FastAPI)                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Orchestrator Controller                   │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Job     │→│ Relevance│→│ Recruiter│→│ Message  │       │
│  │  Finder  │ │ Analyzer │ │  Finder  │ │Generator │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└────────┬─────────────────────────────────────────────────────┘
         │ Storage
         ↓
┌─────────────────────────────────────────────────────────────┐
│              Database (SQLite / PostgreSQL)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Jobs         │  │ Recruiters   │  │ Messages     │      │
│  │ (cached)     │  │ (contacts)   │  │ (generated)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘

External APIs:
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Serper API   │  │ Claude API   │  │ Hunter API   │
│ (Job Search) │  │ (Reasoning)  │  │ (Email Find) │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 8. Data Flow

```
User Input: 
{
  "role": "Backend Engineer",
  "location": "Bangalore",
  "num_results": 10
}
    ↓
Job Finder Agent:
{
  "jobs": [
    { "id": "job_1", "company": "TechCorp", "title": "Senior Backend Engineer", ... }
  ]
}
    ↓
Relevance Analyzer Agent:
{
  "relevant_jobs": [
    { "job_id": "job_1", "relevance_score": 0.95, "reason": "..." }
  ]
}
    ↓
Recruiter Finder Agent:
{
  "recruiters": [
    { "job_id": "job_1", "name": "John Doe", "email": "john@techcorp.com", ... }
  ]
}
    ↓
Message Generator Agent:
{
  "messages": [
    { "job_id": "job_1", "subject": "Scaler...", "body": "Hi John..." }
  ]
}
    ↓
Store in Database + Return to UI
    ↓
Human Review:
- View message
- Edit if needed
- Approve/Reject
- Mark as "ready_to_send"
    ↓
Send (manual or automated)
```

---

## 9. Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| **Frontend** | React 18 + TypeScript | Type safety, modern UX |
| **Styling** | Tailwind CSS | Fast, scalable styling with Scaler branding |
| **Backend** | Python FastAPI | Fast, async-first, great for multi-agent workflows |
| **LLM** | Claude 3.5 Sonnet (Anthropic) | Superior reasoning for job analysis & message generation |
| **Search API** | Serper | Reliable job search at scale |
| **Email Finder** | Hunter.io | High accuracy for recruiter emails |
| **Database** | SQLite (MVP) / PostgreSQL (Production) | Structured data storage, easy to scale |
| **Orchestration** | Python Pydantic + FastAPI | Clean data validation and API design |
| **Deployment** | Docker + Railway/Vercel | Fast, scalable, cost-effective for MVP |

---

## 10. Tradeoffs

| Decision | Tradeoff | Why |
|----------|----------|-----|
| **One day MVP** | Accuracy over coverage | Focus on quality of first 5-10 results vs 100+ results |
| **Claude instead of GPT-4** | Slightly lower max outputs | Better reasoning for multi-step workflows, faster |
| **Serper over LinkedIn API** | Limited to public job posts | LinkedIn API needs enterprise agreement |
| **Email finder APIs** | Cost per lookup | Necessary for recruiter contact info |
| **SQLite over PostgreSQL** | Limited concurrency | Fine for MVP, scales to PostgreSQL easily |
| **React over Streamlit** | More code to write | Streamlit is fast but less flexible for design branding |
| **Manual approval before send** | Slower than fully auto | Reduces risk of bad outreaches, maintains quality |

---

## 11. Future Improvements

**Phase 2:**
- **A/B testing**: Test different message variations
- **Follow-up automation**: Auto-send follow-ups after 5 days
- **Response classification**: Use AI to classify replies (interested, not interested, etc.)
- **Analytics dashboard**: Track reply rates, conversion metrics
- **LinkedIn integration**: Direct message outreach from LinkedIn

**Phase 3:**
- **Persistent memory**: Track which companies/recruiters we've contacted
- **Multi-channel outreach**: Email + LinkedIn + Calls
- **ML model training**: Learn which messages get best response rates
- **Batch processing**: Handle 100+ outreaches per run
- **CRM integration**: Sync with existing CRM systems

---

## Implementation Roadmap (1 Day)

**Hour 1-2:** Setup & Architecture
- [ ] Create backend structure (FastAPI + agents)
- [ ] Setup database schema
- [ ] Configure API keys (Serper, Claude, Hunter)

**Hour 2-3:** Implement Agents
- [ ] Job Finder Agent (using Serper)
- [ ] Relevance Analyzer Agent
- [ ] Recruiter Finder Agent
- [ ] Message Generator Agent

**Hour 3-4:** Orchestrator & Backend API
- [ ] Build orchestrator logic
- [ ] Create FastAPI routes
- [ ] Test agent pipeline end-to-end

**Hour 4-5:** Frontend UI
- [ ] Setup React + Tailwind
- [ ] Build input form
- [ ] Build results display with cards
- [ ] Implement edit/approve functionality

**Hour 5-6:** Integration & Polish
- [ ] Connect frontend to backend
- [ ] Test full workflow
- [ ] Polish UI with Scaler branding
- [ ] Create demo data fallback

**Hour 6-7:** Testing & Demo
- [ ] Test with real queries
- [ ] Demo walkthrough
- [ ] Bug fixes
- [ ] Ready for presentation

---

**Status: Design Complete**
Ready to start implementation immediately.
