"""
NexusTrade Login Window
Login screen for Windows connector using Supabase authentication
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QLinearGradient, QBrush, QPalette, QColor
from supabase import create_client, Client
from loguru import logger

from ui.design_system import DesignTokens as DT, StyleSheets


class LoginWindow(QWidget):
    """Login window for Supabase authentication"""

    login_successful = pyqtSignal(dict)  # Emits user data on successful login

    def __init__(self, supabase_url: str, supabase_key: str):
        super().__init__()
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self._setup_ui()

    def _setup_ui(self):
        """Setup the login UI with design system"""
        self.setWindowTitle("NexusTrade - Login")
        self.setFixedSize(DT.LOGIN_WIDTH, DT.LOGIN_HEIGHT)

        # Apply window background gradient
        self._apply_window_gradient()

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(DT.SPACE_4XL, DT.SPACE_4XL, DT.SPACE_4XL, DT.SPACE_4XL)
        layout.setSpacing(DT.SPACE_LG)

        # Logo with proper gradient using QPalette
        logo = QLabel("⚡ NexusTrade")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_font = QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_5XL, DT.WEIGHT_BLACK)
        logo.setFont(logo_font)

        # Create gradient for logo text
        gradient = QLinearGradient(0, 0, 1, 0)
        gradient.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
        gradient.setColorAt(0, QColor(DT.PRIMARY))
        gradient.setColorAt(1, QColor(DT.SECONDARY))

        palette = logo.palette()
        palette.setBrush(QPalette.ColorRole.WindowText, QBrush(gradient))
        logo.setPalette(palette)

        layout.addWidget(logo)

        # Subtitle
        subtitle = QLabel("Windows Connector")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            color: {DT.TEXT_DISABLED};
            font-size: {DT.FONT_BASE}px;
            font-family: {DT.FONT_FAMILY};
        """)
        layout.addWidget(subtitle)

        layout.addSpacing(DT.SPACE_2XL)

        # Card container - glassmorphism
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                {StyleSheets.glass_card()}
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(DT.SPACE_2XL, DT.SPACE_2XL, DT.SPACE_2XL, DT.SPACE_2XL)
        card_layout.setSpacing(DT.SPACE_LG)

        # Email field
        email_label = QLabel("Email")
        email_label.setStyleSheet(f"""
            color: {DT.TEXT_SECONDARY};
            font-weight: {DT.WEIGHT_SEMIBOLD};
            font-size: {DT.FONT_SM}px;
            font-family: {DT.FONT_FAMILY};
        """)
        card_layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        self.email_input.setFixedHeight(DT.INPUT_HEIGHT)
        self.email_input.returnPressed.connect(self._handle_login)
        self.email_input.setStyleSheet(f"""
            QLineEdit {{
                {StyleSheets.input_field()}
            }}
            QLineEdit:focus {{
                border: 2px solid {DT.BORDER_FOCUS};
                background: {DT.GLASS_DARKEST};
            }}
            QLineEdit::placeholder {{
                color: {DT.TEXT_PLACEHOLDER};
            }}
        """)
        card_layout.addWidget(self.email_input)

        card_layout.addSpacing(DT.SPACE_SM)

        # Password field
        password_label = QLabel("Password")
        password_label.setStyleSheet(f"""
            color: {DT.TEXT_SECONDARY};
            font-weight: {DT.WEIGHT_SEMIBOLD};
            font-size: {DT.FONT_SM}px;
            font-family: {DT.FONT_FAMILY};
        """)
        card_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(DT.INPUT_HEIGHT)
        self.password_input.returnPressed.connect(self._handle_login)
        self.password_input.setStyleSheet(f"""
            QLineEdit {{
                {StyleSheets.input_field()}
            }}
            QLineEdit:focus {{
                border: 2px solid {DT.BORDER_FOCUS};
                background: {DT.GLASS_DARKEST};
            }}
            QLineEdit::placeholder {{
                color: {DT.TEXT_PLACEHOLDER};
            }}
        """)
        card_layout.addWidget(self.password_input)

        card_layout.addSpacing(DT.SPACE_BASE)

        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.setFixedHeight(DT.BUTTON_HEIGHT_LG)
        self.login_btn.clicked.connect(self._handle_login)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet(StyleSheets.primary_button())
        card_layout.addWidget(self.login_btn)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet(f"""
            color: {DT.DANGER};
            font-size: {DT.FONT_SM}px;
            font-family: {DT.FONT_FAMILY};
            padding: {DT.SPACE_MD}px;
            background: rgba(244, 63, 94, 0.1);
            border: 1px solid rgba(244, 63, 94, 0.3);
            border-radius: {DT.RADIUS_MD}px;
        """)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)

        layout.addWidget(card)

        # Info text
        info = QLabel("Use the same account as the web dashboard")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet(f"""
            color: {DT.TEXT_DISABLED};
            font-size: {DT.FONT_SM}px;
            font-family: {DT.FONT_FAMILY};
        """)
        layout.addWidget(info)

        layout.addStretch()

    def _apply_window_gradient(self):
        """Apply gradient background to window"""
        self.setStyleSheet(f"""
            QWidget {{
                background: {StyleSheets.gradient_background()};
                font-family: {DT.FONT_FAMILY};
            }}
        """)

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
