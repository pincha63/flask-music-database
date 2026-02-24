"""
build_css.py — Compile static/scss/main.scss → static/css/main.css using libsass.

Run once before starting the server (or whenever the SCSS changes):
    python3 build_css.py
"""

import os
import sass  # provided by the 'libsass' pip package

BASE = os.path.dirname(__file__)
SRC  = os.path.join(BASE, "static", "scss", "main.scss")
DST  = os.path.join(BASE, "static", "css",  "main.css")

css = sass.compile(filename=SRC, output_style="compressed")
os.makedirs(os.path.dirname(DST), exist_ok=True)
with open(DST, "w") as f:
    f.write(css)

print(f"Compiled {SRC} → {DST}  ({len(css):,} bytes)")
