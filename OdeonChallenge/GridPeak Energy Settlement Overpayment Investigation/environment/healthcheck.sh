#!/bin/sh

apk add --no-cache curl > /dev/null 2>&1

curl -sf http://gateway:8080/health > /dev/null || { echo "FAIL: gateway"; exit 1; }
curl -sf http://settlement_engine:8082/health > /dev/null || { echo "FAIL: settlement_engine"; exit 1; }
curl -sf http://loss_calculator:8081/health > /dev/null || { echo "FAIL: loss_calculator"; exit 1; }

echo "All services healthy"
exit 0
