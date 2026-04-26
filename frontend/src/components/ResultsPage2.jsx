import React, { useState, useMemo, useEffect } from 'react'
import './ResultsPage2.css'
import ConfirmOutreachModal from './ConfirmOutreachModal'

// Platform color mapping
const platformColors = {
  'LinkedIn': '#0077b5',
  'Naukri': '#FF6B35',
  'Instahyre': '#4A90E2',
  'Indeed': '#003366',
  'Shine': '#FFC107',
  'RemoteOK': '#17b978'
}

const ITEMS_PER_PAGE = 10

// Known LinkedIn slugs for companies whose URL doesn't match their name.
// Add entries here when you find a company whose default slug 404s on LinkedIn.
const LINKEDIN_SLUG_OVERRIDES = {
  'swiggy': 'swiggy-in',
  'zomato': 'zomato',
  'flipkart': 'flipkart',
  'paytm': 'paytm',
  'ola': 'olacabs',
  'ola cabs': 'olacabs',
  'phonepe': 'phonepe',
  'cred': 'cred-club',
  'meesho': 'meesho',
  'unacademy': 'unacademy',
  'byju\'s': 'byjus',
  'byjus': 'byjus',
  'razorpay': 'razorpay',
  'urban company': 'urbancompany',
  'urbanclap': 'urbancompany',
  'dream11': 'dream11',
  'cure.fit': 'cure-fit',
  'curefit': 'cure-fit',
  'tata 1mg': '1mgofficial',
  '1mg': '1mgofficial',
  'pharmeasy': 'pharmeasy',
  'nykaa': 'nykaa',
  'snapdeal': 'snapdeal',
  'amazon': 'amazon',
  'microsoft': 'microsoft',
  'google': 'google',
  'meta': 'meta',
  'apple': 'apple',
  'netflix': 'netflix',
  'tesco': '-tesco',
  'kronosx': 'kronosxai',
  'kronosx ai': 'kronosxai',
}

function getLinkedInCompanySlug(company) {
  if (!company) return ''
  const cleaned = company
    .replace(/\s+(Inc\.?|LLC|Ltd\.?|Pvt\.?|Private|Limited|Corp\.?|Corporation|Technologies|Tech|Solutions)$/i, '')
    .trim()
    .toLowerCase()
  if (LINKEDIN_SLUG_OVERRIDES[cleaned]) return LINKEDIN_SLUG_OVERRIDES[cleaned]
  return cleaned.replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
}

// Parse raw LinkedIn description text into structured blocks (headings, lists, paragraphs)
function FormattedDescription({ text }) {
  const blocks = []
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean)

  let currentList = null
  const flushList = () => {
    if (currentList) {
      blocks.push({ type: 'list', items: currentList })
      currentList = null
    }
  }

  const isBullet = (l) => /^([·•●▪◦*\-–—]|\d+[.)])\s+/.test(l)
  const stripBullet = (l) => l.replace(/^([·•●▪◦*\-–—]|\d+[.)])\s+/, '')
  const isHeading = (l) =>
    l.length < 80 && l.endsWith(':') && !isBullet(l)

  for (const line of lines) {
    if (isBullet(line)) {
      if (!currentList) currentList = []
      currentList.push(stripBullet(line))
    } else if (isHeading(line)) {
      flushList()
      blocks.push({ type: 'heading', text: line.replace(/:$/, '') })
    } else {
      flushList()
      blocks.push({ type: 'paragraph', text: line })
    }
  }
  flushList()

  return (
    <div className="desc-formatted">
      {blocks.map((b, i) => {
        if (b.type === 'heading') return <h4 key={i} className="desc-heading">{b.text}</h4>
        if (b.type === 'list') return (
          <ul key={i} className="desc-list">
            {b.items.map((it, j) => <li key={j}>{it}</li>)}
          </ul>
        )
        return <p key={i} className="desc-paragraph">{b.text}</p>
      })}
    </div>
  )
}

// Bulk Action Bar Component
function BulkActionBar({ selectedCount, onBulkPush }) {
  if (selectedCount === 0) return null

  return (
    <div className="bulk-action-bar">
      <div className="bulk-action-content">
        <span className="bulk-info">
          {selectedCount} job{selectedCount !== 1 ? 's' : ''} selected
        </span>
        <button className="bulk-action-button" onClick={onBulkPush}>
          📤 Post Selected to Scaler Portal
        </button>
      </div>
    </div>
  )
}

