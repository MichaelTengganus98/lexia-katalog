# Deploy to staging (cPanel + subdomain/addon domain)

This puts the **`staging`** branch on a separate URL (e.g. `staging.lexia.co.id`)
with its own MySQL database, without touching the live site.

Branches on GitHub (`github.com/MichaelTengganus98/lexia-katalog`):
- **`staging`** — the redesign + SEO + blog + deploy work. The staging server runs this.
- **`master`** — the original pre-redesign site (what production runs today).
- **`main`** — GitHub's default; currently the same commit as `staging`.

Settings are 100% environment-driven — you never edit `settings.py`. Everything
is controlled by the variables in `.env.example`.

> **Security — the repo is public.** Old commits contain the production
> `SECRET_KEY` and the old production MySQL password (`webkojeffry1` for
> `lexiacoi_admin`). Before relying on this: **make the repo private**
> (GitHub → repo → Settings → Danger Zone → Change visibility), OR rotate
> the production MySQL password and set a fresh `DJANGO_SECRET_KEY` env var
> on production. Staging uses its own DB + its own `DJANGO_SECRET_KEY`, so
> staging itself is fine.

---

## 0. One-time: what you need

- cPanel access to the `lexiacoi` account
- The repo on GitHub: `https://github.com/MichaelTengganus98/lexia-katalog.git`
- Python 3.7 or 3.8 available in cPanel → *Setup Python App*

Naming used below (change to taste):

| thing | value |
|---|---|
| subdomain | `staging.lexia.co.id` |
| document root | `/home/lexiacoi/staging.lexia.co.id` |
| app code root | `/home/lexiacoi/apps/katalog-staging` |
| MySQL db / user | `lexiacoi_stg` / `lexiacoi_stg` |

---

## 1. Create the subdomain

cPanel → **Domains** (or *Subdomains*) → create `staging` under `lexia.co.id`.
Document root: `/home/lexiacoi/staging.lexia.co.id`.

Then cPanel → **SSL/TLS Status** → run *AutoSSL* for the new subdomain (or add a cert).
Until the cert is active, set `DJANGO_SECURE_SSL=0` in step 5.

## 2. Create the database

cPanel → **MySQL Databases**:
1. Create database `lexiacoi_stg`
2. Create user `lexiacoi_stg` with a strong password
3. Add the user to the database with **ALL PRIVILEGES**

Your `DATABASE_URL` becomes:
`mysql://lexiacoi_stg:THEPASSWORD@localhost/lexiacoi_stg`

## 3. Get the code onto the server

SSH in (cPanel → *Terminal*), then:

```bash
mkdir -p ~/apps
git clone -b staging https://github.com/MichaelTengganus98/lexia-katalog.git ~/apps/katalog-staging
cd ~/apps/katalog-staging
```

## 4. Create the Python app

cPanel → **Setup Python App** → *Create Application*:

| field | value |
|---|---|
| Python version | 3.8 (or 3.7) |
| Application root | `apps/katalog-staging` |
| Application URL | `staging.lexia.co.id` |
| Application startup file | `passenger_wsgi.py` |
| Application Entry point | `application` |

Click **Create**. cPanel makes a virtualenv and writes the `.htaccess` in the
document root that routes the subdomain to this app.

## 5. Environment variables

Easiest: create `~/apps/katalog-staging/.env` (it is git-ignored):

```ini
DJANGO_ENV=staging
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<paste a long random string>
DJANGO_ALLOWED_HOSTS=staging.lexia.co.id
DATABASE_URL=mysql://lexiacoi_stg:THEPASSWORD@localhost/lexiacoi_stg
DJANGO_STATIC_ROOT=/home/lexiacoi/staging.lexia.co.id/static
DJANGO_MEDIA_ROOT=/home/lexiacoi/staging.lexia.co.id/media
DJANGO_SECURE_SSL=1          # 0 until AutoSSL for the subdomain is live
DJANGO_PREPEND_WWW=0
```

Generate a secret key:
`python -c "import secrets; print(secrets.token_urlsafe(50))"`

(You can instead enter each as an *Environment variable* in the Setup Python App
screen — the `.env` file is just less clicking.)

