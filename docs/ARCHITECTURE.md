# MindTrail — System & Website Architecture

> Companion docs: [`DATABASE.md`](./DATABASE.md) (PostgreSQL schema & privacy design) · [`UI_REVIEW.md`](./UI_REVIEW.md) (Stitch design audit & screen inventory)
>
> Source of truth: repo `README.md` (PRD summary) + Stitch export (`stitch_mindtrail_student_wellbeing_app.zip`).

---

## 1. System Overview

MindTrail is a **chatbot-led early-warning and tiered-support system** for student wellbeing. It runs as an embedded module inside a college's existing student app. One conversational surface handles detection (daily check-ins + deep conversations), support (nudges, peer matching), and escalation (proctor + counsellor handoff).

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           STUDENT / STAFF DEVICES                          │
│                                                                            │
│  ┌─────────────────────────────┐      ┌────────────────────────────────┐  │
│  │  Student App (RN/Expo)      │      │  Staff Console (RN/Expo or Web)│  │
│  │  ├─ Home / Today            │      │  ├─ Proctor: caseload flags    │  │
│  │  ├─ Daily Check-in          │      │  ├─ Counsellor: schedule,      │  │
│  │  ├─ Chat Support            │      │  │   appointment intake         │  │
│  │  ├─ Resources & Support     │      │  └─ Admin: consents, counsellor│  │
│  │  └─ Privacy & Data          │      │      directory, audit view     │  │
│  └──────────────┬──────────────┘      └───────────────┬────────────────┘  │
└─────────────────┼─────────────────────────────────────┼───────────────────┘
                  │ HTTPS + JWT                         │ HTTPS + JWT (role-scoped)
                  ▼                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                        API LAYER — FastAPI (Python 3.11)                   │
│                                                                            │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐ ┌───────────┐ │
│  │ Auth &     │ │ Check-in & │ │ Pattern &  │ │ Peer &    │ │ Escalation│ │
│  │ Consent    │ │ Chat       │ │ Risk       │ │ Nudge     │ │ & Care    │ │
│  │ router     │ │ router     │ │ router     │ │ router    │ │ router    │ │
│  └────────────┘ └────────────┘ └────────────┘ └───────────┘ └───────────┘ │
│                                                                            │
│  Services: consent_gate · conversation_engine (rule + LLM) ·               │
│            sentiment_pipeline · baseline_engine · tier_router ·            │
│            anonymizer (aggregate views for admin)                          │
└───────┬──────────────────────────────────┬────────────────────────────────┘
        │                                  │
        ▼                                  ▼
┌──────────────────┐            ┌──────────────────────────────────────────┐
│ PostgreSQL 15    │            │  Background workers (Celery + Redis)      │
│ (encrypted at    │            │  ├─ ingest_academic_sync   (nightly)      │
│ rest; chat logs  │            │  ├─ recompute_baselines    (nightly)      │
│ & sensitive      │            │  ├─ run_pattern_sweep      (hourly)       │
│ fields AES-256)  │            │  ├─ enqueue_peer_matches   (hourly)       │
└──────────────────┘            │  └─ send_escalation_jobs   (event-driven) │
                                └───────────────┬──────────────────────────┘
                                                │
                          ┌─────────────────────┼──────────────────────┐
                          ▼                     ▼                      ▼
                ┌──────────────────┐  ┌───────────────────┐  ┌────────────────────┐
                │ College App API  │  │ LLM provider      │  │ Notification       │
                │ (mock in MVP:    │  │ (Anthropic/OpenAI │  │ (FCM/APNs push,    │
                │ attendance,      │  │ for deep conversa-│  │ email/SMS for      │
                │ deadlines, exams)│  │ tion flow)        │  │ Stage 3 handoff)   │
                └──────────────────┘  └───────────────────┘  └────────────────────┘
