#!/usr/bin/env python3
"""
Test script for modern component base classes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt
from ui.components.modern_base import ModernCard, ModernButton, ModernInput


class TestWindow(QMainWindow):
    """Test window to showcase modern components"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Components Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Test ModernCard
        self.test_modern_cards(layout)
        
        # Test ModernButton
        self.test_modern_buttons(layout)
        
        # Test ModernInput
        self.test_modern_inputs(layout)
        
    def test_modern_cards(self, layout):
        """Test ModernCard components"""
        layout.addWidget(QLabel("Modern Cards:"))
        
        cards_layout = QHBoxLayout()
        
        # Default card
        card1 = ModernCard(preset="default", clickable=True)
        card1_layout = QVBoxLayout(card1)
        card1_layout.addWidget(QLabel("Default Card"))
        card1_layout.addWidget(QLabel("Clickable with hover effects"))
        cards_layout.addWidget(card1)
        
        # Strong card
        card2 = ModernCard(preset="strong")
        card2_layout = QVBoxLayout(card2)
        card2_layout.addWidget(QLabel("Strong Card"))
        card2_layout.addWidget(QLabel("More prominent glass effect"))
        cards_layout.addWidget(card2)
        
        # Subtle card
        card3 = ModernCard(preset="subtle")
        card3_layout = QVBoxLayout(card3)
        card3_layout.addWidget(QLabel("Subtle Card"))
        card3_layout.addWidget(QLabel("Minimal glass effect"))
        cards_layout.addWidget(card3)
        
        layout.addLayout(cards_layout)
        
    def test_modern_buttons(self, layout):
        """Test ModernButton components"""
        layout.addWidget(QLabel("Modern Buttons:"))
        
        buttons_layout = QHBoxLayout()
        
        # Primary button
        btn1 = ModernButton("Primary", variant="primary", icon="🚀")
        buttons_layout.addWidget(btn1)
        
        # Secondary button
        btn2 = ModernButton("Secondary", variant="secondary", icon="⚙️")
        buttons_layout.addWidget(btn2)
        
        # Danger button
        btn3 = ModernButton("Danger", variant="danger", icon="⚠️")
        buttons_layout.addWidget(btn3)
        
        # Ghost button
        btn4 = ModernButton("Ghost", variant="ghost", icon="👻")
        buttons_layout.addWidget(btn4)
        
        # Loading button
        btn5 = ModernButton("Loading", variant="primary")
        btn5.set_loading(True)
        buttons_layout.addWidget(btn5)
        
        layout.addLayout(buttons_layout)
        
    def test_modern_inputs(self, layout):
        """Test ModernInput components"""
        layout.addWidget(QLabel("Modern Inputs:"))
        
        inputs_layout = QVBoxLayout()
        
        # Default input
        input1 = ModernInput(
            placeholder="Enter your name",
            label="Name",
            helper_text="This is a default input field"
        )
        inputs_layout.addWidget(input1)
        
        # Success input
        input2 = ModernInput(
            placeholder="Valid email",
            label="Email",
            validation_state="success",
            helper_text="Email format is valid"
        )
        input2.setText("user@example.com")
        inputs_layout.addWidget(input2)
        
        # Error input
        input3 = ModernInput(
            placeholder="Password",
            label="Password",
            validation_state="error",
            helper_text="Password must be at least 8 characters"
        )
        inputs_layout.addWidget(input3)
        
        # Input with icons
        input4 = ModernInput(
            placeholder="Search...",
            prefix_icon="🔍",
            suffix_icon="✨"
        )
        inputs_layout.addWidget(input4)
        
        layout.addLayout(inputs_layout)


def main():
    """Main function to run the test"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show test window
    window = TestWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()