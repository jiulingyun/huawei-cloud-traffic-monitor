#!/bin/sh
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <new-version> (e.g. v1.2.3)"
  exit 1
fi

NEW_VERSION="$1"

echo "Updating VERSION -> $NEW_VERSION"
echo "$NEW_VERSION" > VERSION

echo "Updating backend/app/__init__.py"
export NEW_VERSION
python - <<PY
import os, re
from pathlib import Path

p = Path("backend/app/__init__.py")
text = p.read_text(encoding="utf-8")
v = os.environ.get("NEW_VERSION", "")
if re.search(r'__version__\s*=.*', text):
    text = re.sub(r'__version__\s*=.*', '__version__ = "{}"'.format(v), text)
else:
    if not text.endswith("\n"):
        text += "\n"
    text += '__version__ = "{}"'.format(v)
p.write_text(text, encoding="utf-8")
print("done")
PY

echo "Update complete. Please commit VERSION and backend/app/__init__.py"