## 6. Install, migrate, load data, collect static

In the Setup Python App screen, copy the **"Enter to the virtual environment"**
command and run it in Terminal, then:

```bash
cd ~/apps/katalog-staging
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py loaddata fixtures/staging_seed.json   # categories, machines, brochures, blog, users, SiteSettings
python manage.py collectstatic --noinput
```

`staging_seed.json` includes the two admin users with their existing password
hashes, so you can log in at `/admin/` straight away. To add a fresh admin
instead: `python manage.py createsuperuser`.

> If `pip install` fails on **mysqlclient**, see the note at the bottom of
> `requirements.txt` (switch to PyMySQL).

## 7. Upload the media files

The database rows reference image files that live under `media/`. On your PC,
zip these two folders (skip `media/cache/` — it regenerates):

```
media/upload/     ->  product photos + brochure covers + brochure PDFs
media/blog/       ->  blog cover images
```

Upload the zip to `/home/lexiacoi/staging.lexia.co.id/`, extract so you end up
with:

```
/home/lexiacoi/staging.lexia.co.id/media/upload/...
/home/lexiacoi/staging.lexia.co.id/media/blog/...
```

(That path is `DJANGO_MEDIA_ROOT`. Apache/LiteSpeed serves `/media/...` directly
from there; `/static/...` likewise from the `static/` folder collectstatic just
filled.)

## 8. Restart & verify

```bash
mkdir -p ~/apps/katalog-staging/tmp
touch ~/apps/katalog-staging/tmp/restart.txt
```

Open `https://staging.lexia.co.id/` and check:

- [ ] homepage (hero image, categories, featured, brochures)
- [ ] `/katalog/` and a product page (photos load = media OK)
- [ ] `/blog/` and an article
- [ ] `/admin/` login
- [ ] `/sitemap.xml` and `/robots.txt`
- [ ] view-source: `<link rel="canonical">` points to `https://staging.lexia.co.id/...`

Then in the admin → **Pengaturan Situs & SEO**: leave `google_site_verification`
and `ga_measurement_id` **empty** on staging so it's never indexed or tracked.
The subdomain is already `noindex`-safe only if you also add it to robots — for a
private staging site, either password-protect it (cPanel → *Directory Privacy* on
the docroot) or add `Disallow: /` via a staging-only robots override.

## 9. Updating staging later

```bash
cd ~/apps/katalog-staging
git pull origin staging
bash deployment.sh          # pip install + migrate + collectstatic + restart
```

New media added through the admin lands in `DJANGO_MEDIA_ROOT` automatically.

## 10. Promoting to production later

When `staging` is approved, merge it and deploy to the **production** Python app:

```bash
# from your PC
git checkout master && git merge staging && git push origin master
# on the production app root (a separate checkout / Python app)
git fetch origin && git checkout master && git pull
```

Set its env vars (`DJANGO_ENV=production`, `DJANGO_PREPEND_WWW=1`, the
production `DATABASE_URL`, production `DJANGO_STATIC_ROOT` /
`DJANGO_MEDIA_ROOT` under `public_html`), then run `bash deployment.sh`.
Keep `master` around only as a rollback snapshot of the old site. Move
content across with a fresh
`dumpdata`/`loaddata` **or** re-enter it in the production admin — the staging
database does not sync to production automatically.

---

## Troubleshooting

| symptom | fix |
|---|---|
| 500, `ALLOWED_HOSTS` error | add the exact host to `DJANGO_ALLOWED_HOSTS`, `touch tmp/restart.txt` |
| CSS/JS 404 | `collectstatic` not run, or `DJANGO_STATIC_ROOT` not under the docroot |
| images 404 | media zip not extracted to `DJANGO_MEDIA_ROOT` |
| `no such table` / `relation does not exist` | `migrate` not run against the staging DB |
| infinite redirect | `DJANGO_SECURE_SSL=1` but no SSL cert yet → set it to `0`, restart |
| admin CSS missing | `collectstatic` + the `static/` folder must be web-served from the docroot |
| changes not showing | `touch tmp/restart.txt` (Passenger caches the process) |
