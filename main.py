from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from middleware.rate_limiter import rate_limit_middleware
from utils.logging_config import logger

# Load environment variables
load_dotenv()

# Import models to ensure tables are created
from models.chat_models import create_tables

# Initialize the app
app = FastAPI(
    title=os.getenv("APP_TITLE", "Docusaurus RAG Chatbot"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="RAG Chatbot for Docusaurus-based book content",
    docs_url="/docs",  # Enable API documentation
    redoc_url="/redoc"  # Enable ReDoc documentation
)

# Create database tables on startup
@app.on_event("startup")
def startup_event():
    logger.info("Initializing database tables...")
    create_tables()
    logger.info("Database tables initialized successfully")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
@app.middleware("http")
async def add_rate_limiting(request, call_next):
    from config.app_config import app_config
    if app_config.rate_limit_enabled:
        await rate_limit_middleware(request)
    response = await call_next(request)
    return response

# Add logging middleware
@app.middleware("http")
async def add_logging(request, call_next):
    start_time = __import__('time').time()
    response = await call_next(request)
    process_time = __import__('time').time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s")
    return response

@app.get("/")
async def root():
    return {"message": "Docusaurus RAG Chatbot API"}

# Include API routes
from api import chat, search, ingest, health, selected_text
app.include_router(chat.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(selected_text.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)