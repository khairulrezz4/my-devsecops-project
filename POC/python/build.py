"""Compile the POC and create a portable build artifact."""

from pathlib import Path
import shutil


ROOT = Path(__file__).parent
DIST = ROOT / "dist"

if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir()

shutil.copy2(ROOT / "app.py", DIST / "app.py")
shutil.copy2(ROOT / "README.md", DIST / "README.md")
print(f"Created artifact at {DIST}")
