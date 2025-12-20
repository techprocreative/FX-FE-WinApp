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
    
    # Show login window first
    from ui.login_window import LoginWindow
    
    login_window = LoginWindow(
        config.supabase.url,
        config.supabase.anon_key
    )
    
    user_data = {}
    
    def on_login_success(data):
        nonlocal user_data
        user_data = data
        logger.info(f"User logged in: {data['email']}")
    
    login_window.login_successful.connect(on_login_success)
    login_window.show()
    
    # Wait for login window to close
    while login_window.isVisible():
        app.processEvents()
        await asyncio.sleep(0.1)
    
    # Check if login was successful
    if not user_data:
        logger.info("Login cancelled by user")
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
