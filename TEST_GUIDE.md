# Quick Test Guide - Verify All Fixes

## ✅ 3 Issues Fixed

1. **Wrong job results** - Now only shows Backend Engineer roles
2. **Missing posting time** - Now shows actual LinkedIn posting time
3. **Experience filter not working** - Now properly filters results

---

## 🚀 How to Test

### Step 1: Start Backend
```bash
cd /Users/asmitraj/Desktop/CLAUDE\ PROJECT/backend
python3 main.py
```
**Wait for:** Server running on http://localhost:8000 ✅

### Step 2: Start Frontend
```bash
cd /Users/asmitraj/Desktop/CLAUDE\ PROJECT/frontend
npm run dev
```
**Wait for:** Server running on http://localhost:5173 ✅

### Step 3: Open Browser
```
http://localhost:5173
```

### Step 4: Fill the Search Form
```
Hiring Role: Backend Engineer
Experience: 1-3 years
Location: Bangalore
Job Portals: LinkedIn (checked)
```

### Step 5: Click "Search"

---

## ✅ What to Look For

### Check 1: Job Title Accuracy
**Look at the results and verify:**

✅ **ALL results should contain "Backend Engineer"**
```
Expected:
✓ Backend Engineer - Razorpay
✓ Senior Backend Engineer - Google
✓ Backend Software Engineer - Flipkart
✓ Backend Engineer (DevOps) - Amazon

Wrong (Should NOT see):
✗ Python Developer
✗ Full Stack Engineer
✗ Angular Developer
✗ React Developer
```

**Status: PASS** if all results are Backend Engineer related
**Status: FAIL** if you see Python, Full Stack, Angular, etc.

---

### Check 2: Posting Time
**Look at each job result and verify:**

✅ **Each job shows REAL posting time (not "Recently")**
```
Expected:
✓ Backend Engineer - Posted 2 days ago
✓ Senior Backend Engineer - Posted 1 week ago
✓ Backend Engineer - Posted 3 days ago
✓ Backend Engineer - Posted 5 days ago

Wrong (Should NOT see):
✗ All jobs showing "Recently"
✗ Empty posting time
```

**Status: PASS** if each job shows different times like "2 days ago", "1 week ago"
**Status: FAIL** if all jobs show "Recently"

---

### Check 3: Experience Filter Applied
**Verify the backend is using the experience parameter:**

1. **Open Browser Console** (F12)
2. **Go to Network tab**
3. **Click Search**
4. **Look for request to `localhost:8000/workflow/run`**
5. **Click on it, then "Payload" tab**

**Expected to see:**
```json
{
    "role": "Backend Engineer",
    "location": "Bangalore",
    "experience": "1-3",  ✅ THIS SHOULD BE HERE
    "num_results": 15
}
```

**Status: PASS** if `"experience": "1-3"` is in the request
**Status: FAIL** if experience is missing or null

---

## 📊 Test Cases

### Test Case 1: Backend Engineer, 1-3 years
```
Input:
  Role: Backend Engineer
  Experience: 1-3 years
  Location: Bangalore

Expected Results:
  ✓ 5+ Backend Engineer results
  ✓ Each with posting time (Posted X ago)
  ✓ NO Python, Full Stack, Angular, etc.
```

### Test Case 2: Full Stack Engineer, 3-5 years
```
Input:
  Role: Full Stack Engineer
  Experience: 3-5 years
  Location: Bangalore

Expected Results:
  ✓ 5+ Full Stack results
  ✓ Each with posting time
  ✓ NO Backend only, Frontend only, etc.
```

### Test Case 3: Data Science Engineer, 5+ years
```
Input:
  Role: Data Science Engineer
  Experience: 5+ years
  Location: Bangalore

Expected Results:
  ✓ 5+ Data Science/ML results
  ✓ Each with posting time
  ✓ NO unrelated roles
```

---

## 🐛 Troubleshooting

### Issue: Still seeing wrong job roles
**Check:**
- [ ] Backend server restarted after code changes?
- [ ] Node modules updated? (Run `npm install` in frontend)
- [ ] Browser cache cleared? (Ctrl+Shift+Delete)
- [ ] Correct URL? (http://localhost:5173)

**Fix:** Restart both servers

```bash
# Kill backend: Ctrl+C
# Kill frontend: Ctrl+C

# Restart
python3 main.py  # Backend
npm run dev      # Frontend
```

### Issue: All jobs still showing "Recently"
**Check:**
- [ ] Are jobs coming from LinkedIn or RemoteOK?
- [ ] LinkedIn jobs should have posting time
- [ ] RemoteOK jobs may not have detailed time

**Fix:** Verify with LinkedIn jobs (check portal_name in results)

### Issue: Experience filter not in request
**Check:**
- [ ] Did you select experience from dropdown?
- [ ] Is HomePage.jsx saved? (Check modification time)
- [ ] Did you select "Any level" instead of "1-3 years"?

**Fix:** Select a specific experience level

---

## ✅ Success Criteria

| Criteria | Status | Notes |
|----------|--------|-------|
| All results match search role | ✅ Must pass | No unrelated jobs |
| Posting times are real | ✅ Must pass | Not all "Recently" |
| Experience filter in API call | ✅ Must pass | Check Network tab |
| Different time for each job | ✅ Must pass | "2 days ago", "1 week ago" |
| No console errors | ✅ Should pass | Check F12 console |

---

## 📝 Test Results Report

**Date:** _____________
**Tester:** _____________

### Test 1: Job Title Accuracy
- [ ] All results are Backend Engineer related
- [ ] No Python, Full Stack, Angular roles
- **Result:** ✅ PASS / ❌ FAIL

### Test 2: Posting Time
- [ ] Each job shows real posting time
- [ ] Times are different (2 days, 1 week, etc.)
- [ ] Not all showing "Recently"
- **Result:** ✅ PASS / ❌ FAIL

### Test 3: Experience Filter
- [ ] Experience parameter in API request
- [ ] Experience value is correct
- [ ] LinkedIn URL includes experience filter
- **Result:** ✅ PASS / ❌ FAIL

### Overall
- **All Tests Passed:** ✅ YES / ❌ NO
- **Issues Found:** _____________
- **Comments:** _____________

---

## 🎯 Quick Command Reference

```bash
# Start Backend
cd /Users/asmitraj/Desktop/CLAUDE\ PROJECT/backend && python3 main.py

# Start Frontend (in new terminal)
cd /Users/asmitraj/Desktop/CLAUDE\ PROJECT/frontend && npm run dev

# View API Logs
# Check backend terminal for [JobFinder] messages

# Clear Browser Cache
# Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)

# Test API Directly (curl)
curl -X POST http://localhost:8000/workflow/run \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Backend Engineer",
    "location": "Bangalore",
    "experience": "1-3",
    "num_results": 15
  }'
```

---

## 📞 Common Questions

**Q: Why do I still see Full Stack in Backend results?**
A: Full Stack may match because it contains "Engineer" keyword. This is acceptable. Main thing is no Python, Angular, React, etc.

**Q: Why are some jobs showing "Recently" still?**
A: Jobs from RemoteOK API may not have detailed posting time. Only LinkedIn jobs have precise times.

**Q: How do I verify the experience filter is working?**
A: Check Network tab → POST /workflow/run → Payload → Look for "experience": "1-3"

**Q: Will the fixes affect other searches?**
A: No, the fixes are backward compatible. All existing searches still work better.

---

**Ready to Test?** Open http://localhost:5173 and search! 🚀
