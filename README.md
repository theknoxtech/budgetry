# Budgetry

A self-hosted personal budgeting app. Track spending, manage categories, sync bank accounts, and install as a PWA on any device.

## Features

- **Budget tracking** — Categories, category groups, monthly targets, and spending goals
- **Transactions** — Manual entry or automatic sync via Plaid
- **Recurring transactions** — Automate regular income and expenses
- **Automation rules** — Auto-categorize transactions by payee or amount
- **Reports** — Spending breakdowns and trends
- **PWA** — Install on iOS, Android, macOS, or Windows from the browser
- **Authentication** — Local accounts with TOTP MFA, optional Auth0 OAuth
- **Admin panel** — Manage users, promote/demote admins, reset passwords
- **Dark/light theme** — Toggle between themes

## Quick Start (Local Development)

**Prerequisites:** Python 3.10+

```sh
git clone https://github.com/theknoxtech/budgetry.git
cd budgetry
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Optional — SECRET_KEY is auto-generated if not set
python run.py
```

Open `http://localhost:5001`. Register your first account — it will automatically be promoted to admin.

## Self-Hosting with Docker

**Prerequisites:** Docker and Docker Compose

```sh
git clone https://github.com/theknoxtech/budgetry.git
cd budgetry
cp .env.example .env
```

Edit `.env` if you want to configure optional features (Plaid, Auth0, Litestream). A `SECRET_KEY` is auto-generated on first run if not set.

Start the app:

```sh
docker compose up -d
```

Access at `http://localhost:5050`. Your database is persisted in the `./data/` directory.

**Updating:**

```sh
git pull
docker compose up -d --build
```

## Persistent Storage

Budgetry uses SQLite, which stores everything in a single file (`instance/budgetry.db`). Persistence depends on your deployment method:

| Method | How data persists |
|--------|------------------|
| **Docker (self-hosted)** | Volume mount `./data:/app/instance` — already configured |
| **Cloudflare Tunnel** | DB lives on your machine — inherently persistent |
| **Fly.io / Railway / Render** | Attach a persistent volume mounted at `/app/instance` |
| **Any deployment** | **Litestream** replication to S3/R2 for automatic backups |

### Litestream (Recommended for Cloud)

