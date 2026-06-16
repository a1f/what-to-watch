# What to Watch — Product Requirements & Technical Design

> Status: **Design complete, pre-build** · Author: Alex Fetisov · Last updated: 2026-06-15
> This document is the full design. Breaking it into PR-sized slices is the next, separate step (see §16).

---

## 1. Summary

**What to Watch** is a self-hosted, **reminder-first** movie & TV tracker with **AI-assisted discovery**. You add things you want to watch — from a trailer, a recommendation, or a vague memory — and the app watches the world for you. Through a **daily digest** delivered on the channels you choose, it tells you when:

- a **movie** hits **theaters** or **streaming**;
- the **next episode** of a show you follow **airs**;
- a show you love is **renewed or canceled**, or a **new season is announced** months out;

…while keeping your **"stack to watch"** queue and helping you decide what to watch tonight with **taste-aware, mood-based AI suggestions** and **"I can't remember that movie" recall**.

It runs **entirely on your own machine** on **free data sources**.

### Why this exists (evidence-backed positioning)

A 2026 competitive scan (24 sources, 25 claims adversarially verified) showed the reminder types people actually want are either **paywalled** (Trakt gates calendar email + iCal feeds behind VIP, which doubled to **$60/yr** in Feb 2025), **minimal** (Yamtrack/Flox do only basic upcoming-release alerts), or **locked behind a full media-server + downloader stack** (Overseerr/Jellyseerr/Ombi require Plex/Jellyfin + Sonarr/Radarr and only track your *local library*). **"Free, first-class, multi-type reminders without running a media server" is unserved.** That, plus AI discovery, is the wedge.

---

## 2. Goals & non-goals

### Goals
1. Never miss a release or new episode for anything you're tracking.
2. Make "what do I watch next / tonight" easy: a maintained queue + taste-aware AI discovery.
3. Stay free to run (free data APIs, self-hosted open-weight LLM) and private (your data on your box).
4. Be a real product foundation: real accounts/auth, multi-user-capable, portable from laptop to a cheap VPS with no rearchitecting.

