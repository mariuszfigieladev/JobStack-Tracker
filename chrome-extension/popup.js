document.getElementById('scrapeBtn').addEventListener('click', async () => {
  const status = document.getElementById('status');
  status.textContent = 'Scraping...';
  
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    function: extractContent,
  }, async (injectionResults) => {
    if (!injectionResults || !injectionResults[0].result) {
      status.textContent = 'Failed to read page';
      return;
    }

    const data = injectionResults[0].result;

    try {
      const res = await fetch('http://localhost:8000/offers/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      
      if (res.ok) {
        status.textContent = 'Success!';
        status.style.color = '#10b981';
      } else {
        status.textContent = `API Error: ${res.status}`;
        status.style.color = '#ef4444';
      }
    } catch (err) {
      status.textContent = 'Connection failed';
      status.style.color = '#ef4444';
    }
  });
});

function extractContent() {
  // 1. Szukanie kontenera szczegółów oferty dla różnych widoków LinkedIn oraz Pracuj.pl
  const container = document.querySelector('.jobs-search__job-details--container') || 
                    document.querySelector('.job-view-layout') ||
                    document.querySelector('.jobs-description') ||
                    document.querySelector('[class*="job-details"]') ||
                    document.querySelector('[data-test="section-offer-work"]') ||
                    document.getElementById('offer-content');
  
  let content = container ? container.innerText : document.body.innerText;
  
  // 2. Jeśli skrypt pobrał stronę logowania, spróbuj odszukać główny artykuł/opis roli
  if (content.includes("Cookie Policy") && content.includes("Sign in with Apple")) {
    const mainContent = document.querySelector('main') || document.querySelector('#main-content');
    if (mainContent) {
      content = mainContent.innerText;
    }
  }

  // 3. Czyszczenie spamu ze stopki (języki, polityki prywatności), gdyby zaciągnęło całe body
  const cleanContent = content
    .replace(/By clicking Continue, you agree to.*/gi, '')
    .replace(/Sign in Sign in with Apple.*/gi, '')
    .replace(/Language\s+العربية.*/gi, '');

  return {
    url: window.location.href.split('?')[0],
    raw_content: cleanContent.trim()
  };
}