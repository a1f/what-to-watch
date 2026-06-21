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

## Web: typed API client

The web app talks to the API through a generated TypeScript client. When the
FastAPI schema changes, refresh the snapshot and regenerate the types:

```
uv run python -c "import json,sys; from api.app.main import app; json.dump(app.openapi(), sys.stdout, indent=2)" > web/openapi.json
pnpm --filter @wtw/web generate:api
```

Both `web/openapi.json` and the generated `web/src/lib/api/schema.ts` are
committed; do not hand-edit the generated schema.
