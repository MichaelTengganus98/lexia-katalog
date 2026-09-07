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
git clone --depth 1 -b staging https://github.com/MichaelTengganus98/lexia-katalog.git ~/apps/katalog-staging
cd ~/apps/katalog-staging
```

`--depth 1` keeps the download small so the flaky cPanel web-terminal doesn't
drop it. If it still aborts, delete the partial dir (`rm -rf ~/apps/katalog-staging`)
and grab a tarball instead:

```bash
cd ~/apps
curl -L -o s.tgz https://github.com/MichaelTengganus98/lexia-katalog/archive/refs/heads/staging.tar.gz
tar xzf s.tgz && mv lexia-katalog-staging katalog-staging && rm s.tgz
cd katalog-staging
git init -q && git remote add origin https://github.com/MichaelTengganus98/lexia-katalog.git
git fetch --depth 1 -q origin staging && git reset --hard -q origin/staging   # so the installer's git sync works
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

## 6. Run the installer (does everything)

In the Setup Python App screen, copy the **"Enter to the virtual environment"**
command and run it in Terminal, then:

```bash
cd ~/apps/katalog-staging
bash scripts/staging_install.sh
```

That one script: syncs the checkout to `origin/staging`, `pip install`s the
pinned requirements, runs `migrate`, loads **`fixtures/staging_seed.json`**
(8 categories, 20 machines, 3 brochures, 2 blog posts, `SiteSettings`, and the
2 admin users with their existing password hashes), unpacks the bundled
**`fixtures/staging_media.tar.gz`** into `DJANGO_MEDIA_ROOT`, runs
`collectstatic`, and touches `tmp/restart.txt`.

Re-run it any time to pull + redeploy — it's idempotent.

> If `pip install` fails on **mysqlclient**, apply the PyMySQL fallback from the
> bottom of `requirements.txt`, then re-run the installer.

The DB fixture ships the two admin users, so `/admin/` login works immediately
(`jeffry.aldi@gmail.com` + the production password). For a fresh admin instead:
`python manage.py createsuperuser`.

## 7. Verify

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

## 8. Updating staging later

Same one command:

```bash
cd ~/apps/katalog-staging && bash scripts/staging_install.sh
```

It hard-resets to `origin/staging`, so **don't edit files on the server** — they
get overwritten. Media/content you add through the admin persists (it's in the DB
+ `DJANGO_MEDIA_ROOT`, which the installer only adds to, never wipes).

To refresh the shipped example data / photos, on your PC run
`bash scripts/build_staging_fixtures.sh`, commit `fixtures/`, push `staging`.

## 9. Promoting to production later

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
| panel "Isi English dari…" / translate button errors or does nothing | the server has no outbound HTTPS to `clients5.google.com` / `translate.googleapis.com`, or Google is rate-limiting the IP. Editors fill the field manually; "Isi dengan rekomendasi SEO" is unaffected (local-only). |
