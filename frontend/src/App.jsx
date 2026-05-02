import { useState, useEffect } from 'react'
import '../styles.css'

function App() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        setHealth(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }, [])

  return (
    <div className="hero-section">
      <h1>AI HUB</h1>
      <p className="subtitle">
        The ultimate full-stack AI orchestration platform powered by Gemini. 
        Generate text, analyze images, summarize documents, and more.
      </p>
      
      <div className="flex-center" style={{ minHeight: 'auto', gap: '2rem', marginBottom: '3rem' }}>
        <a href="/login.html" className="btn-primary">Get Started</a>
        <a href="/chatbot.html" className="btn-primary" style={{ borderColor: 'rgba(56, 189, 248, 0.5)' }}>Enter Dashboard</a>
      </div>

      <div className="glass-card" style={{ maxWidth: '500px', margin: '0 auto', padding: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem', color: 'var(--accent)' }}>System Status</h3>
        {loading ? (
          <p>Checking systems...</p>
        ) : health ? (
          <div style={{ textAlign: 'left', fontSize: '0.9rem' }}>
            <p><strong>Backend:</strong> <span style={{ color: '#22c55e' }}>ONLINE</span></p>
            <p><strong>Model:</strong> {health.model}</p>
            <p><strong>AI Core:</strong> {health.client_ready ? <span style={{ color: '#22c55e' }}>READY ✅</span> : <span style={{ color: '#ef4444' }}>OFFLINE (Check API Key) ❌</span>}</p>
          </div>
        ) : (
          <p style={{ color: '#ef4444' }}>Backend server is not responding. Please ensure the FastAPI server is running.</p>
        )}
      </div>
      
      <div style={{ marginTop: '3rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        <p>&copy; 2026 AI Hub Orchestration Platform</p>
      </div>
    </div>
  )
}

export default App
