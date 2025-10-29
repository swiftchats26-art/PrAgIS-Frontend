import { useState } from 'react';
import Dashboard from './components/Dashboard';
import InputForm, { type FormData } from './components/InputForm';
import { postPredictSchedule, getMockData } from './services/api';

export default function App() {
  const [farmData, setFarmData] = useState<FormData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFormSubmit = async (data: FormData) => {
    setLoading(true);
    // indicate a pending background submit for UI hooks
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).__PENDING_SUBMIT__ = true;
    setError(null);
    try {
      // Build payload to match backend FarmInput schema
      // Normalize values to match backend `FarmInput` schema
      const crop = (data.crop || '').toString().trim().toLowerCase();
      const soilOption = (data.soilType || '').toString().trim();
      const soilMap: Record<string, string> = {
        'alluvial soil': 'sandy',
        'black soil': 'clay',
        'red soil': 'sandy',
        'clay': 'clay',
        'sandy': 'sandy',
      };

      const soil_type = soilMap[soilOption.toLowerCase()] || 'sandy';

      const payload: any = {
        crop_type: crop,
        soil_type: soil_type,
        sowing_date: data.sowingDate,
        // include coordinates and area from the form when provided
        latitude: data.latitude ?? undefined,
        longitude: data.longitude ?? undefined,
        farm_area_ha: data.farmArea ?? 1.0,
      };

      // If we don't have last_5_days or coordinates, fetch example mock-data from the backend
      // and merge its last_5_days and coords into our payload so climate/et0/soil agents have input.
      let mergedPayload = { ...payload };
      try {
        const mock = await getMockData();
        if (!mergedPayload.last_5_days) mergedPayload.last_5_days = mock.last_5_days;
        if (!mergedPayload.latitude) mergedPayload.latitude = mock.latitude;
        if (!mergedPayload.longitude) mergedPayload.longitude = mock.longitude;
        if (!mergedPayload.farm_area_ha) mergedPayload.farm_area_ha = mock.farm_area_ha || mergedPayload.farm_area_ha;
      } catch (e) {
        // ignore mock data fetch errors and continue with minimal payload
      }

      const resp = await postPredictSchedule(mergedPayload);

      // Log the raw response
      console.log('Backend raw response:', resp);

      // expose remote data to hooks/components
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (window as any).__REMOTE_DATA__ = resp;

      // store original form values too so Dashboard can display them
      setFarmData(data);
    } catch (err: any) {
      setError(err?.message || String(err));
    } finally {
      setLoading(false);
      // clear pending flag
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (window as any).__PENDING_SUBMIT__ = false;
    }
  };

  if (!farmData) {
    return <InputForm onSubmit={handleFormSubmit} />;
  }

  // show loading / error states while awaiting response
  if ((window as any).__REMOTE_DATA__ == null && (window as any).__PENDING_SUBMIT__) {
    return (
      <div className="min-h-screen flex items-center justify-center"> 
        <div className="text-center">Loading schedule from backend...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center"> 
        <div className="text-center text-red-600">Error: {error}</div>
      </div>
    );
  }

  return <Dashboard farmData={farmData} />;
}
