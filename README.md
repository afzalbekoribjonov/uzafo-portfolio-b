# UZAFO Portfolio 

FastAPI + MongoDB + ImageKit backend for the current UZAFO portfolio frontend.

## What this backend covers

- Admin/user authentication with JWT access + refresh tokens
- Public + admin CRUD for profile, site, resume, projects, posts, discussions
- Comments and replies compatible with the current frontend data shapes
- ImageKit signed browser upload flow for images and videos
- Media metadata storage in MongoDB so UI data stays structured
- Seed script based on the latest frontend JSON snapshot
- Input validation, HTML sanitization, audit logging, soft delete for media

## Stack

- FastAPI
- Motor / MongoDB
- Pydantic v2
- Passlib Argon2 hashing
- PyJWT
- ImageKit Python SDK

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open:
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Deploy to Render

Recommended Render settings for this backend:

- Runtime: `Python`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

If you're deploying from a monorepo, set Render's Root Directory to `backend`.

### Required Render environment variables

- `APP_ENV=production`
- `DEBUG=false`
- `MONGO_URI`
- `MONGO_DB`
- `JWT_SECRET`
- `ADMIN_NAME`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `ALLOWED_ORIGINS=https://uzafo.site,https://www.uzafo.site`

Optional but recommended:

- `IMAGEKIT_PUBLIC_KEY`
- `IMAGEKIT_PRIVATE_KEY`
- `IMAGEKIT_URL_ENDPOINT`
- `IMAGEKIT_WEBHOOK_SECRET`

This repo also includes:

- `.python-version` to pin Python on Render
- `render.yaml` as a starter Blueprint

## Important environment variables

- `MONGO_URI`
- `MONGO_DB`
- `MONGO_MIN_POOL_SIZE`
- `MONGO_MAX_POOL_SIZE`
- `MONGO_SERVER_SELECTION_TIMEOUT_MS`
- `MONGO_CONNECT_TIMEOUT_MS`
- `MONGO_SOCKET_TIMEOUT_MS`
- `MONGO_WAIT_QUEUE_TIMEOUT_MS`
- `JWT_SECRET`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `SEED_DEMO_DATA` (`false` by default, set to `true` only when you want demo content seeded)
- `IMAGEKIT_PUBLIC_KEY`
- `IMAGEKIT_PRIVATE_KEY`
- `IMAGEKIT_URL_ENDPOINT`

## Production safety

When `APP_ENV=production`, the backend now refuses to start if:

- `JWT_SECRET` is left at its default fallback
- `ADMIN_PASSWORD` is left at its default fallback
- `ALLOWED_ORIGINS` still contains only localhost origins

This helps fail fast on Render instead of silently deploying with broken auth or CORS.

## Current frontend compatibility

The backend intentionally keeps these response shapes easy to map into the existing frontend:

- `GET /api/profile` -> `Profile`
- `GET /api/projects` -> `{ items, total }`
- `GET /api/posts` -> `{ items, total }`
- `GET /api/discussions` -> `{ items, total }`
- `GET /api/resume` -> `ResumeData`

The current frontend still stores media as `cover: string` and `blocks[].src: string`. This backend keeps those fields in responses, while also storing a separate `media_assets` collection internally.

See `FRONTEND_INTEGRATION.md` for the exact mapping and the ImageKit upload flow.
