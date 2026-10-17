# MindTrail API Contract and Readiness

This document tells frontend developers which backend behavior exists, which behavior is planned, and which compatibility gaps must be handled during the MVP.

## Source of truth

- Interactive documentation: `http://127.0.0.1:8000/docs`
- OpenAPI document: `http://127.0.0.1:8000/openapi.json`
- Versioned base path: `/v1`
- Frontend integration guide: `docs/FRONTEND_HANDOFF.md`

When this document conflicts with the generated OpenAPI document for an implemented endpoint, treat OpenAPI and backend tests as the executable contract and update this document.

## Environment URLs

| Client | Development URL |
|---|---|
| Expo web | `http://127.0.0.1:8000` |
| Android emulator | `http://10.0.2.2:8000` |
| Physical device | `http://<computer-LAN-IP>:8000` |

Physical devices require Uvicorn to bind to the network interface:

```powershell
uvicorn api.app.main:app --reload --host 0.0.0.0
```

This exposes the development server to the local network. Do not use the development server as a production deployment.

## Implemented routes

| Method | Path | Auth | Status |
|---|---|---|---|
| `GET` | `/health` | None | Implemented |
| `GET` | `/v1/health` | None | Implemented |
| `GET` | `/v1/checkins/today` | Session cookie or bearer token | Returns the form and the signed-in user's `completed` state for today |
| `POST` | `/v1/auth/register` | None | Implemented for local demo |
| `POST` | `/v1/auth/login` | None | Implemented for local demo |
| `GET` | `/v1/auth/me` | Session cookie or bearer token | Implemented for local demo |
| `POST` | `/v1/auth/logout` | Session cookie | Implemented for local demo |
| `GET` | `/v1/me/dashboard` | Session cookie or bearer token | Date-wise relational history plus a non-diagnostic ML trend indicator |
| `GET` | `/v1/admin/dashboard?days=30` | Administrator session only | Aggregate completion and wellbeing statistics; 7–180 days |
| `GET` | `/v1/me/consent` | Student session | Current trend-personalization choice |
| `POST` | `/v1/me/consent` | Student session | Append a new personalization consent decision |
| `GET` | `/v1/me/export` | Authenticated owner | Complete JSON export of the caller's account, check-ins, answers, and consent history |
| `DELETE` | `/v1/me/data` | Student session + password | Permanently delete the caller's account and related records after `DELETE` confirmation |
| `POST` | `/v1/checkins` | Session cookie or bearer token | Validates and stores one check-in per user per date; duplicates return HTTP 409 |

## Planned routes

| Area | Routes |
|---|---|
| Authentication | Refresh, password reset, and production identity provider integration |
| Consent | `GET/PUT /v1/me/consent` |
| Submission | `POST /v1/checkins` |
| Conversations | `/v1/conversations/*`, `/v1/me/conversations` |
| Personal data | `/v1/me/baseline`, `/flags`, `/dashboard`, `/pulse`, `/export` |
| Deletion | `DELETE /v1/me/data` |
| Nudges | `/v1/me/nudges/*` |
| Peer support | `/v1/peers/*` |
| Resources | `/v1/resources`, `/v1/counsellors` |
| Appointments | `GET/POST /v1/appointments` |
| Escalations | `/v1/escalations/*`, `/v1/me/escalations` |
| Staff | `/v1/staff/*` |
| Administration | `/v1/admin/*` |
| Ingestion | `/v1/ingest/*` |

Frontend code must place planned routes behind mockable repository interfaces. A screen must not claim that a planned operation succeeded.

## Success envelope

Implemented success responses are serialized as:

```json
{
  "data": {},
  "error": null
}
```

`data` depends on the endpoint. The frontend must reject a successful HTTP response if both `data` and a meaningful successful empty-state contract are absent.

## Target error envelope

The intended contract is:

```json
{
  "data": null,
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": {}
  }
}
```

Target domain codes include:

- `validation_error`
- `not_found`
- `method_not_allowed`
- `internal_error`
- `consent_required`
- `already_checked_in`
- `rate_limited_chat`

## Current error compatibility gap

The backend does not yet register exception handlers. FastAPI currently returns its default error shapes for framework errors, including:

