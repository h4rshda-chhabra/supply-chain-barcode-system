# QR Code Tracking & Traceability Platform — MVP

End-to-end material and product traceability for manufacturing, built on QR
codes. Every raw-material batch and every finished-goods batch gets a unique
**Trace ID** (`TRC-YYYY-NNNNNN`) and a QR code; scanning it opens a live
traceability timeline from goods receipt through dispatch.

Stack: **React 18 + TypeScript + Vite + Tailwind** (frontend) · **FastAPI +
SQLAlchemy** (backend) · **PostgreSQL** (database) · **Docker Compose**
(deployment).

---

## 1. Quick start (Docker Compose)

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API docs (Swagger): http://localhost:8000/docs
- Postgres: localhost:5432 (`traceuser` / `tracepass` / `traceability`)

On first boot the backend automatically creates the schema and seeds
realistic demo data (10 suppliers, 15 customers, 50 products, 200 GRNs,
~500 issue movements, 100 production orders with consumption, 100 finished
goods batches, 100 dispatches — all with generated QR codes). Re-running
`docker compose up` is safe; the seed step detects existing data and skips.

To wipe and reseed: `docker compose down -v && docker compose up --build`.

## 2. Local development (without Docker)

**Backend**

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # or source .venv/bin/activate
pip install -r requirements.txt
# Start a local Postgres, then create backend/.env from .env.example
# pointing DATABASE_URL at it (e.g. localhost:5432)
alembic upgrade head           # creates the schema (see §4a)
uvicorn app.main:app --reload
python -m app.seed.seed_data   # optional, generates demo data
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` and `/static` to `http://localhost:8000` (see
`frontend/vite.config.ts`), so the two run independently in dev.

---

## 3. Folder structure

```
barcode/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                # FastAPI app, router wiring
│   │   ├── core/                  # config.py (env settings), database.py (engine/session)
│   │   ├── models/                # SQLAlchemy ORM models (one file per entity) + enums.py
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── services/               # Business logic layer (see §5)
│   │   ├── routers/                # Thin FastAPI route handlers, one per module
│   │   └── seed/seed_data.py      # Demo data generator
│   └── migrations/                # Alembic revision history (see §4a)
└── frontend/
    ├── Dockerfile, nginx.conf
    └── src/
        ├── api/                   # axios client + TS types mirroring backend schemas
        ├── hooks/useApi.ts        # React Query hooks (one per resource)
        ├── components/layout/     # Sidebar, Topbar, Layout
        ├── components/ui/         # DataGrid (AG Grid), Modal, StatCard, StatusBadge
        ├── components/QRPreview.tsx
        ├── pages/                 # Dashboard, GRN, Batches, Issue, Production,
        │                          # ProductionDetail, FinishedGoods, Dispatch,
        │                          # Traceability, Reports
        └── App.tsx                # Routes
```

## 4. Database schema

### 4a. Migrations (Alembic)

Schema is managed by Alembic, not `create_all` — `backend/migrations/`
holds the revision history, starting from `baseline_schema` (the full
12-table schema). The Docker Compose `backend` command runs
`alembic upgrade head` automatically before every start, so `docker compose
up` always leaves the DB schema in sync with the code.

When you change a model, generate a migration for it before committing:

```bash
cd backend
alembic revision --autogenerate -m "add xyz column"
alembic upgrade head   # apply it locally to verify
```

Always read the generated migration before applying it — autogenerate is a
diff tool, not a guarantee (it won't reliably detect renames, and won't
generate data-migration/backfill logic).

All entities from the spec are modelled (see `backend/app/models/`):
`suppliers`, `customers`, `products`, `grns`, `batches`, `qr_codes`,
`inventory_movements`, `production_orders`, `production_consumption`,
`finished_goods`, `dispatches`, `audit_logs`.

**`batches` is the central traceability node.** Every raw-material lot
(from a GRN) and every finished-goods lot (from a Production Order) is
exactly one `Batch` row, carrying the `trace_id` that the QR code encodes.
Everything else — movements, consumption, dispatches — hangs off `batch_id`:

