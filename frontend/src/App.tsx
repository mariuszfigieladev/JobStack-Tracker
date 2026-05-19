import React, { useState } from 'react';

interface ScrapeResponse {
  status: string;
  inserted_id: number;
}

export default function App() {
  const [url, setUrl] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [brief, setBrief] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [copied, setCopied] = useState<boolean>(false);

  const handleScrape = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setBrief('');
    setCopied(false);

    try {
      const scrapeRes = await fetch('http://localhost:8000/offers/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });

      if (!scrapeRes.ok) {
        throw new Error('Scraping pipeline failed');
      }
      
      const scrapeData: ScrapeResponse = await scrapeRes.json();

      const briefRes = await fetch(`http://localhost:8000/offers/${scrapeData.inserted_id}/notebooklm`);
      if (!briefRes.ok) {
        throw new Error('Failed to fetch NotebookLM document template');
      }
      
      const briefText = await briefRes.text();
      setBrief(briefText);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(brief);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ maxWidth: '800px', margin: '40px auto', padding: '0 20px', fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ fontSize: '28px', marginBottom: '20px' }}>JobStack to NotebookLM Source Generator</h1>
      
      <form onSubmit={handleScrape} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste job board URL (e.g. Pracuj.pl, JustJoin)..."
          required
          style={{ flex: 1, padding: '12px', fontSize: '16px', borderRadius: '6px', border: '1px solid #ccc' }}
        />
        <button 
          type="submit" 
          disabled={loading} 
          style={{ padding: '12px 24px', fontSize: '16px', borderRadius: '6px', border: 'none', backgroundColor: '#0070f3', color: '#fff', cursor: 'pointer', fontWeight: 'bold' }}
        >
          {loading ? 'Processing...' : 'Fetch & Generate'}
        </button>
      </form>

      {error && (
        <div style={{ padding: '12px', backgroundColor: '#fee2e2', color: '#991b1b', borderRadius: '6px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {brief && (
        <div style={{ marginTop: '30px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h2 style={{ fontSize: '20px', margin: 0 }}>Generated Brief Document</h2>
            <button 
              onClick={copyToClipboard} 
              style={{ padding: '8px 16px', fontSize: '14px', borderRadius: '4px', border: '1px solid #0070f3', backgroundColor: copied ? '#e0f2fe' : '#fff', color: '#0070f3', cursor: 'pointer', fontWeight: '500' }}
            >
              {copied ? 'Copied to Clipboard!' : 'Copy Brief'}
            </button>
          </div>
          <pre style={{ backgroundColor: '#f8fafc', padding: '20px', overflowX: 'auto', whiteSpace: 'pre-wrap', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '14px', lineHeight: '1.5', color: '#334155' }}>
            {brief}
          </pre>
        </div>
      )}
    </div>
  );
}