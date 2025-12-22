# rthook-scipy.py
# Runtime hook to pre-import scipy modules before they're needed
# This fixes the "NameError: name 'obj' is not defined" issue in 
# scipy.stats._distn_infrastructure when using PyInstaller

import os
import sys

# Force import scipy.stats early to avoid lazy loading issues
try:
    import scipy
    import scipy.stats
    import scipy.stats._distn_infrastructure
    import scipy.stats.distributions
    import scipy.stats._stats_py
    import scipy.special
    import scipy.linalg
except Exception as e:
    print(f"Warning: Could not pre-import scipy: {e}")

# Also pre-import sklearn
try:
    import sklearn
    import sklearn.utils
    import sklearn.utils.validation
    import sklearn.utils._param_validation
    import sklearn.utils.fixes
    import sklearn.base
    import sklearn.ensemble
    import sklearn.preprocessing
except Exception as e:
    print(f"Warning: Could not pre-import sklearn: {e}")

# Pre-import xgboost
try:
    import xgboost
except Exception as e:
    print(f"Warning: Could not pre-import xgboost: {e}")