// Filter Bar Component
function FilterBar({ filters, onToggleFilter, onSelectAll, isAllSelected, selectedCount, totalCount, searchParams = {} }) {

  return (
    <div className="filter-bar">
      {/* Main Filter Row */}
      <div className="filter-row">
        {/* Select All Checkbox */}
        <div className="filter-group-select">
          <input
            type="checkbox"
            checked={isAllSelected}
            onChange={(e) => onSelectAll(e.target.checked)}
            id="select-all-jobs"
          />
          <label htmlFor="select-all-jobs">Select All</label>
          {selectedCount > 0 && <span className="selection-count">({selectedCount} selected)</span>}
        </div>

        {/* Posted Time Filter */}
        <div className="filter-group">
          <span className="filter-label">Posted:</span>
          <div className="filter-buttons">
            {['24h', '3d', '7d', 'anytime'].map(time => (
              <button
                key={time}
                className={`filter-button ${filters.postedTime === time ? 'active' : ''}`}
                onClick={() => onToggleFilter('postedTime', time)}
              >
                {time === '24h' ? 'Last 24h' : time === '3d' ? 'Last 3 days' : time === '7d' ? 'Last 7 days' : 'Anytime'}
              </button>
            ))}
          </div>
        </div>

        {/* Experience Filter */}
        <div className="filter-group">
          <span className="filter-label">Experience:</span>
          <div className="filter-buttons">
            {Object.entries(experienceLevels).map(([key, label]) => (
              <button
                key={key}
                className={`filter-button ${filters.experience === key ? 'active' : ''}`}
                onClick={() => onToggleFilter('experience', key)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Platform Filter */}
        <div className="filter-group">
          <span className="filter-label">Platform:</span>
          <div className="filter-buttons">
            {['Others', 'LinkedIn', 'Naukri', 'Instahyre'].map(platform => (
              <button
                key={platform}
                className={`filter-button ${filters.platforms.includes(platform) ? 'active' : ''}`}
                onClick={() => onToggleFilter('platform', platform)}
              >
                {platform}
              </button>
            ))}
          </div>
        </div>

        {/* Location Filter */}
        <div className="filter-group location-group">
          <span className="filter-label">Location:</span>
          <input
            type="text"
            placeholder="Filter by location..."
            value={filters.location}
            onChange={(e) => onToggleFilter('location', e.target.value)}
            className="location-input"
          />
        </div>
      </div>
    </div>
  )
}

// Job List Panel Component
function JobListPanel({ jobs, selectedJobId, onSelectJob, currentPage, onPageChange, selectedJobs, onSelectionChange, searchParams = {} }) {
  const totalPages = Math.ceil(jobs.length / ITEMS_PER_PAGE)
  const startIdx = (currentPage - 1) * ITEMS_PER_PAGE
  const paginatedJobs = jobs.slice(startIdx, startIdx + ITEMS_PER_PAGE)

  const formatDate = (date) => {
    if (!date) return 'Recently'
    const now = new Date()
    const jobDate = new Date(date)
    const diffTime = Math.abs(now - jobDate)
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return '1 day ago'
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
    return `${Math.floor(diffDays / 30)} months ago`
  }

  const getMatchScoreBadge = (score) => {
    if (score >= 0.90) return { color: '#10b981', label: 'Excellent' }
    if (score >= 0.85) return { color: '#f59e0b', label: 'Good' }
    if (score >= 0.75) return { color: '#3b82f6', label: 'Fair' }
    return { color: '#6b7280', label: 'Ok' }
  }

  const getPlatformDiversity = () => {
    const platforms = new Set(jobs.map(j => j.platform))
    return Array.from(platforms).slice(0, 6)
  }

  const diversePlatforms = getPlatformDiversity()

  return (
    <div className="job-list-panel">
      {/* Header */}
      <div className="list-header">
        <h2>Jobs Found{searchParams.role ? `: ${searchParams.role}` : ''}</h2>
        <span className="jobs-count">{jobs.length}</span>
        {/* Platform diversity badges */}
        {diversePlatforms.length > 1 && (
          <div className="platform-diversity">
            {diversePlatforms.map((platform) => (
              <span
                key={platform}
                className="diversity-badge"
                style={{ backgroundColor: platformColors[platform] }}
                title={platform}
              >
                {platform.substring(0, 3)}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Jobs List */}
      <div className="jobs-list-container">
        {paginatedJobs.map((job, index) => {
          const isSelected = selectedJobId === job.id

          const isJobSelected = selectedJobs.has(job.id)
          return (
            <div
              key={job.id}
              className={`job-list-item ${isSelected ? 'selected' : ''} ${isJobSelected ? 'checkbox-selected' : ''}`}
            >
              {/* Checkbox */}
              <input
                type="checkbox"
                className="job-checkbox"
                checked={isJobSelected}
                onChange={(e) => {
                  e.stopPropagation()
                  onSelectionChange(job.id)
                }}
              />

              {/* Selection indicator */}
              <div
                className="selection-indicator"
                onClick={() => onSelectJob(job.id)}
              />

              <div
                className="job-list-content"
                onClick={() => onSelectJob(job.id)}
              >

              {/* Job info */}
                {/* Company and source */}
                <div className="job-list-header">
                  <span className="company-name">{job.company}</span>
                  <span
                    className="platform-badge"
                    style={{ borderColor: platformColors[job.platform] }}
                  >
                    <span
                      className="platform-dot"
                      style={{ backgroundColor: platformColors[job.platform] }}
                    />
                    {job.platform === 'Indeed' ? 'Others' : job.platform}
                  </span>
                </div>

                {/* Job role */}
                <h3 className="job-role">{job.role}</h3>

                {/* Location and time */}
                <div className="job-meta">
                  <span>📍 {job.location}</span>
                  {job.postedDate && <span>⏱️ {job.postedDate}</span>}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Pagination */}
      <div className="pagination">
        <button
          className="pagination-btn"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
        >
          ← Previous
        </button>

        <div className="page-numbers">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
            <button
              key={page}
              className={`page-number ${currentPage === page ? 'active' : ''}`}
              onClick={() => onPageChange(page)}
            >
              {page}
            </button>
          ))}
        </div>

        <button
          className="pagination-btn"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
        >
          Next →
        </button>
      </div>

      <div className="pagination-info">
        Page {currentPage} of {totalPages} ({jobs.length} total jobs)
      </div>
    </div>
  )
}

// Job Detail Panel Component
function JobDetailPanel({ job, onBack, onPush, onSkip, isBulkSelectionActive = false }) {
  const [message, setMessage] = useState(job?.message || '')
  const [isEditing, setIsEditing] = useState(false)
  const [isPushing, setIsPushing] = useState(false)
  const [showOutreachModal, setShowOutreachModal] = useState(false)
  const [realDescription, setRealDescription] = useState(null)
  const [descLoading, setDescLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  const jobPageUrl = job?.jobUrl || job?.job_url || ''
  const isLinkedInJob =
    (job?.platform || '').toLowerCase() === 'linkedin' ||
    /linkedin\.com/i.test(jobPageUrl)

  useEffect(() => {
    setRealDescription(null)
    if (!jobPageUrl || !isLinkedInJob) return
    setDescLoading(true)
    fetch(`http://localhost:8000/job-description?url=${encodeURIComponent(jobPageUrl)}`)
      .then(r => r.json())
      .then(data => {
        const desc = data.description || null
        setRealDescription(desc)
        // Generate contextual outreach using the fetched description
        return fetch('http://localhost:8000/generate-outreach', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            company: job?.company || '',
            role: job?.role || '',
            recruiter_name: job?.recruiter?.name || 'Hiring Team',
            description: desc || '',
          }),
        })
      })
      .then(r => r && r.json())
      .then(data => {
        if (data && data.message) setMessage(data.message)
      })
      .catch(err => { console.error('[JobDesc] error:', err) })
      .finally(() => setDescLoading(false))
  }, [job?.id, jobPageUrl, isLinkedInJob])

  if (!job) {
    return (
      <div className="job-detail-panel empty">
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <h2>No job selected</h2>
          <p>Select a job from the list to view details</p>
        </div>
      </div>
    )
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
      } else {
        // Fallback to basic search
        const keywords = encodeURIComponent('HR Recruiter')
        const company = encodeURIComponent(job.company)
        return `https://www.linkedin.com/search/results/people/?keywords=${keywords}&currentCompany=${company}`
      }
    } catch (error) {
      console.error('Error generating LinkedIn URL:', error)
      // Fallback URL generation
      const keywords = encodeURIComponent('HR Recruiter')
      const company = encodeURIComponent(job.company)
      return `https://www.linkedin.com/search/results/people/?keywords=${keywords}&currentCompany=${company}`
    }
  }

  const handleConnectOnLinkedIn = () => {
    // Build URL synchronously — window.open() must be called directly
    // from a user gesture, never after an await, or browsers block it.
    let linkedinUrl
    if (job.recruiter?.linkedinUrl && job.recruiter.linkedinUrl.includes('/in/')) {
      linkedinUrl = job.recruiter.linkedinUrl
    } else {
      const keywords = encodeURIComponent('HR Recruiter')
      const company  = encodeURIComponent(job.company || '')
      linkedinUrl = `https://www.linkedin.com/search/results/people/?keywords=${keywords}&currentCompany=${company}`
    }

    // Open immediately — synchronous, direct from click
    window.open(linkedinUrl, '_blank')

    // Show modal
    setShowOutreachModal(true)

    // Log outreach asynchronously in background (non-blocking)
    fetch('http://localhost:8000/create-outreach', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company_name:   job.company,
        job_role:       job.role,
        recruiter_name: 'Hiring Team',
        recruiter_email: job.recruiter?.role || 'Talent Acquisition',
        linkedin_url:   job.recruiter?.linkedinUrl || ''
      })
    }).catch(err => console.error('Outreach log failed:', err))
  }

  const handleOutreachConfirmed = () => {
    setShowOutreachModal(false)
    console.log('✅ Connection logged with real HR details')
  }

  const handlePush = async () => {
    setIsPushing(true)
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 800))
      onPush(job.id)
      alert(`✅ Job pushed to Scaler! Message sent to ${job.recruiter.name}`)
    } catch (error) {
      alert('Error pushing job')
    } finally {
      setIsPushing(false)
    }
  }

  return (
    <div className="job-detail-panel">
      {/* Detail Header */}
      <div className="detail-header">
        <div className="detail-title">
          <h1>{job.role}</h1>
          <div className="detail-meta">
            <span className="company-badge">@{job.company}</span>
            <span className="location-badge">📍 {job.location}</span>
            {job.postedDate && <span className="posted-time-badge">⏱️ {job.postedDate}</span>}
          </div>
          <button
            className="btn-view-job-header"
            style={{ backgroundColor: platformColors[job.platform] }}
            onClick={() => jobPageUrl && window.open(jobPageUrl, '_blank')}
          >
            View Jobs on Portal
          </button>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="detail-content">
        {/* Recruiter Section */}
        <section className="detail-section">
          <h3>Recruiter / Hiring Manager</h3>
          <div className="recruiter-card">
            <div className="recruiter-avatar">👤</div>
            <div className="recruiter-info">
              <h4>Hiring Team</h4>
              <p className="recruiter-role">{job.recruiter.role || 'Talent Acquisition'}</p>
              <p className="recruiter-company">at {job.company}</p>
            </div>
            <button
              className="btn-linkedin-detail"
              onClick={() => {
                const slug = getLinkedInCompanySlug(job.company)
                window.open(`https://www.linkedin.com/company/${slug}/people/?keywords=HR`, '_blank')
              }}
            >
              🔗 Connect on LinkedIn
            </button>
          </div>
        </section>

        {/* Job Description */}
        <section className="detail-section">
          <h3>Job Description</h3>
          <div className="description-box">
            {descLoading ? (
              <p className="desc-muted">Loading description...</p>
            ) : realDescription ? (
              <FormattedDescription text={realDescription} />
            ) : (
              <p className="desc-muted">
                Description not available. <a href={jobPageUrl} target="_blank" rel="noreferrer">View on {job.platform} ↗</a>
              </p>
            )}
          </div>
        </section>

        {/* Outreach Message */}
        <section className="detail-section">
          <div className="message-header">
            <h3>Outreach Message</h3>
            <button
              className={`btn-copy-message ${copied ? 'copied' : ''}`}
              onClick={() => {
                navigator.clipboard.writeText(message).then(() => {
                  setCopied(true)
                  setTimeout(() => setCopied(false), 2000)
                })
              }}
            >
              {copied ? 'Copied' : 'Copy Message'}
            </button>
          </div>

          {isEditing ? (
            <textarea
              className="message-editor"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onBlur={() => setIsEditing(false)}
              onKeyDown={(e) => { if (e.key === 'Escape') setIsEditing(false) }}
              autoFocus
              placeholder="Edit your outreach message here..."
            />
          ) : (
            <div
              className="message-display"
              onDoubleClick={() => setIsEditing(true)}
              title="Double-click to edit"
            >
              {message.split('\n').map((line, idx) => (
                <p key={idx}>{line}</p>
              ))}
            </div>
          )}
        </section>
      </div>

      {/* Action Footer */}
      <div className="detail-footer">
        <button className="btn-action btn-skip" onClick={() => onSkip(job.id)}>
          ✕ Skip Job
        </button>

        <div className="action-spacer" />

        <button
          className="btn-action btn-push"
          onClick={handlePush}
          disabled={isPushing || isBulkSelectionActive}
          title={isBulkSelectionActive ? 'Use the bulk action button to post selected jobs' : ''}
        >
          {isPushing ? '⏳ Posting...' : isBulkSelectionActive ? 'Use Bulk Action' : 'Post Job on Scaler Hiring'}
        </button>
      </div>

      {/* Outreach Confirmation Modal */}
      {showOutreachModal && (
        <ConfirmOutreachModal
          job={job}
          onConfirm={handleOutreachConfirmed}
          onCancel={() => setShowOutreachModal(false)}
        />
      )}
    </div>
  )
}

