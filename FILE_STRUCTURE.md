# Complete File Structure - Scaler AI Careers Platform

## 📁 Project Organization

```
CLAUDE PROJECT/
│
├── 📄 README_REAL_TIME_SCRAPING.md    ← START HERE (System overview)
├── 📄 QUICK_START.md                   ← How to use the platform
├── 📄 IMPLEMENTATION_SUMMARY.md        ← What was built
├── 📄 SYSTEM_STATUS.md                 ← Architecture & optimization
├── 📄 RECRUITER_FINDER_GUIDE.md        ← Technical deep dive
├── 📄 FILE_STRUCTURE.md                ← This file
│
├── 📁 frontend/                        ← React/Vite Application
│   ├── package.json                    ← Dependencies
│   ├── vite.config.js                  ← Vite configuration
│   ├── index.html                      ← HTML entry point
│   │
│   ├── 📁 src/
│   │   ├── main.jsx                    ← React entry point
│   │   ├── App.jsx                     ← Router & state management
│   │   ├── index.css                   ← Global styles
│   │   │
│   │   └── 📁 components/
│   │       ├── HomePage.jsx            ← Search form interface
│   │       ├── HomePage.css            ← HomePage styles
│   │       ├── ResultsPage.jsx         ← Job display & actions
│   │       ├── ResultsPage.css         ← ResultsPage styles
│   │       └── (legacy components)
│   │
│   ├── 📁 public/
│   │   └── scaler-logo.png            ← Company logo (18KB)
│   │
│   └── 📁 node_modules/               ← Dependencies (auto-generated)
│
├── 📁 backend/                         ← Flask API Server
│   ├── main.py                         ← Flask app & routes
│   ├── agents.py                       ← Agent implementations
│   ├── orchestrator.py                 ← Workflow orchestrator
│   ├── models.py                       ← Data models/factories
│   ├── requirements.txt                ← Python dependencies
│   └── 📁 vendor/                      ← Bundled dependencies
│
└── 📁 other files/
    └── (previous project files)
```

## 📄 Key Files Breakdown

### Frontend Files

#### 1. **App.jsx** (120 lines)
- Main routing component
- State management for view, loading, jobs, error
- API communication with backend
- Loading state UI
- Error handling modal

#### 2. **HomePage.jsx** (250 lines)
- Search form interface
- Hiring role dropdown (10+ Scaler courses)
- Experience level selector
- Job portals multi-select
- Advanced filters (skills, city)
- Form submission handler

#### 3. **ResultsPage.jsx** (370 lines)
- Job card display
- Insights metrics (4 cards)
- Platform distribution tags
- Match score filter slider
- Bulk action button
- Message editor (inline)
- Action buttons (Push, View, Skip)
- Empty state handling

#### 4. **HomePage.css** (800+ lines)
- Header with logo
- Hero section
- Form layout (3 columns)
- Portal dropdown styling
- Advanced filters section
- Info cards section
- Responsive breakpoints

#### 5. **ResultsPage.css** (800+ lines)
- Sticky header
- Insights grid
- Platform tags
- Filter section
- Job cards layout
- Message editor styling
- Action buttons
- Mobile responsive

#### 6. **index.html**
- HTML entry point
- Meta tags
- Root div for React
- Script loader

#### 7. **package.json**
- React 18.2.0
- Vite 5.4.21
- Axios (optional)
- Dev dependencies

### Backend Files

#### 1. **main.py** (118 lines)
- Flask app initialization
- CORS configuration
- `/health` endpoint
- `/workflow/run` endpoint (POST)
- `/messages` endpoints (GET, PUT, POST)
- `/stats` endpoint (GET)
- In-memory message storage

#### 2. **agents.py** (400+ lines)
- **JobFinderAgent**: Scrapes LinkedIn & RemoteOK
- **RelevanceAnalyzerAgent**: Scores jobs
- **RecruiterFinderAgent**: Finds HR from LinkedIn (NEW)
- **MessageGeneratorAgent**: Creates personalized messages
- Helper functions for scraping
- Tech keyword extraction

#### 3. **orchestrator.py** (97 lines)
- **CareersSalesOrchestrator**: Coordinates all agents
- Workflow execution
- Error handling
- Result caching

#### 4. **models.py** (variable)
- Job data structure
- Recruiter data structure
- Message data structure
- Factory functions

#### 5. **requirements.txt**
- Flask 2.x
- BeautifulSoup4
- Requests
- Playwright
- Flask-CORS

## 📊 Documentation Files

### 1. **README_REAL_TIME_SCRAPING.md**
- System overview
- Architecture explanation
- Real-time data flow
- API endpoints
- Recruiter discovery logic
- Technology stack
- Current capabilities
- Data privacy notes
- Performance metrics
- Future enhancements

### 2. **QUICK_START.md**
- Prerequisites (backend, frontend)
- Step-by-step usage guide
- Search form example
- Results interpretation
- Feature explanation
- Advanced configuration
- Troubleshooting guide
- Browser compatibility
- API examples

### 3. **IMPLEMENTATION_SUMMARY.md**
- Project completion overview
- System architecture
- Feature list
- Technical implementation
- Data flow walkthrough
- Real data example
- Design decisions
- Performance characteristics
- Learning outcomes
- Future roadmap
- Project statistics

