"""
NexusTrade Windows Connector
Main entry point for the desktop application
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime
from loguru import logger
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

# Configure logging FIRST
log_dir = Path("./logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"nexustrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logger.add(
    log_file,
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

logger.info("=" * 80)
logger.info("NexusTrade Connector Starting...")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Log file: {log_file}")
logger.info("=" * 80)

# Import modules
try:
    from core.config import Config
    from ui.login_window import LoginWindow
    from ui.main_window import MainWindow
    from api.server import start_api_server
    logger.info("✓ Modules imported successfully")
except Exception as e:
    logger.critical(f"✗ Failed to import modules: {e}", exc_info=True)
    print(f"CRITICAL ERROR: Failed to import modules: {e}")
    print(f"Check log file: {log_file}")
    sys.exit(1)


def show_error_dialog(title: str, message: str, details: str = ""):
    """Show error dialog to user"""
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setDetailedText(details)
        msg.exec()
    except Exception as e:
        logger.error(f"Failed to show error dialog: {e}")
        print(f"ERROR: {title} - {message}")


def exception_hook(exctype, value, tb):
    """Global exception handler"""
    import traceback
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    logger.critical(f"Unhandled exception:\n{error_msg}")
    show_error_dialog(
        "Fatal Error",
        f"An unexpected error occurred:\n{exctype.__name__}: {value}",
        error_msg
    )
    sys.__excepthook__(exctype, value, tb)


async def main():
    """Main application entry point"""
    try:
        logger.info("Initializing application...")

        # Set global exception hook
        sys.excepthook = exception_hook

        # ============================================
        # HIGH-DPI SCALING CONFIGURATION
        # ============================================
        # Enable high-DPI scaling BEFORE creating QApplication
        # This ensures proper scaling on 4K, retina, and high-DPI displays
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

        # Create QApplication
        logger.info("Creating QApplication...")
        app = QApplication(sys.argv)
        app.setApplicationName("NexusTrade")

        # Set high-DPI pixmap policy for crisp icons and images
        app.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        logger.info("✓ QApplication created with High-DPI support")
        
        # Load configuration
        logger.info("Loading configuration...")
        try:
            config = Config()
            logger.info("✓ Configuration loaded successfully")
        except ValueError as e:
            # Config validation error (missing Supabase credentials)
            logger.error(f"Configuration validation failed: {e}")
            show_error_dialog(
                "Configuration Error",
                "Supabase credentials are missing!",
                str(e)
            )
            return 1
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}", exc_info=True)
            show_error_dialog(
                "Configuration Error",
                "Failed to load configuration!",
                str(e)
            )
            return 1

        # Show login window FIRST for fast startup
        logger.info("Creating login window...")
        try:
            login_window = LoginWindow(config.supabase.url, config.supabase.anon_key)
            logger.info("✓ Login window created")
        except Exception as e:
            logger.error(f"Failed to create login window: {e}", exc_info=True)
            show_error_dialog(
                "Login Window Error",
                "Failed to create login window!",
                str(e)
            )
            return 1

        user_data = {}

        # Handle successful login
        def on_login_success(data):
            nonlocal user_data
            user_data = data
            logger.info(f"User logged in: {data.get('email', 'unknown')}")

        login_window.login_successful.connect(on_login_success)
        login_window.show()
        logger.info("✓ Login window displayed")

        # PERFORMANCE: Start API server in background AFTER login window is shown
        # This allows user to start logging in while API server initializes
        logger.info("Starting API server in background...")
        try:
            api_task = asyncio.create_task(start_api_server(config))
            logger.info(f"✓ API server starting on port {config.api_server.port}")
        except Exception as e:
            logger.error(f"Failed to start API server: {e}", exc_info=True)
            # Continue anyway - API server is not critical

        # Wait for login window to close
        while login_window.isVisible():
            app.processEvents()
            await asyncio.sleep(0.1)
        
        # Check if login was successful
        if not user_data:
            logger.info("Login cancelled by user")
            return 0
        
        # Create and show main window
        logger.info("Creating main window...")
        try:
            window = MainWindow(config, user_data)
            window.show()
            logger.info("✓ Main window displayed")
        except Exception as e:
            logger.error(f"Failed to create main window: {e}", exc_info=True)
            show_error_dialog(
                "Main Window Error",
                "Failed to create main window!",
                str(e)
            )
            return 1
        
        # Run application
        logger.info("Starting event loop...")
        exit_code = app.exec()
        
        # Cleanup
        if 'api_task' in locals():
            api_task.cancel()
        
        logger.info(f"Application exited with code: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.critical(f"Fatal error in main(): {e}", exc_info=True)
        show_error_dialog(
            "Fatal Error",
            "A critical error occurred!",
            str(e)
        )
        return 1


if __name__ == "__main__":
    try:
        logger.info("Application starting from __main__")
        exit_code = asyncio.run(main())
        logger.info(f"Application finished with exit code: {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error in __main__: {e}", exc_info=True)
        print(f"\n{'='*80}")
        print(f"FATAL ERROR: {e}")
        print(f"Check log file: {log_file}")
        print(f"{'='*80}\n")
        sys.exit(1)
