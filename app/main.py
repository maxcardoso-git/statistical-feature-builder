"""
Statistical Feature Builder (SFB) - Main Application
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
from app.config import settings
from app.middleware.logging import setup_logging, RequestLoggingMiddleware
from app.routers import v1

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    """
    # Startup
    logger.info(
        f"Starting {settings.service_name} v{settings.service_version}",
        extra={
            "environment": settings.environment,
            "oauth2_enabled": settings.oauth2_enabled,
            "rate_limit_enabled": settings.rate_limit_enabled,
        }
    )

    # Initialize OpenTelemetry if enabled
    if settings.otel_enabled:
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            # Setup trace provider
            trace.set_tracer_provider(TracerProvider())
            tracer_provider = trace.get_tracer_provider()

            # Setup OTLP exporter
            otlp_exporter = OTLPSpanExporter(
                endpoint=settings.otel_exporter_otlp_endpoint,
                insecure=True
            )
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)

            # Instrument FastAPI
            FastAPIInstrumentor.instrument_fastapi(app)

            logger.info(f"OpenTelemetry initialized: {settings.otel_exporter_otlp_endpoint}")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenTelemetry: {e}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.service_name}")


# Create FastAPI app
app = FastAPI(
    title="Statistical Feature Builder",
    description="""
    **Statistical Feature Builder (SFB)** is a specialized microservice for statistical data processing.

    ## Features

    - 📊 **Descriptive Statistics**: Mean, median, quartiles, variance, skewness, kurtosis
    - 📈 **Trend Analysis**: Linear regression, forecasting, period-over-period changes
    - 🔍 **Outlier Detection**: Z-score based detection with severity classification
    - 📉 **Distribution Analysis**: Normality testing and distribution classification
    - 🔗 **Correlation Analysis**: Pearson and Spearman correlations (multi-dataset)

    ## Authentication

    This API uses OAuth2 with Bearer tokens. Include your token in the Authorization header:

    ```
    Authorization: Bearer <your-token>
    ```

    Required scopes:
    - `sfb.read`: Read access
    - `sfb.write`: Write access (required for /generate endpoint)

    ## Rate Limiting

    - **Limit**: 500 requests per minute per client
    - **Window**: Rolling 1-minute window
    - **Response**: HTTP 429 with Retry-After header when exceeded

    ## Error Codes

    - **E001**: Dataset inválido ou inexistente
    - **E002**: Payload fora do padrão esperado
    - **E003**: Falha interna no cálculo estatístico
    - **E004**: Timeout ao processar dados
    - **E005**: Autorização inválida ou ausente
    - **E006**: Rate limit exceeded
    """,
    version=settings.service_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
if settings.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"]
    )

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(v1.router)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(
        f"Validation error: {exc}",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "path": request.url.path,
            "errors": exc.errors()
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "E002",
            "message": "Request validation failed",
            "detail": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "path": request.url.path
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "E003",
            "message": "Internal server error",
            "detail": str(exc) if settings.environment == "development" else None
        }
    )


# Root endpoint
@app.get("/", tags=["General"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "status": "running",
        "docs": "/docs",
        "health": "/v1/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