```
Supplier ──< GRN >── Product
              │
              ▼
            Batch (RAW_MATERIAL) ──1:1── QRCode
              │
              ├──< InventoryMovement (ISSUE, RECEIPT, ...)
              │
              └──< ProductionConsumption >── ProductionOrder ──< FinishedGoods
                                                                       │
                                                                       ▼
                                                    Batch (FINISHED_GOOD) ──1:1── QRCode
                                                                       │
                                                                       └──< Dispatch >── Customer
```

Master data (`suppliers`, `customers`, `products`) each carry a nullable
`erp_reference_no` column reserved for the future Dynamics NAV item/vendor/
customer "No." — unused today, but means the sync job doesn't need a schema
migration when it lands.

## 5. Service layer architecture

Routers stay thin; all mutation logic (and its invariants — quantity checks,
audit logging, status transitions) lives in `app/services/`:

| Service | Responsibility |
|---|---|
| `id_generator.py` | Sequential document numbers (`TRC-`, `GRN-`, `PO-`, `FG-`, `DIS-`, `REQ-`) |
| `qr_service.py` | Renders + persists PNG/SVG QR assets for a trace ID |
| `batch_service.py` | Creates a `Batch` + its `QRCode` atomically (used by both GRN and FG creation) |
| `grn_service.py` | Goods receipt: batch + QR + GRN row + RECEIPT movement |
| `movement_service.py` | Request & Issue: validates and deducts quantity, logs movement |
| `production_service.py` | Raw-material consumption (QR scan) and finished-goods batch creation |
| `dispatch_service.py` | Ships a scanned FG batch to a customer |
| `audit_service.py` | Single `log_action(...)` helper used by every mutating service |
| `traceability_service.py` | Walks the graph above to build the `/trace/{traceId}` timeline |

The demo-data generator (`seed/seed_data.py`) calls these exact same
services — so the data it produces is guaranteed to be exactly as valid as
data created through the UI, and the traceability engine is exercised the
same way in both cases.

## 6. QR code design

- The QR image encodes `{TRACE_PUBLIC_BASE_URL}/trace/{traceId}` so a
  standard phone camera opens the traceability page directly on scan.
- The logical payload is kept minimal — `{"traceId": "TRC-2026-000001"}` —
  no batch, product, quantity, or customer data is ever embedded in the
  code itself, so nothing sensitive leaks if a label is photographed.
- Both PNG (for labels/printing) and SVG (for scalable reprints) are
  available for every batch. Images are **rendered on demand**
  (`GET /api/v1/qr-codes/{traceId}/image?format=png|svg`) from the
  trace ID + target URL already in the database, rather than pre-rendered
  and saved to disk — so the app needs no persistent file storage at all,
  which matters on platforms (Render's standard web services, most
  serverless/container hosts) whose filesystem doesn't survive a restart.
  Download and reprint actions are audit-logged (`QR_DOWNLOADED`,
  `QR_PRINTED`).

## 7. Traceability engine

`GET /api/v1/trace/{traceId}` (frontend route `/trace/:traceId`) returns:

- the batch summary,
- its QR asset URLs,
- a chronologically-sorted **timeline** (`GRN Received → Warehouse →
  Material Issued → Production Consumed → Finished Goods Created →
  Dispatched`), built dynamically from whichever of those stages actually
  happened to this batch,
- **upstream raw materials** (for a finished-goods trace ID — every lot
  that went into it) and **downstream finished goods** (for a raw-material
  trace ID — everything it was turned into and where that shipped).

## 8. API surface

All endpoints are under `/api/v1` (see http://localhost:8000/docs for the
full interactive schema):

```
suppliers, customers, products         CRUD (list/create/get)
grns                                   list, create (→ batch + QR)
batches                                list (filter by type/status/search), get by trace_id
qr-codes/{traceId}                     get, /image?format=png|svg, /print, /download?format=png|svg
movements, movements/issue             list, create (Request & Issue)
production-orders                      list, create, get, /consumption, /consume
finished-goods                         list, create, get
dispatches                             list, create
trace/{traceId}                        full traceability timeline
dashboard/summary, dashboard/trends    KPI cards + 30-day trend series
audit-logs                             full audit trail
```

## 9. MVP simplifications & upgrade path

Per spec, this MVP intentionally ships **without** authentication, ERP
integration, RFID, or a mobile app — but the architecture doesn't fight
adding them later:

