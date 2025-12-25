#!/usr/bin/env python3
"""
Test script for enhanced trading components
Tests the modernized SignalCard, StatCard, and DashboardPage components
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout
from PyQt6.QtCore import QTimer
from ui.components.signal_card import SignalCard
from ui.components.stat_card import StatCard
from ui.pages.dashboard_page import DashboardPage
import random

class TestWindow(QMainWindow):
    """Test window for enhanced components"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Trading Components Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Test individual components
        components_layout = QHBoxLayout()
        
        # Test SignalCard
        self.signal_card = SignalCard("BTCUSD")
        self.signal_card.set_model_loaded("XGBoost_BTC_v2.1", 0.87)
        components_layout.addWidget(self.signal_card)
        
        # Test StatCard
        self.stat_card = StatCard("💰", "P&L TODAY", "$1,250.50", "+15.2%", True, "profit")
        components_layout.addWidget(self.stat_card)
        
        layout.addLayout(components_layout)
        
        # Test DashboardPage
        self.dashboard = DashboardPage()
        layout.addWidget(self.dashboard)
        
        # Setup test timer for dynamic updates
        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self.update_test_data)
        self.test_timer.start(3000)  # Update every 3 seconds
        
        print("✅ Enhanced trading components loaded successfully!")
        print("🔄 Starting dynamic test updates...")
        
    def update_test_data(self):
        """Update components with test data"""
        try:
            # Update signal card
            signals = ["buy", "sell", "hold"]
            signal = random.choice(signals)
            confidence = random.uniform(0.3, 0.95)
            timing_info = f"Generated {random.randint(1, 30)}s ago"
            
            self.signal_card.update_signal(signal, confidence, timing_info)
            
            # Update stat card
            profit = random.uniform(-500, 2000)
            trend = f"{random.uniform(-10, 20):+.1f}%"
            self.stat_card.update_value(f"${profit:+.2f}", trend, profit >= 0, animated=True)
            
            # Update dashboard statistics
            total_trades = random.randint(5, 50)
            win_rate = random.uniform(45, 85)
            total_profit = random.uniform(-1000, 5000)
            active_pos = random.randint(0, 8)
            
            self.dashboard.update_statistics(total_trades, win_rate, total_profit, active_pos)
            
            # Update account metrics
            balance = random.uniform(8000, 15000)
            equity = balance + random.uniform(-1000, 2000)
            margin = random.uniform(2000, 8000)
            drawdown = random.uniform(0, 15)
            
            self.dashboard.update_account_metrics(balance, equity, margin, drawdown)
            
            print(f"📊 Updated: Signal={signal.upper()}, Confidence={confidence:.1%}, P&L=${profit:+.2f}")
            
        except Exception as e:
            print(f"❌ Error updating test data: {e}")

def main():
    """Main test function"""
    print("🚀 Starting Enhanced Trading Components Test...")
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Enhanced Trading Components Test")
    app.setApplicationVersion("1.0")
    
    try:
        # Create and show test window
        window = TestWindow()
        window.show()
        
        print("✨ Test window displayed. Components should show enhanced features:")
        print("   • Real-time confidence meters with animations")
        print("   • Mini-charts with sparklines")
        print("   • Animated counters and trend arrows")
        print("   • Enhanced visual hierarchy and glass morphism")
        print("   • Hover effects and micro-interactions")
        print("\n🔄 Watch for dynamic updates every 3 seconds...")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return 1

if __name__ == "__main__":
    main()