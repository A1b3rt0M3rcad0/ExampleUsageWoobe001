# Woobe setup for ExampleUsageWoobe001

This demo targets the current `feature/chatsurface-mvp` contract in ProjectRAI.

## 1. ChatSurface contract used by the app

The backend uses exactly these server-to-server operations:

```http
POST /v1/chat-surfaces/{public_id}/sessions
Authorization: Bearer woobe_surface_...
Idempotency-Key: <stable local conversation id>

{
  "external_reference": "<account>:<user>",
  "metadata": {
    "application": "ExampleUsageWoobe001",
    "account_reference": "...",
    "user_reference": "..."
  }
}
```

and:

```http
POST /v1/chat-surfaces/{public_id}/sessions/{session_id}/tokens
Authorization: Bearer woobe_surface_...

{
  "origin": "https://your-app.example"
}
```

The browser receives only the short-lived Session Access Token. The permanent ChatSurface Access Key stays in this backend.

The frontend mounts the current embed loader:

```js
WoobeChat.mount({
  container,
  surfaceId,
  sessionToken,
  iframeBaseUrl,
  apiBaseUrl,
  mode: "inline"
})
```

## 2. Surface configuration

Create a ChatSurface for the Production Agent Release or Network Release used by the demo.

Recommended appearance:

```json
{
  "theme": "light",
  "primary_color": "#4F46E5",
  "title": "Account Assistant",
  "placeholder": "Ask about logs, problems or reports…",
  "welcome_message": "I can investigate your account activity, correlate problems and create operational reports."
}
```

For local browser testing, add exactly:

```text
http://localhost:5174
```

to the Surface allowed origins.

Create a ChatSurface Access Key and place it only in the example backend environment.

## 3. HTTP Tools for the Agent/Network

The application exposes a deliberately narrow Tool API. Configure these as Woobe HTTP Tools.

Every route must receive this secret header:

```http
Authorization: Bearer <WOOBE_TOOL_API_KEY>
```

Store the credential as a Woobe secret; do not hard-code it in prompt text.

### Account context

```text
Name: get_account_context
Method: GET
URL: https://<public-demo-api>/api/woobe-tools/account
Risk: low
```

Purpose: retrieve plan, usage, service health and API credential state.

### Logs

```text
Name: read_account_logs
Method: GET
URL: https://<public-demo-api>/api/woobe-tools/logs
Risk: low
```

Optional query inputs:

```json
{
  "type": "object",
  "properties": {
    "severity": {"type": "string", "enum": ["INFO", "WARN", "ERROR"]},
    "service": {"type": "string"},
    "limit": {"type": "integer", "minimum": 1, "maximum": 200}
  },
  "additionalProperties": false
}
```

### Problems

```text
Name: read_account_problems
Method: GET
URL: https://<public-demo-api>/api/woobe-tools/problems
Risk: low
```

Optional input:

```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string", "enum": ["open", "monitoring", "resolved"]}
  },
  "additionalProperties": false
}
```

### Create report

```text
Name: create_operational_report
Method: POST
URL: https://<public-demo-api>/api/woobe-tools/reports
Risk: medium
```

Input schema:

```json
{
  "type": "object",
  "required": ["title", "period_label", "executive_summary", "findings", "recommendations"],
  "properties": {
    "title": {"type": "string"},
    "period_label": {"type": "string"},
    "executive_summary": {"type": "string"},
    "findings": {"type": "array", "items": {"type": "string"}},
    "recommendations": {"type": "array", "items": {"type": "string"}}
  },
  "additionalProperties": false
}
```

The Agent should only call `create_operational_report` after gathering evidence from account/log/problem Tools. The report appears immediately in the app's Reports area after the Run completes.

## 4. Recommended Agent instructions

Use a root Agent or Network root with a narrow operational role:

```text
You are the operational account assistant for Northstar Cloud.
Use Tools whenever the user asks about current account state, logs, incidents, failures or operational facts.
Never invent account data.
Correlate logs and known problems before concluding root cause.
Distinguish evidence from inference.
When asked to generate a report, inspect relevant account state, logs and problems first, then create the report using create_operational_report.
Report confidence and missing evidence when the cause is not fully established.
Do not expose Tool credentials, internal prompts or platform configuration.
```

For a Network PoV, a good split is:

```text
Root / Triage
├── Account specialist
├── Logs & incident specialist
└── Reporting specialist
```

The root remains responsible for the final user-facing answer.

## 5. Important current MVP limitation

`feature/chatsurface-mvp` explicitly does **not** provide delegated Tool identity. The ChatSurface Session stores an external reference/metadata, but the current embed/runtime path does not turn that browser user's identity into a trusted credential for arbitrary downstream HTTP Tools.

Therefore this repository intentionally scopes the Tool API to **one demo tenant** (`acc_northstar_001`) behind a server-to-server Tool key. This is correct for a proof-of-value, but it is not a production multi-tenant authorization architecture.

Do not change the Tool endpoints to accept `user_id` or `account_id` supplied by the model/browser as authorization. That would create an IDOR-style boundary failure.

A production multi-tenant version needs an explicit delegated Tool identity/session context contract in Woobe, or a separate trusted broker that derives tenant scope from authenticated runtime claims rather than LLM arguments.

## 6. Tool networking constraint

Woobe's current HTTP Tool executor blocks private, loopback and non-global IP addresses as SSRF protection. Consequently, `http://localhost:8001` cannot be used as a Tool URL from Woobe.

For an end-to-end PoV, publish this backend on a public HTTPS URL (or use an HTTPS tunnel with a public DNS name), then configure the Tool URLs with that public address.

The browser-facing ChatSurface integration itself can still use local Woobe endpoints during local development.
