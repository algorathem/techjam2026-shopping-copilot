#!/usr/bin/env python3
"""Back-compat wrapper → build_st_cache.py --backend minilm."""
import runpy
import sys
sys.argv = ["build_st_cache.py", "--backend", "minilm"]
runpy.run_path("scripts/build_st_cache.py", run_name="__main__")
