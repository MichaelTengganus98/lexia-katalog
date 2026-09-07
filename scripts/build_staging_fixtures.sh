#!/bin/bash
#
# Rebuild the two files the staging installer ships:
#   fixtures/staging_seed.json       - DB rows (categories, machines, brochures, blog, users, SiteSettings)
#   fixtures/staging_media.tar.gz    - the image files those rows point at
#
# Run on your machine (from the project root, in the local venv) after you
# change catalogue content or replace photos, then commit + push `staging`.
#
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PY="${PYTHON:-python}"
[ -x ".venv/Scripts/python.exe" ] && PY="./.venv/Scripts/python.exe"
[ -x ".venv/bin/python" ] && PY="./.venv/bin/python"

echo "==> DB fixture -> fixtures/staging_seed.json"
"$PY" manage.py dumpdata auth.user page item homepage blog seo \
  --natural-foreign --natural-primary --indent 2 -o fixtures/staging_seed.json

echo "==> media bundle -> fixtures/staging_media.tar.gz"
"$PY" - <<'PYEOF'
import os, tarfile
os.chdir("media")
with tarfile.open("../fixtures/staging_media.tar.gz", "w:gz") as t:
    for d in ("upload", "blog"):
        if os.path.isdir(d):
            t.add(d)
    print("   ", len(t.getnames()), "members")
PYEOF

echo "==> done. Review, then:  git add fixtures/ && git commit && git push origin staging"
