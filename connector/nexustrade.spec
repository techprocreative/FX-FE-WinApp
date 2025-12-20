# -*- mode: python ; coding: utf-8 -*-
"""
NexusTrade Windows Connector - PyInstaller Spec File
Build command: pyinstaller nexustrade.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Get the project root
project_root = Path('.').resolve()

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include only essential modules (not training scripts)
        ('core/*.py', 'core'),
        ('api/*.py', 'api'),
        ('security/*.py', 'security'),
        ('trading/*.py', 'trading'),
        ('ui/*.py', 'ui'),
        # NOTE: ai/*.py training scripts excluded - not needed at runtime
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        # FastAPI
        'fastapi',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'pydantic',
        # ML (XGBoost only - TensorFlow removed for faster startup)
        'sklearn',
        'sklearn.ensemble',
        'sklearn.preprocessing',
        'xgboost',
        'numpy',
        'pandas',
        'joblib',
        # Supabase
        'supabase',
        'httpx',
        # OpenAI (for LLM integration)
        'openai',
        'openai.types',
        # Crypto
        'cryptography',
        'cryptography.fernet',
        # MT5
        'MetaTrader5',
        # Logging
        'loguru',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Heavy unused libraries
        'tensorflow',
        'tensorflow.keras',
        'keras',
        # UI libraries not needed
        'matplotlib',
        'tkinter',
        'PIL',
        # Development tools
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'sphinx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NexusTrade',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if Path('assets/icon.ico').exists() else None,
    version='version_info.txt' if Path('version_info.txt').exists() else None,
)
