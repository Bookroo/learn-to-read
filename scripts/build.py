#!/usr/bin/env python3
"""Rebuild every generated curriculum doc from data/curriculum.json.

Runs, in order:
  1. build-module-order.py  -> MODULE_ORDER_PROPOSED.html
  2. availability.py --check (fails the build if a lesson example word
     is not readable at its own lesson)
  3. availability.py        -> WORD_BANK.html
  4. build-word-matrix.py   -> WORD_MATRIX.csv / WORD_MATRIX.html

Usage: python3 scripts/build.py
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ["build-module-order.py"],
    ["availability.py", "--check"],
    ["availability.py"],
    ["build-word-matrix.py"],
]

for step in STEPS:
    print(f"── {' '.join(step)}")
    r = subprocess.run([sys.executable, os.path.join(HERE, step[0])] + step[1:])
    if r.returncode != 0:
        sys.exit(r.returncode)
print("── all docs rebuilt")
