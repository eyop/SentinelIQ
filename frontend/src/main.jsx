import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';

const samplePrompts = [
  'What CVE should I look at for a buffer overflow?',
  'Summarize the latest high-severity vulnerabilities affecting Linux servers.',
  'Show me the most relevant ATT&CK techniques for phishing campaigns.'
];

function App() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [darkMode, setDarkMode] = useState(true);
  const [alerts, setAlerts] = useState([]);
  const [cveItems, setCveItems] = useState([]);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [alertsRes, cvesRes] = await Promise.all([
          fetch('http://127.0.0.1:8000/alerts'),
          fetch('http://127.0.0.1:8000/cves')
        ]);
        const alertsData = await alertsRes.json();
        const cvesData = await cvesRes.json();
        setAlerts(alertsData);
        setCveItems(cvesData);
      } catch (err) {
        console.error(err);
      }
    }
    loadDashboard();
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!question.trim()) {
      setError('Please enter a question.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await fetch('http://127.0.0.1:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, k: 3 }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Request failed');
      }
      setAnswer(data.answer || 'No answer returned.');
    } catch (err) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  const theme = darkMode
    ? { bg: '#020617', panel: '#0f172a', text: '#e2e8f0', muted: '#94a3b8', border: '#1e293b', button: '#2563eb' }
    : { bg: '#f8fafc', panel: '#ffffff', text: '#0f172a', muted: '#475569', border: '#e2e8f0', button: '#2563eb' };

  return (
    <main style={{ minHeight: '100vh', background: theme.bg, color: theme.text, fontFamily: 'Inter, sans-serif', padding: 24 }}>
      <div style={{ maxWidth: 1320, margin: '0 auto', display: 'grid', gap: 20 }}>
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 20, borderRadius: 16, border: `1px solid ${theme.border}`, background: theme.panel }}>
          <div>
            <h1 style={{ margin: '0 0 6px', fontSize: 28 }}>SentinelIQ Dashboard</h1>
            <p style={{ margin: 0, color: theme.muted }}>Security intelligence workspace for CVEs, alerts, and analyst questions.</p>
          </div>
          <button onClick={() => setDarkMode(!darkMode)} style={{ padding: '8px 12px', borderRadius: 999, border: `1px solid ${theme.border}`, background: theme.panel, color: theme.text, cursor: 'pointer' }}>
            {darkMode ? '☀️ Light' : '🌙 Dark'}
          </button>
        </header>

        <section style={{ display: 'grid', gap: 20, gridTemplateColumns: '1.4fr 0.8fr' }}>
          <div style={{ display: 'grid', gap: 20 }}>
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: 20, borderRadius: 16, border: `1px solid ${theme.border}`, background: theme.panel }}>
              <label htmlFor="question" style={{ fontWeight: 600 }}>Security question</label>
              <textarea
                id="question"
                rows={5}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="e.g. What CVE should I look at for a buffer overflow?"
                style={{ padding: 12, fontSize: 15, border: `1px solid ${theme.border}`, borderRadius: 10, background: darkMode ? '#020617' : '#fff', color: theme.text }}
              />
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {samplePrompts.map((prompt) => (
                  <button key={prompt} type="button" onClick={() => setQuestion(prompt)} style={{ padding: '8px 10px', borderRadius: 999, border: `1px solid ${theme.border}`, background: darkMode ? '#020617' : '#f8fafc', color: theme.text, cursor: 'pointer' }}>
                    {prompt}
                  </button>
                ))}
              </div>
              <button type="submit" disabled={loading} style={{ padding: '10px 14px', width: 140, borderRadius: 10, border: 'none', background: theme.button, color: '#fff', cursor: 'pointer' }}>
                {loading ? 'Asking…' : 'Ask'}
              </button>
            </form>

            <section style={{ padding: 20, borderRadius: 16, border: `1px solid ${theme.border}`, background: theme.panel }}>
              <h2 style={{ marginTop: 0 }}>Answer</h2>
              {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}
              {!answer && !error ? <p style={{ color: theme.muted }}>Your answer will appear here. </p> : null}
              {answer ? <p style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{answer}</p> : null}
            </section>
          </div>

          <aside style={{ display: 'grid', gap: 20 }}>
            <section style={{ padding: 20, borderRadius: 16, border: `1px solid ${theme.border}`, background: theme.panel }}>
              <h3 style={{ marginTop: 0 }}>Alerts</h3>
              {alerts.map((alert) => (
                <div key={alert.id} style={{ padding: '10px 0', borderBottom: `1px solid ${theme.border}` }}>
                  <div style={{ fontWeight: 600 }}>{alert.title || alert.message || `Alert ${alert.id}`}</div>
                  <div style={{ color: theme.muted, fontSize: 13 }}>
                    {alert.source} • {alert.severity}
                    {alert.event_time ? ` • ${new Date(alert.event_time).toLocaleString()}` : null}
                  </div>
                  {alert.correlated_cves && alert.correlated_cves.length ? (
                    <div style={{ marginTop: 6, fontSize: 13 }}>
                      Correlated: {alert.correlated_cves.join(', ')}
                    </div>
                  ) : null}
                </div>
              ))}
            </section>

            <section style={{ padding: 20, borderRadius: 16, border: `1px solid ${theme.border}`, background: theme.panel }}>
              <h3 style={{ marginTop: 0 }}>Threat Timeline</h3>
              {alerts.length === 0 ? <div style={{ color: theme.muted }}>No alerts</div> : null}
              {alerts.map((alert) => (
                <div key={`tl-${alert.id}`} style={{ padding: '8px 0', borderBottom: `1px dashed ${theme.border}` }}>
                  <div style={{ fontSize: 13, color: theme.muted }}>{alert.event_time ? new Date(alert.event_time).toLocaleString() : '—'}</div>
                  <div style={{ fontWeight: 600 }}>{alert.title || alert.message || `Alert ${alert.id}`}</div>
                  <div style={{ fontSize: 13, color: theme.muted }}>{alert.source} • {alert.severity}</div>
                </div>
              ))}
            </section>

            <section style={{ padding: 20, borderRadius: 16, border: `1px solid ${theme.border}`, background: theme.panel }}>
              <h3 style={{ marginTop: 0 }}>CVE Explorer</h3>
              {cveItems.map((item) => (
                <div key={item.id} style={{ padding: '10px 0', borderBottom: `1px solid ${theme.border}` }}>
                  <div style={{ fontWeight: 600 }}>{item.id}</div>
                  <div style={{ color: theme.muted, fontSize: 13 }}>{item.severity} • {item.summary}</div>
                </div>
              ))}
            </section>
          </aside>
        </section>
      </div>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><App /></React.StrictMode>
);
