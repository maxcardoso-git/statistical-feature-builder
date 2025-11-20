"""
Data processing and orchestration layer.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List
import logging
from app.core.statistics import StatisticalEngine
from app.models.schemas import (
    GenerateRequest,
    StatisticalPackage,
    Statistics,
    Trends,
    Outlier,
    Correlation
)

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Processes incoming data and orchestrates statistical calculations.
    """

    def __init__(self):
        self.engine = StatisticalEngine()

    def extract_values(self, data: List[Dict[str, Any]]) -> tuple[np.ndarray, List[str]]:
        """
        Extract numeric values and timestamps from input data.

        Args:
            data: List of data points

        Returns:
            Tuple of (values array, timestamps list)
        """
        values = []
        timestamps = []

        for point in data:
            # Try to extract value
            if isinstance(point, dict):
                value = point.get("value")
                timestamp = point.get("timestamp")
            else:
                value = point
                timestamp = None

            if value is not None:
                try:
                    values.append(float(value))
                    timestamps.append(timestamp)
                except (ValueError, TypeError):
                    logger.warning(f"Skipping non-numeric value: {value}")
                    continue

        return np.array(values), timestamps

    def mask_sensitive_fields(
        self,
        data: List[Dict[str, Any]],
        fields_to_mask: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Mask sensitive fields in the data.

        Args:
            data: List of data dictionaries
            fields_to_mask: List of field names to mask

        Returns:
            Data with masked fields
        """
        if not fields_to_mask:
            return data

        masked_data = []
        for item in data:
            if isinstance(item, dict):
                masked_item = item.copy()
                for field in fields_to_mask:
                    if field in masked_item:
                        masked_item[field] = "***MASKED***"
                masked_data.append(masked_item)
            else:
                masked_data.append(item)

        return masked_data

    def validate_data(self, values: np.ndarray) -> None:
        """
        Validate that data is suitable for statistical analysis.

        Args:
            values: NumPy array of values

        Raises:
            ValueError: If data is invalid
        """
        if len(values) == 0:
            raise ValueError("E002: No valid numeric values found in data")

        if len(values) < 3:
            raise ValueError("E002: Insufficient data points for statistical analysis (minimum 3 required)")

        if np.any(np.isnan(values)):
            raise ValueError("E002: Data contains NaN values")

        if np.any(np.isinf(values)):
            raise ValueError("E002: Data contains infinite values")

    def process_request(
        self,
        request: GenerateRequest,
        masking_fields: List[str] = None
    ) -> StatisticalPackage:
        """
        Main processing function that orchestrates statistical analysis.

        Args:
            request: Input request with data
            masking_fields: Optional list of fields to mask

        Returns:
            Complete statistical package

        Raises:
            ValueError: For data validation errors
            Exception: For processing errors
        """
        try:
            # Extract values and timestamps
            values, timestamps = self.extract_values(request.data)

            # Validate data
            self.validate_data(values)

            logger.info(f"Processing {len(values)} data points for dataset '{request.dataset}'")

            # Calculate descriptive statistics
            stats_dict = self.engine.calculate_descriptive_statistics(values)
            statistics = Statistics(**stats_dict)

            # Analyze trends
            trends_dict = self.engine.analyze_trends(values, period_type="daily")
            trends = Trends(**trends_dict)

            # Detect outliers
            outliers_list = self.engine.detect_outliers(values, timestamps)
            outliers = [Outlier(**outlier) for outlier in outliers_list]

            # Test normality
            p_value, is_normal = self.engine.test_normality(values)

            # Classify distribution
            distribution_type = self.engine.classify_distribution(values, p_value)

            # Build statistical package
            package = StatisticalPackage(
                statistics=statistics,
                trends=trends,
                correlations=None,  # Single dataset, no correlations
                outliers=outliers,
                distribution_type=distribution_type,
                normality_test_p_value=p_value,
                is_normal_distribution=is_normal
            )

            logger.info(f"Successfully generated statistical package for '{request.dataset}'")

            return package

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Processing error: {e}")
            raise Exception(f"E003: {str(e)}")

    def process_multi_dataset(
        self,
        datasets: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Process multiple datasets and calculate cross-correlations.

        Args:
            datasets: Dictionary of dataset_name -> data

        Returns:
            Dictionary with individual packages and correlations
        """
        try:
            packages = {}
            dataset_arrays = {}

            # Process each dataset
            for name, data in datasets.items():
                values, timestamps = self.extract_values(data)
                self.validate_data(values)
                dataset_arrays[name] = values

                # Generate individual package
                request = GenerateRequest(
                    dataset=name,
                    period="multi",
                    data=data
                )
                packages[name] = self.process_request(request)

            # Calculate cross-correlations
            correlations = self.engine.calculate_correlations(dataset_arrays)

            return {
                "packages": packages,
                "cross_correlations": correlations
            }

        except Exception as e:
            logger.error(f"Multi-dataset processing error: {e}")
            raise
