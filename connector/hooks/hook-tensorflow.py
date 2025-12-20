# -*- coding: utf-8 -*-
"""
Hook for TensorFlow - marks as excluded
This overrides the default pyinstaller-hooks-contrib hook
"""

# Empty hook - TensorFlow is explicitly excluded from build
hiddenimports = []
excludedimports = ['tensorflow', 'keras']
datas = []
binaries = []
