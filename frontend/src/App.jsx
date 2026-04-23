import React, { useState } from 'react'
import axios from 'axios'
import InputForm from './components/InputForm'
import ResultsList from './components/ResultsList'
import EditModal from './components/EditModal'
import Dashboard from './components/Dashboard'

function App() {
  const [view, setView] = useState('input') // input, results, dashboard
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState([])
  const [stats, setStats] = useState(null)
  const [editingMessage, setEditingMessage] = useState(null)
  const [error, setError] = useState(null)

  const API_BASE = 'http://localhost:8000'

  const handleRunWorkflow = async (role, location) => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.post(`${API_BASE}/workflow/run`, {
        role,
        location,
        num_results: 5
      })

      if (response.data.error) {
        setError(response.data.error)
      } else {
        setMessages(response.data.results)
        setView('results')
      }
    } catch (err) {
      setError('Failed to run workflow. Make sure backend is running on port 8000.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleEditMessage = (message) => {
    setEditingMessage(message)
  }

  const handleSaveEdit = async (messageId, subject, body) => {
    try {
      const response = await axios.put(
        `${API_BASE}/messages/${messageId}`,
        {
          subject_line: subject,
          message_body: body
        }
      )
      setMessages(messages.map(m => m.id === messageId ? response.data : m))
      setEditingMessage(null)
    } catch (err) {
      setError('Failed to update message')
      console.error(err)
    }
  }

  const handleApprove = async (messageId) => {
    try {
      await axios.post(`${API_BASE}/messages/${messageId}/approve`)
      setMessages(messages.map(m =>
        m.id === messageId ? { ...m, approval_status: 'approved' } : m
      ))
    } catch (err) {
      setError('Failed to approve message')
    }
  }

  const handleReject = async (messageId) => {
    try {
      await axios.post(`${API_BASE}/messages/${messageId}/reject`)
      setMessages(messages.map(m =>
        m.id === messageId ? { ...m, approval_status: 'rejected' } : m
      ))
    } catch (err) {
      setError('Failed to reject message')
    }
  }

  const handleViewDashboard = async () => {
    try {
      const response = await axios.get(`${API_BASE}/stats`)
      setStats(response.data)
      setView('dashboard')
    } catch (err) {
      setError('Failed to load dashboard')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-gray-900 to-gray-800 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold">Scaler AI Careers</h1>
              <p className="text-gray-300 text-sm mt-1">Automate your outreach workflow</p>
            </div>
            <nav className="flex gap-4">
              <button
                onClick={() => setView('input')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  view === 'input' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                New Campaign
              </button>
              <button
                onClick={handleViewDashboard}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  view === 'dashboard' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                Dashboard
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-300 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {view === 'input' && (
          <InputForm onSubmit={handleRunWorkflow} loading={loading} />
        )}

        {view === 'results' && (
          <ResultsList
            messages={messages}
            onEdit={handleEditMessage}
            onApprove={handleApprove}
            onReject={handleReject}
            loading={loading}
          />
        )}

        {view === 'dashboard' && stats && (
          <Dashboard stats={stats} messages={messages} />
        )}
      </main>

      {/* Edit Modal */}
      {editingMessage && (
        <EditModal
          message={editingMessage}
          onSave={handleSaveEdit}
          onClose={() => setEditingMessage(null)}
        />
      )}
    </div>
  )
}

export default App