```

**Stack decisions** (per `requirements.txt` + user choice of React Native/Flutter):

| Layer | Choice | Why |
|---|---|---|
| Mobile client | **React Native (Expo)** — Flutter as noted alternative | Stitch tokens (Tailwind palette, Material Symbols, Plus Jakarta Sans/Inter) port 1:1 to RN; Expo embeds as a module in an existing college app (README's stated deployment mode). Flutter mapping noted in `UI_REVIEW.md`. |
| API | FastAPI + Pydantic v2 | Already pinned in `requirements.txt`; async, typed, OpenAPI docs free. |
| DB | PostgreSQL 15 | Required encryption-at-rest for chat logs; JSONB for flexible check-in payloads. |
| Workers | Celery + Redis (APScheduler acceptable in MVP) | Nightly ingestion, baseline recompute, pattern sweeps. |
| NLP | VADER + TextBlob (fast path); transformers (tone, deep conversations) | Both tiers already in `requirements.txt`. |
| LLM | Anthropic / OpenAI SDKs | Deep-conversation flow; daily check-in stays rule-based (predictable, cheap, private). |
| Auth | JWT (python-jose) + bcrypt (passlib) | Roles: student, peer, proctor, counsellor, admin. |

---

## 2. Client Architecture (React Native / Expo)

### 2.1 Screen map

The Stitch export defines the student-side navigation. Five student screens + a staff surface:

| # | Screen | Purpose | Backing endpoints (§3) |
|---|---|---|---|
| S1 | **Home / Today** | Wellbeing pulse (smoothed wave, not jagged lines), today's check-in CTA, nudge cards, streak | `GET /me/dashboard`, `GET /me/nudges` |
| S2 | **Daily Check-in** | 10–20s semi-forced mood MCQ/micro-quiz (rule-based flow) | `POST /checkins`, `GET /checkins/today` |
| S3 | **Chat Support** | Deep-conversation chat (LLM flow) + tone analysis in background; shows "why am I seeing this" affordances | `POST /conversations`, `POST /conversations/{id}/messages`, `GET /conversations/{id}` |
| S4 | **Resources & Support** | *The implemented Stitch screen* — crisis ribbon, 3-tier support cards (self-guided / peer / counsellor), Oasis Lounge map, Stage 3 warm-handoff preview | `GET /resources`, `GET /peers/availability`, `GET /counsellors`, `POST /appointments`, `POST /escalations/preview` |
| S5 | **Privacy & Data** | Opt-in/out toggles, explainable flag viewer, data export, delete-my-data | `GET/PUT /me/consent`, `GET /me/flags`, `GET /me/export`, `DELETE /me/data` |
| ST1 | **Staff Console** (proctor) | Caseload view — aggregate + explainable flags for opted-in students; Stage 3 roster; acknowledges escalations | `GET /staff/caseload`, `POST /staff/escalations/{id}/ack` |
| ST2 | **Staff Console** (counsellor) | Appointment queue, warm-handoff intakes (with/without shared context per student choice) | `GET /staff/appointments`, `PUT /staff/appointments/{id}` |
| ST3 | **Staff Console** (admin) | Counsellor directory CRUD, consent audit, aggregate-only dashboards | `GET/POST/PATCH /admin/counsellors`, `GET /admin/consents`, `GET /admin/trends` |

### 2.2 Client-layer principles

- **Conversation-first**: Chat (S3) and Check-in (S2) are native surfaces, not webviews — they are the detection engine's input and must feel frictionless.
- **Explainability inline**: every nudge, flag, or escalation card renders a "Why am I seeing this?" sheet — a hard product requirement (README: *explainable flags*).
- **Crisis always one tap away**: the crisis ribbon from S4 is promoted to a global affordance reachable from any screen.
- **Offline tolerance**: check-in answers queue locally (AsyncStorage/SQLite) and replay when connectivity returns; chat requires online.
- **Opt-in gating**: S2/S3 are locked behind consent state; the app routes to S5's opt-in flow first. Stress tracking is **never default-on**.

### 2.3 State & data layer

```
mobile/
  app.config.ts            # Expo config (scheme, push credentials)
  src/
    navigation/            # stack + tab navigators (student tabs, staff stack)
    screens/               # S1..S5, ST1..ST3
    components/            # CheckinCard, PulseWave, NudgeCard, TierCard,
                           # CrisisRibbon, ExplainSheet, PeerAvatarCluster
    theme/                 # Stitch tokens → RN (see UI_REVIEW.md §5)
    api/                   # typed client (axios) + JWT refresh interceptor
    stores/                # zustand: auth, consent, checkinDraft, chat
    db/                    # SQLite/AsyncStorage queue for offline check-ins
