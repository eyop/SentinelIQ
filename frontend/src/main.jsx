import React, { useState } from 'react';
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

  return (
    <main style={{ maxWidth: 920, margin: '40px auto', fontFamily: 'Inter, sans-serif', padding: 24, color: '#0f172a' }}>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ marginBottom: 8, fontSize: 32 }}>SentinelIQ Dashboard</h1>
        <p style={{ margin: 0, fontSize: 16, color: '#475569' }}>
          Ask a security question and receive a grounded reply from the local backend.
        </p>
      </header>

      <section style={{ display: 'grid', gap: 16, gridTemplateColumns: '1.1fr 0.9fr' }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: 20, border: '1px solid #e2e8f0', borderRadius: 14, background: '#fff' }}>
          <label htmlFor="question" style={{ fontWeight: 600 }}>Security question</label>
          <textarea
            id="question"
            rows={5}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. What CVE should I look at for a buffer overflow?"
            style={{ padding: 12, fontSize: 15, border: '1px solid #cbd5e1', borderRadius: 10 }}
          />
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {samplePrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => setQuestion(prompt)}
                style={{ padding: '8px 10px', borderRadius: 999, border: '1px solid #cbd5e1', background: '#f8fafc', cursor: 'pointer' }}
              >
                {prompt}
              </button>
            ))}
          </div>
          <button type="submit" disabled={loading} style={{ padding: '10px 14px', width: 140, borderRadius: 10, border: 'none', background: '#2563eb', color: '#fff', cursor: 'pointer' }}>
            {loading ? 'Asking…' : 'Ask'}
          </button>
        </form>

        <section style={{ padding: 20, border: '1px solid #e2e8f0', borderRadius: 14, background: '#f8fafc' }}>
          <h2 style={{ marginTop: 0 }}>Answer</h2>
          {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}
          {!answer && !error ? <p style={{ color: '#64748b' }}>Your answer will appear here.</p> : null}
          {answer ? <p style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{answer}</p> : null}
        </section>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><App /></React.StrictMode>
);
