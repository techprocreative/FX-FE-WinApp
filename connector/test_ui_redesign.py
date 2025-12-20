"""
Test UI Redesign Integration
Verifies all new components work together correctly
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Test component imports
def test_imports():
    """Test all new components can be imported"""
    print("Testing component imports...")

    try:
        from ui.components.stat_card import StatCard
        print("✓ StatCard imported successfully")
    except Exception as e:
        print(f"✗ StatCard import failed: {e}")
        return False

    try:
        from ui.components.model_card import ModelCard
        print("✓ ModelCard imported successfully")
    except Exception as e:
        print(f"✗ ModelCard import failed: {e}")
        return False

    try:
        from ui.components.signal_card import SignalCard
        print("✓ SignalCard imported successfully")
    except Exception as e:
        print(f"✗ SignalCard import failed: {e}")
        return False

    try:
        from ui.components.trading_statistics import TradingStatistics
        print("✓ TradingStatistics imported successfully")
    except Exception as e:
        print(f"✗ TradingStatistics import failed: {e}")
        return False

    return True


def test_stat_card():
    """Test StatCard instantiation and methods"""
    print("\nTesting StatCard...")

    try:
        from ui.components.stat_card import StatCard

        # Create card
        card = StatCard("📊", "TEST STAT", "100", "+10", True)
        print("✓ StatCard created successfully")

        # Test update
        card.update_value("150", "+50", True)
        print("✓ StatCard update_value works")

        return True
    except Exception as e:
        print(f"✗ StatCard test failed: {e}")
        return False


def test_model_card():
    """Test ModelCard with sample data"""
    print("\nTesting ModelCard...")

    try:
        from ui.components.model_card import ModelCard

        # Sample model data
        model_info = {
            'model_id': 'test-model-123',
            'name': 'Test BTCUSD Model',
            'symbol': 'BTCUSD',
            'accuracy': 0.87,
            'created_at': '2025-01-15T10:30:00Z',
            'file_size': 524288,
            'is_active': False
        }

        # Create card
        card = ModelCard(model_info)
        print("✓ ModelCard created successfully")

        # Test active status update
        card.set_active_status(True)
        print("✓ ModelCard set_active_status works")

        return True
    except Exception as e:
        print(f"✗ ModelCard test failed: {e}")
        return False


def test_signal_card():
    """Test SignalCard with sample data"""
    print("\nTesting SignalCard...")

    try:
        from ui.components.signal_card import SignalCard

        # Create card
        card = SignalCard("BTCUSD")
        print("✓ SignalCard created successfully")

        # Test model loaded
        card.set_model_loaded("btcusd_hybrid", 0.85)
        print("✓ SignalCard set_model_loaded works")

        # Test signal update
        card.update_signal("buy", 0.75)
        print("✓ SignalCard update_signal works")

        # Test stats update
        card.update_statistics(65.5, 10)
        print("✓ SignalCard update_statistics works")

        return True
    except Exception as e:
        print(f"✗ SignalCard test failed: {e}")
        return False


def test_trading_statistics():
    """Test TradingStatistics aggregator"""
    print("\nTesting TradingStatistics...")

    try:
        from ui.components.trading_statistics import TradingStatistics
        from PyQt6.QtCore import QObject

        # Create stats aggregator
        stats = TradingStatistics()
        print("✓ TradingStatistics created successfully")

        # Test signal recording
        stats.record_signal("BTCUSD", "buy", 0.75)
        print("✓ TradingStatistics record_signal works")

        # Test trade recording
        trade_info = {'ticket': 123456, 'volume': 0.01}
        stats.record_trade("BTCUSD", "buy", trade_info)
        print("✓ TradingStatistics record_trade works")

        # Test trade close
        stats.record_trade_close("BTCUSD", 15.50)
        print("✓ TradingStatistics record_trade_close works")

        # Get stats
        overall = stats.get_overall_stats()
        print(f"✓ Overall stats retrieved: {overall['total_trades']} trades, {overall['win_rate']:.1f}% win rate")

        symbol_stats = stats.get_symbol_stats("BTCUSD")
        if symbol_stats:
            print(f"✓ Symbol stats retrieved: {symbol_stats['total_trades']} trades")

        return True
    except Exception as e:
        print(f"✗ TradingStatistics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_design_tokens():
    """Test DesignTokens responsive sizing"""
    print("\nTesting DesignTokens...")

    try:
        from ui.design_system import DesignTokens as DT

        # Test screen size
        screen_w, screen_h = DT.get_screen_size()
        print(f"✓ Screen size: {screen_w}x{screen_h}")

        # Test responsive window size
        window_w, window_h = DT.get_responsive_window_size()
        print(f"✓ Responsive window size: {window_w}x{window_h}")

        # Verify it's within bounds
        assert 1200 <= window_w <= 1920, "Width out of bounds"
        assert 700 <= window_h <= 1200, "Height out of bounds"
        print("✓ Window size within valid bounds")

        return True
    except Exception as e:
        print(f"✗ DesignTokens test failed: {e}")
        return False


def test_main_window_enhancements():
    """Test MainWindow has all new features"""
    print("\nTesting MainWindow enhancements...")

    try:
        from ui.main_window import MainWindow, AutoTraderThread

        # Check AutoTraderThread has new signal
        signals = [attr for attr in dir(AutoTraderThread) if 'signal' in attr.lower()]
        print(f"✓ AutoTraderThread signals: {signals}")

        # Verify trade_closed signal exists
        assert hasattr(AutoTraderThread, 'trade_closed'), "trade_closed signal missing"
        print("✓ AutoTraderThread.trade_closed signal exists")

        # Check MainWindow has new methods
        methods = [
            '_on_trade_close',
            '_auto_load_models',
            '_ensure_ml_loaded',
            '_ensure_supabase_loaded'
        ]

        for method in methods:
            assert hasattr(MainWindow, method), f"Method {method} missing"
            print(f"✓ MainWindow.{method} exists")

        return True
    except Exception as e:
        print(f"✗ MainWindow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("UI REDESIGN INTEGRATION TEST SUITE")
    print("=" * 60)

    # Initialize QApplication for Qt widgets
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Enable High-DPI
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    results = []

    # Run tests
    results.append(("Component Imports", test_imports()))
    results.append(("DesignTokens", test_design_tokens()))
    results.append(("StatCard", test_stat_card()))
    results.append(("ModelCard", test_model_card()))
    results.append(("SignalCard", test_signal_card()))
    results.append(("TradingStatistics", test_trading_statistics()))
    results.append(("MainWindow Enhancements", test_main_window_enhancements()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} | {name}")

    print("-" * 60)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! UI Redesign is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
