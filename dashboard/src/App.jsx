import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const card = {
  background: '#141926', borderRadius: 12, padding: '20px 24px', flex: 1,
  border: '1px solid #232a3b', color: '#e6e9ef',
}
const label = { color: '#8a92a6', fontSize: 13, marginBottom: 6 }
const value = { fontSize: 32, fontWeight: 700 }

export default function App() {
  const [summary, setSummary] = useState(null)
  const [history, setHistory] = useState([])
  const [running, setRunning] = useState(false)
  const [error, setError] = useState(null)

  const load = () => {
    fetch(`${API_URL}/api/dashboard/summary`).then(r => r.json()).then(setSummary).catch(e => setError(e.message))
    fetch(`${API_URL}/api/evaluate/history`).then(r => r.json()).then(setHistory).catch(() => {})
  }

  useEffect(load, [])

  const runSuite = async () => {
    setRunning(true)
    setError(null)
    try {
      const res = await fetch(`${API_URL}/api/evaluate/run`, { method: 'POST' })
      if (!res.ok) throw new Error(`Run failed: ${res.status}`)
      await res.json()
      load()
    } catch (e) {
      setError(e.message)
    } finally {
      setRunning(false)
    }
  }

  const flagged = history.filter(h => h.flag)

  return (
    <div style={{ fontFamily: 'Inter, system-ui, sans-serif', minHeight: '100vh', background: '#0b0e14', padding: 32 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ color: '#e6e9ef', margin: 0 }}>AI Quality Engineer Platform</h1>
          <p style={{ color: '#8a92a6', margin: '4px 0 0' }}>Automated evaluation • hallucination detection • prompt-injection security</p>
        </div>
        <button
          onClick={runSuite}
          disabled={running}
          style={{
            background: running ? '#2b3245' : '#4f7cff', color: 'white', border: 'none',
            borderRadius: 8, padding: '12px 20px', fontSize: 14, fontWeight: 600, cursor: 'pointer',
          }}
        >
          {running ? 'Running test suite…' : '▶ Run Full Test Suite'}
        </button>
      </div>

      {error && <div style={{ color: '#ff6b6b', marginBottom: 16 }}>{error}</div>}

      {!summary || summary.total_runs === 0 ? (
        <div style={card}>
          <p style={{ color: '#8a92a6' }}>No test runs yet. Click "Run Full Test Suite" to evaluate the model
            against the prompt library, hallucination checks, and security attacks.</p>
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
            <div style={card}>
              <div style={label}>Overall Pass Rate</div>
              <div style={value}>{summary.overall_pass_rate_pct ?? '—'}%</div>
            </div>
            <div style={card}>
              <div style={label}>Avg Latency</div>
              <div style={value}>{summary.avg_latency_ms ?? '—'} ms</div>
            </div>
            <div style={card}>
              <div style={label}>Total Test Runs</div>
              <div style={value}>{summary.total_runs}</div>
            </div>
            <div style={card}>
              <div style={label}>Flagged Issues</div>
              <div style={{ ...value, color: flagged.length ? '#ff6b6b' : '#4fd18b' }}>{flagged.length}</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
            <div style={{ ...card, flex: 2 }}>
              <div style={label}>Avg Score by Category</div>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={summary.by_category}>
                  <CartesianGrid stroke="#232a3b" />
                  <XAxis dataKey="category" tick={{ fill: '#8a92a6', fontSize: 11 }} />
                  <YAxis domain={[0, 10]} tick={{ fill: '#8a92a6', fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: '#141926', border: '1px solid #232a3b' }} />
                  <Bar dataKey="avg_score" fill="#4f7cff" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div style={{ ...card, flex: 1 }}>
              <div style={label}>Flags Breakdown</div>
              {Object.entries(summary.flags || {}).length === 0 && <p style={{ color: '#4fd18b' }}>No flags 🎉</p>}
              {Object.entries(summary.flags || {}).map(([flag, count]) => (
                <div key={flag} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', color: '#e6e9ef', borderBottom: '1px solid #232a3b' }}>
                  <span>{flag}</span><span>{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={card}>
            <div style={label}>Recent Test Runs</div>
            <table style={{ width: '100%', borderCollapse: 'collapse', color: '#e6e9ef', fontSize: 13 }}>
              <thead>
                <tr style={{ textAlign: 'left', color: '#8a92a6' }}>
                  <th style={{ padding: 8 }}>Type</th><th>Prompt ID</th><th>Category</th>
                  <th>Score</th><th>Passed</th><th>Latency</th><th>Flag</th>
                </tr>
              </thead>
              <tbody>
                {history.slice(0, 30).map(h => (
                  <tr key={h.id} style={{ borderTop: '1px solid #232a3b' }}>
                    <td style={{ padding: 8 }}>{h.run_type}</td>
                    <td>{h.prompt_id}</td>
                    <td>{h.category}</td>
                    <td>{h.score ?? '—'}</td>
                    <td style={{ color: h.passed ? '#4fd18b' : '#ff6b6b' }}>{h.passed ? 'PASS' : 'FAIL'}</td>
                    <td>{h.latency_ms ? Math.round(h.latency_ms) + 'ms' : '—'}</td>
                    <td style={{ color: h.flag ? '#ff9f43' : '#8a92a6' }}>{h.flag || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
