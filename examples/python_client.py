"""
Example Python client for SFB service.
"""
import requests
from typing import Dict, Any, List
import json


class SFBClient:
    """Client for Statistical Feature Builder service."""

    def __init__(self, base_url: str, token: str):
        """
        Initialize SFB client.

        Args:
            base_url: Base URL of the SFB service (e.g., https://sfb.pulse.ai)
            token: OAuth2 bearer token
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def generate(
        self,
        dataset: str,
        period: str,
        data: List[Dict[str, Any]],
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate statistical package.

        Args:
            dataset: Dataset name
            period: Period identifier
            data: List of data points with 'value' and optional 'timestamp'
            filters: Optional filters applied to data

        Returns:
            Statistical package response

        Raises:
            requests.HTTPError: If request fails
        """
        payload = {
            "dataset": dataset,
            "period": period,
            "data": data
        }

        if filters:
            payload["filters"] = filters

        response = requests.post(
            f"{self.base_url}/v1/generate",
            headers=self.headers,
            json=payload,
            timeout=60
        )

        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        """
        Check service health.

        Returns:
            Health status
        """
        response = requests.get(
            f"{self.base_url}/v1/health",
            timeout=10
        )
        response.raise_for_status()
        return response.json()


def main():
    """Example usage."""

    # Initialize client
    client = SFBClient(
        base_url="http://localhost:8000",
        token="your-token-here"  # Replace with actual token
    )

    # Check health
    print("Checking service health...")
    health = client.health_check()
    print(f"Service status: {health['status']}")
    print()

    # Prepare sample data
    data = [
        {"timestamp": f"2025-01-{i:02d}", "value": 1500 + (i * 25) + (i % 3 * 100)}
        for i in range(1, 32)
    ]

    # Generate statistical package
    print("Generating statistical package...")
    result = client.generate(
        dataset="sales_revenue",
        period="2025-01",
        data=data,
        filters={"region": "southeast"}
    )

    # Display results
    print(f"\nDataset: {result['dataset']}")
    print(f"Period: {result['period']}")
    print(f"Processing time: {result['processing_time_ms']:.2f}ms")
    print()

    stats = result['statistical_package']['statistics']
    print("Statistics:")
    print(f"  Count: {stats['count']}")
    print(f"  Mean: {stats['mean']:.2f}")
    print(f"  Median: {stats['median']:.2f}")
    print(f"  Std Dev: {stats['std_dev']:.2f}")
    print(f"  Min: {stats['min']:.2f}")
    print(f"  Max: {stats['max']:.2f}")
    print()

    trends = result['statistical_package']['trends']
    print("Trends:")
    print(f"  Direction: {trends['trend_direction']}")
    print(f"  Regression slope: {trends['regression_slope']:.2f}")
    print(f"  R²: {trends['r_squared']:.2f}")
    print(f"  Forecast next period: {trends['forecast_next_period']:.2f}")
    print()

    outliers = result['statistical_package']['outliers']
    print(f"Outliers detected: {len(outliers)}")
    if outliers:
        for outlier in outliers:
            print(f"  - Index {outlier['index']}: {outlier['value']} (z-score: {outlier['z_score']:.2f})")
    print()

    print(f"Distribution type: {result['statistical_package']['distribution_type']}")
    print(f"Normal distribution: {result['statistical_package']['is_normal_distribution']}")


if __name__ == "__main__":
    main()
