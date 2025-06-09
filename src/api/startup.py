"""
Startup configuration and initialization for Routiq Backend API
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from various sources"""
    
    # Try to load from .env file if it exists
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment from {env_path}")
    
    # Try to load from config/env.example as fallback for development
    env_example_path = Path(__file__).parent.parent.parent / 'config' / 'env.example'
    if env_example_path.exists() and not os.getenv('DATABASE_URL'):
        logger.warning("No .env file found, some environment variables may be missing")
    
    # Validate required environment variables
    required_vars = [
        'DATABASE_URL',
        'CLERK_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.info("Application will start but some features may not work correctly")
    
    logger.info("Environment configuration loaded successfully")

def configure_logging():
    """Configure application logging"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', 'standard')
    
    if log_format == 'json':
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
        )
    else:
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    logger.info(f"Logging configured - Level: {log_level}, Format: {log_format}")

def initialize():
    """Initialize the application"""
    logger.info("Starting Routiq Backend API initialization")
    
    # Load environment configuration
    load_environment()
    
    # Configure logging
    configure_logging()
    
    # Log startup information
    logger.info(f"App Environment: {os.getenv('APP_ENV', 'production')}")
    logger.info(f"Python Path: {os.getenv('PYTHONPATH', 'not set')}")
    logger.info(f"Port: {os.getenv('PORT', '8000')}")
    
    logger.info("Routiq Backend API initialization complete") 