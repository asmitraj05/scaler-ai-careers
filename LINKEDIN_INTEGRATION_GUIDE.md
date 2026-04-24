# LinkedIn Integration Guide

## 🎯 Overview

The LinkedIn integration provides **AI-assisted recruiter discovery** for sales representatives. Instead of manually searching LinkedIn, users can click "Connect on LinkedIn" and be taken to a **pre-filtered list of relevant recruiters** at the target company.

---

## 🔗 How It Works

### User Workflow

1. **User clicks "Connect on LinkedIn"** on a job card
2. **System checks** if recruiter profile exists
   - ✅ If yes → Opens direct LinkedIn profile
   - ❌ If no → Generates smart search URL
3. **Smart search URL includes:**
   - Company name
   - Context-aware recruiter keywords (HR, Recruiter, Hiring Manager, etc.)
   - Location filter (if available)
4. **User lands on LinkedIn** with pre-filtered recruiter list
5. **User can browse and connect manually** (LinkedIn approval required)

---

## 📦 Architecture

### Backend: `linkedin_utils.py`

**Core Functions:**

#### 1. `generate_linkedin_search_url(company, job_title=None, location=None)`

Generates a precise LinkedIn search URL.

**Parameters:**
- `company` (str, required): Company name
- `job_title` (str, optional): Job title for context
- `location` (str, optional): Location for filtering

**Returns:** Full LinkedIn search URL

**Example:**
```python
from linkedin_utils import generate_linkedin_search_url

url = generate_linkedin_search_url(
    company="Razorpay",
    job_title="Senior Backend Engineer",
    location="Bangalore"
)
# Returns: https://www.linkedin.com/search/results/people/?keywords=HR%20OR%20Recruiter%20OR%20Engineering%20Manager&currentCompany=Razorpay&geoUrn=102713980
```

---

#### 2. `get_recruiter_keywords(job_title=None, seniority=None)`

Generates context-aware recruiter search keywords based on job domain and seniority.

**Parameters:**
- `job_title` (str, optional): Job title to analyze
- `seniority` (str, optional): Job seniority level

**Returns:** Space-separated keywords with OR operators

**Keyword Selection Logic:**

| Job Domain | Keywords |
|-----------|----------|
| **Engineering** | HR, Recruiter, Engineering Manager, Tech Recruiter, Engineering Recruiter |
| **Data Science** | HR, Recruiter, Data Hiring Manager, Analytics Recruiter |
| **Product Manager** | HR, Recruiter, Product Recruiter, Hiring Manager |
| **Sales** | HR, Recruiter, Sales Recruiter, Talent Acquisition |
| **Default** | HR, Recruiter |

**Examples:**
```python
from linkedin_utils import get_recruiter_keywords

# Engineering role
get_recruiter_keywords("Senior Backend Engineer")
# Returns: "HR OR Recruiter OR Engineering Manager OR Tech Recruiter OR Engineering Recruiter"

# Data role
get_recruiter_keywords("Data Science Manager")
# Returns: "HR OR Recruiter OR Data Hiring Manager OR Analytics Recruiter OR Hiring Manager"

# Generic role
get_recruiter_keywords()
# Returns: "HR OR Recruiter"
```

---

#### 3. `extract_job_domain(job_title)`

Categorizes job role into a domain.

**Returns:** One of: `engineering`, `data`, `product`, `sales`, `hr`, `general`

**Examples:**
```python
extract_job_domain("Backend Engineer")       # 'engineering'
extract_job_domain("Data Scientist")         # 'data'
extract_job_domain("Product Manager")        # 'product'
extract_job_domain("Account Executive")      # 'sales'
```

---

#### 4. `sanitize_company_name(company_name)`

Cleans company names for better search results.

**Removes common suffixes:**
- Inc., Inc
- LLC
- Ltd., Ltd
- Corp, Corporation

**Example:**
```python
sanitize_company_name("Razorpay Inc.")  # Returns: "Razorpay"
```

---

#### 5. `get_location_urn(location)`

