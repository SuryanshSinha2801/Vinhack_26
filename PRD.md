# MindTrail Product Requirements Document

**Status:** Hackathon MVP  
**Version:** 1.0  
**Last updated:** 2026-09-18  
**Product type:** Student wellbeing support and early-warning system

## 1. Product summary

MindTrail is a conversation-led wellbeing module for a college student application. It combines voluntary daily check-ins, optional deeper conversations, and existing academic signals to identify sustained changes from each student's personal baseline. It then offers progressively stronger support while preserving student agency, privacy, and human oversight.

MindTrail is a support and routing tool. It does not diagnose mental-health conditions, replace emergency services, or make academic decisions.

## 2. Problem

Students experiencing stress often do not request help. Colleges may separately hold attendance, deadline, and examination data but rarely use those signals to offer timely wellbeing support. Existing approaches can miss students who withdraw academically and students who continue performing while struggling emotionally.

MindTrail addresses this gap through a short recurring check-in and a staged response that starts with low-friction support and escalates to people only under defined, explainable conditions.

## 3. Goals

### MVP goals

- Let a student complete a short, voluntary wellbeing check-in.
- Preserve consent and make the use of responses understandable.
- Calculate understandable, non-diagnostic wellbeing signals.
- Demonstrate a personal-baseline and combined-signal workflow with mock academic data.
- Deliver a concrete Stage 1 wellbeing nudge.
- Demonstrate optional Stage 2 peer support.
- Demonstrate a Stage 3 human handoff with student-visible explanations.
- Keep immediate-support information available without relying on AI.
- Provide a polished Expo interface for web and mobile demonstrations.

### Success measures

- Median daily check-in completion time at or below 60 seconds for the full prototype form, with a future shortened daily variant targeting 10–20 seconds.
- At least 90% successful completion in moderated MVP testing.
- Every generated flag includes a student-readable explanation.
- No staff or administrator view exposes raw chat text.
- No wellbeing pipeline runs for an opted-out student.
- Immediate-support guidance appears without waiting for network AI processing.

## 4. Non-goals

- Medical diagnosis or clinical risk scoring.
- Replacement for licensed counsellors or emergency services.
- Automatic appointment booking without student action.
- Automatic peer connection without explicit opt-in.
- Academic grading, discipline, or faculty performance evaluation.
- Staff access to raw chat messages.
- Production deployment of the hackathon's mock college-data connector.

## 5. Users and roles

| Role | Primary need | Permitted scope |
|---|---|---|
| Student | Reflect, receive support, control data sharing | Own check-ins, conversations, flags, consents, appointments, and exports |
| Peer supporter | Participate in an anonymous support session | Pseudonymous session data only |
| Proctor | Review and acknowledge sustained Stage 3 handoffs | Assigned caseload summaries and explanations; no raw chat |
| Counsellor | Review appointment intake and shared context | Appointment data and only the context the student chose to share |
| Administrator | Manage directories and review trends | Consent audit and aggregate, anonymized trends |
| Service account | Send signed academic data | Ingestion endpoint only |

## 6. Product principles

1. **Voluntary by default:** tracking is opt-in and revocable.
2. **Support, not surveillance:** language and visuals must avoid punishment or diagnosis.
3. **Explain before escalating:** the student sees why a flag or handoff exists.
4. **Minimum necessary data:** each role receives only the data needed for its task.
5. **Human oversight:** Stage 3 creates a proposed handoff that a qualified person acknowledges.
6. **Crisis support without AI:** immediate-support guidance is deterministic and always accessible.
7. **Personal baseline:** changes are measured against the student's history, not a cohort average.

## 7. Student experience

### S1 — Home / Today

- Display today's check-in state.
- Display a calm wellbeing pulse visualization when enough data exists.
- Display active nudges and an explanation affordance.
- Display a global immediate-support entry point.
- Show loading, offline, empty, completed, and error states.

### S2 — Daily Check-in

