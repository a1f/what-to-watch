# What to Watch

A self-hosted, reminder-first movie & TV tracker with AI-assisted discovery.
Add what you want to watch and get a daily digest when it hits theaters or
streaming, when the next episode airs, or when a show is renewed or canceled.
Runs entirely on your own machine on free data sources.

See [`DESIGN.md`](./DESIGN.md) for the full product & technical design.

## Repo layout

```
web/                 Next.js app -- UI, Auth.js (Google OAuth), BFF proxy
api/                 FastAPI app + worker (shared Python package)
  api/app/           FastAPI routes, models, services
  api/worker/        APScheduler entrypoint + daily detection jobs
  api/providers/     pluggable data-source / LLM / search / notify interfaces
  api/alembic/       database migrations
.env.example         shared config template
DESIGN.md            full design doc
```

This PR seeds the tree, ignores, and config only; the apps and their manifests
land in later PRs (FastAPI, then the Next.js web app, then Docker Compose + CI).

## Configuration

Every service reads its config from environment variables. Copy the template and
fill in your own values:

```
cp .env.example .env
```

Never commit `.env` -- only `.env.example` is tracked.
