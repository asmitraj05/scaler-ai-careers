# LinkedIn Integration - Developer Reference

## 🚀 Quick Integration Reference

### For Frontend Developers

**Button Integration:**
```jsx
<button
  className="btn-linkedin-detail"
  onClick={handleConnectOnLinkedIn}
  title="Find relevant recruiters on LinkedIn"
>
  🔗 Connect on LinkedIn
</button>
```

**Handler Function:**
```jsx
const handleConnectOnLinkedIn = async () => {
  // Check for direct profile
  if (job.recruiter?.linkedinUrl?.includes('/in/')) {
    window.open(job.recruiter.linkedinUrl, '_blank')
  } else {
    // Generate smart URL
    const linkedinUrl = await generateLinkedInUrl()
    window.open(linkedinUrl, '_blank')
  }
}

const generateLinkedInUrl = async () => {
  try {
    const response = await fetch('http://localhost:8000/linkedin/search-url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company: job.company,
        job_title: job.role,
        location: job.location
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      return data.url
    }
  } catch (error) {
    console.error('Error:', error)
  }
  
  // Fallback
  return generateFallbackUrl(job.company)
}
```

---

### For Backend Developers

**Python Function Call:**
```python
from linkedin_utils import generate_linkedin_search_url

url = generate_linkedin_search_url(
    company="Razorpay",
    job_title="Backend Engineer",
    location="Bangalore"
)
print(url)
```

**API Endpoint:**
```python
@app.route('/linkedin/search-url', methods=['POST'])
def generate_linkedin_url():
    data = request.get_json()
    company = data.get('company')
    job_title = data.get('job_title')
    location = data.get('location')
    
    url = generate_linkedin_search_url(company, job_title, location)
    
    return jsonify({
        "url": url,
        "keywords": get_recruiter_keywords(job_title),
        "company": company
    })
```

---

## 🔧 Common Customizations

### 1. Add New Job Domain

**File:** `backend/linkedin_utils.py`

**Find:** `extract_job_domain()` function

**Add:**
```python
elif any(kw in title_lower for kw in ['marketing', 'brand', 'growth']):
    return 'marketing'
```

**Then in `get_recruiter_keywords()`:**
```python
elif domain == 'marketing':
    keywords.extend(['Marketing Manager', 'Growth Recruiter'])
```

---

### 2. Add New Location

**File:** `backend/linkedin_utils.py`

**Find:** `get_location_urn()` function

**Add to `location_map` dict:**
```python
'mumbai': '102713273',
'sydney': '102454443',
'toronto': '102394217',
```

To find LinkedIn geo URNs:
1. Open LinkedIn
2. Search for location in People search
3. Copy the `geoUrn` from URL

---

### 3. Change Default Keywords

**File:** `backend/linkedin_utils.py`

**Find:** `get_recruiter_keywords()` function

**Modify:**
```python
base_keywords = ['Talent Acquisition', 'HR Manager']  # Changed from ['HR', 'Recruiter']
```

---

### 4. Update API Endpoint Configuration

**File:** `backend/main.py`

**Current:**
```python
@app.route('/linkedin/search-url', methods=['POST'])
def generate_linkedin_url():
    # endpoint logic
```

**To add authentication:**
```python
@app.route('/linkedin/search-url', methods=['POST'])
@require_auth  # Add your auth decorator
def generate_linkedin_url():
    # endpoint logic
```

---

## 🧪 Testing Snippets

### Test Individual Functions

```python
# Test 1: Extract job domain
from linkedin_utils import extract_job_domain
assert extract_job_domain("Backend Engineer") == 'engineering'
assert extract_job_domain("Data Scientist") == 'data'

# Test 2: Get keywords
from linkedin_utils import get_recruiter_keywords
keywords = get_recruiter_keywords("Senior Backend Engineer")
assert "Engineering Manager" in keywords
assert "Tech Recruiter" in keywords

# Test 3: Generate URL
from linkedin_utils import generate_linkedin_search_url
url = generate_linkedin_search_url("Google", "Product Manager")
assert "Google" in url
assert "keywords=" in url

# Test 4: Sanitize company
from linkedin_utils import sanitize_company_name
assert sanitize_company_name("Microsoft Inc.") == "Microsoft"
assert sanitize_company_name("Amazon LLC") == "Amazon"
```

### Test API Endpoint

```python
# Using requests library
import requests

response = requests.post(
    'http://localhost:8000/linkedin/search-url',
    json={
        'company': 'Google',
        'job_title': 'Product Manager',
        'location': 'San Francisco'
    }
)

assert response.status_code == 200
data = response.json()
assert 'url' in data
assert 'keywords' in data
assert 'Google' in data['url']
```

### Test Frontend Integration

```javascript
// In browser console
// Test 1: Check function exists
typeof handleConnectOnLinkedIn === 'function'  // true

// Test 2: Call with test data
const testJob = {
  company: 'Google',
  role: 'Product Manager',
  location: 'San Francisco',
  recruiter: { linkedinUrl: 'https://linkedin.com/search' }
}

// Test 3: Mock API response
const mockResponse = {
  url: 'https://www.linkedin.com/search/...'
}

// Test 4: Verify URL opens
window.open(mockResponse.url, '_blank')
```

---

## 📊 Performance Considerations

### API Response Time

**Target:** < 200ms

**If slower:**
1. Cache results (company + role combinations)
2. Pre-generate common URLs
3. Move to background worker

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def generate_linkedin_search_url(company, job_title=None, location=None):
    # Cached version
    pass
```

---

### Frontend Optimization

**Current:** Generates URL on-demand

**To optimize:**
```javascript
// Cache generated URLs
const urlCache = new Map()

