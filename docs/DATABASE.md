# MindTrail — Database Architecture (PostgreSQL 15)

> Companion docs: [`ARCHITECTURE.md`](./ARCHITECTURE.md) (system & API — every endpoint here traces to a table below) · [`UI_REVIEW.md`](./UI_REVIEW.md) (screens that consume this data)
>
> Stack pinned in repo `requirements.txt`: SQLAlchemy 2.0 + Alembic + psycopg2/asyncpg.

## Local demo workbook

`data/demo/mindtrail_demo.xlsx` temporarily supplies five fictional accounts and 15 days of synthetic history. At startup, missing demo accounts are imported from the `Demo Users` sheet and their passwords are hashed before local storage.

Excel is not the production database. It lacks suitable concurrency, row-level access control, auditability, and safeguards for real wellbeing records. PostgreSQL remains the intended persistent store; Supabase remains a possible production authentication provider.

---

## 1. Design Principles

1. **Chat logs are the crown jewels.** `messages.body_enc` and other sensitive columns are encrypted at rest (pgcrypto AES-256, P4 in `ARCHITECTURE.md` §5) and are *never* exposed to staff roles — not even via views.
2. **Per-student, not cohort.** Baselines are personal; no cross-student comparison tables exist.
3. **Aggregate-only for staff.** Proctors/admins read through k-anonymized views (§5); raw tables carry no grants for staff roles.
4. **Explainability is data.** Every risk flag has a sibling explanation row — the student can always see *why*.
5. **Consent gates everything.** A `consent_records` append-only table is the single source of truth for pipeline eligibility.
6. **Anonymity by construction for peers.** Peer matching stores pseudonymous handles; no join path from a peer session to a real identity for the *other* participant.

---

## 2. Entity-Relationship Diagram

```
                            ┌──────────────────┐
                            │ users            │
                            │ (PK id, role,    │
                            │  pseudonym)      │
                            └───┬──────────┬───┘
              1:many            │          │             1:many
   ┌────────────┬───────────────┤          ├───────────────┬──────────────────┐
   ▼            ▼               ▼          ▼               ▼                  ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│ consent_records  │  │ checkins         │  │ conversations    │  │ peer_matches         │
│ (append-only,    │  │ (daily MCQ +     │  │  └─ messages     │  │ (anonymized pairing, │
│  opt-in/out log) │  │  rule_score)     │  │  └─ sentiment_   │  │  opt-in queue)       │
└──────────────────┘  └────────┬─────────┘  │     scores       │  └──────────┬───────────┘
                               │            └────────┬─────────┘             │ 1:many
                               │ 1:many              │ 1:many                ▼
                               │                     │            ┌──────────────────────┐
                               │                     │            │ peer_sessions        │
                               │                     │            │ (pseudonym chat)     │
                               ▼                     ▼            └──────────────────────┘
                  ┌──────────────────┐   ┌──────────────────┐
                  │ academic_signals │   │ baselines        │   (baseline_engine inputs:
                  │ (attendance,     │   │ (28-day rolling, │    checkins + sentiment +
                  │  deadlines,      │   │  per-signal      │    academic_signals)
                  │  exams — ingested│   │  mean/σ)         │
                  │  from college)   │   └────────┬─────────┘
                  └──────────────────┘            │ inputs to
                                                  ▼
                  ┌────────────────────────────────────────────┐
                  │ risk_flags  1 ─── 1 ─── flag_explanations  │
                  │ (stage, status, severity)  (inputs, rule,  │
                  │                             thresholds hit)│
                  └───────┬──────────────────────┬─────────────┘
                          │ 1:many               │ drives
                          ▼                      ▼
                  ┌──────────────┐      ┌──────────────────┐
                  │ nudges       │      │ escalations      │──▶ counsellors
                  │ (Stage 1)    │      │ (Stage 3; proctor│    (directory)
                  └──────────────┘      │  ack; warm       │       │ 1:many
                                        │  handoff)        │       ▼
                                        └──────────────────┘  ┌──────────────────┐
                                                              │ appointments     │
                                                              │ (slot, shared-   │
                                                              │  context choice) │
                                                              └──────────────────┘

  Cross-cutting:  audit_log (every protected read / pipeline transition)
                  crisis_events (lexicon hits; bypass staging)
```

