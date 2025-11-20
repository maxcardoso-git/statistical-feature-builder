"""
Tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

# Disable auth for testing
settings.oauth2_enabled = False
settings.rate_limit_enabled = False

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert data["status"] == "running"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == settings.service_name


def test_generate_valid_request():
    """Test generate endpoint with valid data."""
    payload = {
        "dataset": "test_dataset",
        "period": "2025-01",
        "data": [
            {"timestamp": "2025-01-01", "value": 100},
            {"timestamp": "2025-01-02", "value": 105},
            {"timestamp": "2025-01-03", "value": 102},
            {"timestamp": "2025-01-04", "value": 98},
            {"timestamp": "2025-01-05", "value": 103},
        ]
    }

    response = client.post("/v1/generate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["dataset"] == "test_dataset"
    assert data["period"] == "2025-01"
    assert "statistical_package" in data
    assert "statistics" in data["statistical_package"]
    assert "trends" in data["statistical_package"]
    assert "outliers" in data["statistical_package"]
    assert "processing_time_ms" in data


def test_generate_with_filters():
    """Test generate endpoint with filters."""
    payload = {
        "dataset": "sales_data",
        "period": "2025-01",
        "filters": {
            "region": "southeast",
            "category": "electronics"
        },
        "data": [{"value": i * 10} for i in range(1, 11)]
    }

    response = client.post("/v1/generate", json=payload)
    assert response.status_code == 200


def test_generate_empty_data():
    """Test generate endpoint with empty data."""
    payload = {
        "dataset": "test_dataset",
        "period": "2025-01",
        "data": []
    }

    response = client.post("/v1/generate", json=payload)
    assert response.status_code == 422  # Validation error


def test_generate_insufficient_data():
    """Test generate endpoint with insufficient data points."""
    payload = {
        "dataset": "test_dataset",
        "period": "2025-01",
        "data": [{"value": 100}, {"value": 105}]  # Only 2 points
    }

    response = client.post("/v1/generate", json=payload)
    assert response.status_code == 400


def test_generate_invalid_data():
    """Test generate endpoint with invalid data."""
    payload = {
        "dataset": "test_dataset",
        "period": "2025-01",
        "data": [{"value": "not_a_number"}]
    }

    response = client.post("/v1/generate", json=payload)
    assert response.status_code in [400, 422]


def test_generate_with_outliers():
    """Test generate endpoint with data containing outliers."""
    payload = {
        "dataset": "outlier_test",
        "period": "2025-01",
        "data": [
            {"value": 100},
            {"value": 105},
            {"value": 102},
            {"value": 500},  # Outlier
            {"value": 103},
            {"value": 101},
            {"value": 99},
            {"value": 104},
            {"value": 97},
            {"value": 106}
        ]
    }

    response = client.post("/v1/generate", json=payload)
    assert response.status_code == 200

    data = response.json()
    outliers = data["statistical_package"]["outliers"]
    assert len(outliers) > 0
    assert any(o["value"] == 500 for o in outliers)


def test_generate_missing_required_fields():
    """Test generate endpoint with missing required fields."""
    payload = {
        "period": "2025-01",
        "data": [{"value": 100}]
        # Missing 'dataset'
    }

    response = client.post("/v1/generate", json=payload)
    assert response.status_code == 422


def test_statistics_calculation():
    """Test that statistics are calculated correctly."""
    payload = {
        "dataset": "stats_test",
        "period": "2025-01",
        "data": [{"value": float(i)} for i in range(1, 11)]  # 1-10
    }

    response = client.post("/v1/generate", json=payload)
    assert response.status_code == 200

    stats = response.json()["statistical_package"]["statistics"]
    assert stats["count"] == 10
    assert stats["mean"] == pytest.approx(5.5, rel=0.1)
    assert stats["min"] == 1.0
    assert stats["max"] == 10.0


def test_trends_calculation():
    """Test that trends are calculated correctly."""
    payload = {
        "dataset": "trend_test",
        "period": "2025-01",
        "data": [{"value": float(i * 10)} for i in range(1, 11)]  # Upward trend
    }

    response = client.post("/v1/generate", json=payload)
    assert response.status_code == 200

    trends = response.json()["statistical_package"]["trends"]
    assert trends["trend_direction"] == "upward"
    assert trends["regression_slope"] > 0


def test_response_headers():
    """Test that response includes proper headers."""
    payload = {
        "dataset": "header_test",
        "period": "2025-01",
        "data": [{"value": i} for i in range(1, 11)]
    }

    response = client.post("/v1/generate", json=payload)
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers or "x-request-id" in response.headers
