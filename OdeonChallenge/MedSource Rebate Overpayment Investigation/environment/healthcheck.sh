#!/bin/sh

apk add --no-cache curl > /dev/null 2>&1

curl -sf http://gateway:9000/health > /dev/null || { echo "FAIL: gateway"; exit 1; }
curl -sf http://rebate-engine:5001/health > /dev/null || { echo "FAIL: rebate-engine"; exit 1; }
curl -sf http://analytics:5002/health > /dev/null || { echo "FAIL: analytics"; exit 1; }

echo "All services healthy"
exit 0
