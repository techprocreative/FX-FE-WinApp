# -*- coding: utf-8 -*-
"""
Custom hook to completely exclude TensorFlow/Keras
This overrides the default pyinstaller-hooks-contrib hook
"""

# Empty hook - do nothing
# This prevents the default TensorFlow hook from running

def pre_safe_import_module(api):
    """Do nothing - we explicitly exclude TensorFlow"""
    pass