### 4. **SYSTEM_STATUS.md**
- Current system status table
- Complete architecture diagram
- Data processing pipeline
- API request/response examples
- Technology stack details
- Performance metrics
- Data privacy & security
- Optimization opportunities
- Production readiness checklist
- Monitoring & analytics
- Configuration management
- Future roadmap (phases)

### 5. **RECRUITER_FINDER_GUIDE.md**
- RecruiterFinderAgent overview
- Step-by-step operation
- Implementation details
- Keyword priority system
- Fallback strategies
- Real-world examples
- Matching algorithm details
- Configuration options
- Error handling
- Performance characteristics
- Customization examples
- Production recommendations
- Monitoring strategies

## 🔗 File Dependencies

```
App.jsx
  └─ HomePage.jsx
  │   └─ HomePage.css
  └─ ResultsPage.jsx
      └─ ResultsPage.css

main.py
  ├─ orchestrator.py
  │   └─ agents.py
  │       ├─ models.py
  │       └─ (requests, beautifulsoup4)
  └─ (flask, flask-cors)

Frontend loads logo from:
  └─ public/scaler-logo.png
```

## 📦 External Dependencies

### Frontend (npm)
- react@18.2.0
- vite@5.4.21
- tailwindcss@3.3.0 (optional)

### Backend (pip)
- flask==2.x
- beautifulsoup4==4.12.2
- requests==2.31.0
- selenium==4.15.2
- playwright==1.40.0
- flask-cors==4.0.0

## 🚀 How to Navigate

### For Users:
1. Start with `QUICK_START.md` for usage guide
2. Reference `README_REAL_TIME_SCRAPING.md` for system understanding
3. Use `IMPLEMENTATION_SUMMARY.md` for feature overview

### For Developers:
1. Read `SYSTEM_STATUS.md` for architecture
2. Study `RECRUITER_FINDER_GUIDE.md` for recruiter logic
3. Explore source code:
   - `backend/agents.py` - Agent implementations
   - `frontend/src/App.jsx` - Router logic
   - `frontend/src/components/ResultsPage.jsx` - Main UI

### For DevOps/Deployment:
1. Check `SYSTEM_STATUS.md` - Production checklist
2. Review `requirements.txt` - Dependencies
3. Follow `QUICK_START.md` - Setup instructions

## 📝 Code Statistics

| File | Lines | Type | Purpose |
|------|-------|------|---------|
| App.jsx | 120 | JSX | Router & state |
| HomePage.jsx | 250 | JSX | Search form |
| ResultsPage.jsx | 370 | JSX | Job display |
| HomePage.css | 800+ | CSS | Form styling |
| ResultsPage.css | 800+ | CSS | Results styling |
| main.py | 118 | Python | Flask app |
| agents.py | 400+ | Python | Agent logic |
| orchestrator.py | 97 | Python | Coordinator |
| Documentation | 4000+ | Markdown | Guides & docs |

## 🔄 Workflow Files

### Real-Time Data Flow
1. **User Input** → App.jsx
2. **API Call** → main.py /workflow/run
3. **Job Scraping** → agents.py JobFinderAgent
4. **Relevance** → agents.py RelevanceAnalyzerAgent
5. **Recruiters** → agents.py RecruiterFinderAgent
6. **Messages** → agents.py MessageGeneratorAgent
7. **Response** → App.jsx
8. **Display** → ResultsPage.jsx

## 💾 Data Files

### Generated During Runtime
- In-memory message storage (Python dict)
- Frontend state (React useState)
- Browser cache (Vite assets)

### Static Files
- `scaler-logo.png` - Company branding

## 🔐 Configuration Files

- `frontend/vite.config.js` - Build configuration
- `frontend/package.json` - Dependencies & scripts
- `backend/requirements.txt` - Python dependencies

## 📱 Asset Files

- `public/scaler-logo.png` - 18KB PNG with transparency

## 🎯 How to Find Things

**Q: Where is the job scraping code?**  
A: `backend/agents.py` - `scrape_linkedin_jobs()` function

**Q: Where is the recruiter finder?**  
A: `backend/agents.py` - `find_recruiter_from_linkedin()` function

**Q: Where is the message generation?**  
A: `backend/agents.py` - `MessageGeneratorAgent` class

**Q: Where is the frontend router?**  
A: `frontend/src/App.jsx` - State-based conditional rendering

**Q: Where is the results display?**  
A: `frontend/src/components/ResultsPage.jsx`

**Q: Where is the search form?**  
A: `frontend/src/components/HomePage.jsx`

**Q: Where are the styles?**  
A: `frontend/src/components/ResultsPage.css` and `HomePage.css`

**Q: Where is the API setup?**  
A: `backend/main.py` - Flask routes

**Q: Where is the workflow coordination?**  
A: `backend/orchestrator.py` - `CareersSalesOrchestrator` class

## 🚀 Quick Reference

### Start Backend
```bash
cd backend
python3 main.py
```

### Start Frontend
```bash
cd frontend
npm run dev
```

### Test API
```bash
curl http://localhost:8000/health
curl http://localhost:3001
```

### View Logs
```bash
# Backend logs appear in terminal running main.py
# Frontend logs: Browser F12 > Console
```

---

**Version**: 1.0.0  
**Last Updated**: April 23, 2026  
**Total Files**: 15+  
**Status**: ✅ Complete & Operational