---

## 3. Table Specifications

Types are PostgreSQL. `enc_` prefix marks pgcrypto-encrypted columns. All tables have `id UUID PK DEFAULT gen_random_uuid()` unless noted, plus `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`; only notable columns are listed.

### 3.1 Identity & consent

**`users`** — students, peers, proctors, counsellors, admins (single table, role column).
| Column | Type | Notes |
|---|---|---|
| `college_ref` | TEXT UNIQUE | College SSO/roll number (mock in MVP) |
| `display_name` | TEXT | For students, shown only to self & counsellor *after* consent |
| `pseudonym` | TEXT UNIQUE | Generated handle for peer sessions (e.g. "QuietFern42") |
| `role` | ENUM(`student`,`peer`,`proctor`,`counsellor`,`admin`) | |
| `proctor_id` | UUID FK→users | Student → their proctor (null ok) |
| `year`, `department` | TEXT | Used for aggregate trends only |
| `is_active` | BOOLEAN DEFAULT true | |

**`consent_records`** — append-only; current state = latest row per user.
| Column | Type | Notes |
|---|---|---|
| `user_id` | UUID FK→users NOT NULL | |
| `opted_in` | BOOLEAN NOT NULL | |
| `scope` | JSONB | Granular: `{checkins:true, chat:true, academic_sync:true, peer_match:false}` |
| `ip`, `user_agent` | TEXT | Audit context |

### 3.2 Signal capture

**`checkins`** — one per student per day (enforced unique).
| Column | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | `UNIQUE(user_id, checkin_date)` |
| `checkin_date` | DATE NOT NULL | |
| `answers` | JSONB | MCQ responses (question_id → choice) |
| `rule_score` | SMALLINT | 0–100 rule-based wellbeing score from MCQ |
| `mood_tags` | TEXT[] | Optional chips (stressed, sleep-deprived…) |

**`conversations`** — deep-conversation threads (LLM flow).
| Column | Type | Notes |
|---|---|---|
| `user_id` | UUID FK NOT NULL | Owner; no other student can ever read |
| `flow` | ENUM(`deep`,`peer_followup`) | Daily check-in is not a conversation row |
| `status` | ENUM(`open`,`closed`) | |

**`messages`** — chat log. ⚠️ **Encrypted.**
| Column | Type | Notes |
|---|---|---|
| `conversation_id` | UUID FK→conversations NOT NULL | |
| `sender` | ENUM(`student`,`bot`) | |
| `body_enc` | BYTEA | AES-256 (pgcrypto); plaintext never stored |
| `crisis_hit` | BOOLEAN DEFAULT false | Crisis lexicon flag (booleans are not sensitive) |

**`sentiment_scores`** — derived, per message or per check-in free text.
| Column | Type | Notes |
|---|---|---|
| `subject_type` | ENUM(`message`,`checkin`) | + `subject_id` (polymorphic pair, indexed) |
| `user_id` | UUID FK | Denormalized for fast per-student series |
| `valence` | REAL | −1..1 (VADER fast path; transformer ensemble later) |
| `anxiety_marker` | REAL, `withdrawal_marker` | REAL — tone features used by baseline engine |
| `model_version` | TEXT | Provenance |

**`academic_signals`** — ingested from college app (mock in MVP). Append-only time series.
| Column | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | |
| `signal_date` | DATE NOT NULL | |
| `attendance_pct` | REAL | That day/week |
| `missed_deadlines` | SMALLINT | |
| `exam_score_delta` | REAL | vs student's own prior mean |
| `source` | TEXT | `mock` / `webhook` |

### 3.3 Pattern engine

**`baselines`** — one row per user per signal; recomputed nightly (idempotent).
| Column | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | `UNIQUE(user_id, signal_key)` |
| `signal_key` | ENUM(`checkin_score`,`chat_valence`,`anxiety_marker`,`withdrawal_marker`,`attendance_pct`,`deadline_miss_ratio`,`exam_delta`) | |
| `window_days` | SMALLINT DEFAULT 28 | |
| `mean`, `stddev` | REAL, `n_days` | SMALLINT — min 7 before flags allowed |

