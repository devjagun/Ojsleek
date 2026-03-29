export function linearRegression(points: [number, number][]): {
  slope: number;
  intercept: number;
  predict: (x: number) => number;
} {
  if (points.length === 1) {
    const intercept = points[0][1];
    return { slope: 0, intercept, predict: () => intercept };
  }

  const n = points.length;
  let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;
  for (const [x, y] of points) {
    sumX += x;
    sumY += y;
    sumXY += x * y;
    sumXX += x * x;
  }
  const denom = n * sumXX - sumX * sumX;
  const slope = denom === 0 ? 0 : (n * sumXY - sumX * sumY) / denom;
  const intercept = (sumY - slope * sumX) / n;
  return { slope, intercept, predict: (x: number) => slope * x + intercept };
}

export function polynomialRegression(
  points: [number, number][],
  degree: number
): { coefficients: number[]; predict: (x: number) => number } {
  const n = points.length;
  const m = degree + 1;

  // Build Vandermonde matrix and y vector
  const X: number[][] = [];
  const Y: number[] = [];
  for (const [x, y] of points) {
    const row: number[] = [];
    let val = 1;
    for (let j = 0; j < m; j++) {
      row.push(val);
      val *= x;
    }
    X.push(row);
    Y.push(y);
  }

  // X^T * X
  const XtX: number[][] = Array.from({ length: m }, () => Array(m).fill(0));
  const XtY: number[] = Array(m).fill(0);
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < m; j++) {
      for (let k = 0; k < m; k++) {
        XtX[j][k] += X[i][j] * X[i][k];
      }
      XtY[j] += X[i][j] * Y[i];
    }
  }

  // Gaussian elimination with partial pivoting
  const aug: number[][] = XtX.map((row, i) => [...row, XtY[i]]);
  for (let col = 0; col < m; col++) {
    let maxRow = col;
    for (let row = col + 1; row < m; row++) {
      if (Math.abs(aug[row][col]) > Math.abs(aug[maxRow][col])) maxRow = row;
    }
    [aug[col], aug[maxRow]] = [aug[maxRow], aug[col]];
    const pivot = aug[col][col];
    if (pivot === 0) continue;
    for (let j = col; j <= m; j++) aug[col][j] /= pivot;
    for (let row = 0; row < m; row++) {
      if (row === col) continue;
      const factor = aug[row][col];
      for (let j = col; j <= m; j++) aug[row][j] -= factor * aug[col][j];
    }
  }

  const coefficients = aug.map(row => row[m]);

  const predict = (x: number): number => {
    let result = 0;
    let xPow = 1;
    for (const c of coefficients) {
      result += c * xPow;
      xPow *= x;
    }
    return result;
  };

  return { coefficients, predict };
}

export function exponentialRegression(points: [number, number][]): {
  a: number;
  b: number;
  predict: (x: number) => number;
} {
  const filtered = points.filter(([, y]) => y > 0);
  if (filtered.length < 2) {
    return { a: 1, b: 0, predict: () => 1 };
  }

  const logPoints: [number, number][] = filtered.map(([x, y]) => [x, Math.log(y)]);
  const lin = linearRegression(logPoints);
  const a = Math.exp(lin.intercept);
  const b = lin.slope;
  return { a, b, predict: (x: number) => a * Math.exp(b * x) };
}
