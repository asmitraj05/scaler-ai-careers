import React, { useState } from 'react'
import './ConfirmOutreachModal.css'

export default function ConfirmOutreachModal({ job, onConfirm, onCancel }) {
  const [isAuthenticating, setIsAuthenticating] = useState(false)
  const [error, setError] = useState('')
  const [authSuccess, setAuthSuccess] = useState(false)

  const handleLinkedInConnect = async () => {
    setError('')
    setIsAuthenticating(true)

    try {
      // Get LinkedIn OAuth URL
      const response = await fetch('http://localhost:8000/auth/linkedin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })

      if (!response.ok) {
        setError('Failed to start LinkedIn authentication')
        setIsAuthenticating(false)
        return
      }

      const data = await response.json()
      const authUrl = data.auth_url

      if (!authUrl) {
        setError('Failed to get LinkedIn authentication URL')
        setIsAuthenticating(false)
        return
      }

      // Redirect to LinkedIn OAuth
      window.location.href = authUrl
    } catch (err) {
      console.error('Error:', err)
      setError('Error connecting to LinkedIn. Please try again.')
      setIsAuthenticating(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="confirm-modal">
        <div className="modal-header">
          <h2>Connect on LinkedIn ✅</h2>
          <button
            className="modal-close"
            onClick={onCancel}
            disabled={isAuthenticating}
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
            To log this connection with real LinkedIn data, authenticate with your LinkedIn account.
            Your actual LinkedIn connections will be synced to your dashboard automatically.
          </p>

          {error && <div className="error-message">{error}</div>}

          <div className="form-actions">
            <button
              type="button"
              className="btn-cancel"
              onClick={onCancel}
              disabled={isAuthenticating}
            >
              Cancel
            </button>
            <button
              type="button"
              className="btn-confirm"
              onClick={handleLinkedInConnect}
              disabled={isAuthenticating}
            >
              {isAuthenticating ? '🔄 Connecting...' : '🔗 Authenticate with LinkedIn'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
