import React from 'react'

function Dashboard({ stats }) {
  const approvalRate = stats.approval_rate ? (stats.approval_rate * 100).toFixed(1) : 0

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Campaign Dashboard</h2>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="text-sm text-gray-600 font-semibold mb-2">Total Messages</div>
          <div className="text-3xl font-bold text-blue-600">{stats.total_messages}</div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-600 font-semibold mb-2">Approved</div>
          <div className="text-3xl font-bold text-green-600">{stats.approved}</div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-600 font-semibold mb-2">Pending</div>
          <div className="text-3xl font-bold text-yellow-600">{stats.pending}</div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-600 font-semibold mb-2">Rejected</div>
          <div className="text-3xl font-bold text-red-600">{stats.rejected}</div>
        </div>
      </div>

      {/* Approval Rate */}
      <div className="card">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Approval Rate</h3>
        <div className="space-y-4">
          <div className="w-full bg-gray-200 rounded-full h-8 overflow-hidden">
            <div
              className="bg-gradient-to-r from-green-400 to-green-600 h-full flex items-center justify-center text-white font-bold text-sm transition-all"
              style={{ width: `${approvalRate}%` }}
            >
              {approvalRate}%
            </div>
          </div>
          <p className="text-sm text-gray-600">
            {stats.approved} out of {stats.total_messages} messages approved
          </p>
        </div>
      </div>

      {/* Summary */}
      <div className="card bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Quick Summary</h3>
        <div className="space-y-3 text-gray-700">
          <p>
            You've generated <span className="font-bold">{stats.total_messages}</span> personalized outreach messages.
          </p>
          <p>
            <span className="font-bold text-green-600">{stats.approved} messages</span> are ready to send.
          </p>
          {stats.pending > 0 && (
            <p>
              <span className="font-bold text-yellow-600">{stats.pending} messages</span> are waiting for your review.
            </p>
          )}
          {stats.rejected > 0 && (
            <p>
              <span className="font-bold text-red-600">{stats.rejected} messages</span> have been rejected.
            </p>
          )}
        </div>
      </div>

      {/* Tips */}
      <div className="card">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Next Steps</h3>
        <ol className="space-y-3 text-gray-700">
          <li className="flex gap-3">
            <span className="font-bold text-blue-600 flex-shrink-0">1.</span>
            <span>Review all pending messages for accuracy and personalization</span>
          </li>
          <li className="flex gap-3">
            <span className="font-bold text-blue-600 flex-shrink-0">2.</span>
            <span>Edit any messages that could be improved</span>
          </li>
          <li className="flex gap-3">
            <span className="font-bold text-blue-600 flex-shrink-0">3.</span>
            <span>Approve messages that are ready to send</span>
          </li>
          <li className="flex gap-3">
            <span className="font-bold text-blue-600 flex-shrink-0">4.</span>
            <span>Send all approved messages to start the conversation</span>
          </li>
          <li className="flex gap-3">
            <span className="font-bold text-blue-600 flex-shrink-0">5.</span>
            <span>Track replies and follow up with interested recruiters</span>
          </li>
        </ol>
      </div>
    </div>
  )
}

export default Dashboard
