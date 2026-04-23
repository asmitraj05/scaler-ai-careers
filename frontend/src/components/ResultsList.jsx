import React, { useState } from 'react'

function ResultsList({ messages, onEdit, onApprove, onReject }) {
  const [expandedId, setExpandedId] = useState(null)

  const approved = messages.filter(m => m.approval_status === 'approved').length
  const pending = messages.filter(m => m.approval_status === 'pending').length
  const rejected = messages.filter(m => m.approval_status === 'rejected').length

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved':
        return 'bg-green-50 border-green-200'
      case 'rejected':
        return 'bg-red-50 border-red-200'
      default:
        return 'bg-white border-gray-200'
    }
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'approved':
        return <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full">Approved ✓</span>
      case 'rejected':
        return <span className="px-3 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded-full">Rejected ✗</span>
      default:
        return <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded-full">Pending</span>
    }
  }

  return (
    <div className="space-y-6">
      {/* Stats Bar */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card text-center">
          <div className="text-3xl font-bold text-blue-600">{messages.length}</div>
          <div className="text-sm text-gray-600">Total Opportunities</div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-green-600">{approved}</div>
          <div className="text-sm text-gray-600">Approved</div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-yellow-600">{pending}</div>
          <div className="text-sm text-gray-600">Pending Review</div>
        </div>
      </div>

      {/* Messages List */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-gray-900">Review & Edit Messages</h2>

        {messages.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-gray-500">No messages generated. Try a different search.</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`card border transition-all ${getStatusColor(message.approval_status)}`}
            >
              {/* Card Header */}
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-bold text-gray-900">{message.company_name}</h3>
                    {getStatusBadge(message.approval_status)}
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{message.job_title}</p>

                  {/* Portal Attribution */}
                  {message.job && message.job.portal_name && (
                    <div className="flex items-center gap-2 mb-3 px-3 py-1.5 rounded-lg w-fit" style={{ backgroundColor: `${message.job.portal_color || '#f0f0f0'}20`, border: `1px solid ${message.job.portal_color || '#ccc'}40` }}>
                      <span className="text-lg">{message.job.portal_logo}</span>
                      <span className="text-xs font-semibold" style={{ color: message.job.portal_color || '#666' }}>
                        {message.job.portal_name}
                      </span>
                    </div>
                  )}

                  <p className="text-sm text-gray-700 mb-3">
                    <span className="font-semibold">To:</span> {message.recruiter_name} ({message.recruiter_email})
                  </p>

                  {/* Source Link - REAL JOB URL */}
                  {message.job_url && (
                    <a
                      href={message.job_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-800 underline text-xs font-semibold mb-2"
                    >
                      <span>🔗 View Original Job Posting</span>
                      <span className="text-lg">↗</span>
                    </a>
                  )}
                </div>
              </div>

              {/* Subject Line Preview */}
              <div className="mb-4 p-3 bg-gray-100 rounded-lg">
                <p className="text-xs text-gray-600 font-semibold">Subject:</p>
                <p className="text-gray-900 font-medium">{message.subject_line}</p>
              </div>

              {/* Message Body */}
              <div className="mb-4">
                <p className="text-xs text-gray-600 font-semibold mb-2">Message Preview:</p>
                <div className={`p-3 rounded-lg text-sm leading-relaxed ${
                  expandedId === message.id ? 'max-h-none' : 'max-h-20 overflow-hidden'
                } bg-gray-50`}>
                  <p className="text-gray-700 whitespace-pre-wrap">{message.message_body}</p>
                </div>
                {message.message_body.length > 100 && (
                  <button
                    onClick={() => setExpandedId(expandedId === message.id ? null : message.id)}
                    className="text-xs text-blue-600 hover:text-blue-700 mt-2 font-semibold"
                  >
                    {expandedId === message.id ? 'Show less' : 'Show more'}
                  </button>
                )}
              </div>

              {/* Edit Indicator */}
              {message.edited_by_user && (
                <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700">
                  ✎ This message has been edited
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4 border-t border-gray-200">
                <button
                  onClick={() => onEdit(message)}
                  className="flex-1 px-4 py-2 bg-blue-100 text-blue-700 hover:bg-blue-200 font-semibold rounded-lg transition-colors"
                >
                  ✎ Edit
                </button>
                <button
                  onClick={() => onApprove(message.id)}
                  disabled={message.approval_status === 'approved'}
                  className={`flex-1 px-4 py-2 font-semibold rounded-lg transition-colors ${
                    message.approval_status === 'approved'
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-green-100 text-green-700 hover:bg-green-200'
                  }`}
                >
                  ✓ Approve
                </button>
                <button
                  onClick={() => onReject(message.id)}
                  disabled={message.approval_status === 'rejected'}
                  className={`flex-1 px-4 py-2 font-semibold rounded-lg transition-colors ${
                    message.approval_status === 'rejected'
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-red-100 text-red-700 hover:bg-red-200'
                  }`}
                >
                  ✗ Reject
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Action Footer */}
      {approved > 0 && (
        <div className="card bg-green-50 border border-green-200">
          <div className="flex justify-between items-center">
            <div>
              <p className="font-semibold text-green-900">{approved} message(s) ready to send</p>
              <p className="text-sm text-green-700">All approved messages are ready for outreach</p>
            </div>
            <button className="px-6 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700">
              Send All ({approved})
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ResultsList
