import React, { useState } from 'react'

function EditModal({ message, onSave, onClose }) {
  const [subject, setSubject] = useState(message.subject_line)
  const [body, setBody] = useState(message.message_body)

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(message.id, subject, body)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-gray-900 to-gray-800 text-white p-6 border-b border-gray-300">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold">Edit Message</h2>
              <p className="text-gray-300 text-sm mt-1">{message.company_name} - {message.recruiter_name}</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-300 text-2xl leading-none"
            >
              ×
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Recipient Info */}
          <div className="space-y-2">
            <label className="block text-sm font-semibold text-gray-700">Recipient</label>
            <div className="p-3 bg-gray-100 rounded-lg">
              <p className="text-gray-900 font-semibold">{message.recruiter_name}</p>
              <p className="text-sm text-gray-600">{message.recruiter_email}</p>
              <p className="text-sm text-gray-600 mt-1">{message.company_name} - {message.job_title}</p>
            </div>
          </div>

          {/* Subject Line */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Subject Line</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              maxLength="100"
              className="input-field"
              placeholder="Keep it compelling and under 50 characters"
            />
            <p className="text-xs text-gray-500 mt-1">
              Characters: {subject.length}/100
            </p>
          </div>

          {/* Message Body */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Message Body</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              className="input-field"
              rows="12"
              placeholder="Write your personalized message here..."
              style={{ resize: 'none' }}
            />
            <p className="text-xs text-gray-500 mt-1">
              Words: {body.split(/\s+/).filter(w => w).length} (Target: 150-200)
            </p>
          </div>

          {/* Tips */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm font-semibold text-blue-900 mb-2">Tips for better messages:</p>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>✓ Keep it personal and specific</li>
              <li>✓ Mention a relevant detail from their job posting</li>
              <li>✓ Include a clear call-to-action</li>
              <li>✓ Keep tone professional but friendly</li>
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 justify-end pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-3 bg-gray-200 text-gray-900 font-semibold rounded-lg hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default EditModal