Maps location names to LinkedIn geo URNs.

**Supported Locations:**
- **India:** Bangalore, Mumbai, Delhi, Hyderabad, Pune, Gurgaon, Noida, Chennai, Kolkata
- **US:** San Francisco, New York, Los Angeles, Seattle, Chicago, Austin, Denver, Boston
- **Europe:** London, Manchester, Berlin, Paris, Amsterdam
- **APAC:** Singapore, Dubai

**Example:**
```python
get_location_urn("Bangalore")  # Returns: "102713980"
get_location_urn("San Francisco")  # Returns: "102393689"
```

---

### API Endpoint: `/linkedin/search-url`

**Method:** `POST`

**Request Body:**
```json
{
  "company": "Razorpay",
  "job_title": "Senior Backend Engineer",
  "location": "Bangalore"
}
```

**Response:**
```json
{
  "url": "https://www.linkedin.com/search/results/people/?keywords=HR%20OR%20Recruiter%20OR%20Engineering%20Manager&currentCompany=Razorpay&geoUrn=102713980",
  "keywords": "HR OR Recruiter OR Engineering Manager OR Tech Recruiter OR Engineering Recruiter",
  "company": "Razorpay",
  "job_title": "Senior Backend Engineer",
  "location": "Bangalore"
}
```

**Error Response:**
```json
{
  "error": "Company name is required"
}
```

---

### Frontend: React Integration

#### Component: `JobDetailPanel`

**New Function:** `handleConnectOnLinkedIn()`

```javascript
const handleConnectOnLinkedIn = async () => {
  // Check if recruiter has a direct LinkedIn profile URL
  if (job.recruiter && job.recruiter.linkedinUrl && job.recruiter.linkedinUrl.includes('/in/')) {
    window.open(job.recruiter.linkedinUrl, '_blank')
  } else {
    // Generate smart search URL
    const linkedinUrl = await generateLinkedInUrl()
    window.open(linkedinUrl, '_blank')
  }
}
```

**Flow:**
1. Check if job object has recruiter profile link (LinkedIn /in/ URL)
2. If yes, open that profile directly
3. If no, call backend API to generate smart search URL
4. Open generated URL in new tab

**Fallback Logic:**
```javascript
const generateLinkedInUrl = async () => {
  try {
    // Call backend API
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
    } else {
      // Fallback: Basic search with HR + Recruiter keywords
      const keywords = encodeURIComponent('HR Recruiter')
      const company = encodeURIComponent(job.company)
      return `https://www.linkedin.com/search/results/people/?keywords=${keywords}&currentCompany=${company}`
    }
  } catch (error) {
    // Fallback: Basic search on error
    const keywords = encodeURIComponent('HR Recruiter')
    const company = encodeURIComponent(job.company)
    return `https://www.linkedin.com/search/results/people/?keywords=${keywords}&currentCompany=${company}`
  }
}
```

---

## 🚀 Usage Examples

### Example 1: Engineering Role at Razorpay

**Input:**
```
Company: Razorpay
Job Title: Senior Backend Engineer
Location: Bangalore
```

**Generated URL:**
```
https://www.linkedin.com/search/results/people/?keywords=HR%20OR%20Recruiter%20OR%20Engineering%20Manager%20OR%20Tech%20Recruiter%20OR%20Engineering%20Recruiter&currentCompany=Razorpay&geoUrn=102713980
```

**What User Sees:**
- LinkedIn list of people at Razorpay
- Filtered by keywords: HR, Recruiter, Engineering Manager, Tech Recruiter
- Located in Bangalore

---

### Example 2: Data Science Role at Google

**Input:**
```
Company: Google
Job Title: Data Science Manager
Location: San Francisco
```

**Generated URL:**
```
https://www.linkedin.com/search/results/people/?keywords=HR%20OR%20Recruiter%20OR%20Data%20Hiring%20Manager%20OR%20Analytics%20Recruiter%20OR%20Hiring%20Manager&currentCompany=Google&geoUrn=102393689
```

---

### Example 3: Recruiter Profile Available

**Input:**
```
Company: Flipkart
Recruiter LinkedIn: https://www.linkedin.com/in/john-smith/
```

**Behavior:**
- Opens direct profile link: `https://www.linkedin.com/in/john-smith/`
- Skips URL generation (direct approach is more efficient)

