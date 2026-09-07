# Lexia Machinery — katalog (lexia.co.id)

Django 2.1 catalogue + blog + bilingual (ID / EN) content, with a custom staff
panel at `/panel/`. This file is the entry point; the deep docs are
[`LOCAL_SETUP.md`](LOCAL_SETUP.md) and [`DEPLOY_STAGING.md`](DEPLOY_STAGING.md).

| | Local | Staging / Production (cPanel) |
|---|---|---|
| Python | 3.8 (`uv`, `.venv/`) | 3.7 – 3.8 (Setup Python App) |
| Django | 2.1.15 | 2.1.x |
| Database | SQLite (`db.sqlite3`) | MySQL |
| Config | none needed — DEBUG + SQLite auto | env vars only, never edit `settings.py` |
| Branch | `staging` | `staging` (staging server) · `master` (production) |

---

## Install & run locally

Prerequisites: Python 3.8 and [`uv`](https://docs.astral.sh/uv/)
(`winget install --id astral-sh.uv`).

```powershell
# from the repo root
uv venv --python 3.8 .venv
uv pip install --python .\.venv\Scripts\python.exe -r requirements-local.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
```

Run it:

```powershell
powershell -ExecutionPolicy Bypass -File run-local.ps1   # -> http://127.0.0.1:8000
```

- Public site: <http://127.0.0.1:8000/> · English: <http://127.0.0.1:8000/en/>
- Staff panel: <http://127.0.0.1:8000/panel/> · Django admin: `/admin/`
- Login `jeffry.aldi@gmail.com` (superuser, production password). Or make your
  own: `.\.venv\Scripts\python.exe manage.py createsuperuser`.

No `.env` is needed locally — `settings.py` falls back to SQLite + `DEBUG=True`
when `DATABASE_URL` is unset. `requirements-local.txt` is the production stack
minus the cPanel-only packages (`mysqlclient`, `python-memcached`, …).

Product photos are **not** in the repo — pages work without them, images 404.
See [`LOCAL_SETUP.md` → "Missing: product images"](LOCAL_SETUP.md) to pull them
from the server.

---

## Sync changes to staging or production

Code, templates, and static files travel through git. **Database rows and
uploaded media do not** — move catalogue content with a fixture or re-enter it
in the target admin (see below).

### Routine deploy (staging *and* production)

From the cPanel Terminal, in the app root, inside its virtualenv:

```bash
# 1. enter the venv — copy this line from cPanel → Setup Python App
source ~/virtualenv/apps/<app>/3.8/bin/activate && cd ~/apps/<app>

# 2. pull + apply, one command
bash sync.sh --pull
```

`sync.sh` is idempotent and safe on a live install. It runs, in order:
`git pull --ff-only` → `pip install` *(only if `requirements.txt` changed)* →
`migrate` → `compilemessages` → `update_translation_fields` → `collectstatic`
→ `touch tmp/restart.txt` (Passenger reload). Flags: `--pip` / `--no-pip`,
`--no-static`, `--help`. `deployment.sh` is the older, minimal equivalent
(always pip + migrate + collectstatic).

After it finishes, hard-refresh the site (Ctrl+Shift+R) to drop cached CSS.

> **Do not edit files on the server.** The staging installer hard-resets to
> `origin/staging`; `sync.sh --pull` is fast-forward only. Commit and push
> instead, then pull.

### First-time staging setup

One `.env` file + one script — full walkthrough in
[`DEPLOY_STAGING.md`](DEPLOY_STAGING.md) (subdomain, MySQL, Setup Python App,
env vars). Then:

```bash
cd ~/apps/katalog-staging && bash scripts/staging_install.sh
```

That also loads `fixtures/staging_seed.json` (8 categories, 20 machines,
brochures, blog posts, `SiteSettings`, admin users) and unpacks
`fixtures/staging_media.tar.gz`.

### Promoting to production

```bash
# your PC — when staging is approved
git checkout master && git merge staging && git push origin master

# production app root (its own checkout + Python app)
git fetch origin && git checkout master && git pull
bash sync.sh          # or deployment.sh
```

Production env vars: `DJANGO_ENV=production`, `DJANGO_DEBUG=0`,
`DJANGO_PREPEND_WWW=1`, the production `DATABASE_URL`, and
`DJANGO_STATIC_ROOT` / `DJANGO_MEDIA_ROOT` under `public_html`. Keep `master`
as a rollback snapshot of the pre-redesign site.

### Moving catalogue content between environments

```powershell
.\.venv\Scripts\python.exe manage.py dumpdata page item blog seo homepage --indent 2 -o transfer.json
# upload transfer.json, then on the target:
python manage.py loaddata transfer.json
```

Image files still have to be uploaded separately into `<MEDIA_ROOT>/upload/`.

---

## Operational notes

- **Migrations** are committed with the code. Never run `makemigrations` on the
  server — only `migrate` (via `sync.sh`).
- **Panel "⚡ Isi dengan rekomendasi SEO"** (product / blog / category forms) is
  pure local logic — no network.
- **Panel translate buttons** ("Isi English dari Indonesia", etc.) call Google's
  keyless endpoints (`clients5.google.com`, `translate.googleapis.com`) over
  **outbound HTTPS from the server**. If the host blocks outbound HTTPS the
  button shows a friendly error and editors fill the field manually — nothing
  else breaks. No API key, no cost; the endpoints are rate-limited by IP.
- **SEO Health** — read-only audit at `/panel/seo/` (Pengaturan → SEO Health):
  noindex pages, weak/over-length meta, missing share images, thin category
  pages, blank site verification, etc. The sidebar badge counts critical
  (noindex) issues.
- On staging keep `google_site_verification` and `ga_measurement_id` **empty**
  (admin → Pengaturan Situs & SEO) and password-protect the subdomain so it is
  never indexed or tracked.

## Do not commit

`.venv/`, `db.sqlite3`, `katalog/static/` (rebuilt by `collectstatic`),
`media/cache/`, `media/upload/image/`, `__pycache__/`, `*.pyc`, `*.log`, `.env`,
loose `*.tar.gz` / `*.zip` deploy bundles. All covered by `.gitignore`
(`fixtures/staging_media.tar.gz` is the one committed bundle — the installer
ships it).
