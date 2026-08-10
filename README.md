# ExampleUsageWoobe001

A proof-of-value SaaS application showing an AI account assistant embedded into a real product surface.

The end-user application is branded **Northstar Cloud**. It deliberately does not present the AI control plane to the user. The user sees an account console with operational data and an assistant capable of investigating that data and producing reports.

## What the demo proves

- ChatSurface embedded into a normal SaaS account experience.
- A Woobe Session bound server-side to the authenticated application user.
- Short-lived browser access; the ChatSurface Access Key never reaches the frontend.
- Account data, logs and detected problems exposed as narrow HTTP Tools.
- Agent/Network reasoning over current operational evidence.
- AI-generated reports persisted back into the SaaS through a Tool call.
- Existing ChatSurface history/streaming behavior instead of a custom chat implementation.

The integration follows the `feature/chatsurface-mvp` behavior currently implemented in ProjectRAI: server-side Session creation, Session Access Token issuance, `WoobeChat.mount(...)`, immutable Session release binding and token refresh without rebuilding the conversation.

## Demo flow

1. Sign in with the seeded demo account.
2. Review account usage, current service health, logs and detected problems.
3. Ask the embedded assistant questions such as:
   - `Why are authentication requests failing?`
   - `Is the webhook problem still happening?`
   - `What are the most important errors in the recent logs?`
   - `Generate an executive operational report with findings and recommendations.`
4. The configured Woobe Agent/Network reads the application's Tool API.
5. When a report is created, the Reports area updates after the ChatSurface Run completes.

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
```

The permanent ChatSurface Access Key exists only in `backend` and is used for Session creation/token issuance.

## Stack

- Backend: FastAPI + SQLite + httpx
- Frontend: React + TypeScript + Vite
- Chat UI: the Woobe ChatSurface loader/iframe
- Local orchestration: Docker Compose

## Local setup

### 1. Configure the example

```bash
cp .env.example .env
```

Set:

```dotenv
WOOBE_CHAT_SURFACE_PUBLIC_ID=...
WOOBE_CHAT_SURFACE_ACCESS_KEY=...
WOOBE_TOOL_API_KEY=...
```

### 2. Run Woobe ChatSurface branch

Run ProjectRAI from:

```text
feature/chatsurface-mvp
```

Expected local endpoints from that branch:

```text
Woobe API:        http://localhost:8000
Chat embed:       http://localhost:8081/chat/v1/embed.js
Control plane:    http://localhost:5173  # if running Woobe web separately
```

### 3. Start this application

```bash
docker compose up --build
```

Open:

```text
http://localhost:5174
```

Demo credentials:

```text
Email:    demo@northstar.local
Password: demo123
```

### 4. Configure Tools in Woobe

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
