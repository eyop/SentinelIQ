import React from 'react';
import ReactDOM from 'react-dom/client';

function App() {
  return (
    <main style={{ fontFamily: 'sans-serif', padding: 24 }}>
      <h1>SentinelIQ Dashboard</h1>
      <p>Connect this frontend to the FastAPI backend to query CVEs and alerts.</p>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><App /></React.StrictMode>
);