**`risk_flags`** — the early-warning record.
| Column | Type | Notes |
|---|---|---|
| `user_id` | UUID FK NOT NULL | |
| `detected_date` | DATE | `UNIQUE(user_id, detected_date)` — one active flag per day |
| `stage` | ENUM(`stage1_nudge`,`stage2_peer_offer`,`stage3_escalate`) | Tier reached |
| `severity_z` | REAL | Combined z-score at detection |
| `status` | ENUM(`active`,`nudged`,`peer_offered`,`escalated`,`resolved`,`dismissed_by_student`) | State machine |

**`flag_explanations`** — 1:1 with `risk_flags` (`flag_id` FK UNIQUE). **Explainability contract** (`P2`).
| Column | Type | Notes |
|---|---|---|
| `signal_inputs` | JSONB | e.g. `{"chat_valence_z":-2.1,"attendance_z":-1.7}` |
| `rule_fired` | TEXT | e.g. `"combined_dip_v1: z<=-1.5 for 2 days"` |
| `thresholds` | JSONB | The exact thresholds in force at detection time |
| `narrative` | TEXT | Human-readable sentence shown in the app's "Why am I seeing this?" sheet |

**`crisis_events`** — lexicon hits; bypass staging.
| Column | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | |
| `subject_type`/`subject_id` | ENUM(`message`,`checkin`)/UUID | Source |
| `matched_terms` | TEXT[] | |
| `review_status` | ENUM(`pending`,`human_reviewed`,`resolved`) | Human review queue — never auto-escalates silently |

### 3.4 Tiered response

**`nudges`** — Stage 1 deliveries.
| Column | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | |
| `flag_id` | UUID FK→risk_flags, nullable | Crisis nudges may precede a flag |
| `nudge_key` | TEXT | Concrete suggestion id (`box_breathing_3min`, `deadline_triage`…) |
| `delivered_via` | ENUM(`push`,`in_app`) | |
| `ack_status` | ENUM(`sent`,`viewed`,`acted`,`dismissed`) + `acked_at` | |

**`peer_matches`** — Stage 2, opt-in queue only.
| Column | Type | Notes |
|---|---|---|
| `requester_id` | UUID FK→users | Requested the match |
| `matched_user_id` | UUID FK→users, nullable | Until pairing |
| `similarity_basis` | TEXT | Rule summary, e.g. `"similar stage-2 pattern cohort"` — never raw scores |
| `state` | ENUM(`queued`,`matched`,`active`,`closed`,`expired`) | TTL 7 days → `expired` |

**`peer_sessions`** — anonymized chat between two students.
| Column | Type | Notes |
|---|---|---|
| `match_id` | UUID FK→peer_matches | |
| `participant_a` / `participant_b` | UUID FK→users | Schema-level CHECK forbids cross-referencing messages back to real identity *for the other party*; app exposes pseudonyms only |
| `body_enc` | BYTEA | Encrypted like `messages` |
| `flagged` | BOOLEAN | Either side can flag; goes to human review |

### 3.5 Escalation & care directory

**`counsellors`** — curated directory (admin CRUD, shown on S4).
| Column | Type | Notes |
|---|---|---|
| `full_name`, `credentials` | TEXT | e.g. "Dr. Eleanor Vance", "Licensed Clinical Psychologist" |
| `specialties` | TEXT[] | `{"Academic Stress","Life Transitions"}` |
| `modality` | ENUM(`in_person`,`virtual`,`both`) | |
| `location` | TEXT, `booking_url` | TEXT |
| `is_college_affiliated` | BOOLEAN DEFAULT true | Curated per README |

