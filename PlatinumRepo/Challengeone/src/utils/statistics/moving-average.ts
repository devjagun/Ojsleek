export function simpleMovingAverage(values: number[], window: number): number[] {
  if (values.length === 0) return [];
  const result: number[] = [];
  for (let i = 0; i < values.length; i++) {
    const start = Math.max(0, i - window + 1);
    const slice = values.slice(start, i + 1);
    result.push(slice.reduce((s, v) => s + v, 0) / slice.length);
  }
  return result;
}

export function exponentialMovingAverage(values: number[], smoothingFactor: number): number[] {
  if (values.length === 0) return [];
  const result: number[] = [values[0]];
  for (let i = 1; i < values.length; i++) {
    result.push(smoothingFactor * values[i] + (1 - smoothingFactor) * result[i - 1]);
  }
  return result;
}
