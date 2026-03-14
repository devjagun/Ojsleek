# API Endpoints

## Gateway Service (Port 9000)

The gateway provides a unified entry point for all services.

### Health Check
```
GET /health
```
Returns status of all backend services.

### Rebate Engine Proxy
```
GET /rebate/*
POST /rebate/*
```
Proxies requests to the rebate engine service.

### Analytics Proxy
```
GET /analytics/*
POST /analytics/*
```
Proxies requests to the analytics service.

---

## Rebate Engine Service (Port 5001)

### Health Check
```
GET /health
Response: {"status": "healthy", "service": "rebate-engine"}
```

### Calculate Single Rebate
```
POST /calculate
Content-Type: application/json

Request:
{
    "customer_id": 123,
    "start_date": "2024-10-01",
    "end_date": "2024-12-31"
}

Response:
{
    "customer_id": 123,
    "total_rebate": 12543.78,
    "volume_index": 1.10,
    "product_mix_factor": 1.18,
    "customer_class_rate": 0.04,
    "base_revenue": 238456.00,
    "total_units": 67234
}
```

### Batch Calculate
```
POST /batch-calculate
Content-Type: application/json

Request:
{
    "customer_ids": [123, 456, 789],
    "start_date": "2024-10-01",
    "end_date": "2024-12-31"
}

Response:
{
    "results": [
        {"customer_id": 123, "total_rebate": 12543.78, ...},
        {"customer_id": 456, "total_rebate": 8234.56, ...},
        {"customer_id": 789, "total_rebate": 5678.90, ...}
    ],
    "total_rebate_sum": 26457.24
}
```

---

## Analytics Service (Port 5002)

### Health Check
```
GET /health
Response: {"status": "healthy", "service": "analytics"}
```

### Variance Analysis
```
GET /report/variance?start_date=2024-10-01&end_date=2024-12-31

Response:
{
    "report_type": "variance_analysis",
    "period": {"start": "2024-10-01", "end": "2024-12-31"},
    "results": [
        {
            "customer_id": 123,
            "customer_name": "MedPharm Specialty",
            "expected_rebate": 10234.56,
            "actual_rebate": 12543.78,
            "variance": 2309.22,
            "variance_pct": 22.56
        },
        ...
    ]
}
```

### Customer Detail
```
GET /report/customer/{customer_id}?start_date=2024-10-01&end_date=2024-12-31

Response:
{
    "customer_id": 123,
    "customer_name": "MedPharm Specialty",
    "customer_class": "specialty",
    "certification_status": {
        "specialty_certified": true,
        "certification_date": "2024-06-15",
        "days_certified": 199
    },
    "volume_summary": {
        "total_units": 67234,
        "total_revenue": 238456.00,
        "order_count": 45
    },
    "rebate_calculation": {
        "volume_index": 1.10,
        "product_mix_factor": 1.18,
        "customer_class_rate": 0.04,
        "total_rebate": 12543.78
    }
}
```

### Hospital Impact Analysis
```
GET /report/hospital-impact?start_date=2024-10-01&end_date=2024-12-31

Response:
{
    "report_type": "hospital_impact",
    "summary": {
        "total_hospital_customers": 8,
        "total_hospital_rebates": 45678.90,
        "avg_rebate_per_hospital": 5709.86
    },
    "details": [...]
}
```

### Seasonal Trends
```
GET /report/seasonal-trends?year=2024

Response:
{
    "report_type": "seasonal_trends",
    "year": 2024,
    "quarters": [
        {"quarter": "Q1", "total_units": 234567, "total_rebates": 89234.56},
        {"quarter": "Q2", "total_units": 212345, "total_rebates": 78456.78},
        {"quarter": "Q3", "total_units": 198765, "total_rebates": 72345.67},
        {"quarter": "Q4", "total_units": 287654, "total_rebates": 112456.78}
    ]
}
```

### Specialty Certification Analysis
```
GET /report/specialty-analysis?start_date=2024-10-01&end_date=2024-12-31

Response:
{
    "report_type": "specialty_analysis",
    "summary": {
        "total_specialty_customers": 15,
        "newly_certified_count": 3,
        "avg_certification_age_days": 234
    },
    "details": [
        {
            "customer_id": 123,
            "customer_name": "MedPharm Specialty",
            "certification_date": "2024-06-15",
            "days_certified": 199,
            "qualifies_for_enhanced": true,
            "rebate_amount": 12543.78
        },
        ...
    ]
}
```

### Price List Impact
```
GET /report/price-impact?start_date=2024-10-01&end_date=2024-12-31

Response:
{
    "report_type": "price_list_impact",
    "price_changes": [
        {
            "effective_date": "2024-11-01",
            "products_affected": 45,
            "avg_price_change_pct": 3.2
        }
    ],
    "rebate_impact_estimate": 12345.67
}
```
