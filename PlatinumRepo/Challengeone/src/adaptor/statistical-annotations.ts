import { Params } from '../core/adaptor';
import { mean, standardDeviation, percentile } from '../utils/statistics/descriptive';
import { linearRegression, polynomialRegression, exponentialRegression } from '../utils/statistics/regression';
import { simpleMovingAverage, exponentialMovingAverage } from '../utils/statistics/moving-average';
import type { StatisticalOverlay, TrendLineOverlay, ReferenceBandOverlay, MovingAverageOverlay } from '../types/statistical-annotations';

interface AnnotationConfig {
  type: 'line' | 'region';
  start: [any, any];
  end: [any, any];
  style: Record<string, any>;
}

const MIN_POLYNOMIAL_DEGREE = 1;
const MAX_POLYNOMIAL_DEGREE = 6;
const DEFAULT_POLYNOMIAL_DEGREE = 2;
const DEFAULT_STDDEV_MULTIPLIER = 1;
const DEFAULT_PERCENTILE_RANGE: [number, number] = [25, 75];
const DEFAULT_SMA_WINDOW = 5;
const DEFAULT_EMA_SMOOTHING = 0.3;
const MIN_TREND_POINTS = 2;
const MIN_MA_POINTS = 2;

function clampDegree(degree: number | undefined): number {
  const d = degree || DEFAULT_POLYNOMIAL_DEGREE;
  return Math.max(MIN_POLYNOMIAL_DEGREE, Math.min(MAX_POLYNOMIAL_DEGREE, d));
}

function resolveOverlayStyle(overlay: StatisticalOverlay): Record<string, any> {
  return overlay.style || {};
}

function buildTrendLineAnnotations(
  points: [number, number][],
  xValues: any[],
  overlay: TrendLineOverlay,
): AnnotationConfig[] {
  if (points.length < MIN_TREND_POINTS) return [];

  const style = resolveOverlayStyle(overlay);

  if (overlay.method === 'linear') {
    const reg = linearRegression(points);
    return [{
      type: 'line',
      start: [xValues[0], reg.predict(points[0][0])],
      end: [xValues[xValues.length - 1], reg.predict(points[points.length - 1][0])],
      style,
    }];
  }

  let predictFn: (x: number) => number;
  if (overlay.method === 'polynomial') {
    const degree = clampDegree(overlay.degree);
    const reg = polynomialRegression(points, degree);
    predictFn = reg.predict;
  } else {
    const reg = exponentialRegression(points);
    predictFn = reg.predict;
  }

  const annotations: AnnotationConfig[] = [];
  for (let i = 0; i < points.length - 1; i++) {
    annotations.push({
      type: 'line',
      start: [xValues[i], predictFn(points[i][0])],
      end: [xValues[i + 1], predictFn(points[i + 1][0])],
      style,
    });
  }
  return annotations;
}

function computeStddevBounds(
  yValues: number[],
  multiplier: number,
): { upper: number; lower: number } {
  const m = mean(yValues);
  const sd = standardDeviation(yValues);
  return { upper: m + multiplier * sd, lower: m - multiplier * sd };
}

function computePercentileBounds(
  yValues: number[],
  range: [number, number],
): { upper: number; lower: number } {
  return {
    lower: percentile(yValues, range[0]),
    upper: percentile(yValues, range[1]),
  };
}

function buildReferenceBandAnnotations(
  yValues: number[],
  xValues: any[],
  overlay: ReferenceBandOverlay,
  themeAnnotationStyle?: any,
): AnnotationConfig[] {
  let bounds: { upper: number; lower: number };

  if (overlay.method === 'stddev') {
    const multiplier = overlay.multiplier ?? DEFAULT_STDDEV_MULTIPLIER;
    bounds = computeStddevBounds(yValues, multiplier);
  } else {
    const range = overlay.range || DEFAULT_PERCENTILE_RANGE;
    bounds = computePercentileBounds(yValues, range);
  }

  const themeRegionStyle = themeAnnotationStyle?.region?.style || {};
  const userStyle = resolveOverlayStyle(overlay);
  const mergedStyle = { ...themeRegionStyle, ...userStyle };

  return [{
    type: 'region',
    start: [xValues[0], bounds.upper],
    end: [xValues[xValues.length - 1], bounds.lower],
    style: mergedStyle,
  }];
}

function buildMovingAverageAnnotations(
  yValues: number[],
  xValues: any[],
  overlay: MovingAverageOverlay,
): AnnotationConfig[] {
  if (yValues.length < MIN_MA_POINTS) return [];

  const style = resolveOverlayStyle(overlay);
  let smoothed: number[];

  if (overlay.method === 'simple') {
    const window = overlay.window ?? DEFAULT_SMA_WINDOW;
    smoothed = simpleMovingAverage(yValues, window);
  } else {
    const factor = overlay.smoothingFactor ?? DEFAULT_EMA_SMOOTHING;
    smoothed = exponentialMovingAverage(yValues, factor);
  }

  const annotations: AnnotationConfig[] = [];
  for (let i = 0; i < smoothed.length - 1; i++) {
    annotations.push({
      type: 'line',
      start: [xValues[i], smoothed[i]],
      end: [xValues[i + 1], smoothed[i + 1]],
      style,
    });
  }
  return annotations;
}

export function computeStatisticalAnnotations(
  data: Record<string, any>[],
  xField: string,
  yField: string,
  seriesField: string | undefined,
  overlays: StatisticalOverlay[],
  themeAnnotationStyle?: any,
): AnnotationConfig[] {
  if (!data || data.length === 0) return [];

  const groups: Map<string, Record<string, any>[]> = new Map();
  if (seriesField) {
    for (const datum of data) {
      const key = String(datum[seriesField]);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(datum);
    }
  } else {
    groups.set('__all__', data);
  }

  const allAnnotations: AnnotationConfig[] = [];

  groups.forEach((groupData) => {
    const xValues = groupData.map(d => d[xField]);
    const yValues: number[] = groupData.map(d => d[yField]);
    const points: [number, number][] = groupData.map((d, i) => [i, d[yField]]);

    for (const overlay of overlays) {
      switch (overlay.type) {
        case 'trendLine': {
          const numericPoints: [number, number][] = groupData.map(d => [d[xField], d[yField]]);
          allAnnotations.push(
            ...buildTrendLineAnnotations(numericPoints, xValues, overlay)
          );
          break;
        }
        case 'referenceBand':
          allAnnotations.push(
            ...buildReferenceBandAnnotations(yValues, xValues, overlay, themeAnnotationStyle)
          );
          break;
        case 'movingAverage':
          allAnnotations.push(
            ...buildMovingAverageAnnotations(yValues, xValues, overlay)
          );
          break;
      }
    }
  });

  return allAnnotations;
}

export function statisticalAnnotations<O extends Record<string, any>>(params: Params<O>): Params<O> {
  const { chart, options } = params;
  const { data, xField, yField, seriesField, statisticalAnnotations: overlays } = options as any;

  if (!overlays || overlays.length === 0) return params;

  const themeAnnotationStyle = chart.getTheme()?.components?.annotation || {};
  const annotations = computeStatisticalAnnotations(data, xField, yField, seriesField, overlays, themeAnnotationStyle);

  const controller = chart.getController('annotation');
  if (controller) {
    for (const ann of annotations) {
      (controller as any).annotation(ann);
    }
  }

  return params;
}
