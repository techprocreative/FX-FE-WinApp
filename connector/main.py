"""
NexusTrade Windows Connector
Main entry point for the desktop application
"""

import sys
import asyncio
from loguru import logger
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from core.config import Config
from ui.main_window import MainWindow
from api.server import start_api_server

# Configure logging
logger.add(
    "logs/nexustrade_{time}.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG"
)


def setup_exception_handler():
    """Setup global exception handler"""
    def exception_hook(exctype, value, traceback):
        logger.exception(f"Uncaught exception: {value}")
        sys.__excepthook__(exctype, value, traceback)
    
    sys.excepthook = exception_hook


async def main():
    """Main application entry point"""
    logger.info("Starting NexusTrade Windows Connector...")
    
    # Load configuration
    config = Config()
    logger.info(f"Configuration loaded from {config.config_path}")
    
    # Setup exception handler
    setup_exception_handler()
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("NexusTrade")
    app.setOrganizationName("NexusTrade")
    app.setApplicationVersion("1.0.0")
    
    # Enable high DPI scaling
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create main window
    window = MainWindow(config)
    window.show()
    
    # Start API server in background
    api_task = asyncio.create_task(start_api_server(config))
    logger.info("Local API server started")
    
    # Run application
    exit_code = app.exec()
    
    # Cleanup
    api_task.cancel()
    logger.info("Application closed")
    
    return exit_code


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
