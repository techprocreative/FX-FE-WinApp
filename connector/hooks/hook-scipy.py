# hook-scipy.py
# PyInstaller hook to fix scipy.stats import issues

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all scipy submodules to ensure nothing is missed
hiddenimports = collect_submodules('scipy')

# Also collect data files that scipy needs
datas = collect_data_files('scipy')
