// Vite exposes env vars on import.meta.env; cast to any to avoid TS complaints in this starter
const API_BASE = ((import.meta as any).env?.VITE_API_BASE_URL) || 'http://localhost:8000';

async function postPredictSchedule(payload: any) {
  const url = `${API_BASE.replace(/\/$/, '')}/predict-schedule`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }

  const data = await res.json();
  console.log('Backend response:', data);  // Debug logging
  return data;
}

async function getMockData() {
  const url = `${API_BASE.replace(/\/$/, '')}/mock-data`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch mock data: ${res.status}`);
  }
  return await res.json();
}

export { postPredictSchedule, getMockData };
