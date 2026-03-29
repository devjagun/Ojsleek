import { mean, standardDeviation, percentile } from '../../src/utils/statistics/descriptive';
import { linearRegression, polynomialRegression, exponentialRegression } from '../../src/utils/statistics/regression';
import { simpleMovingAverage, exponentialMovingAverage } from '../../src/utils/statistics/moving-average';
import { computeStatisticalAnnotations, statisticalAnnotations } from '../../src/adaptor/statistical-annotations';
import type { LineOptions } from '../../src/plots/line/types';
import type { AreaOptions } from '../../src/plots/area/types';
import type { ColumnOptions } from '../../src/plots/column/types';
import {
  mean as barrelMean,
  standardDeviation as barrelStdDev,
  percentile as barrelPercentile,
  linearRegression as barrelLinReg,
  polynomialRegression as barrelPolyReg,
  exponentialRegression as barrelExpReg,
  simpleMovingAverage as barrelSMA,
  exponentialMovingAverage as barrelEMA,
} from '../../src/utils/statistics';

describe('statistical overlay annotations', () => {
  describe('descriptive statistics', () => {
    it('should compute arithmetic mean for non-empty arrays', () => {
      expect(mean([1, 2, 3, 4, 5])).toBe(3);
      expect(mean([10])).toBe(10);
      expect(mean([-2, 0, 2])).toBe(0);
      expect(mean([1.5, 2.5, 3.5])).toBeCloseTo(2.5, 10);
    });

    it('should return zero mean for empty array', () => {
      expect(mean([])).toBe(0);
    });

    it('should compute population standard deviation with ddof defaulting to 0', () => {
      expect(standardDeviation([2, 4, 4, 4, 5, 5, 7, 9])).toBe(2);
      expect(standardDeviation([1, 1, 1, 1])).toBe(0);
      expect(standardDeviation([10, 10, 10])).toBe(0);
    });

    it('should compute sample standard deviation when ddof is 1', () => {
      const sd = standardDeviation([2, 4, 4, 4, 5, 5, 7, 9], 1);
      expect(sd).toBeCloseTo(Math.sqrt(32 / 7), 10);
    });

    it('should distinguish population vs sample stddev for same data', () => {
      const data = [4, 8, 6, 2, 10];
      const popSd = standardDeviation(data, 0);
      const sampleSd = standardDeviation(data, 1);
      expect(sampleSd).toBeGreaterThan(popSd);
      const m = mean(data);
      const sumSq = data.reduce((s, v) => s + (v - m) ** 2, 0);
      expect(popSd).toBeCloseTo(Math.sqrt(sumSq / 5), 10);
      expect(sampleSd).toBeCloseTo(Math.sqrt(sumSq / 4), 10);
    });

    it('should compute percentile via linear interpolation on sorted copy', () => {
      expect(percentile([1, 2, 3, 4, 5], 50)).toBe(3);
      expect(percentile([1, 2, 3, 4, 5], 0)).toBe(1);
      expect(percentile([1, 2, 3, 4, 5], 100)).toBe(5);
      expect(percentile([1, 2, 3, 4, 5], 25)).toBe(2);
      expect(percentile([1, 2, 3, 4, 5], 75)).toBe(4);
    });

    it('should handle unsorted input for percentile without mutating original', () => {
      const original = [5, 1, 3, 2, 4];
      const copy = [...original];
      expect(percentile(original, 50)).toBe(3);
      expect(original).toStrictEqual(copy);
    });

    it('should interpolate between adjacent ranks for non-integer percentile', () => {
      const values = [10, 20, 30, 40, 50];
      const p30 = percentile(values, 30);
      expect(p30).toBeCloseTo(10 + 0.3 * 4 * (10), 10);
    });
  });

  describe('regression', () => {
    it('should compute exact linear regression for perfectly linear data', () => {
      const result = linearRegression([[0, 1], [1, 3], [2, 5], [3, 7]]);
      expect(result.slope).toBeCloseTo(2, 10);
      expect(result.intercept).toBeCloseTo(1, 10);
      expect(result.predict(4)).toBeCloseTo(9, 10);
      expect(result.predict(-1)).toBeCloseTo(-1, 10);
    });

    it('should handle two-point linear regression', () => {
      const result = linearRegression([[0, 0], [10, 50]]);
      expect(result.slope).toBeCloseTo(5, 10);
      expect(result.intercept).toBeCloseTo(0, 10);
    });

    it('should handle single-point linear regression gracefully', () => {
      const result = linearRegression([[5, 10]]);
      expect(result.slope).toBe(0);
      expect(result.intercept).toBe(10);
      expect(result.predict(100)).toBe(10);
    });

    it('should compute polynomial regression coefficients in ascending power order', () => {
      const points: [number, number][] = [[-2, 1], [-1, 0], [0, 1], [1, 4], [2, 9]];
      const result = polynomialRegression(points, 2);
      expect(result.coefficients).toHaveLength(3);
      expect(result.coefficients[0]).toBeCloseTo(1, 4);
      expect(result.coefficients[1]).toBeCloseTo(2, 4);
      expect(result.coefficients[2]).toBeCloseTo(1, 4);
      expect(result.predict(3)).toBeCloseTo(16, 3);
    });

    it('should produce degree+1 coefficients for polynomial regression', () => {
      const pts: [number, number][] = Array.from({ length: 10 }, (_, i) => [i, i ** 3]);
      const result = polynomialRegression(pts, 3);
      expect(result.coefficients).toHaveLength(4);
      expect(result.coefficients[3]).toBeCloseTo(1, 2);
    });

    it('should compute exponential regression via log-linearized least squares', () => {
      const a = 2, b = 0.5;
      const points: [number, number][] = [0, 1, 2, 3, 4].map(x => [x, a * Math.exp(b * x)]);
      const result = exponentialRegression(points);
      expect(result.a).toBeCloseTo(2, 4);
      expect(result.b).toBeCloseTo(0.5, 4);
      expect(result.predict(5)).toBeCloseTo(2 * Math.exp(2.5), 1);
    });

    it('should silently exclude non-positive y-values from exponential fit', () => {
      const points: [number, number][] = [[0, -1], [1, 0], [2, 2], [3, 4], [4, 8]];
      const result = exponentialRegression(points);
      expect(Number.isFinite(result.a)).toBe(true);
      expect(Number.isFinite(result.b)).toBe(true);
      expect(result.a).toBeGreaterThan(0);
      expect(typeof result.predict(5)).toBe('number');
    });

    it('should handle all non-positive y-values in exponential regression', () => {
      const points: [number, number][] = [[0, -5], [1, 0], [2, -3]];
      const result = exponentialRegression(points);
      expect(result.a).toBe(1);
      expect(result.b).toBe(0);
      expect(result.predict(10)).toBe(1);
    });

    it('should match linear regression when polynomial degree is 1', () => {
      const points: [number, number][] = [[0, 2], [1, 5], [2, 8], [3, 11]];
      const linResult = linearRegression(points);
      const polyResult = polynomialRegression(points, 1);
      expect(polyResult.coefficients).toHaveLength(2);
      expect(polyResult.coefficients[0]).toBeCloseTo(linResult.intercept, 4);
      expect(polyResult.coefficients[1]).toBeCloseTo(linResult.slope, 4);
      expect(polyResult.predict(4)).toBeCloseTo(linResult.predict(4), 4);
    });
  });

  describe('moving average', () => {
    it('should compute SMA with cumulative mean for leading positions', () => {
      const result = simpleMovingAverage([1, 2, 3, 4, 5], 3);
      expect(result).toHaveLength(5);
      expect(result[0]).toBeCloseTo(1, 10);
      expect(result[1]).toBeCloseTo(1.5, 10);
      expect(result[2]).toBeCloseTo(2, 10);
      expect(result[3]).toBeCloseTo(3, 10);
      expect(result[4]).toBeCloseTo(4, 10);
    });

    it('should return original values when SMA window is 1', () => {
      const input = [10, 20, 30, 40];
      const result = simpleMovingAverage(input, 1);
      expect(result).toStrictEqual([10, 20, 30, 40]);
    });

    it('should degrade to cumulative mean when window exceeds data length', () => {
      const result = simpleMovingAverage([1, 2, 3], 10);
      expect(result).toHaveLength(3);
      expect(result[0]).toBeCloseTo(1, 10);
      expect(result[1]).toBeCloseTo(1.5, 10);
      expect(result[2]).toBeCloseTo(2, 10);
    });

    it('should compute SMA correctly for larger window on longer data', () => {
      const values = [2, 4, 6, 8, 10, 12, 14];
      const result = simpleMovingAverage(values, 4);
      expect(result).toHaveLength(7);
      expect(result[0]).toBeCloseTo(2, 10);
      expect(result[1]).toBeCloseTo(3, 10);
      expect(result[2]).toBeCloseTo(4, 10);
      expect(result[3]).toBeCloseTo(5, 10);
      expect(result[4]).toBeCloseTo(7, 10);
      expect(result[5]).toBeCloseTo(9, 10);
      expect(result[6]).toBeCloseTo(11, 10);
    });

    it('should compute EMA exactly per recurrence formula', () => {
      const result = exponentialMovingAverage([1, 2, 3, 4, 5], 0.5);
      expect(result).toHaveLength(5);
      expect(result[0]).toBeCloseTo(1, 10);
      expect(result[1]).toBeCloseTo(1.5, 10);
      expect(result[2]).toBeCloseTo(2.25, 10);
      expect(result[3]).toBeCloseTo(3.125, 10);
      expect(result[4]).toBeCloseTo(4.0625, 10);
    });

    it('should return empty array for empty input to both SMA and EMA', () => {
      expect(simpleMovingAverage([], 3)).toStrictEqual([]);
      expect(exponentialMovingAverage([], 0.5)).toStrictEqual([]);
    });

    it('should return original values when EMA smoothing factor is 1', () => {
      const input = [5, 10, 15, 20];
      const result = exponentialMovingAverage(input, 1.0);
      expect(result).toStrictEqual([5, 10, 15, 20]);
    });

    it('should stay at first value when EMA smoothing factor is 0', () => {
      const input = [5, 10, 15, 20];
      const result = exponentialMovingAverage(input, 0);
      expect(result).toStrictEqual([5, 5, 5, 5]);
    });
  });

  describe('computeStatisticalAnnotations', () => {
    const linearData = [
      { x: 0, y: 1 },
      { x: 1, y: 3 },
      { x: 2, y: 5 },
      { x: 3, y: 7 },
      { x: 4, y: 9 },
    ];

    it('should produce a single line annotation for linear trend line', () => {
      const annotations = computeStatisticalAnnotations(linearData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'linear' },
      ]);
      expect(annotations).toHaveLength(1);
      expect(annotations[0].type).toBe('line');
      expect(annotations[0].start[0]).toBe(0);
      expect(annotations[0].end[0]).toBe(4);
      expect(annotations[0].start[1]).toBeCloseTo(1, 5);
      expect(annotations[0].end[1]).toBeCloseTo(9, 5);
    });

    it('should produce multiple line segments for polynomial trend line', () => {
      const quadData = Array.from({ length: 10 }, (_, i) => ({ x: i, y: i * i }));
      const annotations = computeStatisticalAnnotations(quadData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'polynomial', degree: 2 },
      ]);
      expect(annotations.length).toBeGreaterThan(1);
      annotations.forEach(ann => expect(ann.type).toBe('line'));
      expect(annotations[0].start[0]).toBe(0);
    });

    it('should produce multiple line segments for exponential trend line', () => {
      const expData = [0, 1, 2, 3, 4].map(x => ({ x, y: 2 * Math.exp(0.5 * x) }));
      const annotations = computeStatisticalAnnotations(expData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'exponential' },
      ]);
      expect(annotations.length).toBeGreaterThan(1);
      annotations.forEach(ann => expect(ann.type).toBe('line'));
    });

    it('should produce region annotation for stddev reference band', () => {
      const annotations = computeStatisticalAnnotations(linearData, 'x', 'y', undefined, [
        { type: 'referenceBand', method: 'stddev', multiplier: 1 },
      ]);
      expect(annotations).toHaveLength(1);
      expect(annotations[0].type).toBe('region');

      const yValues = linearData.map(d => d.y);
      const m = mean(yValues);
      const sd = standardDeviation(yValues);
      expect(annotations[0].start[1]).toBeCloseTo(m + sd, 5);
      expect(annotations[0].end[1]).toBeCloseTo(m - sd, 5);
    });

    it('should produce region annotation for percentile reference band', () => {
      const data100 = Array.from({ length: 100 }, (_, i) => ({ x: i, y: i + 1 }));
      const annotations = computeStatisticalAnnotations(data100, 'x', 'y', undefined, [
        { type: 'referenceBand', method: 'percentile', range: [25, 75] },
      ]);
      expect(annotations).toHaveLength(1);
      expect(annotations[0].type).toBe('region');

      const yValues = data100.map(d => d.y);
      const p25 = percentile(yValues, 25);
      const p75 = percentile(yValues, 75);
      expect(annotations[0].start[1]).toBeCloseTo(p75, 5);
      expect(annotations[0].end[1]).toBeCloseTo(p25, 5);
    });

    it('should produce line segment annotations for SMA moving average', () => {
      const annotations = computeStatisticalAnnotations(linearData, 'x', 'y', undefined, [
        { type: 'movingAverage', method: 'simple', window: 3 },
      ]);
      expect(annotations).toHaveLength(4);
      annotations.forEach(ann => expect(ann.type).toBe('line'));
      expect(annotations[0].start[0]).toBe(0);
      expect(annotations[0].end[0]).toBe(1);
    });

    it('should produce line segment annotations for EMA moving average', () => {
      const annotations = computeStatisticalAnnotations(linearData, 'x', 'y', undefined, [
        { type: 'movingAverage', method: 'exponential', smoothingFactor: 0.5 },
      ]);
      expect(annotations).toHaveLength(4);
      annotations.forEach(ann => expect(ann.type).toBe('line'));
    });

    it('should compute independently per series group', () => {
      const groupedData = [
        { x: 0, y: 10, series: 'A' },
        { x: 1, y: 20, series: 'A' },
        { x: 2, y: 30, series: 'A' },
        { x: 0, y: 100, series: 'B' },
        { x: 1, y: 200, series: 'B' },
        { x: 2, y: 300, series: 'B' },
      ];
      const annotations = computeStatisticalAnnotations(groupedData, 'x', 'y', 'series', [
        { type: 'referenceBand', method: 'stddev', multiplier: 1 },
      ]);
      expect(annotations).toHaveLength(2);

      const band1Center = (annotations[0].start[1] + annotations[0].end[1]) / 2;
      const band2Center = (annotations[1].start[1] + annotations[1].end[1]) / 2;
      expect(band1Center).toBeCloseTo(mean([10, 20, 30]), 5);
      expect(band2Center).toBeCloseTo(mean([100, 200, 300]), 5);
    });

    it('should produce per-group moving average segments', () => {
      const groupedData = [
        { x: 0, y: 2, cat: 'X' },
        { x: 1, y: 4, cat: 'X' },
        { x: 2, y: 6, cat: 'X' },
        { x: 0, y: 20, cat: 'Y' },
        { x: 1, y: 40, cat: 'Y' },
        { x: 2, y: 60, cat: 'Y' },
      ];
      const annotations = computeStatisticalAnnotations(groupedData, 'x', 'y', 'cat', [
        { type: 'movingAverage', method: 'simple', window: 2 },
      ]);
      expect(annotations).toHaveLength(4);

      const groupXSegments = annotations.filter(a => a.start[1] < 10);
      const groupYSegments = annotations.filter(a => a.start[1] >= 10 || a.end[1] >= 10);
      expect(groupXSegments.length).toBe(2);
      expect(groupYSegments.length).toBe(2);
    });

    it('should deep-merge reference band style with theme annotation defaults', () => {
      const themeStyle = {
        region: { style: { fill: '#000', fillOpacity: 0.1, lineWidth: 1 } },
      };
      const annotations = computeStatisticalAnnotations(linearData, 'x', 'y', undefined, [
        { type: 'referenceBand', method: 'stddev', multiplier: 1, style: { fill: '#f00', stroke: '#0f0' } },
      ], themeStyle);

      expect(annotations).toHaveLength(1);
      expect(annotations[0].style.fill).toBe('#f00');
      expect(annotations[0].style.stroke).toBe('#0f0');
      expect(annotations[0].style.fillOpacity).toBe(0.1);
      expect(annotations[0].style.lineWidth).toBe(1);
    });

    it('should use user style only when no theme annotation style provided', () => {
      const annotations = computeStatisticalAnnotations(linearData, 'x', 'y', undefined, [
        { type: 'referenceBand', method: 'stddev', style: { fill: '#abc', opacity: 0.5 } },
      ]);
      expect(annotations[0].style.fill).toBe('#abc');
      expect(annotations[0].style.opacity).toBe(0.5);
    });

    it('should use theme defaults when no user style properties overlap', () => {
      const themeStyle = {
        region: { style: { fill: '#ddd', fillOpacity: 0.2 } },
      };
      const annotations = computeStatisticalAnnotations(linearData, 'x', 'y', undefined, [
        { type: 'referenceBand', method: 'stddev', style: { stroke: '#000' } },
      ], themeStyle);
      expect(annotations[0].style.fill).toBe('#ddd');
      expect(annotations[0].style.fillOpacity).toBe(0.2);
      expect(annotations[0].style.stroke).toBe('#000');
    });

    it('should produce completely different annotations when called with new data', () => {
      const data1 = [{ x: 0, y: 1 }, { x: 1, y: 2 }, { x: 2, y: 3 }];
      const data2 = [{ x: 0, y: 100 }, { x: 1, y: 200 }, { x: 2, y: 300 }];
      const overlays = [{ type: 'trendLine' as const, method: 'linear' as const }];

      const ann1 = computeStatisticalAnnotations(data1, 'x', 'y', undefined, overlays);
      const ann2 = computeStatisticalAnnotations(data2, 'x', 'y', undefined, overlays);

      expect(ann1[0].start[1]).not.toEqual(ann2[0].start[1]);
      expect(ann1[0].end[1]).not.toEqual(ann2[0].end[1]);
    });

    it('should return empty array when data is empty', () => {
      const annotations = computeStatisticalAnnotations([], 'x', 'y', undefined, [
        { type: 'trendLine', method: 'linear' },
      ]);
      expect(annotations).toStrictEqual([]);
    });

    it('should handle multiple overlays in a single call', () => {
      const annotations = computeStatisticalAnnotations(linearData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'linear' },
        { type: 'referenceBand', method: 'stddev', multiplier: 2 },
        { type: 'movingAverage', method: 'simple', window: 2 },
      ]);

      const lineAnns = annotations.filter(a => a.type === 'line');
      const regionAnns = annotations.filter(a => a.type === 'region');
      expect(regionAnns).toHaveLength(1);
      expect(lineAnns.length).toBeGreaterThanOrEqual(5);
    });

    it('should apply custom style to trend line annotations', () => {
      const customStyle = { stroke: '#ff0000', lineWidth: 3 };
      const annotations = computeStatisticalAnnotations(linearData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'linear', style: customStyle },
      ]);
      expect(annotations[0].style).toStrictEqual(customStyle);
    });

    it('should apply custom style to moving average segments', () => {
      const customStyle = { stroke: '#00ff00', lineDash: [4, 4] };
      const annotations = computeStatisticalAnnotations(linearData, 'x', 'y', undefined, [
        { type: 'movingAverage', method: 'simple', window: 2, style: customStyle },
      ]);
      annotations.forEach(ann => {
        expect(ann.style).toStrictEqual(customStyle);
      });
    });

    it('should handle three series groups with per-group trend lines', () => {
      const threeGroupData = [
        { x: 0, y: 1, g: 'a' }, { x: 1, y: 2, g: 'a' }, { x: 2, y: 3, g: 'a' },
        { x: 0, y: 10, g: 'b' }, { x: 1, y: 20, g: 'b' }, { x: 2, y: 30, g: 'b' },
        { x: 0, y: 100, g: 'c' }, { x: 1, y: 200, g: 'c' }, { x: 2, y: 300, g: 'c' },
      ];
      const annotations = computeStatisticalAnnotations(threeGroupData, 'x', 'y', 'g', [
        { type: 'trendLine', method: 'linear' },
      ]);
      expect(annotations).toHaveLength(3);
      expect(annotations[0].end[1]).toBeCloseTo(3, 4);
      expect(annotations[1].end[1]).toBeCloseTo(30, 4);
      expect(annotations[2].end[1]).toBeCloseTo(300, 4);
    });
  });

  describe('polynomial degree constraints', () => {
    const polyData: [number, number][] = Array.from({ length: 20 }, (_, i) => [i, Math.sin(i)]);

    it('should clamp degree below 1 to 1', () => {
      const annotations = computeStatisticalAnnotations(
        polyData.map(([x, y]) => ({ x, y })), 'x', 'y', undefined,
        [{ type: 'trendLine', method: 'polynomial', degree: -1 }]
      );
      expect(annotations.length).toBeGreaterThan(1);
      annotations.forEach(a => expect(a.type).toBe('line'));
    });

    it('should clamp degree above 6 to 6', () => {
      const annotations = computeStatisticalAnnotations(
        polyData.map(([x, y]) => ({ x, y })), 'x', 'y', undefined,
        [{ type: 'trendLine', method: 'polynomial', degree: 99 }]
      );
      expect(annotations.length).toBeGreaterThan(1);
      annotations.forEach(a => expect(a.type).toBe('line'));
      const reg = polynomialRegression(polyData, 6);
      expect(reg.coefficients).toHaveLength(7);
    });

    it('should respect valid degree within 1-6 range', () => {
      const pts: [number, number][] = Array.from({ length: 10 }, (_, i) => [i, i * i * i]);
      const reg3 = polynomialRegression(pts, 3);
      const reg4 = polynomialRegression(pts, 4);
      expect(reg3.coefficients).toHaveLength(4);
      expect(reg4.coefficients).toHaveLength(5);
    });
  });

  describe('statisticalAnnotations adaptor integration', () => {
    function createMockChart(themeComponents?: any) {
      const annotationCalls: any[] = [];
      return {
        chart: {
          getTheme: () => ({
            components: { annotation: themeComponents || {} },
          }),
          getController: (name: string) => {
            if (name === 'annotation') {
              return {
                annotation: (cfg: any) => annotationCalls.push(cfg),
              };
            }
            return null;
          },
        },
        annotationCalls,
      };
    }

    it('should pass annotations to chart annotation controller for linear trend', () => {
      const { chart, annotationCalls } = createMockChart();
      const params = {
        chart,
        options: {
          data: [{ x: 0, y: 1 }, { x: 1, y: 3 }, { x: 2, y: 5 }],
          xField: 'x',
          yField: 'y',
          statisticalAnnotations: [{ type: 'trendLine' as const, method: 'linear' as const }],
        },
      };

      const result = statisticalAnnotations(params as any);
      expect(result).toBe(params);
      expect(annotationCalls).toHaveLength(1);
      expect(annotationCalls[0].type).toBe('line');
      expect(annotationCalls[0].start[0]).toBe(0);
      expect(annotationCalls[0].end[0]).toBe(2);
    });

    it('should return params unchanged when no overlays configured', () => {
      const { chart, annotationCalls } = createMockChart();
      const params = {
        chart,
        options: {
          data: [{ x: 0, y: 1 }],
          xField: 'x',
          yField: 'y',
        },
      };

      const result = statisticalAnnotations(params as any);
      expect(result).toBe(params);
      expect(annotationCalls).toHaveLength(0);
    });

    it('should return params unchanged when overlays array is empty', () => {
      const { chart, annotationCalls } = createMockChart();
      const params = {
        chart,
        options: {
          data: [{ x: 0, y: 1 }],
          xField: 'x',
          yField: 'y',
          statisticalAnnotations: [],
        },
      };

      const result = statisticalAnnotations(params as any);
      expect(result).toBe(params);
      expect(annotationCalls).toHaveLength(0);
    });

    it('should pass theme annotation style to reference band merge', () => {
      const themeComponents = {
        region: { style: { fill: '#eee', fillOpacity: 0.3 } },
      };
      const { chart, annotationCalls } = createMockChart(themeComponents);
      const params = {
        chart,
        options: {
          data: [{ x: 0, y: 10 }, { x: 1, y: 20 }, { x: 2, y: 30 }],
          xField: 'x',
          yField: 'y',
          statisticalAnnotations: [
            { type: 'referenceBand' as const, method: 'stddev' as const, multiplier: 1, style: { fill: '#f00' } },
          ],
        },
      };

      statisticalAnnotations(params as any);
      expect(annotationCalls).toHaveLength(1);
      expect(annotationCalls[0].type).toBe('region');
      expect(annotationCalls[0].style.fill).toBe('#f00');
      expect(annotationCalls[0].style.fillOpacity).toBe(0.3);
    });

    it('should handle seriesField to produce per-group annotations', () => {
      const { chart, annotationCalls } = createMockChart();
      const params = {
        chart,
        options: {
          data: [
            { x: 0, y: 1, g: 'A' }, { x: 1, y: 2, g: 'A' }, { x: 2, y: 3, g: 'A' },
            { x: 0, y: 10, g: 'B' }, { x: 1, y: 20, g: 'B' }, { x: 2, y: 30, g: 'B' },
          ],
          xField: 'x',
          yField: 'y',
          seriesField: 'g',
          statisticalAnnotations: [{ type: 'trendLine' as const, method: 'linear' as const }],
        },
      };

      statisticalAnnotations(params as any);
      expect(annotationCalls).toHaveLength(2);
      expect(annotationCalls[0].start[1]).toBeCloseTo(1, 4);
      expect(annotationCalls[1].start[1]).toBeCloseTo(10, 4);
    });

    it('should produce moving average segments via adaptor', () => {
      const { chart, annotationCalls } = createMockChart();
      const params = {
        chart,
        options: {
          data: [{ x: 0, y: 2 }, { x: 1, y: 4 }, { x: 2, y: 6 }, { x: 3, y: 8 }],
          xField: 'x',
          yField: 'y',
          statisticalAnnotations: [
            { type: 'movingAverage' as const, method: 'simple' as const, window: 2 },
          ],
        },
      };

      statisticalAnnotations(params as any);
      expect(annotationCalls).toHaveLength(3);
      annotationCalls.forEach(a => expect(a.type).toBe('line'));
    });

    it('should wire multiple overlay types through adaptor in one call', () => {
      const { chart, annotationCalls } = createMockChart();
      const params = {
        chart,
        options: {
          data: [
            { x: 0, y: 1 }, { x: 1, y: 3 }, { x: 2, y: 5 },
            { x: 3, y: 7 }, { x: 4, y: 9 },
          ],
          xField: 'x',
          yField: 'y',
          statisticalAnnotations: [
            { type: 'trendLine' as const, method: 'linear' as const },
            { type: 'referenceBand' as const, method: 'stddev' as const },
            { type: 'movingAverage' as const, method: 'exponential' as const, smoothingFactor: 0.5 },
          ],
        },
      };

      statisticalAnnotations(params as any);
      const lines = annotationCalls.filter(a => a.type === 'line');
      const regions = annotationCalls.filter(a => a.type === 'region');
      expect(regions).toHaveLength(1);
      expect(lines.length).toBeGreaterThanOrEqual(5);
    });
  });

  describe('plot type option contracts', () => {
    const overlayFixture = [{ type: 'trendLine' as const, method: 'linear' as const }];

    it('LineOptions should accept statisticalAnnotations', () => {
      const opts: Pick<LineOptions, 'statisticalAnnotations'> = {
        statisticalAnnotations: overlayFixture,
      };
      expect(opts.statisticalAnnotations).toHaveLength(1);
    });

    it('AreaOptions should accept statisticalAnnotations', () => {
      const opts: Pick<AreaOptions, 'statisticalAnnotations'> = {
        statisticalAnnotations: overlayFixture,
      };
      expect(opts.statisticalAnnotations).toHaveLength(1);
    });

    it('ColumnOptions should accept statisticalAnnotations', () => {
      const opts: Pick<ColumnOptions, 'statisticalAnnotations'> = {
        statisticalAnnotations: overlayFixture,
      };
      expect(opts.statisticalAnnotations).toHaveLength(1);
    });
  });

  describe('style pass-through vs theme merge', () => {
    const data = [
      { x: 0, y: 1 }, { x: 1, y: 3 }, { x: 2, y: 5 },
      { x: 3, y: 7 }, { x: 4, y: 9 },
    ];
    const themeStyle = {
      region: { style: { fill: '#eee', fillOpacity: 0.3 } },
      line: { style: { stroke: '#000', lineWidth: 2, lineDash: [5, 5] } },
    };

    it('should not merge theme line defaults into trend line style', () => {
      const userStyle = { stroke: '#f00' };
      const annotations = computeStatisticalAnnotations(data, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'linear', style: userStyle },
      ], themeStyle);
      expect(annotations[0].style).toStrictEqual(userStyle);
      expect(annotations[0].style.lineWidth).toBeUndefined();
      expect(annotations[0].style.lineDash).toBeUndefined();
    });

    it('should not merge theme line defaults into moving average style', () => {
      const userStyle = { stroke: '#0f0', lineWidth: 1 };
      const annotations = computeStatisticalAnnotations(data, 'x', 'y', undefined, [
        { type: 'movingAverage', method: 'simple', window: 2, style: userStyle },
      ], themeStyle);
      annotations.forEach(ann => {
        expect(ann.style).toStrictEqual(userStyle);
        expect(ann.style.lineDash).toBeUndefined();
      });
    });

    it('should use empty style for trend line when no user style and theme present', () => {
      const annotations = computeStatisticalAnnotations(data, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'linear' },
      ], themeStyle);
      expect(annotations[0].style).toStrictEqual({});
    });

    it('should use empty style for moving average when no user style and theme present', () => {
      const annotations = computeStatisticalAnnotations(data, 'x', 'y', undefined, [
        { type: 'movingAverage', method: 'exponential', smoothingFactor: 0.5 },
      ], themeStyle);
      annotations.forEach(ann => {
        expect(ann.style).toStrictEqual({});
      });
    });
  });

  describe('polynomial degree clamping in compute path', () => {
    const cubicData = Array.from({ length: 15 }, (_, i) => ({ x: i, y: i * i * i - 3 * i + 1 }));
    const cubicPoints: [number, number][] = cubicData.map(d => [d.x, d.y]);

    it('should produce identical annotations for degree -5 and degree 1', () => {
      const annNeg = computeStatisticalAnnotations(cubicData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'polynomial', degree: -5 },
      ]);
      const annDeg1 = computeStatisticalAnnotations(cubicData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'polynomial', degree: 1 },
      ]);
      expect(annNeg).toHaveLength(annDeg1.length);
      for (let i = 0; i < annNeg.length; i++) {
        expect(annNeg[i].start[1]).toBeCloseTo(annDeg1[i].start[1], 8);
        expect(annNeg[i].end[1]).toBeCloseTo(annDeg1[i].end[1], 8);
      }
    });

    it('should produce identical annotations for degree 99 and degree 6', () => {
      const annDeg99 = computeStatisticalAnnotations(cubicData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'polynomial', degree: 99 },
      ]);
      const annDeg6 = computeStatisticalAnnotations(cubicData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'polynomial', degree: 6 },
      ]);
      expect(annDeg99).toHaveLength(annDeg6.length);
      for (let i = 0; i < annDeg99.length; i++) {
        expect(annDeg99[i].start[1]).toBeCloseTo(annDeg6[i].start[1], 8);
        expect(annDeg99[i].end[1]).toBeCloseTo(annDeg6[i].end[1], 8);
      }
    });

    it('should produce different annotations for degree 1 vs degree 3', () => {
      const annDeg1 = computeStatisticalAnnotations(cubicData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'polynomial', degree: 1 },
      ]);
      const annDeg3 = computeStatisticalAnnotations(cubicData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'polynomial', degree: 3 },
      ]);
      expect(annDeg1).toHaveLength(annDeg3.length);
      const midIdx = Math.floor(annDeg1.length / 2);
      expect(Math.abs(annDeg1[midIdx].start[1] - annDeg3[midIdx].start[1])).toBeGreaterThan(0.01);
    });
  });

  describe('barrel re-export from statistics index', () => {
    it('should re-export all descriptive statistics functions', () => {
      expect(barrelMean).toBe(mean);
      expect(barrelStdDev).toBe(standardDeviation);
      expect(barrelPercentile).toBe(percentile);
    });

    it('should re-export all regression functions', () => {
      expect(barrelLinReg).toBe(linearRegression);
      expect(barrelPolyReg).toBe(polynomialRegression);
      expect(barrelExpReg).toBe(exponentialRegression);
    });

    it('should re-export all moving average functions', () => {
      expect(barrelSMA).toBe(simpleMovingAverage);
      expect(barrelEMA).toBe(exponentialMovingAverage);
    });
  });

  describe('annotation style property access', () => {
    const data5 = [
      { x: 0, y: 2 }, { x: 1, y: 4 }, { x: 2, y: 6 },
      { x: 3, y: 8 }, { x: 4, y: 10 },
    ];

    it('should allow indexed property access on reference band merged style', () => {
      const themeStyle = {
        region: { style: { fill: '#ccc', fillOpacity: 0.25, lineWidth: 1 } },
      };
      const annotations = computeStatisticalAnnotations(data5, 'x', 'y', undefined, [
        { type: 'referenceBand', method: 'stddev', multiplier: 1, style: { fill: '#ff0', stroke: '#00f' } },
      ], themeStyle);
      const s = annotations[0].style;
      expect(s.fill).toBe('#ff0');
      expect(s.stroke).toBe('#00f');
      expect(s.fillOpacity).toBe(0.25);
      expect(s.lineWidth).toBe(1);
      expect(s.nonExistent).toBeUndefined();
    });

    it('should allow indexed property read on trend line empty style', () => {
      const annotations = computeStatisticalAnnotations(data5, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'linear' },
      ]);
      const s = annotations[0].style;
      expect(s.stroke).toBeUndefined();
      expect(s.lineWidth).toBeUndefined();
    });

    it('should allow indexed property read on moving average user style', () => {
      const annotations = computeStatisticalAnnotations(data5, 'x', 'y', undefined, [
        { type: 'movingAverage', method: 'simple', window: 2, style: { stroke: '#0a0', lineDash: [3, 3] } },
      ]);
      const s = annotations[0].style;
      expect(s.stroke).toBe('#0a0');
      expect(s.lineDash).toStrictEqual([3, 3]);
    });
  });

  describe('degree zero default behavior', () => {
    const quadData = Array.from({ length: 10 }, (_, i) => ({ x: i, y: i * i + 2 * i + 1 }));

    it('should treat degree 0 identically to degree 2 (not degree 1)', () => {
      const annDeg0 = computeStatisticalAnnotations(quadData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'polynomial', degree: 0 },
      ]);
      const annDeg2 = computeStatisticalAnnotations(quadData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'polynomial', degree: 2 },
      ]);
      const annDeg1 = computeStatisticalAnnotations(quadData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'polynomial', degree: 1 },
      ]);
      expect(annDeg0).toHaveLength(annDeg2.length);
      for (let i = 0; i < annDeg0.length; i++) {
        expect(annDeg0[i].start[1]).toBeCloseTo(annDeg2[i].start[1], 8);
        expect(annDeg0[i].end[1]).toBeCloseTo(annDeg2[i].end[1], 8);
      }
      const midIdx = Math.floor(annDeg0.length / 2);
      expect(Math.abs(annDeg0[midIdx].start[1] - annDeg1[midIdx].start[1])).toBeGreaterThan(0.1);
    });

    it('should treat undefined degree as degree 2', () => {
      const annUndef = computeStatisticalAnnotations(quadData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'polynomial' },
      ]);
      const annDeg2 = computeStatisticalAnnotations(quadData, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'polynomial', degree: 2 },
      ]);
      expect(annUndef).toHaveLength(annDeg2.length);
      for (let i = 0; i < annUndef.length; i++) {
        expect(annUndef[i].start[1]).toBeCloseTo(annDeg2[i].start[1], 8);
      }
    });
  });

  describe('theme line.style isolation', () => {
    const data = [
      { x: 0, y: 1 }, { x: 1, y: 3 }, { x: 2, y: 5 },
      { x: 3, y: 7 }, { x: 4, y: 9 },
    ];
    const themeWithLineStyle = {
      region: { style: { fill: '#eee' } },
      line: { style: { stroke: '#999', lineWidth: 3, lineDash: [8, 4] } },
    };

    it('should not bleed theme line.style into trend line with user style', () => {
      const annotations = computeStatisticalAnnotations(data, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'linear', style: { stroke: '#f00' } },
      ], themeWithLineStyle);
      expect(annotations[0].style).toStrictEqual({ stroke: '#f00' });
    });

    it('should not bleed theme line.style into trend line without user style', () => {
      const annotations = computeStatisticalAnnotations(data, 'x', 'y', undefined, [
        { type: 'trendLine', method: 'linear' },
      ], themeWithLineStyle);
      expect(annotations[0].style).toStrictEqual({});
      expect(annotations[0].style.stroke).toBeUndefined();
      expect(annotations[0].style.lineWidth).toBeUndefined();
    });

    it('should not bleed theme line.style into moving average', () => {
      const annotations = computeStatisticalAnnotations(data, 'x', 'y', undefined, [
        { type: 'movingAverage', method: 'simple', window: 2 },
      ], themeWithLineStyle);
      annotations.forEach(a => {
        expect(a.style).toStrictEqual({});
        expect(a.style.lineDash).toBeUndefined();
      });
    });

    it('should still merge theme region.style into reference band', () => {
      const annotations = computeStatisticalAnnotations(data, 'x', 'y', undefined, [
        { type: 'referenceBand', method: 'stddev', multiplier: 1 },
      ], themeWithLineStyle);
      expect(annotations[0].style.fill).toBe('#eee');
    });
  });

  describe('moving average edge cases', () => {
    it('should return no annotations for single data point', () => {
      const annotations = computeStatisticalAnnotations(
        [{ x: 0, y: 5 }], 'x', 'y', undefined,
        [{ type: 'movingAverage', method: 'simple', window: 3 }]
      );
      expect(annotations).toStrictEqual([]);
    });

    it('should return exactly one segment for two data points', () => {
      const annotations = computeStatisticalAnnotations(
        [{ x: 0, y: 5 }, { x: 1, y: 10 }], 'x', 'y', undefined,
        [{ type: 'movingAverage', method: 'exponential', smoothingFactor: 0.5 }]
      );
      expect(annotations).toHaveLength(1);
      expect(annotations[0].type).toBe('line');
      expect(annotations[0].start[0]).toBe(0);
      expect(annotations[0].end[0]).toBe(1);
    });
  });

  describe('default parameter behavior', () => {
    const defaultData = [
      { x: 0, y: 10 }, { x: 1, y: 20 }, { x: 2, y: 30 },
      { x: 3, y: 40 }, { x: 4, y: 50 }, { x: 5, y: 60 },
    ];

    it('should use default multiplier of 1 for stddev reference band', () => {
      const withDefault = computeStatisticalAnnotations(defaultData, 'x', 'y', undefined, [
        { type: 'referenceBand', method: 'stddev' },
      ]);
      const withExplicit = computeStatisticalAnnotations(defaultData, 'x', 'y', undefined, [
        { type: 'referenceBand', method: 'stddev', multiplier: 1 },
      ]);
      expect(withDefault[0].start[1]).toBeCloseTo(withExplicit[0].start[1], 10);
      expect(withDefault[0].end[1]).toBeCloseTo(withExplicit[0].end[1], 10);
    });

    it('should use default range [25, 75] for percentile reference band', () => {
      const withDefault = computeStatisticalAnnotations(defaultData, 'x', 'y', undefined, [
        { type: 'referenceBand', method: 'percentile' },
      ]);
      const withExplicit = computeStatisticalAnnotations(defaultData, 'x', 'y', undefined, [
        { type: 'referenceBand', method: 'percentile', range: [25, 75] },
      ]);
      expect(withDefault[0].start[1]).toBeCloseTo(withExplicit[0].start[1], 10);
      expect(withDefault[0].end[1]).toBeCloseTo(withExplicit[0].end[1], 10);
    });

    it('should use default window of 5 for simple moving average', () => {
      const withDefault = computeStatisticalAnnotations(defaultData, 'x', 'y', undefined, [
        { type: 'movingAverage', method: 'simple' },
      ]);
      const withExplicit = computeStatisticalAnnotations(defaultData, 'x', 'y', undefined, [
        { type: 'movingAverage', method: 'simple', window: 5 },
      ]);
      expect(withDefault).toHaveLength(withExplicit.length);
      for (let i = 0; i < withDefault.length; i++) {
        expect(withDefault[i].start[1]).toBeCloseTo(withExplicit[i].start[1], 10);
        expect(withDefault[i].end[1]).toBeCloseTo(withExplicit[i].end[1], 10);
      }
    });

    it('should use default smoothingFactor of 0.3 for exponential moving average', () => {
      const withDefault = computeStatisticalAnnotations(defaultData, 'x', 'y', undefined, [
        { type: 'movingAverage', method: 'exponential' },
      ]);
      const withExplicit = computeStatisticalAnnotations(defaultData, 'x', 'y', undefined, [
        { type: 'movingAverage', method: 'exponential', smoothingFactor: 0.3 },
      ]);
      expect(withDefault).toHaveLength(withExplicit.length);
      for (let i = 0; i < withDefault.length; i++) {
        expect(withDefault[i].start[1]).toBeCloseTo(withExplicit[i].start[1], 10);
        expect(withDefault[i].end[1]).toBeCloseTo(withExplicit[i].end[1], 10);
      }
    });

    it('should return no annotations for single-point trend line', () => {
      const annotations = computeStatisticalAnnotations(
        [{ x: 5, y: 10 }], 'x', 'y', undefined,
        [{ type: 'trendLine', method: 'linear' }]
      );
      expect(annotations).toStrictEqual([]);
    });
  });

  describe('reference band x-coordinate values', () => {
    it('should use first and last x-field values for band boundaries', () => {
      const data = [
        { t: 100, val: 10 },
        { t: 200, val: 20 },
        { t: 300, val: 30 },
        { t: 400, val: 40 },
      ];
      const annotations = computeStatisticalAnnotations(data, 't', 'val', undefined, [
        { type: 'referenceBand', method: 'stddev', multiplier: 1 },
      ]);
      expect(annotations[0].start[0]).toBe(100);
      expect(annotations[0].end[0]).toBe(400);
    });

    it('should use string x-field values when present', () => {
      const data = [
        { month: 'Jan', revenue: 100 },
        { month: 'Feb', revenue: 200 },
        { month: 'Mar', revenue: 300 },
      ];
      const annotations = computeStatisticalAnnotations(data, 'month', 'revenue', undefined, [
        { type: 'referenceBand', method: 'percentile', range: [25, 75] },
      ]);
      expect(annotations[0].start[0]).toBe('Jan');
      expect(annotations[0].end[0]).toBe('Mar');
    });
  });
});
