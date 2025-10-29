import type { FarmSummary, AgentOutput, IrrigationSchedule, Explanation } from '../types';

export const mockFarmSummary: FarmSummary = {
  totalArea: 45.2,
  cropTypes: [
    { name: 'Wheat', icon: 'wheat' },
    { name: 'Maize', icon: 'corn' },
    { name: 'Rice', icon: 'sprout' }
  ],
  soilType: 'Sandy Loam',
  lastRun: '2025-10-26 08:30'
};

export const mockAgentOutputs: AgentOutput[] = [
  {
    category: 'Climate',
    confidence: 92,
    metrics: [
      { label: 'Temperature', value: '28', unit: '°C' },
      { label: 'Humidity', value: '65', unit: '%' },
      { label: 'Wind Speed', value: '12', unit: 'km/h' }
    ]
  },
  {
    category: 'Soil & Water',
    confidence: 78,
    metrics: [
      { label: 'Soil Moisture', value: '42', unit: '%' },
      { label: 'Water Table', value: '3.2', unit: 'm' },
      { label: 'Salinity', value: '0.8', unit: 'dS/m' }
    ]
  },
  {
    category: 'Crop Growth',
    confidence: 85,
    metrics: [
      { label: 'Growth Stage', value: 'Vegetative', unit: '' },
      { label: 'NDVI', value: '0.72', unit: '' },
      { label: 'Health Index', value: '8.5', unit: '/10' }
    ]
  },
  {
    category: 'ET0',
    confidence: 88,
    metrics: [
      { label: 'Reference ET', value: '5.8', unit: 'mm/day' },
      { label: 'Crop ET', value: '4.6', unit: 'mm/day' },
      { label: 'Kc Factor', value: '0.79', unit: '' }
    ]
  }
];

export const mockIrrigationSchedule: IrrigationSchedule = {
  overallConfidence: 84,
  modules: [
    { module: 'Zone A - Wheat', volume: 18.5, mode: 'Drip' },
    { module: 'Zone B - Maize', volume: 22.3, mode: 'Drip' },
    { module: 'Zone C - Rice', volume: 35.7, mode: 'Flood' },
    { module: 'Zone D - Wheat', volume: 17.9, mode: 'Drip' }
  ]
};

export const mockExplanation: Explanation = {
  reasoning: 'Because ET0 is high (5.8 mm/day) and soil moisture is moderate (42%), the system recommends targeted irrigation with adjusted volumes based on crop-specific water requirements and growth stages.',
  waterSaved: '23% reduction vs baseline (estimated 1,240 L saved today)'
};
