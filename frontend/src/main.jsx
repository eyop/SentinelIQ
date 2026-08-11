import React, { useEffect, useRef, useState } from 'react';
import ReactDOM from 'react-dom/client';

const API_BASE = ''; // uses Vite dev proxy -> backend

const samplePrompts = [
  'What CVE should I look at for a buffer overflow?',
  'Summarize the latest high-severity vulnerabilities affecting Linux servers.',
  'Show me the most relevant ATT&CK techniques for phishing campaigns.',
];

function App() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [darkMode, setDarkMode] = useState(true);
  const [alerts, setAlerts] = useState([]);
  const [cveItems, setCveItems] = useState([]);
  const abortRef = useRef(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [alertsRes, cvesRes] = await Promise.all([
          fetch(`${API_BASE}/alerts`),
          fetch(`${API_BASE}/cves`),
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
    return () => abortRef.current?.abort();
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!question.trim()) {
      setError('Please enter a question.');
      return;
    }

    setLoading(true);
    setError('');
    setAnswer('');
    abortRef.current = new AbortController();

    try {
      const response = await fetch(`${API_BASE}/query/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, k: 3 }),
        signal: abortRef.current.signal,
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Request failed');
      }

      // Parse Server-Sent Events stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let full = '';
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data:')) {
            const payload = trimmed.slice(5).trim();
            if (payload) {
              full += payload + '\n';
              setAnswer(full);
            }
          }
        }
      }
      if (!full) setAnswer('No answer returned.');
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Something went wrong');
      }
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
              <div style={{ display: 'flex', gap: 8 }}>
                <button type="submit" disabled={loading} style={{ padding: '10px 14px', width: 140, borderRadius: 10, border: 'none', background: theme.button, color: '#fff', cursor: 'pointer' }}>
                  {loading ? 'Asking…' : 'Ask'}
                </button>
                {loading && (
                  <button type="button" onClick={() => abortRef.current?.abort()} style={{ padding: '10px 14px', borderRadius: 10, border: `1px solid ${theme.border}`, background: theme.panel, color: theme.text, cursor: 'pointer' }}>
                    Stop
                  </button>
                )}
              </div>
            </form>

            <section style={{ padding: 20, borderRadius: 16, border: `1px solid ${theme.border}`, background: theme.panel }}>
              <h2 style={{ marginTop: 0 }}>Answer</h2>
              {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}
              {!answer && !error ? <p style={{ color: theme.muted }}>Your answer will appear here (streamed live).</p> : null}
              {answer ? <p style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{answer}</p> : null}
            </section>
          </div>

          <aside style={{ display: 'grid', gap: 20 }}>
            <section style={{ padding: 20, borderRadius: 16, border: `1px solid ${theme.border}`, background: theme.panel }}>
              <h3 style={{ marginTop: 0 }}>Alerts</h3>
              {alerts.map((alert) => (
                <div key={alert.id} style={{ padding: '10px 0', borderBottom: `1px solid ${theme.border}` }}>
                  <span style={{ display: 'inline-block', marginRight: 8, padding: '2px 8px', borderRadius: 999, fontSize: 12, background: alert.severity === 'High' ? '#dc2626' : '#d97706', color: '#fff' }}>
                    {alert.severity}
                  </span>
                  <div style={{ fontWeight: 600 }}>{alert.message || `Alert ${alert.id}`}</div>
                  <div style={{ color: theme.muted, fontSize: 13 }}>
                    {alert.source} • {alert.event_time ? new Date(alert.event_time).toLocaleString() : ''}
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