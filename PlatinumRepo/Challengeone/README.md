Repository
https://github.com/antvis/G2Plot
Commit: 0c1205eb9c2de90f3e6b4f8ff017f410edaa278a

Title
Statistical Overlay Annotations for Chart Plots

Description

G2Plot's Line, Area, and Column charts must support statistical overlay annotations declared in configuration and rendered at chart-render time.

Trend Lines fit a model and draw annotations. Linear fits expose slope, intercept, and a prediction function, producing a single line annotation spanning the full x-range. Polynomial fits expose coefficients in ascending power order plus prediction; exponential fits expose multiplicative and exponent parameters plus prediction. Non-linear fits produce segmented line annotations. Polynomial degree defaults to 2 when absent or zero, then is clamped to [1, 6]. Trend lines require at least two points; single point produces no annotation. Linear regression of one point yields slope 0, intercept at that y, constant predict. Exponential fitting excludes non-positive y-values; if none remain, returns finite defaults.

Reference Bands shade a region between computed boundaries. Standard-deviation uses population formula (dividing by N). Mean of empty collection is zero. Percentile uses linear interpolation: rank = (p / 100) * (n - 1), interpolating between nearest sorted values without mutating input. Band x-boundaries use actual first and last data values from the x-field. Region start is upper boundary; end is lower.

Moving Averages draw line segments between consecutive smoothed values. For SMA, positions before a full window use cumulative mean; window exceeding data length uses all points; window 1 returns originals. For EMA, factor 0 produces a constant first value; factor 1 reproduces the original series. Fewer than two points produces no annotations. Empty input returns empty.

Style Resolution: each overlay may carry an optional style. Trend lines and moving averages use only user-supplied style, or an empty indexable object when absent. Reference bands deep-merge theme region defaults with user style (user wins). Theme line-annotation defaults must never bleed into trend lines or moving averages.

Grouping: when a series field is present, computations run independently per group, producing separate annotations for each.

Integration: the capability must plug into the existing rendering pipeline. The pipeline step must no-op when unconfigured and return its input unchanged. Type definitions must integrate with the existing type hierarchy.

Configuration Property: LineOptions, AreaOptions, and ColumnOptions each expose a `statisticalAnnotations` property accepting an array of overlay descriptors. Each descriptor is one of:
Trend line: `{ type: 'trendLine', method: 'linear'|'polynomial'|'exponential', degree?: number, style?: Record<string, any> }`
Reference band: `{ type: 'referenceBand', method: 'stddev'|'percentile', multiplier?: number (default 1), range?: [number, number] (default [25, 75]), style?: Record<string, any> }`
Moving average: `{ type: 'movingAverage', method: 'simple'|'exponential', window?: number (default 5), smoothingFactor?: number (default 0.3), style?: Record<string, any> }`

Module Layout:
`src/utils/statistics/descriptive` exports: `mean`, `standardDeviation(values, ddof=0)`, `percentile`
`src/utils/statistics/regression` exports: `linearRegression`, `polynomialRegression`, `exponentialRegression`
`src/utils/statistics/moving-average` exports: `simpleMovingAverage`, `exponentialMovingAverage`
`src/utils/statistics` (barrel) re-exports all of the above
`src/adaptor/statistical-annotations` exports: `computeStatisticalAnnotations` and `statisticalAnnotations`

Signature: `computeStatisticalAnnotations(data, xField, yField, seriesField?, overlays, themeComponents?)` returns an array of annotation configs: `{ type: 'line'|'region', start: [x, y], end: [x, y], style: object }`. The adaptor `statisticalAnnotations(params: Params): Params` accepts the pipeline params object, dispatches computed annotations to the chart's annotation controller, and returns params unchanged.
