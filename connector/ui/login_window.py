"""
NexusTrade Login Window
Login screen for Windows connector using Supabase authentication
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from supabase import create_client, Client
from loguru import logger


class LoginWindow(QWidget):
    """Login window for Supabase authentication"""
    
    login_successful = pyqtSignal(dict)  # Emits user data on successful login
    
    def __init__(self, supabase_url: str, supabase_key: str):
        super().__init__()
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the login UI"""
        self.setWindowTitle("NexusTrade - Login")
        self.setFixedSize(450, 550)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f172a, stop:1 #1e3a8a
                );
                color: white;
                font-family: 'Segoe UI', Arial;
            }
            QLineEdit {
                background: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(6, 182, 212, 0.3);
                border-radius: 8px;
                padding: 12px 16px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #06b6d4;
            }
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06b6d4, stop:1 #14b8a6
                );
                border: none;
                border-radius: 8px;
                padding: 12px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0891b2, stop:1 #0d9488
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0e7490, stop:1 #0f766e
                );
            }
            QPushButton:disabled {
                background: rgba(6, 182, 212, 0.3);
            }
            QLabel {
                color: white;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Logo
        logo = QLabel("NexusTrade")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_font = QFont("Segoe UI", 32, QFont.Weight.Black)
        logo.setFont(logo_font)
        logo.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #06b6d4, stop:1 #14b8a6
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            color: transparent;
        """)
        layout.addWidget(logo)
        
        # Subtitle
        subtitle = QLabel("Windows Connector")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #94a3b8; font-size: 14px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Card container
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(6, 182, 212, 0.3);
                border-radius: 16px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)
        
        # Email field
        email_label = QLabel("Email")
        email_label.setStyleSheet("color: #e2e8f0; font-weight: 600; font-size: 13px;")
        card_layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        self.email_input.returnPressed.connect(self._handle_login)
        card_layout.addWidget(self.email_input)
        
        # Password field
        password_label = QLabel("Password")
        password_label.setStyleSheet("color: #e2e8f0; font-weight: 600; font-size: 13px;")
        card_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self._handle_login)
        card_layout.addWidget(self.password_input)
        
        card_layout.addSpacing(10)
        
        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self._handle_login)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        card_layout.addWidget(self.login_btn)
        
        # Error label
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("""
            color: #f43f5e;
            font-size: 12px;
            padding: 8px;
            background: rgba(244, 63, 94, 0.1);
            border: 1px solid rgba(244, 63, 94, 0.3);
            border-radius: 6px;
        """)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)
        
        layout.addWidget(card)
        
        # Info text
        info = QLabel("Use the same account as the web dashboard")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(info)
        
        layout.addStretch()
    
    def _handle_login(self):
        """Handle login button click"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            self._show_error("Please enter both email and password")
            return
        
        # Disable UI during login
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Logging in...")
        self.error_label.hide()
        
        try:
            # Authenticate with Supabase
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                logger.info(f"Login successful for user: {email}")
                user_data = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "access_token": response.session.access_token if response.session else None
                }
                self.login_successful.emit(user_data)
                self.close()
            else:
                self._show_error("Login failed. Please check your credentials.")
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            error_msg = str(e)
            if "Invalid login credentials" in error_msg:
                self._show_error("Invalid email or password")
            elif "Email not confirmed" in error_msg:
                self._show_error("Please confirm your email first")
            else:
                self._show_error("Login failed. Please try again.")
        
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Login")
    
    def _show_error(self, message: str):
        """Show error message"""
        self.error_label.setText(message)
        self.error_label.show()
