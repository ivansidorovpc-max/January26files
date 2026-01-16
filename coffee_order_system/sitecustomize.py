from __future__ import annotations

import os
import sys


PROJECT_ROOT = os.path.dirname(__file__)
PYCACHE_DIR = os.path.join(PROJECT_ROOT, ".pycache")

os.makedirs(PYCACHE_DIR, exist_ok=True)
if hasattr(sys, "pycache_prefix"):
    sys.pycache_prefix = PYCACHE_DIR
else:
    sys.dont_write_bytecode = True
