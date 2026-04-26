import React, { useState, useEffect } from 'react'
import HomePage from './components/HomePage'
import ResultsPage2 from './components/ResultsPage2'
import LoaderPage from './components/LoaderPage'
import OutreachDashboard from './components/OutreachDashboard'

function App() {
  const [view, setView] = useState('input') // input, results, loading, outreach-dashboard
  const [loading, setLoading] = useState(false)
  const [jobs, setJobs] = useState([])
  const [error, setError] = useState(null)
  const [searchParams, setSearchParams] = useState({ role: '', location: '', portals: [], experience: '' })

  // Caching has been removed. Wipe any stale jobs_cache_* entries from
  // previous visits so users don't accidentally see them via leftover code.
  useEffect(() => {
    try {
      Object.keys(localStorage)
        .filter(k => k.startsWith('jobs_cache_'))
        .forEach(k => localStorage.removeItem(k))
    } catch (e) {
      // localStorage may be unavailable in private mode — ignore
    }
  }, [])

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  const handleSubmit = async (role, location, experience = '', portals = []) => {
    setLoading(true)
    setError(null)
    setSearchParams({ role, location, portals, experience })
    setView('loading')

    try {
      const response = await fetch(`${API_BASE}/workflow/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          role,
          location,
          experience: experience || undefined,
          portals,
          num_results: 100
        })
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      const data = await response.json()

      // Show loader for 5 seconds for better UX (applies to all roles)
      setTimeout(() => {
        processJobResults(data, role, location, portals)
        setLoading(false)
      }, 5000)
    } catch (err) {
      console.error('Workflow error:', err)
      setError(`Failed to search jobs. Make sure backend is running on port 8000. Error: ${err.message}`)
      setView('input')
      setLoading(false)
    }
  }

  const processJobResults = (data, role, location, portals) => {
    if (data.error) {
      setError(data.error)
      setView('input')
    } else if (data.results && data.results.length > 0) {
      // Transform API results to match ResultsPage2 format

        // Parse posted_at into both age-in-ms (for filters) and a friendly
        // display string. Handles two upstream shapes: ISO timestamps from
        // Indeed (e.g. "2026-04-05T00:00:00.000Z") and relative strings
        // from the LinkedIn scraper (e.g. "2 weeks ago", "1 day ago").
        const parsePostedAt = (raw) => {
          if (!raw) return { ms: null, display: 'Recently' }

          const str = String(raw).trim()

          // Try ISO / RFC2822 / parseable date first.
          const parsed = Date.parse(str)
          if (!isNaN(parsed)) {
            const ms = Math.max(0, Date.now() - parsed)
            return { ms, display: relativeLabel(ms) }
          }

          // Fall back to "<n> <unit> ago" relative strings.
          const match = str.toLowerCase().match(/(\d+|a|an|few)\s*(hour|day|week|month|year)s?/)
          if (!match) return { ms: null, display: str }

          let n = match[1]
          if (n === 'a' || n === 'an') n = 1
          else if (n === 'few') n = 3
          else n = parseInt(n, 10)

          const unit = match[2]
          const HOUR = 60 * 60 * 1000
          const DAY  = 24 * HOUR
          const factor = unit === 'hour' ? HOUR
            : unit === 'day'   ? DAY
            : unit === 'week'  ? 7 * DAY
            : unit === 'month' ? 30 * DAY
            : 365 * DAY
          const ms = n * factor
          return { ms, display: relativeLabel(ms) }
        }

        const relativeLabel = (ms) => {
          const HOUR = 60 * 60 * 1000
          const DAY  = 24 * HOUR
          if (ms < HOUR)        return 'Just now'
          if (ms < DAY)         return `${Math.floor(ms / HOUR)}h ago`
          if (ms < 7 * DAY)     return `${Math.floor(ms / DAY)}d ago`
          if (ms < 30 * DAY)    return `${Math.floor(ms / (7 * DAY))}w ago`
          if (ms < 365 * DAY)   return `${Math.floor(ms / (30 * DAY))}mo ago`
          return `${Math.floor(ms / (365 * DAY))}y ago`
        }

        // Helper function to parse experience
        const parseExperience = (expStr) => {
          if (!expStr) return ''
          const str = expStr.toLowerCase().trim()
          if (str.includes('0-1') || str.includes('0 to 1') || str.includes('fresher') || str.includes('entry')) return '0-1'
          if (str.includes('1-3') || str.includes('1 to 3')) return '1-3'
          if (str.includes('3-5') || str.includes('3 to 5')) return '3-5'
          if (str.includes('5+') || str.includes('5 year') || str.includes('senior') || str.includes('expert')) return '5+'
          return ''
        }

        const transformedJobs = data.results.map((result, idx) => {
          // Prefer the canonical posted_at (ISO from Indeed; relative string
          // from LinkedIn). Fall back to legacy posted_date fields.
          const rawPosted = result.job['posted_at']
            || result.job['posted_date']
            || result.posted_date
            || null
          const { ms: postedDateMs, display: postedDateDisplay } = parsePostedAt(rawPosted)

          // Get and parse experience
          const experienceStr = result.job['experience'] || result.experience_required || result.job['experience_required'] || ''
          const experience = parseExperience(experienceStr)

          return {
            id: result.id || `job-${idx}`,
            company: result.company_name || 'Unknown Company',
            role: result.job_title || 'Unknown Role',
            location: result.job['city'] || result.job['full_address'] || result.job['state'] || result.job['location'] || 'India',
            platform: result.job['source_portal'] || result.job['portal_name'] || 'LinkedIn',
            jobUrl: (result.job['apply_link'] || result.job['job_url'] || result.job_url || '#').replace(/^(https?:\/\/)([a-z]{2,3})\.linkedin\.com\//i, '$1www.linkedin.com/'),
            postedDate: postedDateDisplay,
            postedDateMs: postedDateMs,
            experience: experience,
            matchScore: result.relevance_score || 0.85,
            reason: result.reason || 'Relevant opportunity',
            status: 'qualified',
            recruiter: {
              name: result.recruiter_name || 'Hiring Manager',
              role: result.recruiter_title || 'Talent Acquisition',
              linkedinUrl: `https://linkedin.com/search/results/people/?keywords=${encodeURIComponent(result.recruiter_name)}`
            },
            message: result.message_body || `Hi ${result.recruiter_name},\n\nI came across your opening for ${result.job_title} at ${result.company_name}.\n\nI have extensive experience with the technologies and practices your team uses. I believe I would be a great fit for this role.\n\nWould love to discuss how I can contribute to your team.\n\nBest regards,\nScaler Academy`,
            pushed: false,
            messageGenerated: true,
            tech_stack: result.job['tech_stack'] || [],
            description: result.job['description'] || ''
          }
        })

        setJobs(transformedJobs)
        setView('results')
      } else {
        setError('No jobs found matching your criteria')
        setView('input')
      }
  }

  const handleBack = () => {
    setView('input')
    setJobs([])
    setError(null)
  }

  return (
    <div className="app">
      {view === 'input' && (
        <HomePage
          onSubmit={handleSubmit}
          loading={loading}
          onNavigateToDashboard={() => setView('outreach-dashboard')}
        />
      )}

      {view === 'loading' && (
        <LoaderPage
          role={searchParams.role}
          location={searchParams.location}
          portals={searchParams.portals}
          onNavigateToDashboard={() => setView('outreach-dashboard')}
        />
      )}

      {view === 'results' && jobs.length > 0 && (
        <ResultsPage2
          jobs={jobs}
          onBack={handleBack}
          searchParams={searchParams}
          onNavigateToDashboard={() => setView('outreach-dashboard')}
        />
      )}

      {view === 'outreach-dashboard' && (
        <OutreachDashboard
          onNavigateBack={() => setView('input')}
        />
      )}

      {error && view === 'input' && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'white',
            padding: '2rem',
            borderRadius: '12px',
            maxWidth: '500px',
            textAlign: 'center'
          }}>
            <h2 style={{ color: '#ef4444', marginBottom: '1rem' }}>Error</h2>
            <p style={{ marginBottom: '1.5rem', color: '#4a5568' }}>{error}</p>
            <button onClick={() => setError(null)} style={{
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '1rem'
            }}>
              Try Again
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
