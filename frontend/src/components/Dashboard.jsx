import React from 'react'

const PORTAL_META = {
  'linkedin.com': { label: 'LinkedIn', color: '#0077b5', bg: '#e8f3fb' },
  'naukri.com':   { label: 'Naukri',   color: '#ff7555', bg: '#fff1ee' },
  'remoteok.io':  { label: 'RemoteOK', color: '#17b978', bg: '#eafaf4' },
}

function portalMeta(url = '') {
  for (const [domain, meta] of Object.entries(PORTAL_META)) {
    if (url.includes(domain)) return meta
  }
  return { label: 'Job Board', color: '#6b7280', bg: '#f3f4f6' }
}

function Dashboard({ stats, messages = [] }) {
  const approvalRate = stats.approval_rate ? (stats.approval_rate * 100).toFixed(1) : 0

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Campaign Dashboard</h2>

      {/* Stats */}
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
        <div className="w-full bg-gray-200 rounded-full h-8 overflow-hidden">
          <div
            className="bg-gradient-to-r from-green-400 to-green-600 h-full flex items-center justify-center text-white font-bold text-sm transition-all"
            style={{ width: `${approvalRate}%` }}
          >
            {approvalRate}%
          </div>
        </div>
        <p className="text-sm text-gray-600 mt-3">
          {stats.approved} out of {stats.total_messages} messages approved
        </p>
      </div>

      {/* Job Listings */}
      {messages.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-bold text-gray-900 mb-4">
            Job Listings
            <span className="ml-2 text-sm font-normal text-gray-500">({messages.length} found)</span>
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 pr-4 text-gray-500 font-semibold">Company</th>
                  <th className="text-left py-2 pr-4 text-gray-500 font-semibold">Role</th>
                  <th className="text-left py-2 pr-4 text-gray-500 font-semibold">Recruiter</th>
                  <th className="text-left py-2 pr-4 text-gray-500 font-semibold">Portal</th>
                  <th className="text-left py-2 text-gray-500 font-semibold">Status</th>
                  <th className="py-2"></th>
                </tr>
              </thead>
              <tbody>
                {messages.map((msg) => {
                  const portal = portalMeta(msg.job_url)
                  const statusColors = {
                    approved: 'text-green-700 bg-green-100',
                    rejected: 'text-red-700 bg-red-100',
                    pending:  'text-yellow-700 bg-yellow-100',
                  }
                  return (
                    <tr key={msg.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 pr-4 font-semibold text-gray-900">{msg.company_name}</td>
                      <td className="py-3 pr-4 text-gray-700">{msg.job_title}</td>
                      <td className="py-3 pr-4 text-gray-600">{msg.recruiter_name}</td>
                      <td className="py-3 pr-4">
                        <span
                          className="inline-block px-2 py-0.5 rounded text-xs font-semibold"
                          style={{ color: portal.color, backgroundColor: portal.bg }}
                        >
                          {portal.label}
                        </span>
                      </td>
                      <td className="py-3 pr-4">
                        <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold capitalize ${statusColors[msg.approval_status] || statusColors.pending}`}>
                          {msg.approval_status}
                        </span>
                      </td>
                      <td className="py-3 text-right">
                        {msg.job_url ? (
                          <a
                            href={msg.job_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-block px-3 py-1 text-xs font-semibold text-blue-600 border border-blue-300 rounded hover:bg-blue-50 transition-colors"
                          >
                            View Job →
                          </a>
                        ) : null}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Next Steps */}
      <div className="card">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Next Steps</h3>
        <ol className="space-y-3 text-gray-700">
          {[
            'Review all pending messages for accuracy and personalization',
            'Edit any messages that could be improved',
            'Approve messages that are ready to send',
            'Send all approved messages to start the conversation',
            'Track replies and follow up with interested recruiters',
          ].map((step, i) => (
            <li key={i} className="flex gap-3">
              <span className="font-bold text-blue-600 flex-shrink-0">{i + 1}.</span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}

export default Dashboard