- Load the current form from `GET /v1/checkins/today`.
- Render one question at a time from backend-provided types and options.
- Validate required questions before advancing.
- Save a local draft by date and form version.
- Show immediate-support guidance when the selected option requests urgent help.
- Submit answers to `POST /v1/checkins` when that endpoint is implemented.
- Avoid diagnostic or judgmental completion language.

### S3 — Chat Support

- Provide an optional deeper conversation surface.
- Keep AI provider credentials on the backend only.
- Display reflective prompts and explanation links.
- Run deterministic crisis-language handling before or independently of an AI response.
- Remain a local demonstration until the conversation endpoints are implemented.

### S4 — Resources & Support

- Present self-guided, peer, and professional-support options.
- Never auto-connect a student to a peer.
- Let the student choose whether to share recent context during a warm handoff.
- Clearly label simulated booking behavior until real endpoints exist.

### S5 — Privacy & Data

- Explain current consent and data use in plain language.
- Let the student opt in or out when consent endpoints exist.
- Show explainable flag history.
- Provide data export through `GET /v1/me/export`.
- Provide deletion through `DELETE /v1/me/data` with explicit confirmation.
- Never show export or deletion as successful without backend confirmation.

## 8. Staff experience

### Proctor console

- Show assigned students with active Stage 3 handoffs.
- Show explanation summaries, not raw messages.
- Let the proctor acknowledge a handoff.
- Record every protected-data access in the audit log.

### Counsellor console

- Show appointment and intake queues.
- Show only context explicitly shared by the student.
- Allow appointment status updates.

### Administrator console

- Manage the counsellor directory.
- Review consent audit records.
- View aggregate trends only when the anonymity threshold is satisfied.

## 9. Check-in requirements

The MVP question catalog is based on the MindTrail Student Wellbeing Check-in form and includes:

- Optional student identifier for form fidelity; authenticated production flows derive identity from the session.
- Year of study.
- Mood and stress scales.
- Energy and sleep quality.
- Optional sleep duration.
- Academic workload and affected areas.
- Desired support and optional free text.
- Immediate-support question.
- Follow-up choice, trend-use choice, and privacy acknowledgement.

The backend owns question identifiers, types, options, bounds, required status, and immediate-support metadata. The frontend must render the contract rather than duplicate the questions.

## 10. Detection and staged support

### Inputs

- Check-in score.
- Chat valence and tone signals.
- Attendance change.
- Missed-deadline ratio.
- Examination-result change.

### Baseline

- Rolling 28-day baseline per student.
- Minimum seven days before risk flags can be produced.
- Each signal represented as a deviation from that student's baseline.

### MVP stage rules

- **Stage 1:** combined deviation at or below −1.5 for two consecutive days. Deliver a concrete wellbeing nudge.
- **Stage 2:** Stage 1 already delivered and deviation at or below −2.0 for three days. Offer optional anonymous peer support.
- **Stage 3:** deviation at or below −2.5 for five days with no Stage 1/2 engagement. Propose a proctor/counsellor handoff with an explanation.
- **Immediate-support override:** an urgent-help response or crisis-language match displays lifelines and creates a human-review path without waiting for staged thresholds.

Thresholds are demonstration defaults and require professional review before any pilot or deployment.

## 11. Functional requirements

| ID | Requirement | MVP acceptance criterion |
|---|---|---|
| FR-01 | Health check | `/health` and `/v1/health` return status `ok` |
| FR-02 | Question delivery | `/v1/checkins/today` returns all supported question types in the common envelope |
| FR-03 | Check-in submission | A valid submission is stored once per student/day; duplicates return a domain error |
| FR-04 | Consent gate | Protected pipelines return `403 consent_required` without active consent |
| FR-05 | Immediate support | An urgent-help choice displays deterministic support content immediately |
| FR-06 | Personal baseline | No risk flag is produced before seven valid baseline days |
| FR-07 | Explainability | Every risk flag has an explanation containing contributing signals and thresholds |
| FR-08 | Stage 1 | Eligible flags create one non-duplicate nudge |
| FR-09 | Stage 2 | Peer matching occurs only after explicit student opt-in |
| FR-10 | Stage 3 | A proposed handoff requires staff acknowledgement before outreach |
| FR-11 | Data export | A student can retrieve a machine-readable export of their data |
| FR-12 | Data deletion | A confirmed request removes or anonymizes data according to the retention policy |
| FR-13 | Audit | Protected reads and pipeline transitions create audit records |
| FR-14 | Role isolation | Staff and admin roles cannot access raw chat tables through application routes |

