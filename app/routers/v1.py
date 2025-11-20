"""
API v1 routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Dict, Any
import time
import logging
from app.models.schemas import (
    GenerateRequest,
    GenerateResponse,
    ErrorResponse,
)
from app.core.processor import DataProcessor
from app.middleware.auth import get_current_user_with_write_permission
from app.middleware.rate_limiter import rate_limiter
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["Statistical Analysis"])

# Initialize processor
processor = DataProcessor()


@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Statistical Package",
    description="Generates a complete statistical analysis package from raw analytical data.",
    responses={
        200: {
            "description": "Statistical package generated successfully",
            "model": GenerateResponse
        },
        400: {
            "description": "Invalid request data",
            "model": ErrorResponse
        },
        401: {
            "description": "Unauthorized - invalid or missing token",
            "model": ErrorResponse
        },
        404: {
            "description": "Dataset not found",
            "model": ErrorResponse
        },
        429: {
            "description": "Rate limit exceeded",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        },
        504: {
            "description": "Request timeout",
            "model": ErrorResponse
        }
    }
)
async def generate_statistical_package(
    request_data: GenerateRequest,
    request: Request,
    user: dict = Depends(get_current_user_with_write_permission)
) -> GenerateResponse:
    """
    Generate a comprehensive statistical package.

    This endpoint receives raw analytical data and produces:
    - Descriptive statistics (mean, median, quartiles, etc.)
    - Trend analysis and forecasting
    - Outlier detection
    - Distribution analysis
    - Correlation analysis (when applicable)

    **Required Scopes:** `sfb.write`

    **Rate Limit:** 500 requests per minute
    """
    start_time = time.time()
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        # Check rate limit
        await rate_limiter.check_rate_limit(request)

        logger.info(
            f"Processing statistical package request",
            extra={
                "request_id": request_id,
                "dataset": request_data.dataset,
                "period": request_data.period,
                "data_points": len(request_data.data),
                "user": user.get("sub", "unknown")
            }
        )

        # Process the request
        statistical_package = processor.process_request(
            request_data,
            masking_fields=settings.masking_fields_list if settings.data_masking_enabled else None
        )

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Build response
        response = GenerateResponse(
            dataset=request_data.dataset,
            period=request_data.period,
            processing_time_ms=round(processing_time_ms, 2),
            statistical_package=statistical_package,
            metadata={
                "request_id": request_id,
                "data_points_processed": len(request_data.data),
                "outliers_detected": len(statistical_package.outliers),
                "user": user.get("sub", "system")
            }
        )

        logger.info(
            f"Statistical package generated successfully",
            extra={
                "request_id": request_id,
                "dataset": request_data.dataset,
                "processing_time_ms": round(processing_time_ms, 2),
                "exec_status": "success"
            }
        )

        return response

    except ValueError as e:
        # Data validation errors
        error_msg = str(e)
        error_code = "E002"

        if "E001" in error_msg:
            error_code = "E001"
        elif "E002" in error_msg:
            error_code = "E002"

        logger.warning(
            f"Validation error: {error_msg}",
            extra={
                "request_id": request_id,
                "dataset": request_data.dataset,
                "error_code": error_code,
                "exec_status": "error"
            }
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": error_code,
                "message": error_msg,
                "dataset": request_data.dataset
            }
        )

    except TimeoutError:
        logger.error(
            f"Request timeout",
            extra={
                "request_id": request_id,
                "dataset": request_data.dataset,
                "error_code": "E004",
                "exec_status": "error"
            }
        )

        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "error_code": "E004",
                "message": "Request timeout - processing took too long",
                "timeout_ms": settings.request_timeout_ms
            }
        )

    except Exception as e:
        # Internal errors
        error_msg = str(e)
        error_code = "E003"

        if "E003" in error_msg:
            error_msg = error_msg.replace("E003: ", "")

        logger.error(
            f"Internal error: {error_msg}",
            extra={
                "request_id": request_id,
                "dataset": request_data.dataset,
                "error_code": error_code,
                "exec_status": "error"
            },
            exc_info=True
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": error_code,
                "message": "Internal processing error",
                "detail": error_msg if settings.environment == "development" else None
            }
        )


@router.get(
    "/health",
    summary="Health Check",
    description="Check if the service is healthy and responding"
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns service status and version information.
    """
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.service_version,
        "environment": settings.environment
    }