- **RBAC / approval workflows** — `Settings.ENABLE_RBAC` /
  `ENABLE_APPROVAL_WORKFLOWS` flags exist as no-ops; the service layer's
  `performed_by` parameter (currently defaulted to `"system"`) is already
  threaded through every mutation and audit log entry, ready to be wired
  to a real principal once auth exists.
- **Dynamics NAV 2016 sync** — `erp_reference_no` columns on
  Supplier/Customer/Product are reserved for NAV's `No.` fields;
  `Settings.ENABLE_NAV_SYNC` is a placeholder flag. A sync job would live
  as a new `services/nav_sync_service.py` populating those columns and
  master data — no changes needed to batches, movements, or the
  traceability engine.
- **Customer portal** — `GET /trace/{traceId}` is already a public,
  read-only, non-sensitive endpoint (see QR design above), so a
  customer-facing view is a routing/auth concern, not a data-model change.
- **Recall management** — `downstreamFinishedGoods` in the traceability
  response already answers "what shipped and to whom" for any raw-material
  lot; a recall feature is primarily a UI (bulk trace + notify) on top of
  data this API already returns.

## 10. Step-by-step implementation plan (as delivered)

1. **Schema & models** — define all 12 entities in SQLAlchemy
   (`app/models/`), with enums for status/type fields and a shared
   `TimestampMixin`.
2. **Core services** — ID generation, QR rendering, and the
   `create_batch_with_qr` primitive that GRN and Finished Goods both build on.
3. **GRN module** — supplier/product/batch capture → batch + QR generation
   → GRN record, wired end-to-end (API + form UI).
4. **QR system** — PNG/SVG generation, static serving, download/reprint
   endpoints with audit logging.
5. **Request & Issue** — scan-to-lookup UX, quantity validation, movement
   ledger.
6. **Production consumption** — production orders, multi-scan raw-material
   consumption against a PO.
7. **Finished goods** — FG batch + QR generation from a production order,
   rolling produced quantity back onto the order.
8. **Dispatch** — scan-to-ship against a customer, quantity validation.
9. **Traceability engine** — graph walk producing the timeline +
   upstream/downstream views; `/trace/:traceId` page.
10. **Dashboard & reports** — KPI cards, 30-day trend charts (Recharts),
    audit trail (AG Grid).
11. **Demo data** — seed script reusing the exact same services, so the
    demo is a faithful stand-in for real usage.
12. **Docker Compose** — one-command spin-up of Postgres + API + frontend,
    with automatic (idempotent) seeding on first boot.

## 11. Deploying to a real environment

### 11a. Self-hosted (Docker Compose)

The frontend nginx container proxies `/api/` to the backend on the internal
Docker network (see `frontend/nginx.conf`), so in the standard Compose
topology the browser only ever talks to one origin — CORS doesn't come into
play, and no extra config is needed there.

Two things do need to be set correctly for a real deploy, both via
environment variables on the `backend` service:

- **`TRACE_PUBLIC_BASE_URL`** — the public URL a scanned QR code should
  open, e.g. `https://trace.acme-manufacturing.com`. This gets encoded
  *into the QR image itself* at batch-creation time (see `qr_service.py`);
  it is not something a running deploy can retroactively fix for QR codes
  that have already been generated and printed. Set it correctly **before**
  any real GRN/production data is created. As a safety net, the app
  refuses to start with `ENVIRONMENT=production` if this still points at
  `localhost`/`127.0.0.1`.
- **`ENVIRONMENT`** — set to `production` to enable the guard above.

If you split the frontend and backend across different hosts/domains
instead of using the bundled nginx proxy (e.g. frontend on one PaaS, API on
another), CORS *does* matter — the backend automatically allows whatever
`TRACE_PUBLIC_BASE_URL` is set to, and you can add further origins via the
comma-separated `CORS_ORIGINS` env var (e.g.
`CORS_ORIGINS=https://admin.acme.com,https://staging.acme.com`).

Also worth hardening for a production deploy (not done by the default
`docker-compose.yml`, which is tuned for local use):

- Don't publish Postgres's `5432` to the host/internet — the `backend`
  service only needs it on the internal Compose network.
