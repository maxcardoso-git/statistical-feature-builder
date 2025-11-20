#!/bin/bash

# SFB API Examples using cURL

BASE_URL="http://localhost:8000"
TOKEN="your-token-here"  # Replace with actual token

echo "======================================"
echo "Statistical Feature Builder - Examples"
echo "======================================"
echo ""

# 1. Health Check
echo "1. Health Check"
echo "--------------------------------------"
curl -X GET "$BASE_URL/v1/health" \
  -H "Accept: application/json" | jq '.'
echo ""
echo ""

# 2. Generate Statistical Package
echo "2. Generate Statistical Package"
echo "--------------------------------------"
curl -X POST "$BASE_URL/v1/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "sales_revenue",
    "period": "2025-01",
    "filters": {
      "region": "southeast",
      "product_category": "electronics"
    },
    "data": [
      {"timestamp": "2025-01-01", "value": 1500.50},
      {"timestamp": "2025-01-02", "value": 2300.75},
      {"timestamp": "2025-01-03", "value": 1800.25},
      {"timestamp": "2025-01-04", "value": 2100.00},
      {"timestamp": "2025-01-05", "value": 1950.50},
      {"timestamp": "2025-01-06", "value": 2250.00},
      {"timestamp": "2025-01-07", "value": 1700.75},
      {"timestamp": "2025-01-08", "value": 2400.00},
      {"timestamp": "2025-01-09", "value": 2050.25},
      {"timestamp": "2025-01-10", "value": 1850.00}
    ]
  }' | jq '.'
echo ""
echo ""

# 3. Generate with data file
echo "3. Generate from JSON file"
echo "--------------------------------------"
curl -X POST "$BASE_URL/v1/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @example_request.json | jq '.'
echo ""
echo ""

# 4. Example with error (invalid data)
echo "4. Example with error (invalid data)"
echo "--------------------------------------"
curl -X POST "$BASE_URL/v1/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "test_dataset",
    "period": "2025-01",
    "data": []
  }' | jq '.'
echo ""
echo ""

# 5. Example with outliers
echo "5. Example with outliers"
echo "--------------------------------------"
curl -X POST "$BASE_URL/v1/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "outlier_test",
    "period": "2025-01",
    "data": [
      {"value": 100},
      {"value": 105},
      {"value": 102},
      {"value": 98},
      {"value": 103},
      {"value": 500},
      {"value": 101},
      {"value": 99},
      {"value": 104},
      {"value": 97}
    ]
  }' | jq '.'
echo ""
echo ""

echo "======================================"
echo "Examples completed!"
echo "======================================"
