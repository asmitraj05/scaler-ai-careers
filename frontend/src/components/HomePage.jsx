import React, { useState, useEffect, useRef } from 'react'
import './HomePage.css'

const SCALER_COURSES = [
  'Backend Engineer',
  'Frontend Engineer',
  'Full Stack Engineer',
  'Data Science Engineer',
  'DevOps Engineer',
  'Mobile Developer (Android)',
  'Mobile Developer (iOS)',
  'System Design Expert',
  'Machine Learning Engineer',
  'Cloud Engineer'
]

const JOB_PORTALS = ['LinkedIn', 'Naukri', 'Instahyre', 'Indeed', 'Shine']
const ALL_PORTALS = 'ALL'

export default function HomePage({ onSubmit, loading }) {
  const [formData, setFormData] = useState({
    role: '',
    experience: '',
    portals: ['LinkedIn', 'Naukri', 'Indeed'],
    skills: '',
    city: ''
  })

  const [showAdvanced, setShowAdvanced] = useState(false)
  const [showPortalDropdown, setShowPortalDropdown] = useState(false)
  const portalWrapperRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (portalWrapperRef.current && !portalWrapperRef.current.contains(event.target)) {
        setShowPortalDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handlePortalToggle = (portal) => {
    setFormData(prev => {
      let portals
      if (portal === ALL_PORTALS) {
        // Toggle ALL: if all selected, deselect all; otherwise select all
        portals = prev.portals.length === JOB_PORTALS.length ? [] : [...JOB_PORTALS]
      } else {
        // Toggle individual portal
        portals = prev.portals.includes(portal)
          ? prev.portals.filter(p => p !== portal)
          : [...prev.portals, portal]
      }
      return { ...prev, portals }
    })
  }

  const getPortalDisplayText = () => {
    if (formData.portals.length === 0) return 'Select portals'
    if (formData.portals.length === JOB_PORTALS.length) return ALL_PORTALS
    if (formData.portals.length === 1) return formData.portals[0]
    return `${formData.portals.length} Selected`
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!formData.role) {
      alert('Please select a hiring role')
      return
    }
    // Location is optional - defaults to "India" for Pan-India search
    const location = formData.city || 'India'
    onSubmit(formData.role, location, formData.experience, formData.portals)
  }

  return (
    <div className="homepage">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <div className="scaler-logo">
              <img src="/scaler-logo.png" alt="Scaler Logo" />
            </div>
          </div>
          <nav className="header-nav">
            <a href="#outreach-dashboard" className="nav-link">
              Outreach Dashboard
            </a>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-area">

        {/* Header Section */}
        <section className="page-header">
          <h1 className="page-title">
            <span className="title-primary">AI-Powered Hiring Outreach</span>
          </h1>
          <p className="page-subtitle">Discover, qualify, and connect with hiring teams—without switching platforms</p>
        </section>

        {/* Search Form */}
        <section className="search-box">
          <form onSubmit={handleSubmit} className="form">
            <div className="form-row">
              {/* 1. Hiring Role Dropdown */}
              <div className="form-group">
                <label className="label">Hiring Role</label>
                <select
                  value={formData.role}
                  onChange={(e) => handleChange('role', e.target.value)}
                  disabled={loading}
                  className="select-input"
                >
                  <option value="">Select role...</option>
                  {SCALER_COURSES.map(course => (
                    <option key={course} value={course}>
                      {course}
                    </option>
                  ))}
                </select>
              </div>

              {/* 2. Experience Dropdown */}
              <div className="form-group">
                <label className="label">Experience</label>
                <select
                  value={formData.experience}
                  onChange={(e) => handleChange('experience', e.target.value)}
                  disabled={loading}
                  className="select-input"
                >
                  <option value="">Any level</option>
                  <option value="0-1">0–1 years</option>
                  <option value="1-3">1–3 years</option>
                  <option value="3-5">3–5 years</option>
                  <option value="5+">5+ years</option>
                </select>
              </div>

              {/* 3. Job Portals Multi-Select Dropdown */}
              <div className="form-group portal-group">
                <label className="label">Job Portals</label>
                <div className="portal-wrapper" ref={portalWrapperRef}>
                  <button
                    type="button"
                    className="portal-select-btn"
                    onClick={() => setShowPortalDropdown(!showPortalDropdown)}
                    disabled={loading}
                  >
                    <span className="portal-text">{getPortalDisplayText()}</span>
                    <span className="portal-arrow">▼</span>
                  </button>

                  {showPortalDropdown && (
                    <div className="portal-dropdown">
                      <label key={ALL_PORTALS} className="portal-checkbox-item portal-all-option">
                        <input
                          type="checkbox"
                          checked={formData.portals.length === JOB_PORTALS.length}
                          onChange={() => handlePortalToggle(ALL_PORTALS)}
                          disabled={loading}
                        />
                        <span className="portal-label"><strong>{ALL_PORTALS}</strong></span>
                      </label>
                      <div className="portal-divider"></div>
                      {JOB_PORTALS.map(portal => (
                        <label key={portal} className="portal-checkbox-item">
                          <input
                            type="checkbox"
                            checked={formData.portals.includes(portal)}
                            onChange={() => handlePortalToggle(portal)}
                            disabled={loading}
                          />
                          <span className="portal-label">{portal}</span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Search Button */}
              <button
                type="submit"
                disabled={loading || !formData.role}
                className={`btn-search ${loading ? 'loading' : ''}`}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Searching...
                  </>
                ) : (
                  <>Search</>
                )}
              </button>
            </div>

            {/* Advanced Filters Toggle */}
            <div className="toggle-section">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="toggle-btn"
                disabled={loading}
              >
                <span className="toggle-icon">{showAdvanced ? '−' : '+'}</span>
                Advanced Filters
              </button>
            </div>

            {/* Advanced Filters */}
            {showAdvanced && (
              <div className="advanced-section">
                <div className="advanced-row">
                  <div className="form-group">
                    <label className="label">Skills (Optional)</label>
                    <input
                      type="text"
                      placeholder="E.g., Python, SQL, Docker"
                      value={formData.skills}
                      onChange={(e) => handleChange('skills', e.target.value)}
                      disabled={loading}
                      className="text-input"
                    />
                  </div>

                  <div className="form-group">
                    <label className="label">City (Optional - Pan-India by default)</label>
                    <input
                      type="text"
                      placeholder="Leave empty for Pan-India search, or specify city e.g., Bangalore"
                      value={formData.city}
                      onChange={(e) => handleChange('city', e.target.value)}
                      disabled={loading}
                      className="text-input"
                    />
                  </div>
                </div>
              </div>
            )}
          </form>
        </section>

        {/* Info Cards */}
        <section className="info-section">
          <div className="info-card">
            <div className="icon">🇮🇳</div>
            <h3>Pan-India Search</h3>
            <p>Search job openings across all of India by default</p>
          </div>
          <div className="info-card">
            <div className="icon">🔍</div>
            <h3>Search Opportunities</h3>
            <p>Find hiring jobs across multiple portals instantly</p>
          </div>
          <div className="info-card">
            <div className="icon">✨</div>
            <h3>AI Qualification</h3>
            <p>Smart filtering and ranking by relevance</p>
          </div>
          <div className="info-card">
            <div className="icon">📧</div>
            <h3>Generate Outreach</h3>
            <p>Create personalized messages for recruiters</p>
          </div>
        </section>
      </main>
    </div>
  )
}
