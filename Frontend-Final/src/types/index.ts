export interface FarmSummary {
  totalArea: number;
  cropTypes: Array<{
    name: string;
    icon: string;
  }>;
  soilType: string;
  lastRun: string;
}

export interface AgentOutput {
  category: string;
  metrics: Array<{
    label: string;
    value: string;
    unit?: string;
  }>;
  confidence: number;
}

export interface IrrigationModule {
  module: string;
  volume: number;
  mode: string;
}

export interface IrrigationSchedule {
  modules: IrrigationModule[];
  overallConfidence: number;
}

export interface Explanation {
  reasoning: string;
  waterSaved: string;
}
