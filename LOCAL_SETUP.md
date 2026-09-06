# Local development — katalog (lexia.co.id)

Recreated from the cPanel backup + `lexiacoi_katalog.sql.gz` on 2026-09-06.

## Stack

| | Local | Production (cPanel) |
|---|---|---|
| Python | 3.8.20 (managed by `uv`, lives in `.venv/`) | 3.7 (cPanel "Setup Python App") |
| Django | 2.1.15 | 2.1.2 |
| Database | SQLite (`db.sqlite3`) | MySQL `lexiacoi_katalog` |
| Static/media | local `katalog/static/`, `media/` | `/home/lexiacoi/public_html/{static,media}` |

`katalog/settings.py` already branches on the `DATABASE_URL` env var. Locally it is
unset, so the SQLite + `DEBUG=True` branch is used automatically — no settings edits.

## First-time setup (already done, for reference)

```powershell
# uv was installed via: winget install --id astral-sh.uv
uv python install 3.8
uv venv --python 3.8 .venv
uv pip install --python .\.venv\Scripts\python.exe -r requirements-local.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
# data (categories / items / users) imported from lexiacoi_katalog.sql.gz
```

`requirements-local.txt` mirrors the production stack minus the cPanel-only pieces
(`mysqlclient`, `gunicorn`, `python-memcached`, `social-auth-app-django`).

## Run it

```powershell
powershell -ExecutionPolicy Bypass -File run-local.ps1
#  -> http://127.0.0.1:8000
```

Admin: `http://127.0.0.1:8000/admin/`
 * user `jeffry.aldi@gmail.com` — superuser, **same password as production** (original hash imported from the dump)
 * user `lexia` — production hash, but `is_staff=False` so it cannot enter the admin (same as production)

If you ever need a fresh local admin without touching the imported accounts:
`.\.venv\Scripts\python.exe manage.py createsuperuser`

## What was imported from the SQL dump

* 8 categories (`page_category`)
* 20 machines (`item_item`) — descriptions, specs, video URLs, image *paths*
* 2 users (`auth_user`) with their production password hashes

Not imported (regenerates itself / disposable): `django_session`, `django_admin_log`,
`thumbnail_kvstore`.

## Missing: product images

The backup's `media/upload/image/` only has old test folders (`Mesin 1`, `Mesin 2`).
The real photos referenced by the DB (`upload/image/Mesin Potong Kertas/...` etc.)
are on the server at `/home/lexiacoi/public_html/media/upload/`.

Download that folder from cPanel and drop it in as `media/upload/` here. Until then,
product images 404 (pages still work). You can delete the stale `media/upload/image/Mesin 1`
and `media/upload/image/Mesin 2` folders.

## Pushing changes back to cPanel

* **Code / templates / static** — upload the changed files; run `deployment.sh`
  (`pip install -r requirements.txt`, `migrate`, `collectstatic`) and touch
  `tmp/restart.txt` to reload Passenger.
* **New migrations** — if you change models, commit the generated
  `*/migrations/00xx_*.py` files and upload them too; `migrate` runs on the server.
* **Catalog content (categories / machines)** — this is *database* data and does
  **not** travel with a file upload. Either re-enter it in the production Django
  admin, or move it with a fixture:
  ```powershell
  .\.venv\Scripts\python.exe manage.py dumpdata page item --indent 2 -o transfer.json
  # upload transfer.json, then on the server:  python manage.py loaddata transfer.json
  ```
  (image files still have to be uploaded separately into `public_html/media/`.)

## Do not upload

`.venv/`, `db.sqlite3`, `katalog/static/` (server rebuilds it), `media/cache/`,
`__pycache__/`, `*.pyc`, `requirements-local.txt`. See `.gitignore`.
