#!/bin/bash
#
# sync.sh — apply already-pulled code to the running cPanel app.
#
# Routine deploy from the cPanel Terminal:
#
#   1.  source ~/virtualenv/apps/katalog-staging/3.8/bin/activate && cd ~/apps/katalog-staging
#       (copy this line from cPanel -> Setup Python App -> "Enter to the virtual environment")
#   2.  git pull
#   3.  bash sync.sh
#
# What it does: pip install (only if requirements.txt changed) -> migrate ->
# collectstatic -> restart Passenger. It never touches the database rows or
# uploaded media, so it is safe to run on a live install any time.
#
# Options:
#   bash sync.sh --pull      also run `git pull --ff-only` first (steps 2+3 in one)
#   bash sync.sh --pip       force `pip install` even if requirements look unchanged
#   bash sync.sh --no-pip    skip `pip install` entirely
#   bash sync.sh --no-static skip `collectstatic`
#
# Env: SYNC_PYTHON=/path/to/python overrides interpreter detection.
#
set -euo pipefail

DO_PULL=0
FORCE_PIP=0
SKIP_PIP=0
SKIP_STATIC=0
for arg in "$@"; do
  case "$arg" in
    --pull)      DO_PULL=1 ;;
    --pip)       FORCE_PIP=1 ;;
    --no-pip)    SKIP_PIP=1 ;;
    --no-static) SKIP_STATIC=1 ;;
    -h|--help)   sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "!! unknown option: $arg" >&2; exit 2 ;;
  esac
done

# --- locate the app root (this script lives at the repo root) -------------
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(pwd)"
echo "==> app root: $APP_ROOT"
[ -f manage.py ] || { echo "!! manage.py not found here — run this from the app root"; exit 1; }

# --- pick the interpreter (prefer the active virtualenv) -----------------
if [ -n "${SYNC_PYTHON:-}" ]; then
  PY="$SYNC_PYTHON"
elif [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
  PY="$VIRTUAL_ENV/bin/python"
elif command -v python >/dev/null 2>&1; then
  PY="$(command -v python)"
  [ -n "${VIRTUAL_ENV:-}" ] || echo "!! warning: no virtualenv active — run the 'source .../activate' line from Setup Python App first"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
else
  echo "!! no python interpreter found"; exit 1
fi
echo "==> python: $("$PY" --version 2>&1)"

mkdir -p tmp

# --- 0. optional: pull -------------------------------------------------
if [ "$DO_PULL" = 1 ]; then
  echo "==> git pull --ff-only"
  git pull --ff-only
fi
if command -v git >/dev/null 2>&1 && [ -d .git ]; then
  git log -1 --pretty='==> at %h  %s  (%cr)'
fi

# --- 1. dependencies (skip when requirements.txt is unchanged) --------
STAMP="tmp/.sync-reqhash"
REQ_HASH=""
if command -v sha1sum >/dev/null 2>&1; then REQ_HASH="$(sha1sum requirements.txt 2>/dev/null | awk '{print $1}')"
elif command -v shasum  >/dev/null 2>&1; then REQ_HASH="$(shasum  requirements.txt 2>/dev/null | awk '{print $1}')"
elif command -v md5sum  >/dev/null 2>&1; then REQ_HASH="$(md5sum  requirements.txt 2>/dev/null | awk '{print $1}')"
fi

if [ "$SKIP_PIP" = 1 ]; then
  echo "==> pip: skipped (--no-pip)"
elif [ "$FORCE_PIP" != 1 ] && [ -n "$REQ_HASH" ] && [ -f "$STAMP" ] && [ "$(cat "$STAMP")" = "$REQ_HASH" ]; then
  echo "==> pip: requirements.txt unchanged — skipping (use --pip to force)"
else
  echo "==> pip install -r requirements.txt"
  "$PY" -m pip install --disable-pip-version-check -q -r requirements.txt
  [ -n "$REQ_HASH" ] && printf '%s' "$REQ_HASH" > "$STAMP" || true
fi

# --- 2. database schema (committed migrations only) ------------------
echo "==> manage.py migrate --noinput"
"$PY" manage.py migrate --noinput

# --- 2b. compile translation catalogs (best effort; .mo is also committed) ---
if command -v msgfmt >/dev/null 2>&1; then
  echo "==> manage.py compilemessages"
  "$PY" manage.py compilemessages 2>&1 || echo "!! compilemessages failed — using the committed .mo files"
else
  echo "==> compilemessages: gettext not installed — using the committed .mo files"
fi

# --- 3. static files ----------------------------------------------
if [ "$SKIP_STATIC" = 1 ]; then
  echo "==> collectstatic: skipped (--no-static)"
else
  echo "==> manage.py collectstatic --noinput"
  "$PY" manage.py collectstatic --noinput
fi

# --- 4. reload Passenger ----------------------------------------
touch tmp/restart.txt
echo "==> touched tmp/restart.txt — Passenger will reload on the next request"

echo
echo "==> DONE.  Hard-refresh the site (Ctrl+Shift+R) to clear the old CSS."