- Put a real TLS-terminating reverse proxy (or a platform load balancer) in
  front of the `frontend` container rather than exposing it on a raw HTTP
  port directly.
- Change the default `POSTGRES_PASSWORD` / `traceuser` credentials.

### 11b. Split deploy: Vercel (frontend) + Render (backend + Postgres)

This topology puts the frontend and backend on different origins/domains,
so unlike §11a, the pieces below (`vercel.json`'s rewrite, `TRACE_PUBLIC_BASE_URL`,
CORS) all matter and are wired together for you already — just follow the
order below, since a couple of steps depend on values produced by earlier
ones.

**How it avoids CORS entirely:** `frontend/vercel.json` makes Vercel proxy
any `/api/*` request straight through to the Render backend at the edge, so
the browser only ever talks to your Vercel domain — exactly what
`frontend/nginx.conf` does locally, just on Vercel's infrastructure instead
of an nginx container. CORS headers are irrelevant to this path (though the
backend still sends permissive ones as a fallback for direct API access,
e.g. hitting the Render URL's `/docs` from elsewhere).

**Step 1 — push to GitHub.** Both Vercel and Render deploy by watching a
GitHub repo.

**Step 2 — deploy the frontend to Vercel** (do this *before* Render, see
why in step 3):
1. [vercel.com/new](https://vercel.com/new) → import the repo.
2. **Root Directory**: `frontend`. Framework preset: Vite (auto-detected).
   Build command / output directory: leave the Vite defaults (`npm run
   build` / `dist`).
3. Deploy. Note the resulting URL, e.g. `https://your-project.vercel.app`.

`frontend/vercel.json` already rewrites `/api/*` to
`https://traceability-backend.onrender.com` — the URL Render will assign
based on the `name: traceability-backend` in `render.yaml` — so the
frontend build doesn't need to know the backend's URL at build time.

**Step 3 — deploy the backend to Render, using the Vercel URL from step 2:**
1. [dashboard.render.com](https://dashboard.render.com) → **New +** →
   **Blueprint** → pick the repo. Render reads `render.yaml` at the repo
   root and provisions both the Postgres database and the API web service.
2. When prompted for `TRACE_PUBLIC_BASE_URL` (marked `sync: false` in
   `render.yaml` because it can't be known ahead of time), paste the
   **Vercel URL from step 2**. This has to be right *before* the first
   deploy — the backend seeds demo data and generates its first QR codes
   as part of that first boot, and `TRACE_PUBLIC_BASE_URL` is baked into
   each one at creation time (see §11a above).
3. Apply. First deploy runs `alembic upgrade head`, seeds demo data, then
   starts serving — watch the deploy log for all three.
4. Once live, confirm the assigned URL is exactly
   `https://traceability-backend.onrender.com`. Render.com service names
   are globally unique, so on the very small chance that name was already
   taken, Render will have asked you to pick a different one during setup
   — if so, update the `destination` in `frontend/vercel.json` to match,
   push, and Vercel redeploys automatically (seconds, not a rebuild of
   anything on the Render side).

**Step 4 — verify end to end:**
- Open the Vercel URL, create a GRN, then open its Trace ID's `/trace/...`
  page and confirm the QR image renders and its download links work (this
  round-trips through Vercel → Render → back, proving the rewrite works).
- Scan the QR with a phone (or check the target URL shown on that page) —
  it should open `https://your-project.vercel.app/trace/...`, not a Render
  or localhost URL.

**Notes / limitations of the `render.yaml` as committed:**
- Both services use Render's **free** plan: the web service spins down
  after ~15 min of no traffic (next request wakes it, ~30-60s cold start),
  and the free Postgres database **expires after 90 days** unless upgraded
  to a paid plan. Fine for a demo; switch `plan: free` to `plan: starter`
  (or higher) in `render.yaml` for anything longer-lived.
- Demo data seeding is on by default (`python -m app.seed.seed_data` in
  `startCommand`) — it's idempotent (skips if data already exists) so it's
  harmless to leave in, but if you don't want the fictional demo
  suppliers/products/batches in what becomes a real deployment, drop that
  segment from `startCommand` before the first deploy.
- `region: oregon` is used for both services so they share a network
  region (lower latency, and Render's internal DB networking works best
  within one region) — change both if you're closer to another Render
  region.
