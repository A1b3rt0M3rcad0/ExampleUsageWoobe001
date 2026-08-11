# ExampleUsageWoobe001

A proof-of-value SaaS application showing an AI account assistant embedded into a real product surface.

The end-user application is branded **Northstar Cloud**. It deliberately does not present the AI control plane to the user. The user sees an operational SaaS console with service health, logs, detected problems and reports, while the assistant is operated through Woobe.

## Mock-only demo dataset

All operational telemetry in this repository is intentionally synthetic. Northstar does not wait for, ingest or depend on any external monitoring system for this proof of value.

The API seeds a fresh, internally consistent mock incident window on every startup. The current dataset includes several independent failure patterns so the assistant is not reduced to a single authentication example:

- database connection-pool saturation causing downstream API failures;
- revoked production credential still used by a legacy importer;
- intermittent customer webhook HTTP 503 failures;
- payment-provider authorization and capture timeouts;
- notification queue backlog and provider HTTP 429 responses;
- Redis cache hit-rate degradation, memory pressure and evictions;
- API Gateway traffic approaching the configured request-rate limit;
- a transient billing/invoice lock that recovered through retry.

The mock logs contain INFO, WARN and ERROR events across `api-gateway`, `database`, `orders-api`, `auth-api`, `webhook-worker`, `payments-api`, `notifications-worker`, `cache`, `billing-api` and `reporting-api`. Detected problems contain evidence that can be correlated with those logs. Timestamps are regenerated relative to application startup so the demo always looks current.

Reports created by the Woobe assistant remain normal application data and are persisted in SQLite; only synthetic logs and detected problems are refreshed on startup.

## What the demo proves

- ChatSurface embedded into a normal SaaS account experience.
- A Woobe Session bound server-side to the authenticated application user.
- Short-lived browser access; the ChatSurface Access Key never reaches the frontend.
- Account data, logs and detected problems exposed as narrow HTTP Tools.
- Agent/Network reasoning over current operational evidence.
- Correlation across several simultaneous mock incidents rather than one hard-coded answer path.
- AI-generated reports persisted back into the SaaS through a Tool call.
- Existing ChatSurface history/streaming behavior instead of a custom chat implementation.

The integration follows the `feature/chatsurface-mvp` behavior currently implemented in ProjectRAI: server-side Session creation, Session Access Token issuance, `WoobeChat.mount(...)`, immutable Session release binding and token refresh without rebuilding the conversation.

## Quick start with Docker

The application is designed to boot with Docker Compose only.

```bash
cp .env.example .env
docker compose up --build -d
```

Then open:

```text
http://localhost:5174
```

Demo credentials:

```text
Email:    demo@northstar.local
Password: demo123
```

Check container health with:

```bash
docker compose ps
```

Expected services:

```text
api   healthy   http://localhost:8001/health
web   healthy   http://localhost:5174
```

Stop the stack with:

```bash
docker compose down
```

Reset the demo database as well:

```bash
docker compose down -v
```

### Woobe credentials

Copying `.env.example` unchanged is enough to build and start the Northstar application. The embedded assistant requires an actual ChatSurface, so replace these values when you want the end-to-end Woobe integration to work:

```dotenv
WOOBE_CHAT_SURFACE_PUBLIC_ID=csf_...
WOOBE_CHAT_SURFACE_ACCESS_KEY=woobe_surface_...
WOOBE_TOOL_API_KEY=<same private key configured in the Woobe HTTP Tools>
```

The default local topology expects ProjectRAI/ChatSurface to be running on the host:

```text
Woobe API:     http://localhost:8000
Woobe embed:   http://localhost:8081/chat/v1/embed.js
Northstar API: http://localhost:8001
Northstar Web: http://localhost:5174
```

Inside the backend container, `WOOBE_API_BASE_URL` defaults to `http://host.docker.internal:8000`, including Linux support through the Compose `host-gateway` mapping.

## Demo flow

1. Sign in with the seeded demo account.
2. Review current service health, mock logs and detected problems.
3. Ask the embedded assistant questions such as:
   - `What is the most severe problem happening right now?`
   - `Why are order requests returning 503?`
   - `Is the database problem related to the order failures?`
   - `What is happening with payments?`
   - `Why are notifications delayed?`
   - `Which failures are external dependencies and which are internal?`
   - `Is the webhook problem related to the authentication problem?`
   - `Which issues should engineering prioritize first and why?`
   - `Generate an executive operational report with findings and recommendations.`
4. The configured Woobe Agent/Network reads the application's Tool API and correlates the synthetic evidence.
5. When a report is created, the Reports area updates after the ChatSurface Run completes.

The important behavior is that the assistant must inspect the mock evidence through Tools. There is no hidden integration with a real monitoring provider and no expected single canned diagnosis.

## Architecture

```text
Browser
├── Northstar Cloud UI
│   ├── Overview
│   ├── Logs
│   ├── Problems
│   └── Reports
│
└── Woobe ChatSurface iframe
      │ short-lived Session Access Token
      ▼
Woobe ChatSurface / Runtime
      │
      └── Agent or Network Release
            ├── GET account context
            ├── GET logs
            ├── GET problems
            └── POST operational report
                    │
                    ▼
           ExampleUsageWoobe001 API
                │
                └── deterministic mock operational dataset
```

The permanent ChatSurface Access Key exists only in `backend` and is used for Session creation/token issuance.

## Stack

- Backend: FastAPI + SQLite + httpx
- Frontend: React + TypeScript + Vite
- Chat UI: Woobe ChatSurface loader/iframe
- Runtime packaging: Docker Compose

## Docker behavior

`docker-compose.yml` builds both services, waits for the backend healthcheck before starting the web service, persists SQLite in a named volume, and configures both services with `restart: unless-stopped`.

Default host ports can be changed in `.env`:

```dotenv
APP_API_PORT=8001
APP_WEB_PORT=5174
```

If those ports are changed, also update the browser-visible URLs and `FRONTEND_ORIGIN` in `.env` so CORS and ChatSurface origin validation continue to match.

## Configure Tools in Woobe

See [`docs/WOOBE_SETUP.md`](docs/WOOBE_SETUP.md).

Important: Woobe HTTP Tools currently reject localhost/private-IP targets. The backend Tool API must be available on a public HTTPS endpoint for the Agent/Network to call it end to end.

## Security model

The repository intentionally preserves the current ChatSurface security split:

```text
Browser
  -> Surface Public ID
  -> Session Access Token (short-lived)

Application backend
  -> ChatSurface Access Key (persistent secret)

Woobe Tool runtime
  -> Tool API key (persistent server-to-server secret)
```

The demo is account-scoped to one seeded tenant because delegated per-user Tool identity is not part of the current ChatSurface MVP. Do not treat the demo Tool API as a general multi-tenant authorization template. The exact constraint and the safe production direction are documented in `docs/WOOBE_SETUP.md`.

## Repository intent

This is not a second AI platform and not a showcase of control-plane UI. It is an external SaaS whose AI feature is operated through Woobe. The value should be visible from the finished user experience first; Woobe can be revealed afterward as the infrastructure that configured, versioned, published and observed the AI product.
