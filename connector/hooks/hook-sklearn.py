# hook-sklearn.py
# PyInstaller hook to fix sklearn import issues

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all sklearn submodules
hiddenimports = collect_submodules('sklearn')

# Collect data files
datas = collect_data_files('sklearn')