---

## 🔒 Compliance & Safety

### ✅ What This Does (Compliant)

- **Assists navigation** to LinkedIn search results
- **Filters by company and keywords**
- **Opens LinkedIn in user's browser**
- **User manually connects** (LinkedIn approval required)

### ❌ What This Does NOT Do (Safe)

- ❌ Automate login to LinkedIn
- ❌ Scrape LinkedIn pages
- ❌ Send connection requests
- ❌ Use bots or headless browsers
- ❌ Store LinkedIn data
- ❌ Bypass LinkedIn policies

---

## 🛠️ Testing

### Test Backend Function

```bash
# From backend directory
python -m linkedin_utils
```

**Output:**
```
Engineering Role URL:
https://www.linkedin.com/search/results/people/?keywords=HR%20OR%20Recruiter%20OR%20Engineering%20Manager%20OR%20Tech%20Recruiter%20OR%20Engineering%20Recruiter&currentCompany=Razorpay&geoUrn=102713980

Data Role URL:
https://www.linkedin.com/search/results/people/?keywords=HR%20OR%20Recruiter%20OR%20Data%20Hiring%20Manager%20OR%20Analytics%20Recruiter%20OR%20Hiring%20Manager&currentCompany=Flipkart&geoUrn=102713980

Simple URL:
https://www.linkedin.com/search/results/people/?keywords=HR%20OR%20Recruiter&currentCompany=Google
```

---

### Test API Endpoint

```bash
curl -X POST http://localhost:8000/linkedin/search-url \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Razorpay",
    "job_title": "Senior Backend Engineer",
    "location": "Bangalore"
  }'
```

---

### Test Frontend

1. Open app at `http://localhost:5173`
2. Search for jobs
3. Click on a job card
4. Click "🔗 Connect on LinkedIn" button
5. Should open LinkedIn with filtered recruiter list

---

## 📊 Benefits Summary

| Before | After |
|--------|-------|
| ❌ Random search results | ✅ Context-aware keywords |
| ❌ 4-5 manual clicks | ✅ 1-2 clicks (search + browse) |
| ❌ No company context | ✅ Pre-filtered by company |
| ❌ No location filter | ✅ Optional location filter |
| ❌ Wrong recruiter type | ✅ Smart role-based keywords |

---

## 🔄 Integration Checklist

- [x] Backend: `linkedin_utils.py` created
- [x] API endpoint: `/linkedin/search-url` added
- [x] Frontend: `handleConnectOnLinkedIn()` integrated
- [x] Fallback logic implemented
- [x] Error handling added
- [x] Tooltip added to button
- [x] Documentation created

---

## 📝 Data Passed to LinkedIn

The system sends to LinkedIn:
- **Company name** (from job data)
- **Keywords** (generated, not scraped)
- **Location** (optional, from job data)

No personal data, passwords, or automation tokens are sent.

---

## 🚀 Future Enhancements

1. **Expanded Location Mapping**: Add more locations and geo URNs
2. **Role Templates**: Pre-built keyword sets for common roles
3. **Analytics**: Track which buttons are clicked
4. **A/B Testing**: Compare keyword effectiveness
5. **Custom Keywords**: Allow users to customize search terms
6. **Multi-language**: Support non-English company names

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| Button doesn't open URL | Check if backend is running on port 8000 |
| URL has encoding issues | Ensure company name is properly sanitized |
| Location URN not found | Check if location is in supported list |
| Direct profile not opening | Verify recruiter.linkedinUrl format (must contain '/in/') |
| Search results empty | LinkedIn may require login; user can refine search manually |

---

**Version:** 1.0.0  
**Status:** ✅ Production Ready  
**Last Updated:** April 23, 2026

---