### Non-goals (explicitly out of scope)
- **Price/sale tracking** — no reliable free multi-store source exists (JustWatch holds price data but is partner-gated; TMDB/Watchmode give availability only). Left out by decision; a clean provider seam is preserved (the known free Apple-only path is the iTunes Search API) but **no price feature is designed**.
- **Being a media server / downloader** — no Plex/Jellyfin/Sonarr/Radarr role. Reminders and tracking only.
- **Social network features** (followers, feeds, comments).
- **Native mobile apps** — responsive web + PWA-friendly only.
- **Sub-day / real-time notifications** — detection runs daily; reminders are a daily digest. (TMDB's availability data itself lags ~24–48h, so real-time would be false precision.)

---

## 3. Users & accounts

- **Multi-user-capable from day one**; only Alex uses it initially.
- **Auth:** Google OAuth via **Auth.js (NextAuth)** in the Next.js layer; the Next BFF forwards a signed identity (JWT) to FastAPI, which is the data authority. `users` are keyed by Google `sub` + email.
- All tracking data is **user-scoped** in the database.

---

## 4. Features — the four jobs

### Job A — Movie reminders
- Add a movie to your watchlist (search by title; results from TMDB with poster, year, rating, overview).
- Get reminded when it: reaches **theaters** (by your region), becomes available to **stream** (any service, or specifically a service you subscribe to), and **now free on a service you have**.
- *(Out of scope: digital price-drop/sale alerts.)*

### Job B — Future-season tracking
- Follow a show that's between seasons. Get reminded when:
  - it's **renewed** (high-confidence signal: a new season object appears on TMDB) or **canceled**;
  - a **new season is announced / dated** (6–12 months out and as it firms up).
- **Renew/cancel is multi-signal** (see §5) because free status fields frequently mislabel cancellations — each status is shown with a **source + confidence label** ("new season dated on TMDB" vs "reported canceled — web, 2 sources").

### Job C — Currently-airing shows + the stack
- Track airing shows; get the daily digest when a **new episode airs**.
- **Per-episode watched marks**; the app computes your **"stack to watch"** (aired-but-unwatched episodes) and a cross-show **Up Next**.
- The **Up Next queue is manually curated** for now (you order it); automated population/sorting is a later enhancement (the per-episode data already supports it).

### Job D — Discovery & AI
- **Smart rec lists** (no heavy graph viz): "Similar to X," "Because you watched Y," "Highly rated in {genre} you can stream now" — from TMDB similar/recommendations + OMDb ratings + your taste + an availability filter.
- **AI mood search:** natural language → suggestions ("something tense and short on a service I have tonight").
- **"Can't-remember" recall:** vague description → identify the title (web-search-grounded).
- **Find-similar** by title or description.
- All AI results are **resolved to real TMDB titles** (poster, availability, one-tap "add to watchlist").

---

## 5. Detection engine & event catalog

A single **daily scheduled run** (APScheduler worker) drives all reminders. Each run, for the union of all users' tracked items:

1. **Refresh** cached metadata for due titles (respecting rate limits / TTLs).
2. **Detect changes** against the previous cached state → write **events**.
3. **Enrich** ambiguous show statuses with an LLM + web-search pass (see below).
4. **Dispatch** the day's events to the in-app feed and, per user prefs, the daily digest.

### Event catalog

| Event type | Source signal | Confidence |
|---|---|---|
| `movie.theatrical_release` | TMDB regional release_dates (type 3) | high |
| `movie.now_streaming` | TMDB watch-providers gains a flatrate offer | high (lags ~24–48h) |
| `movie.now_on_your_service` | watch-providers ∩ user's subscribed services | high |
| `show.next_episode_dated` | TMDB/TVmaze episode air_date set | high |
| `show.episode_aired` | episode air_date passes | high |
| `show.new_season_announced` | new season object appears on TMDB | high |
| `show.season_finale` / `show.series_finale` | derived from season/episode structure + status | medium |
| `show.renewed` | new season object appears (primary) + status | high |
| `show.canceled` | TMDB status `Canceled` **or** LLM+web enrichment | labeled (see below) |
| `show.now_streaming` | watch-providers for the show | high (lags) |

> "Now streaming" is detected by **polling watch-providers per tracked title** each run — TMDB does **not** expose provider changes via its Changes API, and the data is a once-daily JustWatch export (~24–48h lag). At personal watchlist sizes this is cheap; for a few high-priority titles we can optionally cross-check the Watchmode free tier (2,500 req/mo, 3 countries).

### Renew/cancel enrichment (the hard part)
Free status fields are reliable for **renewed** (a new season object is a strong positive) but weak for **canceled** (TMDB often leaves canceled shows as "Ended" or "Returning"). So:
- Combine **TMDB status transitions + new-season-object detection + TVmaze status**.
- For tracked returning/ended shows whose free status is **ambiguous**, run a periodic **Ollama + SearXNG web-search enrichment** ("has {show} been renewed or canceled? cite sources") and store the verdict with its sources.
- Every renew/cancel state is surfaced with a **source + confidence label**; the LLM verdict never silently overrides a strong free signal.

---

## 6. Data sources & sync

Best-of-breed **free tiers**, with **TMDB as the hub** and **IMDb ID as the cross-source join key** (TMDB ↔ TVmaze ↔ OMDb all map to it).

| Need | Source | Notes |
|---|---|---|
| Catalog, posters, genres, release dates, seasons/episodes, **show status**, watch-providers, similar/recommendations, external IDs | **TMDB** (free key) | The backbone. |
| Precise episode **airtimes** + show status | **TVmaze** (free, no key) | Secondary TV signal. |
| **Ratings** (IMDb/RT/Metacritic) | **OMDb** (free ~1k/day) | Enrichment. |
| Web grounding for recall + renew/cancel | **SearXNG** (self-hosted) or a free search API | Feeds the LLM. |

**Sync strategy:** a local **cache/mirror** of titles, seasons, episodes, and watch-provider snapshots in Postgres. Selective polling (TTL per entity; refresh tracked items more often than cold catalog rows) to respect free-tier limits. All external responses cached; raw JSON retained for reprocessing.

---

## 7. Tracking model

**Statuses**
- **Movies:** `Watchlist` → `Watched` (with optional watched date + personal rating).
- **Shows:** `Watchlist` → `Watching` → `Completed`, plus `Paused` / `Dropped`. Per-episode progress underneath.
- Any title can sit in `Watchlist` purely for reminders without being watched yet.

**Progress:** **per-episode** watched marks (supports out-of-order viewing, history, future stats). "Stack to watch" = aired-but-unwatched episodes per Watching show.

**Queue:** a **manually curated** cross-show **Up Next** (pin/reorder/snooze). Auto-population/sorting is a later enhancement; the data already supports it.

**Personal rating:** lightweight per-title rating, used to feed taste-aware discovery.

---

## 8. Notifications

**Channels (all in the design):**
- **In-app feed** — a "what's new" list + unread badge; the canonical home for every event.
- **Apprise** — one dispatcher fanning out to **email (SMTP)** plus opt-in **Telegram / Discord / ntfy / Pushover / …**. (This replaces wiring a standalone email provider and matches what self-hosters expect.)
- **iCal feed** — a free, tokenized, subscribable `.ics` of your upcoming releases & episode air dates (subscribe in Google/Apple Calendar). This is the exact capability Trakt paywalls behind VIP.

**Cadence:** a **daily digest** aligned to the daily detection run — one well-formatted summary of new + upcoming items. A **per-user notification-preferences model** governs: which channels, which event types, cadence, and **lead times** (default: notify on release day + optional "X days before" heads-up for theatrical / returning seasons).

---

## 9. Discovery & AI

**Rec lists** are classic + cheap: TMDB similar/recommendations + OMDb ratings, filtered by your taste and current availability, surfaced as browsable rows.

**AI features** (mood search, recall, find-similar) use a **grounded LLM**:
- **Runtime:** **Ollama** (OpenAI-compatible) running a local **open-weight instruct model** (Qwen2.5/Qwen3 or Llama 3.x, sized to the host's hardware), behind a **pluggable provider interface** (OpenAI-compatible client) so the model is swappable and a hosted fallback for the hardest recall stays possible with no code change.
- **Grounding:** tool access to our catalog + TMDB discover, and **SearXNG** web search for recall/news; pass the user's taste (watchlist/ratings) as context.
- **Structure:** **guided/JSON decoding** so results come back as typed objects, then **resolved to real TMDB titles** for posters, availability, and one-tap add.

> Framing note: the research did **not** establish the AI-discovery competitive landscape, so we treat AI discovery as **differentiated, not proven-unique**.

---

## 10. Architecture

Decoupled services on one Docker Compose network, on the local host (portable to a VPS unchanged):

```
        Browser
           │  HTTPS
           ▼
   ┌───────────────────────────┐
   │  Next.js (React, TS)      │  SSR/UI · Auth.js Google OAuth · BFF proxy
   └───────────┬───────────────┘
               │  server→server, signed JWT identity
               ▼
   ┌───────────────────────────┐        ┌──────────────┐
   │  FastAPI (REST API)        │◄──────►│  Postgres    │
   └───────────┬───────────────┘        │  (+pgvector  │
               ▲                         │   reserved)  │
               │ shares code/db          └──────▲───────┘
   ┌───────────┴───────────────┐                │
   │  APScheduler worker        │────────────────┘
   │  (daily detect → enrich    │
   │   → dispatch digest)       │
   └─┬───────┬────────┬────────┬┘
     │       │        │        │
     ▼       ▼        ▼        ▼
   TMDB   TVmaze/   Ollama   SearXNG     Apprise (email/Telegram/Discord/ntfy)
          OMDb      (LLM)    (search)    + iCal feed endpoint (served by FastAPI)
```

**Request/auth flow:** the browser only talks to the Next.js origin (same-site cookies); Auth.js handles Google sign-in; Next's BFF calls FastAPI server-side with a signed identity. FastAPI owns all data and business logic. The worker shares the FastAPI codebase/DB and runs the schedule.

**Scheduler:** APScheduler in its **own worker process** (graduate to `arq` + Redis only if we later need queues/retries/concurrency; not Celery).

---

## 11. Data model (schema sketch)

```
users(id, google_sub, email, display_name, subscribed_services[], region, created_at)
titles(id, tmdb_id, imdb_id, type[movie|show], title, year, overview, poster_path,
       genres[], show_status, number_of_seasons, ratings{tmdb,imdb,rt,metacritic},
       last_synced_at, raw_json)
seasons(id, title_id→titles, season_number, air_date, episode_count)
episodes(id, title_id→titles, season_number, episode_number, name, air_date, runtime, last_synced_at)
availability(title_id→titles, country, providers_json, fetched_at)        -- TMDB watch-providers snapshot
tracked_items(id, user_id→users, title_id→titles,
              status[watchlist|watching|completed|paused|dropped|watched],
              rating, notes, priority, snoozed_until, added_at)
episode_watches(id, user_id→users, episode_id→episodes, watched_at)       -- per-episode progress
queue_items(id, user_id→users, kind[show_episode|movie], ref_id, position, added_at)
status_findings(id, title_id→titles, verdict[renewed|canceled|unknown],
                source[tmdb|tvmaze|llm_web], confidence, sources_json, found_at)
events(id, user_id→users, title_id→titles, type, payload_json, source, confidence,
       detected_at, seen_at)                                              -- in-app feed + digest source
notifications(id, user_id→users, event_ids[], channel, status, digest_date, sent_at)
notification_prefs(id, user_id→users, cadence, lead_times_json,
                   enabled_event_types[], apprise_urls[], ical_token, channel_config_json)
```

Migrations via **Alembic**; ORM via **SQLAlchemy/SQLModel**.

---

## 12. Tech stack & repo layout

| Layer | Choice |
|---|---|
| Frontend | **Next.js** (React, TypeScript); Tailwind + a component kit; typed API client generated from FastAPI's OpenAPI |
| Auth | **Auth.js** Google OAuth in Next; BFF → FastAPI (signed JWT) |
| Backend | **Python + FastAPI**; SQLAlchemy/SQLModel + Alembic |
| DB | **Postgres** (pgvector reserved for later semantic similarity) |
| Worker/scheduler | **APScheduler** (own process) |
| AI | **Ollama** (open-weight, OpenAI-compatible) behind a pluggable provider interface; **SearXNG** for grounding |
| Notifications | **Apprise** (email + push channels) + a generated **iCal** feed |
| Packaging | **Docker Compose** (web, api, worker, postgres, ollama, searxng) |

**Repo re-seed:** the current `.gitignore` is a Rust/Cargo template — swap it for Python/Node as the first setup step.

**Proposed layout:**
```
/web                 Next.js app (UI + Auth.js + BFF)
/api                 FastAPI app + worker (shared package)
  /api/app           FastAPI routes, models, services
  /api/worker        APScheduler entrypoint + detection jobs
  /api/providers     pluggable interfaces: data sources (TMDB/TVmaze/OMDb), LLM (Ollama), search (SearXNG), notify (Apprise)
  /api/alembic       migrations
docker-compose.yml
.env.example
DESIGN.md            (this file)
```

---

## 13. Risks & validation spikes

1. **Renew/cancel accuracy (Job B)** — the riskiest data dependency. *Spike:* before relying on it, check TMDB/TVmaze status + new-season detection + the LLM/web enrichment against a set of known recently renewed/canceled shows; tune confidence thresholds.
2. **AI-discovery quality** — depends on the chosen open-weight model and the host's hardware. *Spike:* benchmark recall/mood quality across a couple of models (Qwen vs Llama, sizes) on real prompts before committing.
3. **TMDB availability lag (~24–48h)** — accepted; daily-digest cadence makes it a non-issue. Documented so it isn't mistaken for a bug.
4. **Free-tier rate limits** — caching + selective polling must stay disciplined; watch OMDb's ~1k/day cap as tracked-item count grows.
5. **Time-sensitive facts** — re-verify Trakt pricing and all API tiers/limits before building (the landscape shifts often).

---

## 14. Competitive landscape & differentiation (from research)

Verified facts that shape positioning:
- **Trakt** has the most granular reminders (per-episode iCal `&alarm=X`) but **paywalls calendar email + iCal feeds** behind VIP (**$30→$60/yr, Feb 2025**); free notifications are social-only.
- **TMDB** watch-providers = once-daily JustWatch export, **~24–48h lag**, no Changes-API exposure, **no price**.
- **JustWatch** holds real price data but is **partner-gated**; **Watchmode** free tier = availability only (2,500 req/mo, 3 countries).
- **Yamtrack** (AGPL — reference only, no code copied) is the nearest analog: Apprise + iCal, **basic reminders only**. **Flox/MediaTracker** minimal/stale. **Seerr/Ombi** require a full media-server + downloader stack.

**Differentiation we can own:** free unlimited reminders (vs Trakt's paywall); reminder **types** no verified competitor offers (theatrical→streaming, leaving-soon, renew/cancel, new-season-6–12mo); **zero media-server requirement**; multi-channel push + free iCal as table stakes; AI discovery as the differentiator.

---

## 15. Explicitly out of scope (recap)
Price/sale tracking · media server / downloads · social features · native mobile apps · real-time notifications · interactive similarity-graph visualization (rec lists instead).

---

## 16. Next step — slicing (separate pass)
This design is complete. The next step is to break it into **vertical, buildable slices / PRs** (tracer bullet first: add a title → detect a change → deliver a reminder end-to-end, then widen). That slicing is intentionally **not** done here.

---

## Appendix — research provenance
Deep-research pass, 2026-06-15: 6 angles, 24 sources fetched, 110 claims extracted, 25 adversarially verified (16 confirmed / 9 killed). Primary sources included Trakt support/forums, TMDB's own staff forum thread on provider-data latency, the Watchmode and JustWatch API docs, and the Yamtrack/Flox/MediaTracker/Seerr/Ombi repositories. Coverage gaps (treated as unknown, not settled): the AI-discovery tool landscape, and renewal/cancellation data accuracy.
