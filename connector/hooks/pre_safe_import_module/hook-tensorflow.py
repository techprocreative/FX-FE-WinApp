# -*- coding: utf-8 -*-
"""
Pre-safe-import-module hook for tensorflow
Overrides the default pyinstaller-hooks-contrib hook
that causes conflicts when TensorFlow is excluded.
"""

def pre_safe_import_module(api):
    """
    Empty hook - prevents the default TensorFlow hook from running.
    We explicitly exclude TensorFlow from the build, so no aliasing needed.
    """
    pass
