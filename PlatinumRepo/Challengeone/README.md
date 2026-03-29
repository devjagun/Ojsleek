Repository
https://github.com/antvis/G2Plot
Commit: 0c1205eb9c2de90f3e6b4f8ff017f410edaa278a

Title
Statistical Overlay Annotations for Chart Plots

Description

G2Plot Line, Area, and Column charts support statistical overlay annotations via a `statisticalAnnotations` config array on LineOptions, AreaOptions, and ColumnOptions.

Trend Lines: Linear fits produce one line annotation spanning the full x-range. Polynomial and exponential fits produce segmented line annotations between consecutive data x-values. Degree defaults to 2 when absent or zero, clamped to [1, 6]. Two+ points required; single point yields no annotation. Single-point linear regression: slope 0, intercept at that y, constant predict. Exponential fit excludes non-positive y; if none remain, returns a=1, b=0.

Reference Bands: Region annotation between computed y-boundaries. Stddev uses population formula (N divisor). Mean of empty is zero. Percentile uses linear interpolation: rank = (p / 100) * (n - 1), without mutating input. X-boundaries use first/last data x-values. Region start = upper boundary, end = lower.

Moving Averages: Line segments between consecutive smoothed values. SMA uses cumulative mean before a full window; window > length uses all points; window 1 returns originals. EMA factor 0 = constant first value; factor 1 = originals. Fewer than two points = no annotations. Empty = empty.

Style: Trend lines and moving averages use only user style, or empty `{}` when absent. Reference bands deep-merge theme `region.style` with user style (user wins). Theme `line.style` never bleeds into trend lines or moving averages.

Grouping: With a series field, computations run per group independently.

Integration: Pipeline step no-ops when unconfigured, returns input unchanged. Types integrate with existing hierarchy.

Overlay descriptors:
`{ type: 'trendLine', method: 'linear'|'polynomial'|'exponential', degree?: number, style?: Record<string, any> }`
`{ type: 'referenceBand', method: 'stddev'|'percentile', multiplier?: number (default 1), range?: [number, number] (default [25, 75]), style?: Record<string, any> }`
`{ type: 'movingAverage', method: 'simple'|'exponential', window?: number (default 5), smoothingFactor?: number (default 0.3), style?: Record<string, any> }`

Module layout:
`src/utils/statistics/descriptive` exports: `mean`, `standardDeviation`, `percentile`
`src/utils/statistics/regression` exports: `linearRegression`, `polynomialRegression`, `exponentialRegression`
`src/utils/statistics/moving-average` exports: `simpleMovingAverage`, `exponentialMovingAverage`
`src/utils/statistics` barrel re-exports all above
`src/adaptor/statistical-annotations` exports: `computeStatisticalAnnotations`, `statisticalAnnotations`

Signatures (all regression takes `[number, number][]` tuples, moving averages take/return flat `number[]`):
`mean(values: number[]): number`
`standardDeviation(values: number[], ddof: number = 0): number`
`percentile(values: number[], p: number): number`
`linearRegression(points: [number, number][]): { slope: number; intercept: number; predict: (x: number) => number }`
`polynomialRegression(points: [number, number][], degree: number): { coefficients: number[]; predict: (x: number) => number }`
`exponentialRegression(points: [number, number][]): { a: number; b: number; predict: (x: number) => number }`
`simpleMovingAverage(values: number[], window: number): number[]`
`exponentialMovingAverage(values: number[], smoothingFactor: number): number[]`

`computeStatisticalAnnotations(data: Record<string, any>[], xField: string, yField: string, seriesField: string | undefined, overlays: StatisticalOverlay[], themeAnnotationStyle?: any)` returns `{ type: 'line'|'region', start: [x, y], end: [x, y], style: Record<string, any> }[]`. The themeAnnotationStyle is `chart.getTheme().components.annotation`, with optional `region.style` and `line.style` sub-objects.

`statisticalAnnotations(params: Params): Params` reads theme from `params.chart.getTheme().components.annotation`, dispatches annotations to the annotation controller, returns params unchanged.
