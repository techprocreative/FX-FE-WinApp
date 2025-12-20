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
logger.info("=" * 80)
logger.info("NexusTrade Connector Starting...")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Log file: {log_file}")
logger.info("=" * 80)

try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt
    logger.info("✓ PyQt6 imported successfully")
except Exception as e:
    logger.critical(f"✗ Failed to import PyQt6: {e}")
    print(f"CRITICAL ERROR: Failed to import PyQt6: {e}")
    print(f"Check log file: {log_file}")
    sys.exit(1)

try:
    from core.config import Config
    from ui.login_window import LoginWindow
        return 0
    
    # Create main window with user data
    window = MainWindow(config, user_data)
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