```json
{
  "detail": []
}
```

This affects validation errors and may also affect `404`, `405`, and unexpected server errors. Until standardized handlers are implemented, the client should resolve an error message in this order:

1. `payload.error.message`
2. A string `payload.detail`
3. Validation details mapped to a short readable message
4. A generic message based on HTTP status

Do not expose stack traces or raw server exception text to students.

## CORS readiness

CORS middleware is not yet implemented. Native Expo requests are not governed by browser CORS, but Expo web requests from another origin will be blocked.

Before web integration, the backend must use a configuration-driven allowlist. Expected local origins include:

- `http://localhost:8081`
- `http://127.0.0.1:8081`
- `http://localhost:19006`
- `http://127.0.0.1:19006`

Do not use wildcard origins with credentialed requests in production.

## Check-in response

`GET /v1/checkins/today` returns:

- Date and form version.
- Title and description.
- The signed-in user's real once-per-day completion state.
- A curated set of core and adaptive sections/questions.
- Personalization metadata: strategy version, selected focus areas, number of history days used, and a user-facing explanation.
- Question options and numeric bounds.
- Immediate-support metadata and message.

The core mood, stress, energy, support, immediate-help, follow-up, consent, and privacy questions are never removed. Two additional focus areas are ranked from recent trends: sleep, academic pressure, connection, and support preferences. If trend personalization consent is `No`, the endpoint uses a rotating generic mix and does not use recent history for question selection.

## Administrator aggregation contract

Public registration always creates a `student`. Administrator accounts must be created or promoted from the local terminal. `/v1/admin/dashboard` returns HTTP `401` without authentication and `403` for authenticated students.

The response contains active-student count, today's unique completion count and rate, total check-ins in the selected calendar window, and daily aggregate rows. When a day contains fewer than five distinct participants, mood average, stress average, and follow-up-request count are returned as `null` with `suppressed: true`. The endpoint never returns usernames, user IDs, raw answer JSON, notes, or individual records.

## Privacy controls

Consent decisions are append-only. The most recent explicit `POST /v1/me/consent` decision overrides consent captured in older check-in answers. When disabled, the question curator does not read history for focus-area selection and uses its generic rotating mix.

`GET /v1/me/export` is owner-only and intentionally includes sensitive raw answers, so clients must save it locally and must not expose the response to administrators. `DELETE /v1/me/data` requires the current password and the exact confirmation value `DELETE`; deletion cascades to check-ins and consent history and clears the session cookie. Administrator deletion is intentionally rejected with HTTP `409` and requires a controlled operator process.

Supported question types:

- `text`
- `number`
- `single_choice`
- `multiple_choice`
- `linear_scale`

The frontend must render questions by `type` and identify them by `id`. Prompt text is content and must not be used as a programmatic key.

## Immediate-support contract

An option with `triggers_immediate_support: true` requires an immediate deterministic UI response. This behavior must not depend on:

- Check-in submission.
- Database availability.
- AI completion.
- Risk scoring.

The interface should show the backend-provided `immediate_support_message` and configured campus/emergency contacts.

## Authentication target

Planned authenticated requests use:

```http
Authorization: Bearer <access-token>
```

Tokens must not be stored in source code, committed environment files, logs, analytics events, or Figma artifacts. The final mobile storage mechanism must use an appropriate secure-storage facility.

## Contract testing requirements

Before declaring the API contract complete, tests must cover:

- Successful envelopes.
- `404` normalization.
- `405` normalization.
- `422` validation normalization.
- Safe `500` normalization without leaked exception text.
- Allowed and rejected CORS origins.
- Every check-in question type.
- Immediate-support trigger metadata.
- Planned consent and role boundaries when implemented.

## Compatibility checklist

- [x] Successful health envelope matches frontend types.
- [x] Successful check-in envelope matches frontend types.
- [x] Question field names and nullability are documented.
- [x] Immediate-support option is represented.
- [x] Figma and frontend token source exists.
- [ ] Framework errors use the common envelope.
- [ ] CORS supports Expo web development origins.
- [x] Check-in submission exists.
- [x] Demo database persistence exists.
- [x] Authentication and trend-personalization consent gates exist.
- [ ] Deletion and export operations exist.
