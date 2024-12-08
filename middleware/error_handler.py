# middleware/error_handler.py
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
import traceback

logger = logging.getLogger(__name__)


async def error_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        # Log the full error with traceback
        logger.error(f"Unhandled error: {str(e)}")
        logger.error(traceback.format_exc())

        # Return a safe error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "request_id": request.state.request_id
            }
        )


# Add to your app:
app.middleware("http")(error_handler)