```

---

## 3. API Surface (FastAPI)

All endpoints under `/v1`. JSON, JWT bearer auth unless noted. Every endpoint below maps to tables in [`DATABASE.md`](./DATABASE.md) §3.

### 3.1 Auth & consent
| Method | Path | Purpose | Role |
|---|---|---|---|
| POST | `/v1/auth/register` | Provision account (college SSO token exchange in prod; mock in MVP) | any |
| POST | `/v1/auth/login` | Issue JWT pair | any |
| POST | `/v1/auth/refresh` | Rotate access token | any |
| GET | `/v1/me/consent` | Current consent state + history pointers | student |
| PUT | `/v1/me/consent` | Opt in / out (creates `consent_records` row; opt-out suspends pipelines) | student |

### 3.2 Check-ins & chat
| Method | Path | Purpose | Role |
|---|---|---|---|
| GET | `/v1/checkins/today` | Today's MCQ set (rule-based) + whether done | student |
| POST | `/v1/checkins` | Submit answers → immediate rule score → sentiment hook | student |
| POST | `/v1/conversations` | Open deep-conversation thread (LLM system prompt per consent scope) | student |
| POST | `/v1/conversations/{id}/messages` | Send message; returns bot reply + runs sentiment/tone async | student |
| GET | `/v1/conversations/{id}` | Thread history (owner or counsellor-with-consent only) | student |
| GET | `/v1/me/conversations` | List own threads | student |

### 3.3 Pattern, risk & data rights
| Method | Path | Purpose | Role |
|---|---|---|---|
| GET | `/v1/me/baseline` | Show the student their own personal baseline | student |
| GET | `/v1/me/flags` | List risk flags **with explanations** (trigger inputs, stage, status) | student |
| GET | `/v1/me/dashboard` | Pulse series, streak, open nudges, check-in status | student |
| GET | `/v1/me/pulse` | Smoothed wellbeing pulse series for charts | student |
| GET | `/v1/me/export` | Machine-readable export of the student's own data | student |

### 3.4 Nudge, peer & resources
| Method | Path | Purpose | Role |
|---|---|---|---|
| GET | `/v1/me/nudges` | Stage-1 nudges delivered | student |
| POST | `/v1/me/nudges/{id}/ack` | Mark nudge acted-upon/dismissed | student |
| GET | `/v1/peers/availability` | Live availability (anonymized) for Stage 2 card | student |
| POST | `/v1/peers/match` | Request anonymous peer match (rule-based similarity) | student |
| GET | `/v1/peers/sessions` | My anonymous peer sessions (pseudonyms only) | student |
| GET | `/v1/resources` | Self-guided exercises catalog (box breathing, workbooks…) | student |
| GET | `/v1/counsellors` | Curated college-affiliated counsellor directory | student |
| POST | `/v1/appointments` | Book counsellor slot (warm handoff; honors share-context choice) | student |
| GET | `/v1/appointments` | My upcoming appointments | student |

### 3.5 Escalation
| Method | Path | Purpose | Role |
|---|---|---|---|
| POST | `/v1/escalations/preview` | Dry-run the escalation flow (demo/hackathon "Preview Counselor Booking Flow") | student |
| POST | `/v1/escalations` | Trigger Stage 3 (system-initiated after threshold, or student-initiated) | system/student |
| GET | `/v1/me/escalations` | Student's own escalation history + explanations | student |
| POST | `/v1/staff/escalations/{id}/ack` | Proctor/counsellor acknowledges handoff | proctor/counsellor |
| GET | `/v1/staff/caseload` | Aggregate + explainable flags for assigned students (opted-in only) | proctor |

### 3.6 Admin & ingestion
| Method | Path | Purpose | Role |
|---|---|---|---|
| GET/POST/PATCH/DELETE | `/v1/admin/counsellors` | Counsellor directory CRUD | admin |
| GET | `/v1/admin/consents` | Consent audit trail | admin |
| GET | `/v1/admin/trends` | **Aggregate, anonymized** trends only (no raw scores — enforced by views, §5) | admin |
| POST | `/v1/ingest/college` | Webhook receiver for college-app academic data (HMAC-signed; MVP uses mock) | service |
| GET/POST | `/v1/ingest/mock/generate` | Seed/generate mock attendance, deadlines, exams (demo) | admin |

### 3.7 Error & envelope conventions
- Envelope: `{ "data": ..., "error": null }` or `{ "data": null, "error": { code, message, details? } }`.
- Domain errors: `403 consent_required` (pipelines blocked), `409 already_checked_in`, `404 flag_not_found`, `429 rate_limited_chat`.
- All list endpoints cursor-paginate: `?cursor=&limit=`.

---

## 4. Detection Pipeline (core data flow)

The heart of MindTrail — chat-tone + academic-dip **combined** detection against a **per-student baseline**.

```
                 ┌────────────────────┐        ┌─────────────────────────┐
 Student ───────▶│ Daily Check-in (S2)│───────▶│ rule_score (MCQ)         │
                 └────────────────────┘        └───────────┬─────────────┘
                                                           │
                 ┌────────────────────┐                    ▼
            ┌───▶│ Deep Conversation  │───▶ sentiment_pipeline ───▶ tone signals
            │    │ (S3, LLM flow)     │    (VADER fast path;       (valence, anxiety
            │    └────────────────────┘     transformers deep)     markers, withdrawal)
            │                                                        │
 College ───┼──▶ ingest_academic_sync (Celery nightly + webhooks) ──▶ attendance %,
 App        │                                                        missed deadlines,
 (mock MVP) │                                                        exam deltas
            │                                                        │
            │        ┌───────────────────────────────────────────────▼──┐
            └───────▶│            baseline_engine (per student)          │
                     │  • rolling 28-day personal baseline (NOT cohorts) │
                     │  • z-score deviation per signal                   │
                     │  • combined dip rule: chat_tone ↓ AND academic ↑d │
                     └───────────────────────┬───────────────────────────┘
                                             │ signals deviate together
                                             ▼
                     ┌───────────────────────────────────────────────────┐
                     │ tier_router (Stage logic, human-in-the-loop)      │
                     │  Stage 1: nudge      → concrete micro-suggestion  │
                     │  Stage 2: peer offer → OPT-IN anonymous match     │
                     │  Stage 3: escalate   → proctor + counsellor list  │
                     └──────┬──────────────────┬──────────────────┬──────┘
                            ▼                  ▼                  ▼
                     nudges (DB)       peer_matches (DB)    escalations (DB)
                     shown on S1/S2    shown on S4 card     staff console ST1/ST2
                                             +                     +
                                       explanation rows ──▶ audit_log (DB)
