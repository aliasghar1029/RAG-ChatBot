from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceErrorHandler:
    """
    Centralized error handling for service unavailability and other issues
    """

    @staticmethod
    async def handle_external_service_error(error: Exception, service_name: str) -> Dict[str, Any]:
        """
        Handle errors from external services (Cohere, Qdrant, OpenRouter)
        """
        logger.error(f"External service error in {service_name}: {str(error)}")

        return {
            "error": f"{service_name}_unavailable",
            "message": f"The {service_name} service is currently unavailable. Please try again later.",
            "fallback_message": "This information is not available in the book.",
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

    @staticmethod
    async def handle_database_error(error: Exception) -> Dict[str, Any]:
        """
        Handle database-related errors
        """
        logger.error(f"Database error: {str(error)}")

        return {
            "error": "database_unavailable",
            "message": "The database service is currently unavailable. Chat history may not be saved.",
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

    @staticmethod
    async def handle_general_error(error: Exception) -> Dict[str, Any]:
        """
        Handle general application errors
        """
        logger.error(f"General error: {str(error)}")

        return {
            "error": "internal_error",
            "message": "An internal error occurred. Please try again later.",
            "fallback_message": "This information is not available in the book.",
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

# Global instance
error_handler = ServiceErrorHandler()

# FastAPI exception handlers
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An internal server error occurred",
            "fallback_message": "This information is not available in the book.",
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
    )