const getCachedUrl = async (company, role, location) => {
  const key = `${company}|${role}|${location}`
  
  if (urlCache.has(key)) {
    return urlCache.get(key)
  }
  
  const url = await generateLinkedInUrl()
  urlCache.set(key, url)
  return url
}
```

---

## 🔍 Debugging Guide

### Check Backend

```bash
# 1. Verify imports work
cd backend
python3 -c "from linkedin_utils import generate_linkedin_search_url; print('OK')"

# 2. Test function directly
python3 -c "from linkedin_utils import generate_linkedin_search_url; print(generate_linkedin_search_url('Google', 'Backend Engineer', 'San Francisco'))"

# 3. Check API endpoint
curl -X POST http://localhost:8000/linkedin/search-url \
  -H "Content-Type: application/json" \
  -d '{"company": "Google"}'

# 4. Check CORS
curl -I http://localhost:8000/health
```

### Check Frontend

```javascript
// 1. Check function exists
console.log(typeof handleConnectOnLinkedIn)

// 2. Test API call
fetch('http://localhost:8000/linkedin/search-url', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ company: 'Google' })
})
.then(r => r.json())
.then(d => console.log(d))
.catch(e => console.error(e))

// 3. Check job data
console.log(job)

// 4. Verify button attached
document.querySelector('.btn-linkedin-detail')
```

---

## 🐛 Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| 404 on API call | Backend not running | Start `python3 main.py` |
| CORS error | Cross-origin blocked | Already enabled in main.py, check origins |
| Empty keywords | Job title not parsed | Check job_title format |
| Invalid URL | Company name too short | Verify company name |
| No location filter | Location not in map | Add to `get_location_urn()` |
| Profile URL not opening | URL format wrong | Check for `/in/` in URL |

---

## 📈 Extending the System

### Add Custom Keyword Rules

```python
def get_recruiter_keywords_advanced(job_title, company=None, level=None):
    keywords = get_recruiter_keywords(job_title)
    
    # Add company-specific keywords
    if company and 'startup' in company.lower():
        keywords.extend(['Founder', 'Co-founder'])
    
    # Add level-specific keywords
    if level == 'executive':
        keywords.extend(['VP', 'C-Level'])
    
    return keywords
```

### Add ML-Based Domain Detection

```python
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# Train once
model = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('nb', MultinomialNB())
])

# Use in production
def extract_job_domain_ml(job_title):
    prediction = model.predict([job_title])[0]
    return prediction
```

### Add Analytics

```python
import logging

logger = logging.getLogger(__name__)

@app.route('/linkedin/search-url', methods=['POST'])
def generate_linkedin_url():
    data = request.get_json()
    
    # Log the request
    logger.info(f"LinkedIn search: {data['company']}, {data.get('job_title')}")
    
    # ... generate URL ...
    
    # Log the success
    logger.info(f"Generated URL for: {data['company']}")
    
    return jsonify(result)
```

---

## 🔐 Security Checklist

- [x] No hardcoded credentials
- [x] Input validation (company name required)
- [x] CORS configured
- [x] No user data stored
- [x] HTTPS ready (uses external LinkedIn URLs)
- [x] Rate limiting possible to add
- [x] Error messages don't leak info

---

## 📚 Related Code Locations

```
Project Structure:
├── backend/
│   ├── linkedin_utils.py          ← Core logic
│   ├── linkedin_examples.py       ← Examples
│   ├── main.py                    ← API endpoint (line ~100)
│   └── ...
├── frontend/
│   ├── src/components/
│   │   ├── ResultsPage2.jsx       ← handleConnectOnLinkedIn (line ~150)
│   │   └── ...
│   └── ...
├── LINKEDIN_INTEGRATION_GUIDE.md  ← Full docs
├── LINKEDIN_SETUP_QUICKSTART.md   ← Quick start
└── LINKEDIN_DEVELOPER_REFERENCE.md ← This file
```

---

## 🎯 Key Functions at a Glance

| Function | Location | Input | Output |
|----------|----------|-------|--------|
| `generate_linkedin_search_url()` | linkedin_utils.py:80 | company, job_title, location | Full LinkedIn URL |
| `get_recruiter_keywords()` | linkedin_utils.py:45 | job_title, seniority | Keywords string |
| `extract_job_domain()` | linkedin_utils.py:10 | job_title | Domain category |
| `sanitize_company_name()` | linkedin_utils.py:95 | company_name | Clean name |
| `get_location_urn()` | linkedin_utils.py:115 | location | LinkedIn geo URN |
| `handleConnectOnLinkedIn()` | ResultsPage2.jsx:150 | None (uses job context) | Opens URL |

---

## 💬 Integration Patterns

### Pattern 1: Direct URL Opening

```jsx
window.open(url, '_blank')
```

### Pattern 2: API-Based (Current)

```jsx
const response = await fetch('/linkedin/search-url', {
  method: 'POST',
  body: JSON.stringify(data)
})
const { url } = await response.json()
window.open(url, '_blank')
```

### Pattern 3: Server-Rendering (Alternative)

```jsx
// Pre-generate URLs on backend, pass in job data
// No API call needed on click
```

---

## 📝 Code Quality Standards

- ✅ Functions have docstrings
- ✅ Variable names are descriptive
- ✅ No hardcoded values (except defaults)
- ✅ Error handling present
- ✅ Modular design
- ✅ Tested and documented

---

## 🚀 Deployment Checklist

- [ ] Backend running on production URL
- [ ] Frontend updated with production backend URL
- [ ] CORS properly configured
- [ ] Error logging enabled
- [ ] Rate limiting configured
- [ ] Database backups in place
- [ ] Monitoring alerts set up
- [ ] Load testing completed

---

**Document Version:** 1.0.0  
**Last Updated:** April 23, 2026  
**Status:** ✅ Complete

---
