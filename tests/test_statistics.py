"""
Tests for statistical calculation engine.
"""
import pytest
import numpy as np
from app.core.statistics import StatisticalEngine


@pytest.fixture
def engine():
    """Create a StatisticalEngine instance."""
    return StatisticalEngine()


@pytest.fixture
def sample_data():
    """Generate sample data for testing."""
    return np.array([100, 105, 102, 98, 103, 101, 99, 104, 97, 106])


def test_descriptive_statistics(engine, sample_data):
    """Test descriptive statistics calculation."""
    stats = engine.calculate_descriptive_statistics(sample_data)

    assert stats["count"] == 10
    assert stats["mean"] == pytest.approx(101.5, rel=0.1)
    assert stats["median"] == pytest.approx(101.5, rel=0.1)
    assert stats["min"] == 97
    assert stats["max"] == 106
    assert stats["std_dev"] > 0
    assert stats["variance"] > 0
    assert "q1" in stats
    assert "q3" in stats
    assert "iqr" in stats
    assert "skewness" in stats
    assert "kurtosis" in stats


def test_outlier_detection(engine):
    """Test outlier detection."""
    # Data with obvious outliers
    data = np.array([100, 105, 102, 98, 103, 500, 101, 99, 104, 97])

    outliers = engine.detect_outliers(data)

    assert len(outliers) > 0
    assert any(o["value"] == 500 for o in outliers)
    assert all("z_score" in o for o in outliers)
    assert all("is_extreme" in o for o in outliers)


def test_outlier_detection_with_timestamps(engine):
    """Test outlier detection with timestamps."""
    data = np.array([100, 105, 102, 500, 103])
    timestamps = ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05"]

    outliers = engine.detect_outliers(data, timestamps)

    assert len(outliers) > 0
    outlier = next(o for o in outliers if o["value"] == 500)
    assert outlier["timestamp"] == "2025-01-04"


def test_trend_analysis(engine, sample_data):
    """Test trend analysis."""
    trends = engine.analyze_trends(sample_data)

    assert "regression_slope" in trends
    assert "regression_intercept" in trends
    assert "r_squared" in trends
    assert "forecast_next_period" in trends
    assert trends["trend_direction"] in ["upward", "downward", "stable"]
    assert 0 <= trends["r_squared"] <= 1


def test_normality_test(engine, sample_data):
    """Test normality testing."""
    p_value, is_normal = engine.test_normality(sample_data)

    assert 0 <= p_value <= 1
    assert isinstance(is_normal, bool)


def test_distribution_classification(engine, sample_data):
    """Test distribution classification."""
    p_value, _ = engine.test_normality(sample_data)
    dist_type = engine.classify_distribution(sample_data, p_value)

    assert dist_type in [
        "normal",
        "approximately_normal",
        "right_skewed",
        "left_skewed",
        "heavy_tailed",
        "light_tailed",
        "non_normal"
    ]


def test_correlations(engine):
    """Test correlation calculation."""
    datasets = {
        "dataset1": np.array([1, 2, 3, 4, 5]),
        "dataset2": np.array([2, 4, 6, 8, 10])  # Perfect positive correlation
    }

    correlations = engine.calculate_correlations(datasets)

    assert len(correlations) > 0
    key = "dataset1_vs_dataset2"
    assert key in correlations
    assert "pearson" in correlations[key]
    assert "spearman" in correlations[key]
    assert abs(correlations[key]["pearson"]["coefficient"]) > 0.9  # Strong correlation


def test_empty_data(engine):
    """Test handling of empty data."""
    with pytest.raises(Exception):
        engine.calculate_descriptive_statistics(np.array([]))


def test_insufficient_data(engine):
    """Test handling of insufficient data."""
    data = np.array([1, 2])  # Only 2 points
    p_value, is_normal = engine.test_normality(data)

    assert is_normal is False  # Not enough data
