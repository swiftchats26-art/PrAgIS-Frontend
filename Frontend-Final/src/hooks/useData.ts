import { mockFarmSummary, mockAgentOutputs, mockExplanation } from '../data/mockData';
import type { FarmSummary, AgentOutput, Explanation } from '../types';
import type { IrrigationData } from '../types/irrigation';

// The frontend was originally using static mock data. For quick integration
// with the backend we expose the same hooks but they will prefer remote data
// if the app sets `window.__REMOTE_DATA__` after a successful POST.

function extractAgentOutputsFromRemote(remote: any): AgentOutput[] {
  try {
    const agents = remote?.agents || {};
    const out: AgentOutput[] = [];
    // Map climate
    if (agents.climate) {
      const c = agents.climate.output || {};
      out.push({
        category: 'Climate',
        confidence: Math.round((agents.climate.confidence || 0) * 100),
        metrics: [
          { label: 'Temperature', value: (c.avg_tmax_c ?? '-'), unit: '°C' },
          { label: 'Humidity', value: (c.avg_tmin_c ?? '-'), unit: '°C' },
          { label: 'Rainfall', value: (c.total_rainfall_mm ?? '-'), unit: 'mm' },
        ],
      });
    }

    if (agents.soil_water) {
      const s = agents.soil_water.output || {};
      out.push({
        category: 'Soil & Water',
        confidence: Math.round((agents.soil_water.confidence || 0) * 100),
        metrics: [
          { label: 'Soil Moisture', value: (s.avg_soil_moisture_pct ?? '-'), unit: '%' },
          { label: 'Rain Sum', value: (s.rain_sum_mm ?? '-'), unit: 'mm' },
          { label: 'Drought Risk', value: (s.drought_risk ?? '-'), unit: '%' },
        ],
      });
    }

    if (agents.crop_growth) {
      const g = agents.crop_growth.output || {};
      out.push({
        category: 'Crop Growth',
        confidence: Math.round((agents.crop_growth.confidence || 0) * 100),
        metrics: [
          { label: 'Growth Stage', value: (g.growth_stage ?? '-'), unit: '' },
          { label: 'Days After Sowing', value: (g.days_after_sowing ?? '-'), unit: 'days' },
          { label: 'Yield Index', value: (g.yield_index ?? '-'), unit: '' },
        ],
      });
    }

    if (agents.et0) {
      const e = agents.et0.output || {};
      out.push({
        category: 'ET0',
        confidence: Math.round((agents.et0.confidence || 0) * 100),
        metrics: [
          { label: 'Reference ET', value: (e.et0_mm_per_day ?? '-'), unit: 'mm/day' },
          { label: 'Kc', value: (e.kc_factor ?? '-'), unit: '' },
        ],
      });
    }

    return out.length ? out : mockAgentOutputs;
  } catch (e) {
    return mockAgentOutputs;
  }
}

function extractIrrigationScheduleFromRemote(remote: any) {
  try {
    console.log('Extracting irrigation data from:', remote);
    
    // Get irrigation volume from the response
    const irrigationVolume = Number(remote.irrigation_volume_mm);
    console.log('Extracted irrigation volume:', irrigationVolume);
    
    const data = {
      overallConfidence: Math.round((remote.confidence_score || 0) * 100),
      irrigationVolume: isNaN(irrigationVolume) ? 0 : irrigationVolume,
      irrigationMode: remote.irrigation_mode ?? 'drip',
      daysAfterSowing: remote.days_after_sowing ?? 0,
      yieldIndex: remote.yield_index ?? 0
    };
    
    console.log('Returning irrigation data:', data);
    return data;
  } catch (e) {
    return {
      overallConfidence: 0,
      irrigationVolume: 0,
      irrigationMode: 'drip',
      daysAfterSowing: 0,
      yieldIndex: 0
    };
  }
}

function extractExplanationFromRemote(remote: any) {
  try {
    return {
      reasoning: remote.short_reasoning || mockExplanation.reasoning,
      waterSaved: remote.time_factors ? `Adjusted by factors: ${JSON.stringify(remote.time_factors)}` : mockExplanation.waterSaved,
    };
  } catch (e) {
    return mockExplanation;
  }
}

export function useFarmSummary(): FarmSummary {
  // frontend doesn't send farm summary in response; keep using mock
  return mockFarmSummary;
}

export function useAgentOutputs(): AgentOutput[] {
  // prefer remote if available
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const remote = (window as any).__REMOTE_DATA__;
  if (remote) return extractAgentOutputsFromRemote(remote);
  return mockAgentOutputs;
}

export function useIrrigationSchedule(): IrrigationData {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const remote = (window as any).__REMOTE_DATA__;
  if (remote) {
    console.log('Raw remote data:', remote);
    const result = extractIrrigationScheduleFromRemote(remote);
    console.log('Extracted irrigation data:', result);
    return result;
  }
  return {
    overallConfidence: 0,
    irrigationVolume: 0,
    irrigationMode: 'drip',
    daysAfterSowing: 0,
    yieldIndex: 0
  };
}

export function useExplanation(): Explanation {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const remote = (window as any).__REMOTE_DATA__;
  if (remote) return extractExplanationFromRemote(remote);
  return mockExplanation;
}
