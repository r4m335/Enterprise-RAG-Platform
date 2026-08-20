import uuid
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from core.config import settings
from core.exceptions import AppException
from api.v1 import auth, documents, search, chat

# Setup logging
logger.add("logs/app.log", rotation="500 MB", retention="10 days", level="INFO")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise RAG Platform API",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "request_id": request_id
            }
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": request_id
            }
        },
    )

# Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()
    
    # We will grab user_id and document_id from scope/state if they exist in later endpoints
    logger.info(f"Incoming Request | ID: {request_id} | {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request failed | ID: {request_id} | Error: {str(e)}")
        raise e
    
    process_time = (time.time() - start_time) * 1000
    logger.info(f"Completed Request | ID: {request_id} | Status: {response.status_code} | Latency: {process_time:.2f}ms")
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.PROJECT_NAME}...")

# Health Endpoints
@app.get("/health", tags=["Health"])
@app.get("/ready", tags=["Health"])
async def health_check():
    """
    Comprehensive health check. 
    In the future, this will ping PostgreSQL, Redis, and Qdrant.
    """
    # TODO: Add actual connection checks
    return {
        "status": "ok", 
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }

# We will include routers here
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["documents"])
app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["search"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
