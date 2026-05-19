import React, { useEffect, useState } from 'react';

interface Offer {
  id: number;
  title: string;
  company_name: string;
  application_date: string;
  tech_tags: string[];
  raw_content: string;
}

export default function App() {
  const [offers, setOffers] = useState<Offer[]>([]);
  const [url, setUrl] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [showTable, setShowTable] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedOffer, setSelectedOffer] = useState<Offer | null>(null);
  const [downloading, setDownloading] = useState<boolean>(false);
  
  const [isEditingCompany, setIsEditingCompany] = useState<boolean>(false);
  const [editCompanyName, setEditCompanyName] = useState<string>('');
  const [updatingCompany, setUpdatingCompany] = useState<boolean>(false);

  const fetchOffers = async () => {
    try {
      const res = await fetch('http://localhost:8000/offers');
      if (res.ok) {
        const data = await res.json();
        setOffers(data);
        
        if (selectedOffer) {
          const updatedSelected = data.find((o: Offer) => o.id === selectedOffer.id);
          if (updatedSelected) setSelectedOffer(updatedSelected);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchOffers();
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/offers/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          url: url,
          raw_content: null 
        }),
      });
      if (res.ok) {
        setUrl('');
        await fetchOffers();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateCompany = async () => {
    if (!selectedOffer || !editCompanyName.trim()) return;
    setUpdatingCompany(true);
    try {
      const res = await fetch(`http://localhost:8000/offers/${selectedOffer.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_name: editCompanyName.trim() }),
      });
      if (res.ok) {
        setIsEditingCompany(false);
        await fetchOffers();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setUpdatingCompany(false);
    }
  };

  const downloadNotebookLMTxt = async (offerId: number, company: string, title: string) => {
    setDownloading(true);
    try {
      const res = await fetch(`http://localhost:8000/offers/${offerId}/notebooklm`);
      if (!res.ok) throw new Error('Failed to fetch template');
      
      const text = await res.text();
      const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      
      const cleanCompanyName = company.replace(/[^a-z0-9]/gi, '_').toLowerCase();
      link.href = downloadUrl;
      link.download = `notebooklm_${cleanCompanyName}_${offerId}.txt`;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error(err);
    } finally {
      setDownloading(false);
    }
  };

  const filteredOffers = offers.filter((offer) =>
    offer.company_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div style={{ maxWidth: '1000px', margin: '40px auto', padding: '0 20px', fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ fontSize: '28px', marginBottom: '20px' }}>JobStack Tracker</h1>
      
      <form onSubmit={handleAdd} style={{ display: 'flex', gap: '10px', marginBottom: '30px' }}>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste job board URL to apply..."
          required
          style={{ flex: 1, padding: '12px', fontSize: '16px', borderRadius: '6px', border: '1px solid #ccc' }}
        />
        <button 
          type="submit" 
          disabled={loading} 
          style={{ padding: '12px 24px', fontSize: '16px', borderRadius: '6px', border: 'none', backgroundColor: '#0070f3', color: '#fff', cursor: 'pointer', fontWeight: 'bold' }}
        >
          {loading ? 'Processing...' : 'Add Application'}
        </button>
      </form>

      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={() => setShowTable(!showTable)}
          style={{ padding: '10px 20px', fontSize: '15px', borderRadius: '6px', border: '1px solid #0070f3', backgroundColor: showTable ? '#e0f2fe' : '#fff', color: '#0070f3', cursor: 'pointer', fontWeight: '500' }}
        >
          {showTable ? 'Hide Applications' : 'Show Applications'}
        </button>
      </div>

      {showTable && (
        <div style={{ marginBottom: '40px' }}>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by company name..."
            style={{ width: '100%', padding: '10px', fontSize: '15px', borderRadius: '6px', border: '1px solid #ccc', marginBottom: '15px', boxSizing: 'border-box' }}
          />

          <table style={{ width: '100%', borderCollapse: 'collapse', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', borderRadius: '6px', overflow: 'hidden' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                <th style={{ textAlign: 'left', padding: '12px' }}>Company</th>
                <th style={{ textAlign: 'left', padding: '12px' }}>Title</th>
                <th style={{ textAlign: 'left', padding: '12px' }}>Date</th>
              </tr>
            </thead>
            <tbody>
              {filteredOffers.map((o) => (
                <tr 
                  key={o.id} 
                  onClick={() => {
                    setSelectedOffer(o);
                    setIsEditingCompany(false);
                  }}
                  style={{ borderBottom: '1px solid #e2e8f0', cursor: 'pointer', backgroundColor: selectedOffer?.id === o.id ? '#f1f5f9' : '#fff' }}
                >
                  <td style={{ padding: '12px', fontWeight: '500' }}>{o.company_name}</td>
                  <td style={{ padding: '12px', color: '#334155' }}>{o.title}</td>
                  <td style={{ padding: '12px', color: '#64748b' }}>{new Date(o.application_date).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedOffer && (
        <div style={{ padding: '25px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '15px' }}>
            <div>
              <h2 style={{ margin: 0 }}>{selectedOffer.title}</h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '5px' }}>
                {isEditingCompany ? (
                  <>
                    <input 
                      type="text" 
                      value={editCompanyName} 
                      onChange={(e) => setEditCompanyName(e.target.value)}
                      style={{ padding: '4px 8px', fontSize: '16px', borderRadius: '4px', border: '1px solid #ccc' }}
                    />
                    <button onClick={handleUpdateCompany} disabled={updatingCompany} style={{ padding: '4px 10px', backgroundColor: '#0070f3', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                      {updatingCompany ? 'Saving...' : 'Save'}
                    </button>
                    <button onClick={() => setIsEditingCompany(false)} style={{ padding: '4px 10px', backgroundColor: '#e2e8f0', color: '#334155', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Cancel</button>
                  </>
                ) : (
                  <>
                    <span style={{ fontSize: '18px', color: '#475569', fontWeight: '500' }}>@ {selectedOffer.company_name}</span>
                    <button 
                      onClick={() => {
                        setEditCompanyName(selectedOffer.company_name);
                        setIsEditingCompany(true);
                      }}
                      style={{ padding: '2px 8px', fontSize: '12px', backgroundColor: 'transparent', border: '1px solid #cbd5e1', borderRadius: '4px', cursor: 'pointer', color: '#64748b' }}
                    >
                      Edit Company Name
                    </button>
                  </>
                )}
              </div>
            </div>
            <button
              onClick={() => downloadNotebookLMTxt(selectedOffer.id, selectedOffer.company_name, selectedOffer.title)}
              disabled={downloading}
              style={{ padding: '10px 16px', fontSize: '14px', borderRadius: '6px', border: 'none', backgroundColor: '#10b981', color: '#fff', cursor: 'pointer', fontWeight: 'bold' }}
            >
              {downloading ? 'Downloading...' : 'Generate NotebookLM Template'}
            </button>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ fontSize: '16px', margin: '0 0 8px 0', color: '#475569' }}>Extracted Skillset</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {selectedOffer.tech_tags.length > 0 ? (
                selectedOffer.tech_tags.map((tag, idx) => (
                  <span key={idx} style={{ padding: '4px 10px', backgroundColor: '#e2e8f0', color: '#1e293b', borderRadius: '4px', fontSize: '13px', fontWeight: '500' }}>
                    {tag}
                  </span>
                ))
              ) : (
                <span style={{ color: '#64748b', fontSize: '14px' }}>No tags found</span>
              )}
            </div>
          </div>

          <div>
            <h3 style={{ fontSize: '16px', margin: '0 0 8px 0', color: '#475569' }}>Raw Content</h3>
            <pre style={{ backgroundColor: '#fff', padding: '15px', borderRadius: '6px', border: '1px solid #cbd5e1', overflowX: 'auto', whiteSpace: 'pre-wrap', maxHeight: '300px', fontSize: '13px', lineHeight: '1.6', color: '#334155', margin: 0 }}>
              {selectedOffer.raw_content}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}