```

**Stage rules (MVP thresholds — tune in pilot):**
- Signals: `checkin_score`, `chat_valence`, `attendance_delta`, `deadline_miss_ratio`, `exam_delta`.
- Each signal → z-score vs the student's own 28-day baseline (min 7 baseline days required, else "collecting" state — no flags).
- **Stage 1** when: combined z ≤ −1.5 for 2 consecutive days → bot nudge (concrete: sleep pacing, box breathing, deadline triage — never a bare "are you okay?").
- **Stage 2 offer** when: Stage 1 nudged and z ≤ −2.0 for 3 days → offer optional anonymous peer connection. *Never auto-connect.*
- **Stage 3** when: z ≤ −2.5 for 5 days **and** no engagement with Stage 1/2 → proctor + curated counsellors. Every Stage 3 flag ships its explanation bundle (which inputs, which thresholds) to the student first.
- **Crisis override**: crisis lexicon hits in chat or check-in bypass staging → immediate lifeline ribbon + human review queue.

**What the pipeline never does:** diagnose, auto-book appointments, notify faculty without the student's Stage-3-consent design above, or expose raw chat text to staff.

---

## 5. Privacy Enforcement Points

Privacy is a cross-cutting layer, not a feature (README: opt-in, explainable flags, data minimization, human-in-the-loop).

| # | Point | Layer | Mechanism |
|---|---|---|---|
| P1 | **Opt-in gate** | API middleware | `consent_gate` dependency: any check-in/chat/pattern endpoint 403s unless latest `consent_records` row = opted-in. Opt-out suspends pipelines; historical data retained per retention policy (D2), not deleted silently. |
| P2 | **Explainable flags** | Pattern engine | Every `risk_flags` row writes a sibling `flag_explanations` row; `GET /me/flags` returns it verbatim to the student before any staff sees it. |
| P3 | **Data minimization** | DB views | Staff/admin read only through `vw_caseload_summary` / `vw_admin_trends` (aggregate, k-anonymized ≥5, no free text). Raw tables are not grantable to staff roles. |
| P4 | **Encryption** | DB | Chat `messages.body` and sensitive columns AES-256 at rest (pgcrypto); TLS in transit; keys in KMS (env var in MVP). |
| P5 | **Human-in-the-loop** | Escalation | Stage 3 creates a *proposed* handoff; proctor acknowledges (ST1) before outreach. Student sees the same explanation bundle. |
| P6 | **Audit** | API + workers | Every read of protected data and every pipeline transition writes `audit_log`. |

---

## 6. Background Jobs

| Job | Schedule | Input → Output | Failure mode |
|---|---|---|---|
| `ingest_academic_sync` | nightly 02:00 + webhook | College API (mock) → `academic_signals` | retry ×3, dead-letter to `audit_log` |
| `recompute_baselines` | nightly 03:00 | `checkins`, `sentiment_scores`, `academic_signals` → `baselines` | idempotent full recompute |
| `run_pattern_sweep` | hourly | baselines + latest signals → `risk_flags` (+ explanations), tier_router side-effects | idempotent; sweeps skip opted-out |
| `enqueue_peer_matches` | hourly | risk-flag cohort → `peer_matches` (opt-in queue only) | no match → stays queued, TTL 7d |
| `send_escalation_jobs` | event | Stage 3 → push/SMS/email to proctor + counsellor digest | retry ×5 with backoff |

---

## 7. Target Repository Structure

```
Vinhack_26/
├── README.md
├── PRD.md                      # referenced by README — to be added
├── requirements.txt            # (exists) Python deps
├── docs/
│   ├── ARCHITECTURE.md         # this file
│   ├── DATABASE.md
│   └── UI_REVIEW.md
├── mobile/                     # Expo (React Native) client
│   ├── app.config.ts
│   ├── package.json
│   └── src/ …                  # screens, components, theme, api, stores
├── api/                        # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── core/               # config, security, consent_gate dependency
│   │   ├── routers/            # auth, checkins, conversations, patterns,
│   │   │                       # peers, resources, escalations, staff, admin, ingest
│   │   ├── services/           # conversation_engine, sentiment_pipeline,
│   │   │                       # baseline_engine, tier_router, anonymizer
│   │   └── schemas/            # Pydantic v2 DTOs
│   ├── alembic/                # migrations
│   └── tests/
└── workers/                    # Celery tasks (thin wrappers over api/app/services)
```

---

## 8. Build Order (hackathon MVP path)

1. DB schema + Alembic migrations (per `DATABASE.md`) — tables, views, seed counsellors.
2. Auth + consent gate (`P1`) — blocks everything else meaningfully.
3. Check-in flow (S2) with rule scoring — first detection signal, fully offline-capable.
4. Chat (S3) with VADER sentiment + LLM deep-conversation — second signal.
5. Mock ingestion + baseline engine + pattern sweep — the "combined dip" demo.
6. Nudge delivery (Stage 1) on S1/S2 — visible bot response.
7. Peer matching queue (Stage 2, opt-in) + S4 availability card.
8. Escalation (Stage 3) + staff console (ST1/ST2) + explanation bundles.
9. Implement the Stitch screen (S4) 1:1 with the RN mapping in `UI_REVIEW.md`; then build S1/S5.
