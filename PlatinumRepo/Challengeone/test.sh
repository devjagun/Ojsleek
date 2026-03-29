#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-new}"

if [ "$MODE" = "base" ]; then
  npx jest --config jest.stat.config.js \
    __tests__/unit/utils/flow-spec.ts \
    __tests__/unit/utils/deep-assign-spec.ts \
    __tests__/unit/utils/pick-spec.ts \
    __tests__/unit/utils/number-spec.ts \
    __tests__/unit/utils/kebab-case-spec.ts \
    __tests__/unit/utils/template-spec.ts \
    __tests__/unit/utils/data-spec.ts \
    __tests__/unit/utils/is-between-spec.ts \
    __tests__/unit/utils/conversion-spec.ts \
    __tests__/unit/utils/path-spec.ts \
    __tests__/unit/utils/padding-spec.ts \
    __tests__/unit/utils/transform/percent-spec.ts \
    __tests__/unit/utils/transform/deepPercent-spec.ts \
    __tests__/unit/utils/transform/chord-spec.ts
elif [ "$MODE" = "new" ]; then
  npx jest --config jest.stat.config.js __tests__/unit/statistical-annotations-spec.ts
else
  echo "Usage: $0 [base|new]" >&2
  exit 1
fi
