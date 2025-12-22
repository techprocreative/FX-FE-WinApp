# hook-scipy.stats.py
# Fix scipy.stats._distn_infrastructure runtime import issues

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('scipy.stats')