**`escalations`** — Stage 3.
| Column | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | Student being escalated (they see this row + its explanation) |
| `flag_id` | UUID FK→risk_flags | |
| `initiated_by` | ENUM(`system`,`student`) | |
| `proctor_id` | UUID FK→users | Routed to |
| `proctor_ack_at` | TIMESTAMPTZ, nullable | **Human-in-the-loop**: outreach only after ack (`P5`) |
| `status` | ENUM(`proposed`,`acknowledged`,`contacted`,`closed`) | |
| `shared_context_enc` | BYTEA, nullable | Student-chosen 7-day summary bundle; **null = student chose "start fresh"** (the demo modal's radio) |

**`appointments`** — counsellor bookings (warm handoff).
| Column | Type | Notes |
|---|---|---|
| `student_id` | UUID FK→users | |
| `counsellor_id` | UUID FK→counsellors | |
| `slot_start`, `slot_end` | TIMESTAMPTZ | `CHECK(slot_end > slot_start)`; no double-book (`EXCLUDE` constraint) |
| `modality` | ENUM(`in_person`,`virtual`) | |
| `shared_context` | BOOLEAN DEFAULT false | Mirrors the student's share-context radio choice |

### 3.6 Cross-cutting

**`audit_log`** — append-only, no updates/deletes (rule enforced via revoke).
| Column | Type | Notes |
|---|---|---|
| `actor_id` | UUID FK→users, nullable | System jobs have null actor + `action` prefix `job.` |
| `action` | TEXT | `consent.opt_in`, `flag.read`, `escalation.ack`, `job.pattern_sweep`… |
| `subject_type`/`subject_id` | TEXT/UUID | What was touched |
| `meta` | JSONB | Minimal context; never contains chat text |

---

## 4. Indexing & Query Patterns

The pattern sweep and dashboard charts are the hot paths — per-student time-series lookups.

```sql
-- Per-student signal series (baseline_engine, sweep, pulse charts)
CREATE INDEX idx_checkins_user_date   ON checkins (user_id, checkin_date DESC);
CREATE INDEX idx_sentiment_user_date  ON sentiment_scores (user_id, created_at DESC);
CREATE INDEX idx_academic_user_date   ON academic_signals (user_id, signal_date DESC);

-- Polymorphic subject lookup for sentiment_scores
CREATE INDEX idx_sentiment_subject    ON sentiment_scores (subject_type, subject_id);

-- Flag lookups: staff caseload (aggregate view), student "my flags", sweep dedupe
CREATE INDEX idx_flags_user_date      ON risk_flags (user_id, detected_date DESC);
CREATE INDEX idx_flags_status         ON risk_flags (status) WHERE status IN ('active','nudged','peer_offered');

-- Active consent check on every gated request (P1)
CREATE INDEX idx_consent_user_latest  ON consent_records (user_id, created_at DESC);

-- Crisis review queue
CREATE INDEX idx_crisis_pending       ON crisis_events (review_status) WHERE review_status = 'pending';

-- Booking conflict prevention
CREATE UNIQUE INDEX idx_appt_slot     ON appointments (counsellor_id, slot_start);
```

**Representative hot queries**
- *Sweep (hourly):* last 3 days of each signal per opted-in student → join `baselines` → z-scores → upsert `risk_flags` + explanations.
- *Dashboard (S1):* `checkins` last 14d + `sentiment_scores` last 14d → smoothed pulse series (client renders wave, per design system).
- *Caseload view:* `vw_caseload_summary` filtered by `proctor_id` — aggregates only.

---

## 5. Views, Roles & Data Minimization (P3)

Staff roles never receive grants on raw signal tables — only on views:

```sql
-- Proctor caseload: aggregate per student, no free text, explainability pointers only
CREATE VIEW vw_caseload_summary AS
SELECT u.id AS student_id, u.department,
       rf.detected_date, rf.stage, rf.severity_z, rf.status,
       fe.narrative                        -- the same text the student sees
FROM risk_flags rf
JOIN users u ON u.id = rf.user_id
JOIN flag_explanations fe ON fe.flag_id = rf.id
JOIN consent_records c ON c.user_id = u.id
WHERE u.proctor_id = $proctor        -- enforced via view + role predicate
  AND c.opted_in = true              -- opt-out students vanish from staff views
  AND rf.detected_date > current_date - 14;

-- Admin trends: k-anonymized, no individuals possible
CREATE VIEW vw_admin_trends AS
SELECT department,
       date_trunc('week', rf.detected_date) AS week,
       count(*)              AS flag_count,
       count(DISTINCT rf.user_id) AS students_flagged
FROM risk_flags rf JOIN users u ON u.id = rf.user_id
GROUP BY department, week
HAVING count(DISTINCT rf.user_id) >= 5;   -- k-anonymity ≥ 5
```

Role grants:

| Role | Raw signal tables (`checkins`, `messages`, `sentiment_scores`, `academic_signals`) | Views | PII |
|---|---|---|---|
| `student` | own rows only (app-layer scoping) | — | own |
| `peer` | none | — | pseudonym only |
| `proctor` | **none** | `vw_caseload_summary` | none (aggregate) |
| `counsellor` | none; shared-context bundle only **after appointment + student consent** | appointment rows | what student chose to share |
| `admin` | **none** | `vw_admin_trends` | none |

Severe-risk exception: only `crisis_events` (with human review) can identify a student to staff — mirroring README's "unless a severe-risk threshold is hit".

---

## 6. Encryption, Retention & Opt-Out

| Concern | Policy |
|---|---|
| At rest | `messages.body_enc`, `peer_sessions.body_enc`, `escalations.shared_context_enc` via pgcrypto AES-256; column-level keys from env/KMS. Whole-cluster encryption at the infra layer as second layer. |
| In transit | TLS everywhere; college ingestion webhooks HMAC-signed. |
| Retention — chat | `messages`/`peer_sessions` purged 180 days after conversation close (job), unless part of an unresolved `crisis_events` review. |
| Retention — signals | `checkins`/`sentiment_scores`/`academic_signals` kept 12 months rolling (baseline window + pilot analysis). |
| Retention — audit | `audit_log` 3 years (compliance). |
| Opt-out | Latest `consent_records.opted_in = false` → pipelines skip student (sweep checks), staff views exclude, history frozen (not deleted) pending the student's explicit "delete my data" action. |
| Right to erasure | `DELETE /v1/me/data` → hard delete of chat/checkins/sentiment/flags within 30 days, retaining only `audit_log` tombstone + `consent_records` (legal basis). |

---

## 7. Migration Strategy (Alembic)

- One migration per feature slice; **`consent_records` and `users` ship in migration 0001** so the gate exists before any signal table accepts writes.
- Views and grants are managed as Alembic migrations too (op.execute with SQL above), so role isolation is reproducible.
- Encryption keys rotate by re-encrypting in batches via a backfill migration pattern (dual-column + swap).
- Seeds (baseline migration): counsellor directory fixtures for demo; mock academic data via `POST /v1/ingest/mock/generate`, *not* migrations.
- Every migration must be reversible (`downgrade`); the sweep/baseline jobs are idempotent so schema rollbacks are safe.

---

## 8. Traceability Check (docs consistency)

| API group (`ARCHITECTURE.md` §3) | Tables |
|---|---|
| Auth & consent | `users`, `consent_records`, `audit_log` |
| Check-ins & chat | `checkins`, `conversations`, `messages`, `sentiment_scores` |
| Pattern & risk | `baselines`, `risk_flags`, `flag_explanations`, `crisis_events` |
| Nudge, peer & resources | `nudges`, `peer_matches`, `peer_sessions`, `counsellors`, `appointments` |
| Escalation | `escalations`, `risk_flags`, `counsellors` |
| Admin & ingestion | `counsellors`, `consent_records`, `academic_signals`, `audit_log` |

| UI screen (`UI_REVIEW.md` §6 + `ARCHITECTURE.md` §2.1) | Primary tables |
|---|---|
| S1 Home/Today | `nudges`, `checkins`, `sentiment_scores`, `risk_flags` |
| S2 Daily Check-in | `checkins`, `consent_records` |
| S3 Chat Support | `conversations`, `messages`, `sentiment_scores`, `crisis_events` |
| S4 Resources & Support | `counsellors`, `appointments`, `peer_matches`, `resources catalog`*, `escalations` |
| S5 Privacy & Data | `consent_records`, `flag_explanations`, `audit_log` |
| ST1–ST3 Staff Console | `risk_flags`+views, `escalations`, `appointments`, `consent_records`, `vw_admin_trends` |

\* Resource exercise catalog is static content served by `GET /v1/resources`; no table in MVP — promote to a table when content becomes admin-managed.
