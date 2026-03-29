export interface TrendLineOverlay {
  type: 'trendLine';
  method: 'linear' | 'polynomial' | 'exponential';
  degree?: number;
  style?: Record<string, any>;
}

export interface ReferenceBandOverlay {
  type: 'referenceBand';
  method: 'stddev' | 'percentile';
  multiplier?: number;
  range?: [number, number];
  style?: Record<string, any>;
}

export interface MovingAverageOverlay {
  type: 'movingAverage';
  method: 'simple' | 'exponential';
  window?: number;
  smoothingFactor?: number;
  style?: Record<string, any>;
}

export type StatisticalOverlay = TrendLineOverlay | ReferenceBandOverlay | MovingAverageOverlay;

export type StatisticalAnnotationsOption = StatisticalOverlay[];
