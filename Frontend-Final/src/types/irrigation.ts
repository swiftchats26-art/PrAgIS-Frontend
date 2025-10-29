export interface IrrigationData {
  irrigationVolume: number;
  irrigationMode: 'drip' | 'sprinkler';
  daysAfterSowing: number;
  yieldIndex: number;
  overallConfidence: number;
}