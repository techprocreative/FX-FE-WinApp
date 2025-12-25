#!/usr/bin/env python3
"""
Validation script for the Enhanced Animation System
Tests core functionality without requiring PyQt6 GUI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_animation_imports():
    """Test that all animation modules can be imported"""
    try:
        from ui.animation_system import (
            AnimationConfig, AnimationManager, AnimationUtils,
            HoverAnimator, LoadingAnimator, PageTransitionAnimator,
            MicroInteractionAnimator, animation_manager
        )
        print("✓ Animation system imports successful")
        return True
    except ImportError as e:
        print(f"✗ Animation system import failed: {e}")
        return False

def test_page_transitions_imports():
    """Test that page transition modules can be imported"""
    try:
        from ui.page_transitions import (
            ModernStackedWidget, PageManager, LoadingOverlay,
            create_page_manager, setup_smooth_transitions
        )
        print("✓ Page transitions imports successful")
        return True
    except ImportError as e:
        print(f"✗ Page transitions import failed: {e}")
        return False

def test_loading_states_imports():
    """Test that loading states modules can be imported"""
    try:
        from ui.loading_states import (
            LoadingSpinner, LoadingDots, LoadingProgressBar,
            LoadingCard, LoadingStateManager, loading_manager
        )
        print("✓ Loading states imports successful")
        return True
    except ImportError as e:
        print(f"✗ Loading states import failed: {e}")
        return False

def test_design_system_integration():
    """Test that design system integration works"""
    try:
        from ui.design_system import DesignTokens as DT
        
        # Test that animation timing constants are available
        assert hasattr(DT, 'DURATION_FAST')
        assert hasattr(DT, 'DURATION_NORMAL')
        assert hasattr(DT, 'DURATION_SLOW')
        assert hasattr(DT, 'EASE_OUT_CUBIC')
        assert hasattr(DT, 'EASE_IN_OUT_BACK')
        
        print("✓ Design system integration successful")
        return True
    except (ImportError, AssertionError) as e:
        print(f"✗ Design system integration failed: {e}")
        return False

def test_animation_config():
    """Test AnimationConfig functionality"""
    try:
        from ui.animation_system import AnimationConfig
        from ui.design_system import DesignTokens as DT
        
        # Test default config
        config = AnimationConfig()
        assert config.duration == DT.DURATION_NORMAL
        assert config.easing == DT.EASE_OUT_CUBIC
        assert config.delay == DT.DELAY_NONE
        
        # Test custom config
        custom_config = AnimationConfig(
            duration=500,
            easing=DT.EASE_IN_OUT_BACK,
            delay=100
        )
        assert custom_config.duration == 500
        assert custom_config.easing == DT.EASE_IN_OUT_BACK
        assert custom_config.delay == 100
        
        print("✓ AnimationConfig functionality successful")
        return True
    except Exception as e:
        print(f"✗ AnimationConfig functionality failed: {e}")
        return False

def test_animation_manager():
    """Test AnimationManager functionality"""
    try:
        from ui.animation_system import AnimationManager, animation_manager
        
        # Test singleton instance
        assert animation_manager is not None
        assert isinstance(animation_manager, AnimationManager)
        
        # Test basic functionality
        assert hasattr(animation_manager, 'register_animation')
        assert hasattr(animation_manager, 'start_animation')
        assert hasattr(animation_manager, 'stop_animation')
        assert hasattr(animation_manager, 'set_performance_mode')
        
        print("✓ AnimationManager functionality successful")
        return True
    except Exception as e:
        print(f"✗ AnimationManager functionality failed: {e}")
        return False

def test_convenience_functions():
    """Test convenience functions are available"""
    try:
        from ui.animation_system import (
            animate_fade_in, animate_fade_out, animate_slide_in,
            animate_hover_effect, animate_button_press, animate_loading_state,
            animate_success_feedback, animate_error_feedback
        )
        
        # Test that functions are callable
        assert callable(animate_fade_in)
        assert callable(animate_fade_out)
        assert callable(animate_slide_in)
        assert callable(animate_hover_effect)
        assert callable(animate_button_press)
        assert callable(animate_loading_state)
        assert callable(animate_success_feedback)
        assert callable(animate_error_feedback)
        
        print("✓ Convenience functions available")
        return True
    except Exception as e:
        print(f"✗ Convenience functions failed: {e}")
        return False

def test_modern_base_integration():
    """Test that modern base components integrate with animation system"""
    try:
        from ui.components.modern_base import ModernCard, ModernButton, ModernInput
        
        # Test that classes can be imported (they would fail if animation imports failed)
        assert ModernCard is not None
        assert ModernButton is not None
        assert ModernInput is not None
        
        print("✓ Modern base components integration successful")
        return True
    except ImportError as e:
        print(f"✗ Modern base components integration failed: {e}")
        return False

def test_loading_manager():
    """Test LoadingStateManager functionality"""
    try:
        from ui.loading_states import LoadingStateManager, loading_manager
        
        # Test singleton instance
        assert loading_manager is not None
        assert isinstance(loading_manager, LoadingStateManager)
        
        # Test basic functionality
        assert hasattr(loading_manager, 'register_component')
        assert hasattr(loading_manager, 'start_loading')
        assert hasattr(loading_manager, 'stop_loading')
        assert hasattr(loading_manager, 'is_loading')
        
        print("✓ LoadingStateManager functionality successful")
        return True
    except Exception as e:
        print(f"✗ LoadingStateManager functionality failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("Validating Enhanced Animation System...")
    print("=" * 50)
    
    tests = [
        test_animation_imports,
        test_page_transitions_imports,
        test_loading_states_imports,
        test_design_system_integration,
        test_animation_config,
        test_animation_manager,
        test_convenience_functions,
        test_modern_base_integration,
        test_loading_manager,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All animation system validations passed!")
        return True
    else:
        print("❌ Some validations failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)