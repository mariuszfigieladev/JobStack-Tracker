import React, { useEffect, useState } from 'react';

interface Offer {
  id: number;
  title: string;
  company_name: string;
  salary_min: number | null;
  salary_max: number | null;
  currency: string;
  application_date: string;
  tech_tags: string[];
  raw_content: string;
}

export default function App() {
  const [offers, setOffers] = useState<Offer[]>([]);
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [showTable, setShowTable] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedOffer, setSelectedOffer] = useState<Offer | null>(null);
  const [downloading, setDownloading] = useState(false);
  
  const [isEditing, setIsEditing] = useState({ company: false, salary: false, tags: false });
  const [editFields, setEditFields] = useState<{
    company: string;
    salary_min: number | '';
    salary_max: number | '';
    tags: string;
  }>({ company: '', salary_min: '', salary_max: '', tags: '' });

  const fetchOffers = async () => {
    try {
      const res = await fetch('http://localhost:8000/offers');
      const data = await res.json();
      setOffers(data);
      if (selectedOffer) {
        setSelectedOffer(data.find((o: Offer) => o.id === selectedOffer.id) || null);
      }
    } catch (err) {
      console.error("Error fetching offers:", err);
    }
  };

  useEffect(() => { fetchOffers(); }, []);

  const handleUpdate = async (patchData: any) => {
    try {
      await fetch(`http://localhost:8000/offers/${selectedOffer!.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patchData),
      });
      setIsEditing({ company: false, salary: false, tags: false });
      await fetchOffers();
    } catch (err) {
      console.error("Error updating offer:", err);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/offers/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url, raw_content: null }),
      });
      if (res.ok) {
        setUrl('');
        await fetchOffers();
      }
    } catch (err) {
      console.error("Error adding offer:", err);
    } finally {
      setLoading(false);
    }
  };

  const downloadNotebookLMTxt = async (offerId: number, company: string) => {
    setDownloading(true);
    try {
      const res = await fetch(`http://localhost:8000/offers/${offerId}/notebooklm`);
      if (!res.ok) throw new Error('Failed to fetch template');
      const text = await res.text();
      const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `notebooklm_${company.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_${offerId}.txt`;
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

  return (
    <div style={{ maxWidth: '1100px', margin: '40px auto', padding: '0 20px', fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ fontSize: '28px', marginBottom: '30px' }}>JobStack Tracker</h1>
      
      <form onSubmit={handleAdd} style={{ display: 'flex', gap: '10px', marginBottom: '30px' }}>
        <input value={url} onChange={e => setUrl(e.target.value)} placeholder="Paste job URL..." style={{ flex: 1, padding: '12px', border: '1px solid #ccc', borderRadius: '6px' }} />
        <button type="submit" disabled={loading} style={{ padding: '0 24px', background: '#0070f3', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>
          {loading ? 'Adding...' : 'Add Application'}
        </button>
      </form>

      <button onClick={() => setShowTable(!showTable)} style={{ marginBottom: '20px', padding: '10px 20px', background: showTable ? '#e0f2fe' : '#fff', color: '#0070f3', border: '1px solid #0070f3', borderRadius: '6px', cursor: 'pointer', fontWeight: '500' }}>
        {showTable ? 'Hide Applications' : 'Show Applications'}
      </button>

      {showTable && (
        <div style={{ marginBottom: '40px' }}>
          <input placeholder="Search company..." onChange={(e) => setSearchTerm(e.target.value)} style={{ width: '100%', padding: '10px', border: '1px solid #ccc', borderRadius: '6px', marginBottom: '15px' }} />
          <table style={{ width: '100%', borderCollapse: 'collapse', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', borderRadius: '6px', overflow: 'hidden' }}>
            <thead style={{ background: '#f8fafc' }}>
              <tr>
                <th style={{ padding: '12px', textAlign: 'left' }}>Company</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Title</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Applied Date</th>
              </tr>
            </thead>
            <tbody>
              {offers.filter(o => o.company_name.toLowerCase().includes(searchTerm.toLowerCase())).map(o => (
                <tr key={o.id} onClick={() => setSelectedOffer(o)} style={{ cursor: 'pointer', borderBottom: '1px solid #e2e8f0', background: selectedOffer?.id === o.id ? '#f1f5f9' : '#fff' }}>
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
        <div style={{ padding: '30px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h2 style={{ margin: 0, color: '#1e293b' }}>{selectedOffer.title}</h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginTop: '15px', flexWrap: 'wrap' }}>
                
                {/* Company Name */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '20px', fontWeight: 'bold', color: '#475569' }}>@</span>
                  {isEditing.company ? (
                    <input autoFocus value={editFields.company} onChange={(e) => setEditFields({...editFields, company: e.target.value})} style={{ padding: '4px 8px', borderRadius: '4px', border: '1px solid #cbd5e1' }} />
                  ) : (
                    <span style={{ fontSize: '20px', fontWeight: 'bold', color: '#1e293b' }}>{selectedOffer.company_name}</span>
                  )}
                  <button onClick={() => { 
                      if (isEditing.company) handleUpdate({ company_name: editFields.company.trim() });
                      else { setEditFields({...editFields, company: selectedOffer.company_name}); setIsEditing({...isEditing, company: true}); }
                  }} style={{ padding: '4px 8px', fontSize: '12px', background: 'transparent', border: '1px solid #cbd5e1', borderRadius: '4px', cursor: 'pointer', color: '#64748b' }}>
                    {isEditing.company ? 'Save' : 'Edit Company'}
                  </button>
                </div>

                {/* Salary */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderLeft: '2px solid #cbd5e1', paddingLeft: '15px' }}>
                  <span style={{ fontWeight: '500', color: '#475569' }}>Salary:</span>
                  {isEditing.salary ? (
                    <>
                      <input type="number" placeholder="Min" value={editFields.salary_min} onChange={(e) => setEditFields({...editFields, salary_min: e.target.value ? Number(e.target.value) : ''})} style={{ width: '80px', padding: '4px 8px', borderRadius: '4px', border: '1px solid #cbd5e1' }} />
                      <span>-</span>
                      <input type="number" placeholder="Max" value={editFields.salary_max} onChange={(e) => setEditFields({...editFields, salary_max: e.target.value ? Number(e.target.value) : ''})} style={{ width: '80px', padding: '4px 8px', borderRadius: '4px', border: '1px solid #cbd5e1' }} />
                    </>
                  ) : (
                    <span style={{ color: '#0f172a', fontWeight: '500' }}>
                      {selectedOffer.salary_min || '?'} - {selectedOffer.salary_max || '?'} {selectedOffer.currency}
                    </span>
                  )}
                  <button onClick={() => { 
                      if (isEditing.salary) handleUpdate({ salary_min: editFields.salary_min || null, salary_max: editFields.salary_max || null });
                      else { setEditFields({...editFields, salary_min: selectedOffer.salary_min || '', salary_max: selectedOffer.salary_max || ''}); setIsEditing({...isEditing, salary: true}); }
                  }} style={{ padding: '4px 8px', fontSize: '12px', background: 'transparent', border: '1px solid #cbd5e1', borderRadius: '4px', cursor: 'pointer', color: '#64748b' }}>
                    {isEditing.salary ? 'Save' : 'Edit Salary'}
                  </button>
                </div>

                {/* Date Badge */}
                <div style={{ borderLeft: '2px solid #cbd5e1', paddingLeft: '15px', color: '#64748b', fontSize: '14px', fontWeight: '500' }}>
                  Applied: {new Date(selectedOffer.application_date).toLocaleDateString()}
                </div>

              </div>
            </div>
            <button onClick={() => downloadNotebookLMTxt(selectedOffer.id, selectedOffer.company_name)} disabled={downloading} style={{ padding: '10px 16px', background: '#10b981', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>
              {downloading ? 'Generating...' : 'Generate NotebookLM Template'}
            </button>
          </div>

          {/* Skillset */}
          <div style={{ marginTop: '30px', textAlign: 'center' }}>
            <h3 style={{ fontSize: '16px', color: '#475569', marginBottom: '15px' }}>Extracted Skillset</h3>
            {isEditing.tags ? (
              <div style={{ display: 'flex', justifyContent: 'center', gap: '10px' }}>
                <input autoFocus value={editFields.tags} onChange={(e) => setEditFields({...editFields, tags: e.target.value})} style={{ width: '60%', padding: '8px', borderRadius: '4px', border: '1px solid #cbd5e1' }} placeholder="python, docker, aws..." />
                <button onClick={() => {
                  handleUpdate({ tech_tags: editFields.tags.split(',').map(t => t.trim()).filter(t => t !== '') });
                }} style={{ padding: '8px 16px', background: '#0070f3', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Save Tags</button>
                <button onClick={() => setIsEditing({...isEditing, tags: false})} style={{ padding: '8px 16px', background: '#e2e8f0', color: '#334155', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Cancel</button>
              </div>
            ) : (
              <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '8px' }}>
                {selectedOffer.tech_tags.length > 0 ? (
                  selectedOffer.tech_tags.map((tag, idx) => (
                    <span key={idx} style={{ background: '#e2e8f0', color: '#1e293b', padding: '6px 12px', borderRadius: '4px', fontSize: '13px', fontWeight: '500' }}>{tag}</span>
                  ))
                ) : (
                  <span style={{ color: '#64748b', fontSize: '14px', fontStyle: 'italic', padding: '6px 0' }}>No skills extracted yet</span>
                )}
                <button onClick={() => { setEditFields({...editFields, tags: selectedOffer.tech_tags.join(', ')}); setIsEditing({...isEditing, tags: true}); }} style={{ padding: '6px 12px', fontSize: '13px', background: 'transparent', border: '1px dashed #cbd5e1', borderRadius: '4px', cursor: 'pointer', color: '#64748b' }}>✏️ Edit / Add Tags</button>
              </div>
            )}
          </div>

          <div style={{ marginTop: '30px' }}>
            <h3 style={{ fontSize: '16px', color: '#475569', textAlign: 'center' }}>Raw Content</h3>
            <pre style={{ background: '#fff', padding: '15px', borderRadius: '6px', border: '1px solid #cbd5e1', overflowX: 'auto', whiteSpace: 'pre-wrap', maxHeight: '400px', fontSize: '13px', color: '#334155', lineHeight: '1.6' }}>
              {selectedOffer.raw_content}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}