[Litestream](https://litestream.io) continuously replicates your SQLite database to S3-compatible object storage. If your container restarts or redeploys, the database is automatically restored from the replica. This is **built into the Docker image** — just set an environment variable to enable it.

**With Cloudflare R2 (free 10 GB):**

1. Create an R2 bucket in your Cloudflare dashboard
2. Generate an R2 API token with read/write access
3. Add to your `.env`:

```
LITESTREAM_REPLICA_URL=s3://your-bucket-name/budgetry.db
AWS_ACCESS_KEY_ID=your-r2-access-key
AWS_SECRET_ACCESS_KEY=your-r2-secret-key
AWS_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
```

4. Restart: `docker compose up -d`

**With AWS S3:**

```
LITESTREAM_REPLICA_URL=s3://your-bucket-name/budgetry.db
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
```

**With Backblaze B2:**

```
LITESTREAM_REPLICA_URL=s3://your-bucket-name/budgetry.db
AWS_ACCESS_KEY_ID=your-b2-key-id
AWS_SECRET_ACCESS_KEY=your-b2-app-key
AWS_ENDPOINT_URL=https://s3.us-west-004.backblazeb2.com
```

When `LITESTREAM_REPLICA_URL` is not set, the app runs normally without replication.

## Configuration

All configuration is done through environment variables in `.env`. See `.env.example` for the full template.

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | No | Random string for session signing. Auto-generated and persisted on first run if not set. |
| `AUTH0_DOMAIN` | No | Auth0 domain for OAuth login. Leave blank for local-only auth. |
| `AUTH0_CLIENT_ID` | No | Auth0 application client ID. |
| `AUTH0_CLIENT_SECRET` | No | Auth0 application client secret. |
| `PLAID_CLIENT_ID` | No | Plaid client ID for bank account sync. |
| `PLAID_SECRET` | No | Plaid secret key. |
| `PLAID_ENV` | No | Plaid environment: `sandbox`, `development`, or `production`. Defaults to `sandbox`. |
| `LITESTREAM_REPLICA_URL` | No | S3-compatible URL for SQLite replication. See [Persistent Storage](#persistent-storage). |
| `AWS_ACCESS_KEY_ID` | No | Access key for S3/R2 replication. |
| `AWS_SECRET_ACCESS_KEY` | No | Secret key for S3/R2 replication. |
| `AWS_ENDPOINT_URL` | No | Custom S3 endpoint (required for Cloudflare R2 and Backblaze B2). |

Auth0, Plaid, and Litestream are entirely optional. The app works fully with local accounts, manual transaction entry, and local-only storage.

## Deploy to Cloud Platforms

Budgetry uses SQLite, which stores data in a file. Cloud deployments need **persistent storage** — without it, your data will be lost on each redeploy.

### Railway

1. Connect your GitHub repo on [Railway](https://railway.app)
2. Railway auto-detects the `Dockerfile`
3. Add environment variables in the dashboard (`SECRET_KEY` at minimum)
4. Attach a **volume** and mount it at `/app/instance` to persist the database
5. Deploy

### Fly.io

```sh
fly launch                          # Creates app from Dockerfile
fly volumes create budgetry_data --size 1   # 1 GB persistent volume
fly secrets set SECRET_KEY=your-random-secret-string-here
```

Add to your `fly.toml`:

```toml
[mounts]
  source = "budgetry_data"
  destination = "/app/instance"
```

Then deploy:

```sh
fly deploy
```

### Render

1. Create a **Web Service** on [Render](https://render.com) from your GitHub repo
2. Set runtime to **Docker**
3. Add a **persistent disk** mounted at `/app/instance`
4. Set environment variables (`SECRET_KEY` at minimum)
5. Deploy

### Coolify

[Coolify](https://coolify.io) is a self-hosted PaaS alternative.

1. Add the repo as a **Docker Compose** project
2. Configure environment variables
3. Map a persistent volume for `/app/instance`
4. Deploy

### Cloudflare

Cloudflare Pages and Workers don't support Python/Flask natively. Instead, use **Cloudflare Tunnel** to expose a self-hosted instance:

1. Run Budgetry with Docker on your server or local machine
2. Install `cloudflared`: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
3. Create a tunnel:
   ```sh
   cloudflared tunnel create budgetry
   cloudflared tunnel route dns budgetry your-subdomain.yourdomain.com
   ```
4. Configure `~/.cloudflared/config.yml`:
   ```yaml
   tunnel: budgetry
   ingress:
     - hostname: your-subdomain.yourdomain.com
       service: http://localhost:5050
     - service: http_status:404
   ```
5. Run the tunnel:
   ```sh
   cloudflared tunnel run budgetry
   ```

Your app is now accessible at `https://your-subdomain.yourdomain.com` with Cloudflare's SSL and DDoS protection.

## PWA Installation

Budgetry is a Progressive Web App. Once deployed, you can install it from the browser:

| Platform | How to install |
|----------|---------------|
| **iOS / iPadOS** | Safari → Share button → "Add to Home Screen" |
| **Android** | Chrome → Menu (three dots) → "Add to Home Screen" or "Install app" |
| **macOS** | Chrome → Address bar install icon, or Safari (Sonoma+) → File → "Add to Dock" |
| **Windows** | Chrome/Edge → Address bar install icon → "Install" |

The installed app opens in standalone mode without browser chrome.

## Tech Stack

- **Backend:** Flask, SQLite, Gunicorn
- **Frontend:** Jinja2 templates, Pico CSS
- **Auth:** Werkzeug (local), Authlib (Auth0 OAuth), pyotp (TOTP MFA)
- **Bank sync:** Plaid
- **Deployment:** Docker, Docker Compose