## 12. API contract

All versioned endpoints use `/v1`. Successful responses use:

```json
{
  "data": {},
  "error": null
}
```

The target error format is:

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

The current backend does not yet normalize FastAPI `404`, `405`, `422`, and `500` responses. Until exception handlers are implemented, clients must tolerate the default `{ "detail": ... }` error shape. See `docs/API_CONTRACT.md` for readiness and compatibility details.

## 13. Privacy and security

- Keep `.env`, private CSV exports, virtual environments, and model caches out of Git.
- Encrypt transport with TLS outside local development.
- Encrypt sensitive message content at rest.
- Store production secrets in a deployment secret manager.
- Use short-lived JWT access tokens and rotated refresh tokens.
- Restrict CORS to known frontend origins.
- Record protected-data reads and all escalation transitions.
- Do not use identifiable photos for anonymous peer support.
- Do not send health or wellbeing data to analytics platforms by default.
- Define retention and deletion behavior before a pilot.

## 14. Accessibility and design

- Warm cream surfaces, sage primary actions, and non-clinical language.
- Plus Jakarta Sans headings and Inter body text.
- Minimum 48 × 48 dp touch targets.
- WCAG AA contrast for body text.
- Visible keyboard focus on web.
- Screen-reader labels for all inputs and grouped controls.
- Reduced-motion support.
- Red reserved for urgent or destructive states.
- Figma and application components share `docs/figma-tokens.json`.

## 15. Non-functional requirements

- API response target below 500 ms for non-AI local requests at MVP scale.
- Idempotent scheduled jobs and check-in submission protection.
- Cursor pagination for list endpoints.
- Offline-tolerant check-in drafts.
- Structured logs without raw wellbeing text or secrets.
- Automated tests for route contracts, consent gates, stage boundaries, and role isolation.
- Configurable CORS and deployment URLs.

## 16. MVP release plan

### Milestone 1 — Foundation

- FastAPI configuration, standardized errors, CORS, database session, Alembic.
- Expo application shell and shared design tokens.

### Milestone 2 — Check-in vertical slice

- Users, consent, check-ins, and answers tables.
- Check-in submission and history endpoints.
- Complete frontend check-in flow with offline drafts.

### Milestone 3 — Detection demo

- Mock academic ingestion.
- Sentiment signals, personal baseline, pattern sweep, and explanations.
- Stage 1 nudge on the Home screen.

### Milestone 4 — Human support demo

- Optional peer-support simulation.
- Stage 3 preview, counsellor directory, appointment simulation, and staff acknowledgement.

### Milestone 5 — Review

- Privacy and role-access audit.
- Accessibility review.
- End-to-end demo fixtures and integration tests.

## 17. Current implementation status

Implemented:

- FastAPI application and configuration.
- Health endpoints.
- Backend-owned check-in catalog at `GET /v1/checkins/today`.
- Immediate-support metadata in the question contract.
- Frontend handoff and Figma-compatible tokens.
- Automated health and question-contract tests.

Not yet implemented:

- Database connection, models, migrations, or persistence.
- Check-in submission.
- Authentication and consent.
- Standard error-envelope handlers.
- CORS middleware.
- Baseline, pattern, nudge, peer, escalation, and staff functionality.
- Production AI integration.
- Expo frontend source code.

## 18. Open decisions

- Campus-specific crisis and emergency contact configuration.
- Final shortened daily question set versus periodic full check-in.
- Retention periods and deletion/anonymization rules.
- Approved AI provider and data-processing terms.
- Whether staff tooling is Expo web or a separate web application.
- Pilot ownership and professional review of detection thresholds.

