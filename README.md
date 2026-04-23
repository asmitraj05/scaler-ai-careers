# Scaler AI Careers - Automated Sales Outreach System

A production-ready AI-native system that automates the careers sales workflow end-to-end using multi-agent architecture.

## System Overview

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
Human Review UI (React)
    ├─ View generated messages
    ├─ Edit messages
    ├─ Approve/Reject/Flag
    └─ Track status
```

## Architecture

### Backend (Python + FastAPI)
- **FastAPI**: High-performance API server
- **Claude API**: LLM for reasoning and message generation
- **Agents**: Modular, single-responsibility components
- **Orchestrator**: Coordinates multi-agent workflow

### Frontend (React + TypeScript)
- **React 18**: Modern UI framework
- **Tailwind CSS**: Scaler-branded styling
- **Vite**: Fast build tool
- **Axios**: API client

### Data Flow
1. User inputs role + location
2. Job Finder searches for job postings
3. Relevance Analyzer filters by Scaler alignment
4. Recruiter Finder extracts contact information
5. Message Generator creates personalized emails
6. Human reviews and approves before sending

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Anthropic API Key (from claude.ai/api)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file (from `.env.example`):
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

5. Run backend server:
```bash
python main.py
```

Backend will start on `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

Frontend will start on `http://localhost:3000`

## Usage

1. Open `http://localhost:3000` in your browser
2. Select a job role and location
3. Click "Run AI Outreach"
4. Review generated messages
5. Edit any messages if needed
6. Approve messages to send
7. Track in Dashboard

## System Features

### Multi-Agent Architecture
- **Job Finder**: Uses web search to find job postings
- **Relevance Analyzer**: Uses Claude to filter by Scaler program alignment
- **Recruiter Finder**: Identifies hiring managers from company pages
- **Message Generator**: Creates personalized, contextual outreach emails

### Human-in-the-Loop
- Review all generated messages before sending
- Edit messages for better personalization
- Approve/Reject individual messages
- View approval statistics on dashboard

### API Endpoints

**Workflow:**
- `POST /workflow/run` - Run complete outreach workflow

**Messages:**
- `GET /messages` - Get all messages
- `GET /messages/{id}` - Get specific message
- `PUT /messages/{id}` - Edit message
- `POST /messages/{id}/approve` - Approve message
- `POST /messages/{id}/reject` - Reject message

**Stats:**
- `GET /stats` - Get workflow statistics
- `GET /health` - Health check

## Data Models

### Job
```json
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
```

### RelevantJob
```json
{
  "job_id": "unique_id",
  "job": {...},
  "relevance_score": 0.95,
  "reason": "Backend role + Python + PostgreSQL align with Scaler's Full Stack course"
}
```

### Recruiter
```json
{
  "job_id": "unique_id",
  "recruiter_name": "John Doe",
  "title": "Hiring Manager",
  "email": "john@techcorp.com",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "confidence": 0.85
}
```

### OutreachMessage
```json
{
  "id": "unique_id",
  "job_id": "job_unique_id",
  "company_name": "TechCorp",
  "job_title": "Senior Backend Engineer",
  "recruiter_name": "John Doe",
  "recruiter_email": "john@techcorp.com",
  "subject_line": "Scaler's Backend Program - Your Hiring Needs",
  "message_body": "Hi John,\n\nI noticed TechCorp is hiring...",
  "approval_status": "pending",
  "edited_by_user": false
}
```

## Design System (Scaler Branding)

Colors:
- Primary: `#1F2937` (Dark gray)
- Accent: `#3B82F6` (Bright blue)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#EF4444` (Red)
- Background: `#F9FAFB` (Light gray)

Font: Segoe UI, Roboto, sans-serif

## Tradeoffs & Design Decisions

1. **MVP over completeness**: 5-10 results instead of 100+ for faster iterations
2. **Claude Sonnet** for reasoning: Better for multi-step analysis vs raw API calls
3. **Structured data**: Each agent outputs validated JSON, not text
4. **Mock recruiters**: For MVP, using synthetic data instead of real API integrations
5. **SQLite**: Works for MVP, easily scales to PostgreSQL in production
6. **React over Streamlit**: More flexible UI design matching Scaler branding

## Future Improvements

**Phase 2:**
- A/B testing for message variations
- Automated follow-ups after 5 days
- Response classification using LLM
- Analytics dashboard with reply rates
- LinkedIn direct messaging integration

**Phase 3:**
- Contact deduplication and CRM sync
- Multi-channel outreach (email, LinkedIn, calls)
- ML model to predict reply likelihood
- Batch processing (100+ outreaches per run)
- Email campaign tracking and analytics

## Production Deployment

### Backend (Python)
```bash
# Using Gunicorn + Railway/Vercel
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### Frontend (React)
```bash
# Build for production
npm run build
# Deploy to Vercel, Netlify, or any static host
```

### Database
Upgrade from SQLite to PostgreSQL for production concurrency.

## Troubleshooting

**Backend not starting:**
- Check Python version: `python --version` (should be 3.9+)
- Check API key in `.env`: `echo $ANTHROPIC_API_KEY`
- Check port: `lsof -i :8000`

**Frontend can't reach backend:**
- Ensure backend is running on `http://localhost:8000`
- Check CORS headers in FastAPI app
- Check network: `curl http://localhost:8000/health`

**No messages generated:**
- Check Claude API rate limits
- Verify `.env` file has valid API key
- Check server logs for errors

## Architecture Diagram

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
```

## File Structure

```
CLAUDE PROJECT/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── models.py               # Data models
│   ├── agents.py               # Agent implementations
│   ├── orchestrator.py         # Workflow orchestrator
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Environment variables template
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx            # React entry point
│   │   ├── App.jsx             # Main app component
│   │   ├── index.css           # Global styles
│   │   └── components/
│   │       ├── InputForm.jsx
│   │       ├── ResultsList.jsx
│   │       ├── EditModal.jsx
│   │       └── Dashboard.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
│
├── DESIGN.md                   # System design document
└── README.md                   # This file
```

## Performance Metrics

For demo/MVP:
- Job search: ~2 seconds
- Relevance analysis: ~3 seconds
- Recruiter finding: ~1 second
- Message generation: ~5 seconds
- **Total workflow**: ~15 seconds for 5 messages

## Security Considerations

- API keys stored in `.env` (never commit)
- All user inputs validated with Pydantic
- CORS enabled for dev (restrict in production)
- No credentials stored in frontend
- Message data is in-memory (use persistent DB in production)

## License

Internal Scaler project - confidential

---

**Ready to build?** Start the backend and frontend servers and open `http://localhost:3000`
