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
| `GET` | `/v1/checkins/today` | None in MVP | Implemented |

## Planned routes

| Area | Routes |
|---|---|
| Authentication | `POST /v1/auth/register`, `/login`, `/refresh` |
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
- Completion placeholder.
- Sections and questions.
- Question options and numeric bounds.
- Immediate-support metadata and message.

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
- [ ] Check-in submission exists.
- [ ] Database persistence exists.
- [ ] Authentication and consent gates exist.
- [ ] Deletion and export operations exist.

