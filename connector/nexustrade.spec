# -*- mode: python ; coding: utf-8 -*-
"""
NexusTrade Windows Connector - PyInstaller Spec File
Build command: pyinstaller nexustrade.spec --clean --noconfirm

PyInstaller auto-detects Python imports from main.py.
Only non-Python assets need to be specified in datas.
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
    # Only include non-Python assets here
    # Python modules are auto-detected via imports
    datas=[
        # Assets (icons, etc) - add if they exist
        # ('assets', 'assets'),
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        # FastAPI & uvicorn
        'fastapi',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'pydantic',
        'pydantic_core',
        'pydantic._internal._core_utils',
        # ML libraries
        'sklearn',
        'sklearn.ensemble',
        'sklearn.ensemble._forest',
        'sklearn.preprocessing',
        'sklearn.preprocessing._data',
        'sklearn.model_selection',
        'sklearn.metrics',
        'sklearn.utils',
        'sklearn.utils._param_validation',
        'sklearn.utils.validation',
        'sklearn.utils._array_api',
        'sklearn.utils.fixes',
        'sklearn.base',
        'xgboost',
        'xgboost.core',
        'xgboost.compat',
        'numpy',
        'pandas',
        'joblib',
        # Scipy - required for sklearn
        'scipy',
        'scipy.stats',
        'scipy.stats._distn_infrastructure',
        'scipy.stats.distributions',
        'scipy.stats._stats_py',
        'scipy.special',
        'scipy.special._ufuncs',
        'scipy.linalg',
        'scipy.sparse',
        # Supabase & HTTP
        'supabase',
        'supabase._sync_client',
        'supabase._async_client',
        'gotrue',
        'gotrue._sync_client',
        'gotrue._async_client',
        'postgrest',
        'storage3',
        'realtime',
        'httpx',
        'httpcore',
        # OpenAI
        'openai',
        'openai.types',
        # Crypto
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.kdf.pbkdf2',
        'cryptography.hazmat.backends',
        # MT5
        'MetaTrader5',
        # Logging
        'loguru',
        # Our custom modules (explicit to ensure they're included)
        'core',
        'core.config',
        'core.mt5_client', 
        'core.supabase_sync',
        'api',
        'api.server',
        'api.subscription_checker',
        'api.llm_router',
        'security',
        'security.model_security',
        'trading',
        'trading.auto_trader',
        'ui',
        'ui.login_window',
        'ui.main_window',
        'ui.strategy_builder',
        'ai',
        'ai.model_trainer',
    ],
    # Use custom hooks directory (overrides problematic tensorflow hook)
    hookspath=['hooks'],
    hooksconfig={
        # Disable problematic TensorFlow/Keras hooks
        'gi': {
            'icons': [],
            'themes': [],
            'languages': [],
        },
    },
    runtime_hooks=['hooks/rthook-scipy.py'],
    excludes=[
        # Heavy unused libraries - Complete TensorFlow/Keras exclusion
        'tensorflow',
        'tensorflow.keras',
        'tensorflow.python',
        'tensorflow.core',
        'tensorflow.compiler',
        'tensorflow.lite',
        'keras',
        'keras._tf_keras',
        'keras._tf_keras.keras',
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
        'setuptools',
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
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if Path('assets/icon.ico').exists() else None,
    version='version_info.txt' if Path('version_info.txt').exists() else None,
)
