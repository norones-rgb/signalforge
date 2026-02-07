# SignalForge

Production-ready, automated X (Twitter) publishing + analytics system focused on safe scheduling and measurable outcomes.

## Prerequisites
- Docker + Docker Compose
- Python 3.11+ (optional for running scripts locally)
- Node 18+ (optional for admin UI)

## Quick Start (Docker)
```powershell
cd c:\Projects\signalforge
copy .env.example .env

# Generate a FERNET key and paste into .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

docker compose -f infra\docker-compose.yml up --build
```

API health check:
```powershell
Invoke-RestMethod http://localhost:8010/health
```

## Migrations
From host (requires Python + deps) or inside the API container.

Host:
```powershell
$env:DATABASE_URL="postgresql+psycopg://signalforge:signalforge@localhost:5432/signalforge"
alembic -c apps\api\alembic.ini upgrade head
```

Container:
```powershell
docker compose -f infra\docker-compose.yml exec api alembic -c /app/alembic.ini upgrade head
```

## Seed Dev Data
```powershell
python scripts\seed_dev.py
```

## Admin UI (optional)
This UI is for configuration only: accounts, tokens, sources, scheduling, analytics.

```powershell
cd c:\Projects\signalforge\apps\admin-web
npm install
$env:NEXT_PUBLIC_API_URL="http://localhost:8010"
npm run dev
```

Open `http://localhost:3001` and login/register. Tokens are stored by the API encrypted at rest.

## Connect X Account (OAuth 2.0 PKCE)
SignalForge supports OAuth 2.0 PKCE to connect your X account without pasting tokens.

1. Create an X Developer App and enable OAuth 2.0.
2. In the X app settings, add the callback URL:
   - `http://localhost:8010/oauth/x/callback`
3. Set these variables in `.env`:
   - `X_CLIENT_ID=...`
   - `X_CLIENT_SECRET=...` (optional for PKCE public clients; required for confidential clients)
   - `X_OAUTH_REDIRECT_URI=http://localhost:8010/oauth/x/callback`
   - `X_OAUTH_SCOPES=tweet.read tweet.write users.read offline.access`
   - `ADMIN_WEB_URL=http://localhost:3001`
4. Restart the API container:
   - `docker compose -f infra\docker-compose.yml up -d --build api`
5. In the Admin UI, create an account record, then click **Connect X Account**.

On success, SignalForge stores encrypted access/refresh tokens and updates the handle/name using `/2/users/me`.

## Auth
- `POST /auth/register`
- `POST /auth/login`

Both return a JWT bearer token. Use `Authorization: Bearer <token>` for protected endpoints.

## Core Endpoints
- `GET/POST /workspaces`
- `GET/POST/PATCH /accounts`
- `GET /oauth/x/start?account_id=...`
- `GET /oauth/x/callback`
- `GET/POST /sources`
- `GET /ideas`
- `GET /drafts`
- `POST /scheduler/run`
- `GET /posts`
- `GET /analytics/summary`

## Workers
Run via compose (already configured):
```powershell
docker compose -f infra\docker-compose.yml up --build
```

Manual task execution:
```powershell
docker compose -f infra\docker-compose.yml exec worker celery -A celery_app.celery_app call ingest_sources
```

## Tests
```powershell
cd c:\Projects\signalforge\apps\api
pytest
```

## Environment Variables
See `.env.example` for all available options.

Required:
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `FERNET_KEY`

Operational:
- `POSTING_DISABLED=true` killswitch for publishing
- `X_API_MODE=stub` to use stub client
- `PUBLISH_MAX_ATTEMPTS=3`
- `SAFETY_BLOCKLIST=term1,term2`

## Notes
- No automation of replies/likes/follows/DMs.
- Scheduling respects daily caps, allowed hours, spacing, and per-account killswitches.
