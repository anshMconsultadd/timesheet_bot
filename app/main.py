from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import slack_router
from app.database import init_db
from app.utils.scheduler import TaskScheduler
from app.utils.logging_config import setup_logging, get_log_files_info
from app.config import get_settings
import logging
# from app.routers import slack_router_demo

# Setup comprehensive logging
logs_dir = setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()
scheduler = TaskScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Slack Timesheet Bot...")
    init_db()
    scheduler.start()
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    scheduler.stop()
    logger.info("Application stopped")


app = FastAPI(
    title="Slack Timesheet Bot",
    description="A Slack bot for managing timesheets",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(slack_router.router)

# app.include_router(slack_router_demo.router)


@app.get("/")
async def root():
    return {
        "message": "Slack Timesheet Bot API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "scheduler": "running"
    }


@app.get("/logs/info")
async def logs_info():
    """Get information about current log files."""
    return {
        "logs_directory": str(logs_dir.absolute()),
        "log_files": get_log_files_info()
    }

