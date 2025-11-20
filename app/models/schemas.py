"""
Pydantic schemas for request/response validation.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class DataPoint(BaseModel):
    """Single data point in the dataset."""
    timestamp: Optional[str] = None
    value: float
    metadata: Optional[Dict[str, Any]] = None


class GenerateRequest(BaseModel):
    """Request schema for /v1/generate endpoint."""

    dataset: str = Field(..., description="Nome do dataset a ser analisado")
    period: str = Field(..., description="Período dos dados (e.g., '2025-01', 'Q1-2025')")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Filtros aplicados aos dados")
    data: List[Dict[str, Any]] = Field(..., min_length=1, description="Array de dados brutos")

    @field_validator('data')
    @classmethod
    def validate_data_structure(cls, v):
        """Validate that data array contains numeric values."""
        if not v:
            raise ValueError("Data array cannot be empty")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "dataset": "sales_revenue",
                "period": "2025-01",
                "filters": {
                    "region": "southeast",
                    "product_category": "electronics"
                },
                "data": [
                    {"timestamp": "2025-01-01", "value": 1500.50},
                    {"timestamp": "2025-01-02", "value": 2300.75},
                    {"timestamp": "2025-01-03", "value": 1800.25}
                ]
            }
        }


class Statistics(BaseModel):
    """Descriptive statistics."""
    count: int = Field(..., description="Número de observações")
    mean: float = Field(..., description="Média")
    median: float = Field(..., description="Mediana")
    min: float = Field(..., description="Valor mínimo")
    max: float = Field(..., description="Valor máximo")
    std_dev: float = Field(..., description="Desvio padrão")
    variance: float = Field(..., description="Variância")
    q1: float = Field(..., description="Primeiro quartil (25%)")
    q3: float = Field(..., description="Terceiro quartil (75%)")
    iqr: float = Field(..., description="Intervalo interquartil")
    skewness: float = Field(..., description="Assimetria da distribuição")
    kurtosis: float = Field(..., description="Curtose da distribuição")


class Trends(BaseModel):
    """Trend analysis and forecasting."""
    day_over_day_pct: Optional[float] = Field(None, description="Variação dia a dia (%)")
    month_over_month_pct: Optional[float] = Field(None, description="Variação mês a mês (%)")
    regression_slope: float = Field(..., description="Coeficiente angular da regressão linear")
    regression_intercept: float = Field(..., description="Intercepto da regressão linear")
    r_squared: float = Field(..., description="R² da regressão (qualidade do ajuste)")
    forecast_next_period: float = Field(..., description="Previsão para o próximo período")
    trend_direction: str = Field(..., description="Direção da tendência: 'upward', 'downward', 'stable'")


class Correlation(BaseModel):
    """Correlation data between variables."""
    coefficient: float = Field(..., description="Coeficiente de correlação")
    p_value: float = Field(..., description="P-valor (significância estatística)")
    is_significant: bool = Field(..., description="Se a correlação é estatisticamente significativa")


class Outlier(BaseModel):
    """Outlier detection result."""
    index: int = Field(..., description="Índice do outlier no array original")
    value: float = Field(..., description="Valor do outlier")
    z_score: float = Field(..., description="Z-score do valor")
    is_extreme: bool = Field(..., description="Se é um outlier extremo (|z| > 3)")
    timestamp: Optional[str] = None


class StatisticalPackage(BaseModel):
    """Complete statistical analysis package."""
    statistics: Statistics
    trends: Trends
    correlations: Optional[Dict[str, Correlation]] = Field(
        default=None,
        description="Correlações entre variáveis (quando aplicável)"
    )
    outliers: List[Outlier] = Field(default_factory=list)
    distribution_type: str = Field(..., description="Tipo de distribuição detectada")
    normality_test_p_value: float = Field(..., description="P-valor do teste de normalidade")
    is_normal_distribution: bool = Field(..., description="Se os dados seguem distribuição normal")


class GenerateResponse(BaseModel):
    """Response schema for /v1/generate endpoint."""

    dataset: str
    period: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float = Field(..., description="Tempo de processamento em ms")
    statistical_package: StatisticalPackage
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "dataset": "sales_revenue",
                "period": "2025-01",
                "generated_at": "2025-02-20T12:00:00Z",
                "processing_time_ms": 125.5,
                "statistical_package": {
                    "statistics": {
                        "count": 100,
                        "mean": 1850.50,
                        "median": 1800.25,
                        "min": 1200.00,
                        "max": 2500.00,
                        "std_dev": 250.75,
                        "variance": 62875.56,
                        "q1": 1600.00,
                        "q3": 2100.00,
                        "iqr": 500.00,
                        "skewness": 0.15,
                        "kurtosis": -0.25
                    },
                    "trends": {
                        "day_over_day_pct": 2.5,
                        "month_over_month_pct": 15.3,
                        "regression_slope": 12.5,
                        "regression_intercept": 1500.0,
                        "r_squared": 0.85,
                        "forecast_next_period": 2650.0,
                        "trend_direction": "upward"
                    },
                    "outliers": [],
                    "distribution_type": "normal",
                    "normality_test_p_value": 0.15,
                    "is_normal_distribution": True
                }
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response."""
    error_code: str
    message: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