// Experience level labels
const experienceLevels = {
  '0-1': '0-1 years',
  '1-3': '1-3 years',
  '3-5': '3-5 years',
  '5+': '5+ years'
}

// Main ResultsPage Component
export default function ResultsPage2({ jobs: initialJobs = [], onBack, searchParams = {}, onNavigateToDashboard }) {
  const [jobs, setJobs] = useState(initialJobs)
  const [selectedJobId, setSelectedJobId] = useState(initialJobs.length > 0 ? initialJobs[0].id : null)
  const [currentPage, setCurrentPage] = useState(1)
  const [lastUpdated, setLastUpdated] = useState(null)

  // Handle LinkedIn OAuth callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const authSuccess = params.get('auth_success')
    const userId = params.get('user_id')
    const userName = params.get('name')

    if (authSuccess === 'true' && userId) {
      // Store LinkedIn user_id in localStorage for dashboard syncing
      localStorage.setItem('linkedin_user_id', userId)
      localStorage.setItem('linkedin_user_name', userName || 'User')
      console.log('✅ LinkedIn authenticated:', { userId, userName })

      // Associate recent outreach logs with this user
      fetch('http://localhost:8000/associate-outreach-with-user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      })
        .then(res => res.json())
        .then(data => {
          console.log('✅ Associated outreach logs:', data)
        })
        .catch(err => console.error('Error associating outreach:', err))

      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }, [])

  // Calculate when data was cached
  useEffect(() => {
    const cacheKey = `jobs_cache_${searchParams.role}_${searchParams.location}_${(searchParams.portals || []).join('_')}`
    try {
      const cached = localStorage.getItem(cacheKey)
      if (cached) {
        const { timestamp } = JSON.parse(cached)
        const ageMinutes = Math.round((Date.now() - timestamp) / 1000 / 60)
        setLastUpdated(ageMinutes)
      }
    } catch (e) {
      console.error('Error reading cache timestamp:', e)
    }
  }, [searchParams])

  // Update timestamp every 60 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      const cacheKey = `jobs_cache_${searchParams.role}_${searchParams.location}_${(searchParams.portals || []).join('_')}`
      try {
        const cached = localStorage.getItem(cacheKey)
        if (cached) {
          const { timestamp } = JSON.parse(cached)
          const ageMinutes = Math.round((Date.now() - timestamp) / 1000 / 60)
          setLastUpdated(ageMinutes)
        }
      } catch (e) {
        console.error('Error reading cache timestamp:', e)
      }
    }, 60000) // Update every 60 seconds

    return () => clearInterval(interval)
  }, [searchParams])

  // Filter and Selection State
  const [selectedJobs, setSelectedJobs] = useState(new Set())
  const [filters, setFilters] = useState({
    postedTime: 'anytime',
    platforms: searchParams.portals && searchParams.portals.length > 0 ? searchParams.portals : [],
    experience: searchParams.experience || '',
    location: ''
  })

  const selectedJob = useMemo(() => {
    return jobs.find((j) => j.id === selectedJobId)
  }, [jobs, selectedJobId])

  // Auto-select first job when filters change
  useEffect(() => {
    // Recalculate filtered jobs and select the first one
    const tempFiltered = jobs.filter(job => {
      if (filters.platforms.length > 0) {
        const rawPlatform = (job.platform || 'LinkedIn').toLowerCase().trim()
        const jobPlatform = rawPlatform === 'indeed' ? 'others' : rawPlatform
        const platformsLower = filters.platforms.map(p => p.toLowerCase().trim())
        if (!platformsLower.includes(jobPlatform)) return false
      }

      if (filters.postedTime && filters.postedTime !== 'anytime') {
        const postedMs = job.postedDateMs || 0
        let maxMs = 0
        if (filters.postedTime === '24h') maxMs = 24 * 60 * 60 * 1000
        else if (filters.postedTime === '3d') maxMs = 3 * 24 * 60 * 60 * 1000
        else if (filters.postedTime === '7d') maxMs = 7 * 24 * 60 * 60 * 1000
        if (maxMs > 0 && postedMs > maxMs) return false
      }

      if (filters.experience && filters.experience !== '') {
        if (job.experience !== filters.experience) return false
      }

      if (filters.location && filters.location.trim() !== '') {
        const jobLocation = (job.location || '').toLowerCase()
        const filterLocation = filters.location.toLowerCase().trim()
        if (!jobLocation.includes(filterLocation)) return false
      }

      return true
    })

    if (tempFiltered.length > 0) {
      setSelectedJobId(tempFiltered[0].id)
    } else {
      setSelectedJobId(null)
    }
  }, [filters, jobs])

  const handleSelectJob = (jobId) => {
    setSelectedJobId(jobId)
  }

  const handlePushJob = (jobId) => {
    setJobs((prevJobs) =>
      prevJobs.map((j) => (j.id === jobId ? { ...j, pushed: true } : j))
    )
  }

  const handleSkipJob = (jobId) => {
    setJobs((prevJobs) => prevJobs.filter((j) => j.id !== jobId))

    // Select next job if available
    const remainingJobs = jobs.filter((j) => j.id !== jobId)
    if (remainingJobs.length > 0) {
      setSelectedJobId(remainingJobs[0].id)
    } else {
      setSelectedJobId(null)
    }
  }

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage)
    // Reset selection when changing pages
    const startIdx = (newPage - 1) * ITEMS_PER_PAGE
    if (jobs.length > startIdx) {
      setSelectedJobId(jobs[startIdx].id)
    }
  }

  // Filter functions
  const getFilteredJobs = () => {
    const result = jobs.filter(job => {
      // Platform filter
      if (filters.platforms.length > 0) {
        const rawPlatform = (job.platform || 'LinkedIn').toLowerCase().trim()
        const jobPlatform = rawPlatform === 'indeed' ? 'others' : rawPlatform
        const platformsLower = filters.platforms.map(p => p.toLowerCase().trim())
        if (!platformsLower.includes(jobPlatform)) return false
      }

      // Posted time filter - using parsed milliseconds
      if (filters.postedTime && filters.postedTime !== 'anytime') {
        const postedMs = job.postedDateMs || 0
        let maxMs = 0

        if (filters.postedTime === '24h') maxMs = 24 * 60 * 60 * 1000
        else if (filters.postedTime === '3d') maxMs = 3 * 24 * 60 * 60 * 1000
        else if (filters.postedTime === '7d') maxMs = 7 * 24 * 60 * 60 * 1000

        if (maxMs > 0 && postedMs > maxMs) return false
      }

      // Experience filter
      if (filters.experience && filters.experience !== '') {
        if (job.experience !== filters.experience) return false
      }

      // Location filter
      if (filters.location && filters.location.trim() !== '') {
        const jobLocation = (job.location || '').toLowerCase()
        const filterLocation = filters.location.toLowerCase().trim()
        if (!jobLocation.includes(filterLocation)) return false
      }

      return true
    })

    return result
  }

  const filteredJobs = getFilteredJobs()

  // Selection functions
  const handleJobSelection = (jobId) => {
    const newSelected = new Set(selectedJobs)
    if (newSelected.has(jobId)) {
      newSelected.delete(jobId)
    } else {
      newSelected.add(jobId)
    }
    setSelectedJobs(newSelected)
  }

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedJobs(new Set(filteredJobs.map(j => j.id)))
    } else {
      setSelectedJobs(new Set())
    }
  }

  // Bulk actions
  const handleBulkPush = async () => {
    const jobsToUpdate = filteredJobs.filter(j => selectedJobs.has(j.id))

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 800))

    jobsToUpdate.forEach(job => {
      handlePushJob(job.id)
    })

    const recruiterNames = jobsToUpdate.map(job => job.recruiter.name).slice(0, 3).join(', ')
    const additionalCount = jobsToUpdate.length > 3 ? ` +${jobsToUpdate.length - 3} more` : ''

    alert(`✅ ${jobsToUpdate.length} Job${jobsToUpdate.length !== 1 ? 's' : ''} posted to Scaler Hiring!\n\nMessages sent to: ${recruiterNames}${additionalCount}`)
    setSelectedJobs(new Set())
  }

  const toggleFilter = (filterType, value) => {
    setFilters(prev => {
      if (filterType === 'postedTime') {
        return { ...prev, postedTime: prev.postedTime === value ? null : value }
      } else if (filterType === 'platform') {
        const platforms = prev.platforms.includes(value)
          ? prev.platforms.filter(p => p !== value)
          : [...prev.platforms, value]
        return { ...prev, platforms }
      } else if (filterType === 'experience') {
        return { ...prev, experience: prev.experience === value ? '' : value }
      } else if (filterType === 'location') {
        return { ...prev, location: value }
      }
      return prev
    })
  }

  const isAllSelected = filteredJobs.length > 0 && selectedJobs.size === filteredJobs.length
  const someSelected = selectedJobs.size > 0

  return (
    <div className="results-page-2">
      {/* Header */}
      <header className="results-header-2">
        <div className="header-content">
          <div className="logo-section-results">
            <button
              onClick={onBack}
              className="logo-back-btn"
              title="Back to Search"
            >
              <img src="/scaler-logo.png" alt="Scaler Logo" className="results-logo" />
            </button>
          </div>
          <div className="header-right">
            <button
              className="nav-link-results"
              onClick={() => onNavigateToDashboard && onNavigateToDashboard()}
            >
              Outreach Dashboard
            </button>
            <span className="status-badge">
              {jobs.length} opportunities | {jobs.filter((j) => j.pushed).length} sent
            </span>
            {lastUpdated !== null && (
              <span
                className="last-updated-badge"
                title="New jobs will be fetched every 4 hours automatically"
              >
                Updated {lastUpdated === 0 ? 'just now' :
                  lastUpdated < 60 ? `${lastUpdated}m ago` :
                  `${Math.floor(lastUpdated / 60)}hr ${lastUpdated % 60}m ago`
                }
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Floating Bulk Action Button - Bottom Right */}
      {selectedJobs.size > 0 && (
        <div className="floating-bulk-action">
          <button className="floating-bulk-button" onClick={handleBulkPush}>
            Post {selectedJobs.size} Job{selectedJobs.size !== 1 ? 's' : ''} To Scaler Hiring
          </button>
        </div>
      )}

      {/* Horizontal Filter Bar - Full Width */}
      <FilterBar
        filters={filters}
        onToggleFilter={toggleFilter}
        onSelectAll={handleSelectAll}
        isAllSelected={isAllSelected}
        selectedCount={selectedJobs.size}
        totalCount={filteredJobs.length}
        searchParams={searchParams}
      />

      {/* Main Content */}
      <main className="results-main-2">
        {filteredJobs.length === 0 ? (
          <div className="empty-results">
            <div className="empty-icon">🔍</div>
            <h2>No jobs found</h2>
            <p>Try adjusting your search filters</p>
            <button onClick={onBack} className="btn-back-primary">
              Back to Search
            </button>
          </div>
        ) : (
          <div className="two-pane-layout">
            {/* Left Panel */}
            <JobListPanel
              jobs={filteredJobs}
              selectedJobId={selectedJobId}
              onSelectJob={handleSelectJob}
              currentPage={currentPage}
              onPageChange={handlePageChange}
              selectedJobs={selectedJobs}
              onSelectionChange={handleJobSelection}
              searchParams={searchParams}
            />

            {/* Divider */}
            <div className="pane-divider" />

            {/* Right Panel */}
            <JobDetailPanel
              job={selectedJob}
              onBack={() => setSelectedJobId(null)}
              onPush={handlePushJob}
              onSkip={handleSkipJob}
              isBulkSelectionActive={selectedJobs.size > 0}
            />
          </div>
        )}
      </main>
    </div>
  )
}
