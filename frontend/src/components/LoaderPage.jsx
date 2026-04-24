import React, { useState, useEffect } from 'react'
import './LoaderPage.css'

export default function LoaderPage({ role, location, portals }) {
  const [progress, setProgress] = useState(0)
  const [currentStage, setCurrentStage] = useState(0)
  const [isCached, setIsCached] = useState(false)

  useEffect(() => {
    // Check if we're using cached data
    const cacheKey = `jobs_cache_${role}_${location}_${portals.join('_')}`
    try {
      const cached = localStorage.getItem(cacheKey)
      if (cached) {
        const { timestamp } = JSON.parse(cached)
        const ageMinutes = (Date.now() - timestamp) / 1000 / 60
        if (ageMinutes < 240) {
          setIsCached(true)
          // Speed up progress for cached data
          const fastInterval = setInterval(() => {
            setProgress(prev => {
              const newProgress = prev + 5
              return Math.min(newProgress, 99)
            })
          }, 100)
          return () => clearInterval(fastInterval)
        }
      }
    } catch (e) {
      console.error('Cache check error:', e)
    }

    // Normal progress for fresh fetch
    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + 2.5
        return Math.min(newProgress, 99)
      })
    }, 600)

    return () => clearInterval(interval)
  }, [])

  const stages = [
    {
      title: 'Fetching latest jobs',
      range: [0, 25]
    },
    {
      title: 'Analyzing job details',
      range: [25, 50]
    },
    {
      title: 'Identifying recruiters',
      range: [50, 75]
    },
    {
      title: 'Generating outreach',
      range: [75, 100]
    }
  ]

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + 2.5
        return Math.min(newProgress, 99)
      })
    }, 600)

    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const stageIndex = stages.findIndex(
      stage => progress >= stage.range[0] && progress < stage.range[1]
    )
    if (stageIndex >= 0) {
      setCurrentStage(stageIndex)
    }
  }, [progress])

  const currentStageData = stages[currentStage]

  return (
    <div className="loader-container">
      {/* Top Header */}
      <header className="loader-top-header">
        <div className="loader-header-content">
          <div className="loader-logo-section">
            <img src="/scaler-logo.png" alt="Scaler Logo" className="loader-header-logo" />
          </div>
          <nav className="loader-header-nav">
            <a href="#outreach-dashboard" className="loader-nav-link">
              Outreach Dashboard
            </a>
          </nav>
        </div>
      </header>

      <div className="loader-header">
        <h1 className="loader-title">AI-Powered Hiring Outreach</h1>
        <p className="loader-subtitle">
          {isCached ? '⚡ Loading cached results...' : `🔍 Finding ${role} opportunities for you...`}
        </p>
      </div>

      <div className="loader-content">
        <div className="progress-section">
          <div className="progress-bar-container">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }}></div>
            </div>
            <div className="progress-percentage">{Math.round(progress)}%</div>
          </div>

          <div className="stages-timeline">
            {stages.map((stage, index) => (
              <div
                key={index}
                className={`timeline-item ${index <= currentStage ? 'active' : ''} ${
                  index < currentStage ? 'completed' : ''
                }`}
              >
                <div className="timeline-step">
                  <div className="step-number">{index + 1}</div>
                  <div className="step-line"></div>
                </div>
                <div className="timeline-title">{stage.title}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="loader-footer">
        <p className="footer-text">Processing {location} opportunities • {portals.join(', ')}</p>
      </div>
    </div>
  )
}
