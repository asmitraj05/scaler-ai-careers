import React, { useState } from 'react'
import './ConfirmOutreachModal.css'

export default function ConfirmOutreachModal({ job, onConfirm, onCancel }) {
  const [hrName, setHrName] = useState('')
  const [hrLinkedInUrl, setHrLinkedInUrl] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!hrName.trim()) {
      setError('Please enter the HR/Recruiter name')
      return
    }

    if (!hrLinkedInUrl.trim()) {
      setError('Please enter the LinkedIn profile URL')
      return
    }

    // Validate LinkedIn URL format
    if (!hrLinkedInUrl.includes('linkedin.com') && !hrLinkedInUrl.includes('in/')) {
      setError('Please enter a valid LinkedIn profile URL')
      return
    }

    setIsSubmitting(true)

    try {
      const response = await fetch('http://localhost:8000/create-outreach', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: job.company,
          job_role: job.role,
          recruiter_name: hrName,
          recruiter_email: job.recruiter?.role || 'Not specified',
          linkedin_url: hrLinkedInUrl
        })
      })

      if (response.ok) {
        const data = await response.json()
        console.log('✅ Connection logged:', data)
        setHrName('')
        setHrLinkedInUrl('')
        onConfirm(data)
      } else {
        setError('Failed to log connection. Please try again.')
      }
    } catch (err) {
      console.error('Error:', err)
      setError('Error logging connection. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="confirm-modal">
        <div className="modal-header">
          <h2>Confirm Connection Sent ✅</h2>
          <button
            className="modal-close"
            onClick={onCancel}
            disabled={isSubmitting}
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          <div className="job-info">
            <h3>{job.company}</h3>
            <p>{job.role} • {job.location}</p>
          </div>

          <p className="instruction-text">
            You just sent a connection request on LinkedIn. Please enter the HR/Recruiter details below to log this connection in your dashboard.
          </p>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="hrName">HR/Recruiter Name *</label>
              <input
                id="hrName"
                type="text"
                placeholder="e.g., John Doe"
                value={hrName}
                onChange={(e) => {
                  setHrName(e.target.value)
                  setError('')
                }}
                disabled={isSubmitting}
                required
              />
              <small>The full name of the person you sent the connection request to</small>
            </div>

            <div className="form-group">
              <label htmlFor="linkedInUrl">LinkedIn Profile URL *</label>
              <input
                id="linkedInUrl"
                type="url"
                placeholder="https://www.linkedin.com/in/johndoe/"
                value={hrLinkedInUrl}
                onChange={(e) => {
                  setHrLinkedInUrl(e.target.value)
                  setError('')
                }}
                disabled={isSubmitting}
                required
              />
              <small>Copy the LinkedIn profile URL from their profile page</small>
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="form-actions">
              <button
                type="button"
                className="btn-cancel"
                onClick={onCancel}
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-confirm"
                disabled={isSubmitting}
              >
                {isSubmitting ? '⏳ Logging...' : '✅ Confirm Connection'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
