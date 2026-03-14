#!/bin/sh

apk add --no-cache curl > /dev/null 2>&1

curl -sf http://gateway:8080/health > /dev/null || { echo "FAIL: gateway"; exit 1; }
curl -sf http://bonus-calc:9000/health > /dev/null || { echo "FAIL: bonus-calc"; exit 1; }
curl -sf http://analytics:5000/health > /dev/null || { echo "FAIL: analytics"; exit 1; }

echo "All services healthy"
exit 0
