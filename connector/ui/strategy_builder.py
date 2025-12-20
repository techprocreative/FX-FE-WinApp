"""
Strategy Builder Tab
UI for creating custom trading strategies with LLM optimization
"""

import asyncio
import json
from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QComboBox, QProgressBar,
    QGroupBox, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from loguru import logger
import httpx


class StrategyGeneratorThread(QThread):
    """Background thread for API request"""
    success = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, api_url: str, user_data: dict, request_data: dict):
        super().__init__()
        self.api_url = api_url
        self.user_data = user_data
        self.request_data = request_data
    
    def run(self):
        try:
            async def make_request():
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.api_url}/api/optimize-strategy",
                        json=self.request_data,
                        headers={
                            "Authorization": f"Bearer {self.user_data['access_token']}",
                            "Content-Type": "application/json"
                        }
                    )
                    
                    if response.status_code == 403:
                        data = response.json()
                        self.error.emit(data.get('message', 'Quota exceeded'))
                        return
                    
                    if response.status_code != 200:
                        self.error.emit(f"API error: {response.status_code}")
                        return
                    
                    self.success.emit(response.json())
            
            asyncio.run(make_request())
            
        except Exception as e:
            logger.exception(f"Strategy generation error: {e}")
            self.error.emit(str(e))


class StrategyBuilderTab(QWidget):
    """Strategy Builder UI"""
    
    training_requested = pyqtSignal(dict, str, str)  # config, symbol, model_name
    
    def __init__(self, api_url: str, user_data: dict):
        super().__init__()
        self.api_url = api_url
        self.user_data = user_data
        self.current_config: Optional[Dict] = None
        self.generator_thread: Optional[StrategyGeneratorThread] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("AI Strategy Builder")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(header)
        
        subtitle = QLabel("Describe your trading strategy and let AI optimize it for you")
        subtitle.setStyleSheet("color: #6b7280; font-size: 13px;")
        layout.addWidget(subtitle)
        
        # Input Section
        input_group = QGroupBox("Strategy Description")
        input_layout = QVBoxLayout(input_group)
        
        # Description
        desc_label = QLabel("Describe your strategy:")
        input_layout.addWidget(desc_label)
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(
            "Example: I want a scalping strategy for XAUUSD using RSI oversold/overbought "
            "levels combined with MACD crossovers. Conservative risk management."
        )
        self.description_input.setMinimumHeight(120)
        input_layout.addWidget(self.description_input)
        
        # Parameters
        params_layout = QHBoxLayout()
        
        # Symbol
        symbol_layout = QVBoxLayout()
        symbol_label = QLabel("Symbol:")
        symbol_layout.addWidget(symbol_label)
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["XAUUSD", "BTCUSD", "EURUSD", "GBPUSD", "USDJPY"])
        symbol_layout.addWidget(self.symbol_combo)
        params_layout.addLayout(symbol_layout)
        
        # Timeframe
        tf_layout = QVBoxLayout()
        tf_label = QLabel("Timeframe:")
        tf_layout.addWidget(tf_label)
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["M1", "M5", "M15", "M30", "H1", "H4", "D1"])
        self.timeframe_combo.setCurrentText("M15")
        tf_layout.addWidget(self.timeframe_combo)
        params_layout.addLayout(tf_layout)
        
        # Risk Level
        risk_layout = QVBoxLayout()
        risk_label = QLabel("Risk Level:")
        risk_layout.addWidget(risk_label)
        self.risk_combo = QComboBox()
        self.risk_combo.addItems(["Low", "Medium", "High"])
        self.risk_combo.setCurrentText("Medium")
        risk_layout.addWidget(self.risk_combo)
        params_layout.addLayout(risk_layout)
        
        input_layout.addLayout(params_layout)
        
        # Generate Button
        self.generate_btn = QPushButton("🤖 Generate Strategy with AI")
        self.generate_btn.setMinimumHeight(45)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06b6d4, stop:1 #14b8a6);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0891b2, stop:1 #0d9488);
            }
            QPushButton:disabled {
                background: #94a3b8;
            }
        """)
        self.generate_btn.clicked.connect(self._generate_strategy)
        input_layout.addWidget(self.generate_btn)
        
        layout.addWidget(input_group)
        
        # Config Preview Section
        self.config_group = QGroupBox("AI-Generated Configuration")
        self.config_group.setVisible(False)
        config_layout = QVBoxLayout(self.config_group)
        
        # Scroll area for config
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(200)
        
        self.config_display = QLabel()
        self.config_display.setWordWrap(True)
        self.config_display.setTextFormat(Qt.TextFormat.RichText)
        self.config_display.setStyleSheet("padding: 10px; background: #f8fafc; border-radius: 6px;")
        scroll.setWidget(self.config_display)
        config_layout.addWidget(scroll)
        
        # Model Name Input
        name_layout = QHBoxLayout()
        name_label = QLabel("Model Name:")
        self.model_name_input = QTextEdit()
        self.model_name_input.setMaximumHeight(40)
        self.model_name_input.setPlaceholderText("e.g., xauusd_rsi_macd_scalping")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.model_name_input)
        config_layout.addLayout(name_layout)
        
        # Train Button
        self.train_btn = QPushButton("🚀 Start Training")
        self.train_btn.setMinimumHeight(45)
        self.train_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #059669);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #047857);
            }
        """)
        self.train_btn.clicked.connect(self._start_training)
        config_layout.addWidget(self.train_btn)
        
        layout.addWidget(self.config_group)
        
        # Progress Section
        self.progress_group = QGroupBox("Training Progress")
        self.progress_group.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(30)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Initializing...")
        self.progress_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(self.progress_group)
        
        layout.addStretch()
    
    def _generate_strategy(self):
        """Generate strategy using LLM"""
        description = self.description_input.toPlainText().strip()
        
        if not description:
            QMessageBox.warning(self, "Input Required", "Please describe your trading strategy")
            return
        
        # Disable UI
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("⏳ Generating...")
        
        # Prepare request
        request_data = {
            "description": description,
            "symbol": self.symbol_combo.currentText(),
            "timeframe": self.timeframe_combo.currentText(),
            "risk_level": self.risk_combo.currentText().lower(),
            "user_id": self.user_data['id']
        }
        
        # Start background thread
        self.generator_thread = StrategyGeneratorThread(
            self.api_url,
            self.user_data,
            request_data
        )
        self.generator_thread.success.connect(self._on_generation_success)
        self.generator_thread.error.connect(self._on_generation_error)
        self.generator_thread.start()
    
    def _on_generation_success(self, response: dict):
        """Handle successful generation"""
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("🤖 Generate Strategy with AI")
        
        self.current_config = response.get('training_config')
        quota_info = response.get('quota_info', {})
        
        # Display config
        config_html = self._format_config_html(self.current_config)
        self.config_display.setText(config_html)
        self.config_group.setVisible(True)
        
        # Auto-fill model name
        symbol = response.get('symbol', '').lower()
        features = '_'.join(self.current_config.get('features', [])[:2])
        self.model_name_input.setText(f"{symbol}_{features}_custom")
        
        # Show quota info if free tier
        if quota_info.get('tier') == 'free':
            used = quota_info.get('used', 0)
            limit = quota_info.get('limit', 10)
            QMessageBox.information(
                self,
                "Strategy Generated",
                f"Strategy configuration generated successfully!\n\n"
                f"AI Generations used: {used}/{limit} this month"
            )
    
    def _on_generation_error(self, error_msg: str):
        """Handle generation error"""
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("🤖 Generate Strategy with AI")
        
        if "quota exceeded" in error_msg.lower():
            QMessageBox.warning(
                self,
                "Quota Exceeded",
                f"{error_msg}\n\nUpgrade to Pro for unlimited AI strategy generations!"
            )
        else:
            QMessageBox.critical(
                self,
                "Generation Failed",
                f"Failed to generate strategy:\n{error_msg}"
            )
    
    def _format_config_html(self, config: dict) -> str:
        """Format config as HTML"""
        features = ", ".join(config.get('features', []))
        hyper = config.get('hyperparameters', {})
        risk = config.get('risk_config', {})
        reasoning = config.get('reasoning', '')
        
        html = f"""
        <div style="font-family: 'Segoe UI'; font-size: 13px;">
            <p><b>Features:</b> {features}</p>
            <p><b>Model Type:</b> {config.get('model_type', 'N/A')}</p>
            
            <p><b>Hyperparameters:</b></p>
            <ul>
                <li>GRU Units: {hyper.get('gru_units', 'N/A')}</li>
                <li>GRU Dropout: {hyper.get('gru_dropout', 'N/A')}</li>
                <li>XGB Max Depth: {hyper.get('xgb_max_depth', 'N/A')}</li>
                <li>XGB Learning Rate: {hyper.get('xgb_learning_rate', 'N/A')}</li>
                <li>Confidence Threshold: {hyper.get('confidence_threshold', 'N/A')}</li>
            </ul>
            
            <p><b>Risk Configuration:</b></p>
            <ul>
                <li>Stop Loss: {risk.get('sl_pips', 'N/A')} pips</li>
                <li>Take Profit: {risk.get('tp_pips', 'N/A')} pips</li>
                <li>Max Positions: {risk.get('max_positions', 'N/A')}</li>
                <li>Risk per Trade: {risk.get('risk_percent', 'N/A')}%</li>
            </ul>
            
            <p><b>AI Reasoning:</b><br/><i>{reasoning}</i></p>
        </div>
        """
        return html
    
    def _start_training(self):
        """Start model training"""
        model_name = self.model_name_input.toPlainText().strip()
        
        if not model_name:
            QMessageBox.warning(self, "Name Required", "Please enter a model name")
            return
        
        if not self.current_config:
            QMessageBox.warning(self, "No Configuration", "Please generate a strategy first")
            return
        
        # Emit signal to start training
        symbol = self.symbol_combo.currentText()
        self.training_requested.emit(self.current_config, symbol, model_name)
        
        # Show progress
        self.progress_group.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Training started...")
        
        # Disable train button
        self.train_btn.setEnabled(False)
    
    def update_progress(self, message: str, percent: int):
        """Update training progress"""
        self.progress_label.setText(message)
        self.progress_bar.setValue(percent)
        
        if percent >= 100:
            self.train_btn.setEnabled(True)
            QMessageBox.information(
                self,
                "Training Complete",
                f"Model training completed successfully!\n\n"
                f"The model is now ready for auto-trading."
            )
