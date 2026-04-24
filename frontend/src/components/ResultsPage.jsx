import React, { useState } from 'react'
import './ResultsPage.css'

const platformColors = {
  'LinkedIn': '#0077b5',
  'Naukri': '#FF6B35',
  'Instahyre': '#4A90E2',
  'Indeed': '#003366',
  'Shine': '#FFC107',
  'RemoteOK': '#17b978'
}

export default function ResultsPage({ onBack, jobs: initialJobs = [] }) {
  const [jobs, setJobs] = useState(initialJobs)
  const [filterScore, setFilterScore] = useState(0.65)
  const [editingMessage, setEditingMessage] = useState(null)
  const [editedText, setEditedText] = useState('')

  // Calculate stats
  const stats = {
    total: jobs.length,
    qualified: jobs.filter(j => j.status === 'qualified').length,
    pushed: jobs.filter(j => j.pushed).length,
    byPlatform: jobs.reduce((acc, job) => {
      acc[job.platform] = (acc[job.platform] || 0) + 1
      return acc
    }, {})
  }

  const filteredJobs = jobs.filter(j => j.matchScore >= filterScore)

  const handlePushJob = (jobId) => {
    setJobs(prev => prev.map(j => j.id === jobId ? { ...j, pushed: true } : j))
  }

  const handlePushAll = () => {
    setJobs(prev => prev.map(j => j.status === 'qualified' ? { ...j, pushed: true } : j))
  }

  const handleEditMessage = (jobId, text) => {
    setJobs(prev => prev.map(j => j.id === jobId ? { ...j, message: text } : j))
    setEditingMessage(null)
  }

  const handleOpenLinkedIn = (linkedinUrl) => {
    window.open(linkedinUrl, '_blank')
  }

  const handleSkipJob = (jobId) => {
    setJobs(prev => prev.filter(j => j.id !== jobId))
  }

  return (
    <div className="results-page">
      {/* Header */}
      <header className="results-header">
        <div className="header-top">
          <button onClick={onBack} className="back-btn">← Back to Search</button>
          <h1>Hiring Opportunities Dashboard</h1>
          <div className="header-right">
            <span className="results-count">{filteredJobs.length} opportunities</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="results-main">

        {/* Insights Section */}
        <section className="insights-section">
          <div className="insights-grid">
            <div className="insight-card">
              <div className="insight-number">{stats.total}</div>
              <div className="insight-label">Total Jobs Found</div>
              <div className="insight-meta">from all platforms</div>
            </div>
            <div className="insight-card">
              <div className="insight-number">{stats.qualified}</div>
              <div className="insight-label">Qualified</div>
              <div className="insight-meta">AI verified matches</div>
            </div>
            <div className="insight-card">
              <div className="insight-number">{stats.pushed}</div>
              <div className="insight-label">Pushed to Platform</div>
              <div className="insight-meta">ready for outreach</div>
            </div>
            <div className="insight-card">
              <div className="insight-number">{Object.keys(stats.byPlatform).length}</div>
              <div className="insight-label">Platforms</div>
              <div className="insight-meta">job sources</div>
            </div>
          </div>

          {/* Platform Distribution */}
          <div className="platform-distribution">
            <h3>Jobs by Platform</h3>
            <div className="platform-tags">
              {Object.entries(stats.byPlatform).map(([platform, count]) => (
                <div key={platform} className="platform-tag" style={{ borderColor: platformColors[platform] }}>
                  <span className="platform-dot" style={{ backgroundColor: platformColors[platform] }}></span>
                  <span className="platform-name">{platform}</span>
                  <span className="platform-count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Filters & Bulk Actions */}
        <section className="filters-section">
          <div className="filter-group">
            <label>Match Score: {Math.round(filterScore * 100)}%</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={filterScore}
              onChange={(e) => setFilterScore(parseFloat(e.target.value))}
              className="score-slider"
            />
          </div>
          <button onClick={handlePushAll} className="btn-bulk-action">
            🚀 Push All to Scaler Platform
          </button>
        </section>

        {/* Jobs List */}
        <section className="jobs-section">
          <h2>Opportunities</h2>
          {filteredJobs.length === 0 ? (
            <div className="empty-state">
              <p>No jobs match your selected filters</p>
              <button onClick={() => setFilterScore(0.5)} className="btn-secondary">
                Adjust filters
              </button>
            </div>
          ) : (
            <div className="jobs-container">
              {filteredJobs.map(job => (
                <div key={job.id} className="job-card">
                  {/* Job Header */}
                  <div className="job-header">
                    <div className="job-main-info">
                      <h3 className="job-company">{job.company}</h3>
                      <p className="job-role">{job.role}</p>
                      <p className="job-location">📍 {job.location}</p>
                    </div>
                    <div className="job-score">
                      <div className="score-circle">{Math.round(job.matchScore * 100)}%</div>
                      <span className="score-label">Match</span>
                    </div>
                  </div>

                  {/* Job Details Grid */}
                  <div className="job-details">
                    <div className="detail-group">
                      <label>Source</label>
                      <div className="platform-badge" style={{ borderColor: platformColors[job.platform] }}>
                        <span className="badge-dot" style={{ backgroundColor: platformColors[job.platform] }}></span>
                        {job.platform}
                      </div>
                    </div>
                    <div className="detail-group">
                      <label>AI Insight</label>
                      <p className="insight-text">{job.reason}</p>
                    </div>
                  </div>

                  {/* Recruiter Section */}
                  <div className="recruiter-section">
                    <h4>Recruiter / Hiring Manager</h4>
                    <div className="recruiter-card">
                      <div className="recruiter-avatar">👤</div>
                      <div className="recruiter-info">
                        <p className="recruiter-name">{job.recruiter.name}</p>
                        <p className="recruiter-role">{job.recruiter.role}</p>
                      </div>
                      <button
                        onClick={() => handleOpenLinkedIn(job.recruiter.linkedinUrl)}
                        className="btn-linkedin"
                        title="Open on LinkedIn"
                      >
                        🔗 Connect
                      </button>
                    </div>
                  </div>

                  {/* Message Section */}
                  <div className="message-section">
                    <div className="message-header">
                      <h4>Outreach Message</h4>
                      <button
                        onClick={() => {
                          setEditingMessage(job.id)
                          setEditedText(job.message)
                        }}
                        className="btn-edit"
                      >
                        ✎ Edit
                      </button>
                    </div>

                    {editingMessage === job.id ? (
                      <div className="message-editor">
                        <textarea
                          value={editedText}
                          onChange={(e) => setEditedText(e.target.value)}
                          className="message-textarea"
                          rows="5"
                        />
                        <div className="editor-actions">
                          <button
                            onClick={() => handleEditMessage(job.id, editedText)}
                            className="btn-save"
                          >
                            💾 Save
                          </button>
                          <button
                            onClick={() => setEditingMessage(null)}
                            className="btn-cancel"
                          >
                            ✕ Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="message-display">
                        {job.message.split('\n').map((line, idx) => (
                          <p key={idx}>{line}</p>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="job-actions">
                    <button
                      onClick={() => handlePushJob(job.id)}
                      className={`btn-action btn-push ${job.pushed ? 'pushed' : ''}`}
                      disabled={job.pushed}
                    >
                      {job.pushed ? '✓ Pushed to Scaler' : '🚀 Push to Scaler'}
                    </button>
                    <a
                      href={job.jobUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-action btn-view"
                    >
                      📄 View Job
                    </a>
                    <button
                      onClick={() => handleSkipJob(job.id)}
                      className="btn-action btn-skip"
                    >
                      ✕ Skip
                    </button>
                  </div>

                  {/* Status Badge */}
                  {job.pushed && <div className="status-badge">✓ Pushed</div>}
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
