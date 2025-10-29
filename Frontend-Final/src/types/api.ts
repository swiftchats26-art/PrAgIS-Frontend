export interface IrrigationResponse {
  irrigation_volume_mm: number;
  irrigation_mode: 'drip' | 'sprinkler';
  days_after_sowing: number;
  yield_index: number;
  confidence_score: number;
  short_reasoning: string;
  agents: Record<string, any>;
}