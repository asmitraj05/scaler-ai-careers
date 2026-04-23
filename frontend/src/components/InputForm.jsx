import React, { useState } from 'react'

function InputForm({ onSubmit, loading }) {
  const [role, setRole] = useState('Backend Engineer')
  const [location, setLocation] = useState('Bangalore')

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(role, location)
  }

  const commonRoles = [
    'Backend Engineer',
    'Full Stack Engineer',
    'Frontend Engineer',
    'DevOps Engineer',
    'Data Engineer'
  ]

  const commonLocations = [
    'Bangalore',
    'Mumbai',
    'Delhi',
    'Hyderabad',
    'Remote'
  ]

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card">
        <h2 className="text-2xl font-bold mb-6 text-gray-900">Find Hiring Opportunities</h2>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Job Role */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              What role are you looking for?
            </label>
            <div className="space-y-2">
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="input-field"
              >
                {commonRoles.map(r => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
              <p className="text-xs text-gray-500">Popular roles from Scaler's programs</p>
            </div>
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Location
            </label>
            <div className="space-y-2">
              <select
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="input-field"
              >
                {commonLocations.map(loc => (
                  <option key={loc} value={loc}>{loc}</option>
                ))}
              </select>
              <p className="text-xs text-gray-500">Where are the candidates looking?</p>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 px-6 font-semibold text-white rounded-lg transition-all ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 active:scale-95'
            }`}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
                  <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Running AI Outreach...
              </span>
            ) : (
              'Run AI Outreach'
            )}
          </button>
        </form>

        {/* Info Box */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <h3 className="font-semibold text-gray-900 mb-3">What happens next:</h3>
          <ol className="space-y-2 text-sm text-gray-600">
            <li className="flex gap-3">
              <span className="font-bold text-blue-600">1.</span>
              <span>We search for companies actively hiring for this role</span>
            </li>
            <li className="flex gap-3">
              <span className="font-bold text-blue-600">2.</span>
              <span>Filter for roles that match Scaler's program focus</span>
            </li>
            <li className="flex gap-3">
              <span className="font-bold text-blue-600">3.</span>
              <span>Identify recruiters and hiring managers</span>
            </li>
            <li className="flex gap-3">
              <span className="font-bold text-blue-600">4.</span>
              <span>Generate personalized outreach messages</span>
            </li>
            <li className="flex gap-3">
              <span className="font-bold text-blue-600">5.</span>
              <span>You review, edit, and approve before sending</span>
            </li>
          </ol>
        </div>
      </div>
    </div>
  )
}

export default InputForm
