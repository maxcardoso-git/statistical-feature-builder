"""
Core statistical calculation engine.
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class StatisticalEngine:
    """
    Statistical calculation engine for analyzing datasets.
    Provides descriptive statistics, trend analysis, outlier detection, and forecasting.
    """

    def __init__(self):
        self.outlier_threshold = 3.0  # Z-score threshold for outliers
        self.extreme_threshold = 3.0  # Z-score threshold for extreme outliers

    def calculate_descriptive_statistics(self, data: np.ndarray) -> Dict[str, float]:
        """
        Calculate comprehensive descriptive statistics.

        Args:
            data: NumPy array of numeric values

        Returns:
            Dictionary with statistical measures
        """
        try:
            # Basic statistics
            mean_val = float(np.mean(data))
            median_val = float(np.median(data))
            std_val = float(np.std(data, ddof=1))  # Sample std dev
            var_val = float(np.var(data, ddof=1))  # Sample variance

            # Quartiles
            q1 = float(np.percentile(data, 25))
            q3 = float(np.percentile(data, 75))
            iqr = q3 - q1

            # Distribution shape
            skewness = float(stats.skew(data))
            kurt = float(stats.kurtosis(data))

            return {
                "count": int(len(data)),
                "mean": mean_val,
                "median": median_val,
                "min": float(np.min(data)),
                "max": float(np.max(data)),
                "std_dev": std_val,
                "variance": var_val,
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "skewness": skewness,
                "kurtosis": kurt
            }
        except Exception as e:
            logger.error(f"Error calculating descriptive statistics: {e}")
            raise

    def detect_outliers(
        self,
        data: np.ndarray,
        timestamps: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect outliers using Z-score method.

        Args:
            data: NumPy array of numeric values
            timestamps: Optional list of timestamps corresponding to data points

        Returns:
            List of outlier dictionaries
        """
        try:
            mean = np.mean(data)
            std = np.std(data, ddof=1)

            outliers = []

            if std == 0:
                # No variance, no outliers
                return outliers

            z_scores = (data - mean) / std

            for idx, (value, z_score) in enumerate(zip(data, z_scores)):
                abs_z = abs(z_score)
                if abs_z > self.outlier_threshold:
                    outlier = {
                        "index": int(idx),
                        "value": float(value),
                        "z_score": float(z_score),
                        "is_extreme": abs_z > self.extreme_threshold
                    }
                    if timestamps and idx < len(timestamps):
                        outlier["timestamp"] = timestamps[idx]
                    else:
                        outlier["timestamp"] = None

                    outliers.append(outlier)

            return outliers

        except Exception as e:
            logger.error(f"Error detecting outliers: {e}")
            raise

    def analyze_trends(
        self,
        data: np.ndarray,
        period_type: str = "daily"
    ) -> Dict[str, Any]:
        """
        Perform trend analysis and forecasting.

        Args:
            data: NumPy array of numeric values (time-ordered)
            period_type: Type of period ('daily', 'monthly', etc.)

        Returns:
            Dictionary with trend metrics
        """
        try:
            n = len(data)

            # Calculate period-over-period changes
            day_over_day = None
            month_over_month = None

            if n >= 2:
                # Simple last vs previous comparison
                last_value = data[-1]
                prev_value = data[-2]
                if prev_value != 0:
                    day_over_day = float(((last_value - prev_value) / prev_value) * 100)

            if n >= 30:
                # Month-over-month (comparing last 30 vs previous 30)
                recent_mean = np.mean(data[-30:])
                if n >= 60:
                    prev_mean = np.mean(data[-60:-30])
                    if prev_mean != 0:
                        month_over_month = float(((recent_mean - prev_mean) / prev_mean) * 100)

            # Linear regression for trend
            X = np.arange(n).reshape(-1, 1)
            y = data.reshape(-1, 1)

            model = LinearRegression()
            model.fit(X, y)

            slope = float(model.coef_[0][0])
            intercept = float(model.intercept_[0])
            r_squared = float(model.score(X, y))

            # Forecast next period
            next_x = np.array([[n]])
            forecast = float(model.predict(next_x)[0][0])

            # Determine trend direction
            if abs(slope) < 0.01 * np.mean(data):
                trend_direction = "stable"
            elif slope > 0:
                trend_direction = "upward"
            else:
                trend_direction = "downward"

            return {
                "day_over_day_pct": day_over_day,
                "month_over_month_pct": month_over_month,
                "regression_slope": slope,
                "regression_intercept": intercept,
                "r_squared": r_squared,
                "forecast_next_period": forecast,
                "trend_direction": trend_direction
            }

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            raise

    def test_normality(self, data: np.ndarray) -> Tuple[float, bool]:
        """
        Test if data follows a normal distribution using Shapiro-Wilk test.

        Args:
            data: NumPy array of numeric values

        Returns:
            Tuple of (p_value, is_normal)
        """
        try:
            if len(data) < 3:
                # Not enough data for normality test
                return 1.0, False

            # Shapiro-Wilk test
            statistic, p_value = stats.shapiro(data)

            # Using alpha = 0.05 significance level
            is_normal = p_value > 0.05

            return float(p_value), is_normal

        except Exception as e:
            logger.error(f"Error testing normality: {e}")
            return 0.0, False

    def classify_distribution(self, data: np.ndarray, p_value: float) -> str:
        """
        Classify the distribution type based on statistical properties.

        Args:
            data: NumPy array of numeric values
            p_value: P-value from normality test

        Returns:
            Distribution type as string
        """
        try:
            if p_value > 0.05:
                return "normal"

            skewness = stats.skew(data)
            kurtosis = stats.kurtosis(data)

            # Classify based on shape
            if abs(skewness) < 0.5 and abs(kurtosis) < 0.5:
                return "approximately_normal"
            elif skewness > 1:
                return "right_skewed"
            elif skewness < -1:
                return "left_skewed"
            elif kurtosis > 3:
                return "heavy_tailed"
            elif kurtosis < -1:
                return "light_tailed"
            else:
                return "non_normal"

        except Exception as e:
            logger.error(f"Error classifying distribution: {e}")
            return "unknown"

    def calculate_correlations(
        self,
        datasets: Dict[str, np.ndarray]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate pairwise correlations between multiple datasets.

        Args:
            datasets: Dictionary of dataset_name -> data array

        Returns:
            Dictionary of correlation results
        """
        try:
            if len(datasets) < 2:
                return {}

            correlations = {}
            dataset_names = list(datasets.keys())

            for i in range(len(dataset_names)):
                for j in range(i + 1, len(dataset_names)):
                    name1 = dataset_names[i]
                    name2 = dataset_names[j]

                    data1 = datasets[name1]
                    data2 = datasets[name2]

                    # Ensure same length
                    min_len = min(len(data1), len(data2))
                    data1 = data1[:min_len]
                    data2 = data2[:min_len]

                    # Pearson correlation
                    pearson_coef, pearson_p = stats.pearsonr(data1, data2)

                    # Spearman correlation (rank-based)
                    spearman_coef, spearman_p = stats.spearmanr(data1, data2)

                    key = f"{name1}_vs_{name2}"
                    correlations[key] = {
                        "pearson": {
                            "coefficient": float(pearson_coef),
                            "p_value": float(pearson_p),
                            "is_significant": pearson_p < 0.05
                        },
                        "spearman": {
                            "coefficient": float(spearman_coef),
                            "p_value": float(spearman_p),
                            "is_significant": spearman_p < 0.05
                        }
                    }

            return correlations

        except Exception as e:
            logger.error(f"Error calculating correlations: {e}")
            raise
