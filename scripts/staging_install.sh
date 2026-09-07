#!/bin/bash
#
# One-command staging install / update for cPanel.
#
#   1. cPanel -> Setup Python App -> copy the "source .../activate && cd ..." line, run it
#   2. make sure  .env  exists next to manage.py  (see .env.example)
#   3. bash scripts/staging_install.sh
#
# Safe to re-run any time. It:
#   - syncs the checkout to origin/staging   (git reset --hard)
#   - installs pinned requirements
#   - runs migrations
#   - loads the staging database fixture     (categories, machines, brochures, blog, users, SiteSettings)
#   - unpacks the bundled media into DJANGO_MEDIA_ROOT
#   - runs collectstatic
#   - restarts Passenger
#
set -euo pipefail

# --- locate the app root (this script lives in ./scripts/) ---------------
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ROOT="$(pwd)"
echo "==> app root: $APP_ROOT"

[ -f manage.py ] || { echo "!! manage.py not found here - aborting"; exit 1; }
[ -f .env ] || { echo "!! .env not found next to manage.py - create it first (see .env.example)"; exit 1; }
[ -n "${VIRTUAL_ENV:-}" ] || echo "!! warning: no virtualenv active - run the 'source .../activate' line from Setup Python App first"

echo "==> python: $(python --version 2>&1)   pip: $(pip --version 2>&1 | awk '{print $2}')"

# --- 1. sync code to origin/staging ------------------------------------
if [ -d .git ]; then
  echo "==> git: fetch + hard reset to origin/staging"
  git fetch --prune origin staging
  git reset --hard origin/staging
  git log -1 --pretty='    now at %h  %s'
else
  echo "==> (no .git dir - skipping git sync; using files as-is)"
fi

# --- 2. dependencies --------------------------------------------------
echo "==> pip install -r requirements.txt"
pip install --disable-pip-version-check -q -r requirements.txt

# --- 3. database schema ---------------------------------------------
echo "==> manage.py migrate"
python manage.py migrate --noinput

# --- 4. inject the staging data ------------------------------------
echo "==> manage.py loaddata fixtures/staging_seed.json"
python manage.py loaddata fixtures/staging_seed.json

# --- 5. media -----------------------------------------------------
MEDIA_ROOT="$(grep -E '^DJANGO_MEDIA_ROOT=' .env | head -1 | cut -d= -f2- | sed "s/^[\"']//;s/[\"']$//" | xargs || true)"
[ -n "$MEDIA_ROOT" ] || MEDIA_ROOT="$APP_ROOT/media"
BUNDLE="fixtures/staging_media.tar.gz"
if [ -f "$BUNDLE" ]; then
  echo "==> unpacking $BUNDLE  ->  $MEDIA_ROOT"
  mkdir -p "$MEDIA_ROOT"
  tar xzf "$BUNDLE" -C "$MEDIA_ROOT"
  echo "    $(find "$MEDIA_ROOT/upload" "$MEDIA_ROOT/blog" -type f 2>/dev/null | wc -l) media files in place"
else
  echo "==> ($BUNDLE not found - skipping media)"
fi

# --- 6. static files -------------------------------------------
echo "==> manage.py collectstatic"
python manage.py collectstatic --noinput

# --- 7. restart Passenger -------------------------------------
mkdir -p tmp
touch tmp/restart.txt
echo "==> touched tmp/restart.txt (Passenger will reload)"

echo
echo "==> DONE. Open your staging URL. If images 404, check that DJANGO_MEDIA_ROOT"
echo "    in .env points inside the subdomain document root."
