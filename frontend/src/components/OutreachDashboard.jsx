import React, { useState, useEffect } from 'react'
import './OutreachDashboard.css'

const statusColors = {
  REQUEST_SENT: '#FDB913',
  CONNECTED: '#10b981',
  MESSAGE_SENT: '#3b82f6',
  NOT_CONTACTED: '#9ca3af'
}

const statusLabels = {
  REQUEST_SENT: '🟡 Request Sent',
  CONNECTED: '🟢 Connected',
  MESSAGE_SENT: '🔵 Message Sent',
  NOT_CONTACTED: '⚫ Not Contacted'
}

export default function OutreachDashboard({ onNavigateBack }) {
  const [logs, setLogs] = useState([])
  const [stats, setStats] = useState({
    sent_today: 0,
    connected: 0,
    messages_sent: 0,
    pending: 0,
    total_all_time: 0
  })
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    fetchDashboardData()
    // Refresh every 5 seconds for real-time updates
    const interval = setInterval(fetchDashboardData, 5000)
    // Sync with LinkedIn every 10 seconds
    const syncInterval = setInterval(syncLinkedInConnections, 10000)
    return () => {
      clearInterval(interval)
      clearInterval(syncInterval)
    }
  }, [])

  const fetchDashboardData = async () => {
    try {
      const userId = localStorage.getItem('linkedin_user_id')

      // Use LinkedIn-synced endpoint if user is authenticated, otherwise use general endpoint
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      const endpoint = userId
        ? `${API_BASE}/outreach-dashboard-with-linkedin?user_id=${userId}`
        : `${API_BASE}/outreach-dashboard`

      const response = await fetch(endpoint)
      if (response.ok) {
        const data = await response.json()
        setLogs(data.logs || [])
        setStats(data.stats || {})
      }
    } catch (error) {
      console.error('Error fetching dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const syncLinkedInConnections = async () => {
    const userId = localStorage.getItem('linkedin_user_id')
    if (!userId) {
      console.warn('No LinkedIn user ID found')
      return
    }

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/sync-linkedin-connections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      })

      if (response.ok) {
        console.log('LinkedIn connections synced')
        fetchDashboardData()
      }
    } catch (error) {
      console.error('Error syncing LinkedIn connections:', error)
    }
  }

  const getFilteredLogs = () => {
    if (filter === 'all') return logs
    return logs.filter(log => log.status === filter)
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const filteredLogs = getFilteredLogs()

  return (
    <div className="outreach-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="dashboard-header-content">
          <div className="dashboard-logo-section">
            <button
              onClick={onNavigateBack}
              className="dashboard-back-btn"
              title="Back to Search"
            >
              <img src="/scaler-logo.png" alt="Scaler Logo" className="dashboard-logo" />
            </button>
          </div>
          <h1 className="dashboard-title">Outreach Dashboard</h1>
          <div className="dashboard-refresh-info">
            Auto-refresh every 5 seconds
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="dashboard-container">
        {/* Top Metrics */}
        <section className="dashboard-metrics">
          <div className="metric-card sent-today">
            <div className="metric-value">{stats.sent_today}</div>
            <div className="metric-label">Sent Today</div>
          </div>

          <div className="metric-card connected">
            <div className="metric-value">{stats.connected}</div>
            <div className="metric-label">Connected</div>
          </div>

          <div className="metric-card messages">
            <div className="metric-value">{stats.messages_sent}</div>
            <div className="metric-label">Messages Sent</div>
          </div>

          <div className="metric-card pending">
            <div className="metric-value">{stats.pending}</div>
            <div className="metric-label">Pending</div>
          </div>

          <div className="metric-card total">
            <div className="metric-value">{stats.total_all_time}</div>
            <div className="metric-label">Total All Time</div>
          </div>
        </section>

        {/* Filter Bar */}
        <section className="dashboard-filters">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({logs.length})
          </button>
          <button
            className={`filter-btn ${filter === 'REQUEST_SENT' ? 'active' : ''}`}
            onClick={() => setFilter('REQUEST_SENT')}
          >
            Request Sent ({stats.pending})
          </button>
          <button
            className={`filter-btn ${filter === 'CONNECTED' ? 'active' : ''}`}
            onClick={() => setFilter('CONNECTED')}
          >
            Connected ({stats.connected})
          </button>
          <button
            className={`filter-btn ${filter === 'MESSAGE_SENT' ? 'active' : ''}`}
            onClick={() => setFilter('MESSAGE_SENT')}
          >
            Message Sent ({stats.messages_sent})
          </button>
        </section>

        {/* Outreach Table */}
        <section className="dashboard-table-section">
          {loading ? (
            <div className="loading-state">
              <p>Loading outreach data...</p>
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <h3>No outreach records yet</h3>
              <p>Start by clicking "Connect on LinkedIn" on job postings to track your outreach</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="outreach-table">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Job Role</th>
                    <th>Recruiter</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLogs.map((log) => (
                    <tr key={log.id} className="table-row">
                      <td className="company-cell">
                        <strong>{log.company_name}</strong>
                      </td>
                      <td className="role-cell">
                        {log.job_role}
                      </td>
                      <td className="recruiter-cell">
                        {log.recruiter_name || 'N/A'}
                        {log.recruiter_email && <div className="email-subtitle">{log.recruiter_email}</div>}
                      </td>
                      <td className="status-cell">
                        <span
                          className="status-badge"
                          style={{ backgroundColor: statusColors[log.status] }}
                        >
                          {statusLabels[log.status]}
                        </span>
                      </td>
                      <td className="date-cell">
                        {formatDate(log.created_at)}
                      </td>
                      <td className="actions-cell">
                        <span className="action-readonly" title="Status synced from LinkedIn">
                          🔗 Synced from LinkedIn
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
