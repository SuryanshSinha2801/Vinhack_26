# MindTrail

**A Chatbot-Led Early Warning & Support System for Student Wellbeing**

> Hackathon Track: Proactive Mental Health for Students

## Overview

MindTrail is a conversational chatbot that lives inside a college's existing student app and talks to every student, every day. Instead of relying on students to self-report distress, it combines two signals — how a student is *talking* (daily check-ins + occasional deep conversations) and how a student is *performing* (attendance, deadlines, exam results already tracked by the college) — to spot early, combined patterns of stress before they become a crisis. When a concerning pattern emerges, the bot itself responds: first with a small wellbeing nudge, optionally with an anonymous peer connection, and — if things keep worsening — by escalating to the student's proctor and a curated list of college-affiliated counsellors.

The chatbot is not a bolt-on feature; it is the single, consistent interface for detection, support, and escalation.

## Problem

- Students under stress are often the least likely to ask for help — they mask symptoms, isolate, or don't notice the signs themselves.
- Colleges already collect rich behavioral data (attendance, deadlines, grades) but only use it administratively, never for wellbeing.
- This leaves two blind spots:
  - Students **withdrawing behaviorally** (skipping class, missing deadlines) go unnoticed until severe.
  - Students **struggling emotionally while still performing academically** are missed entirely.

## Solution at a Glance

| Layer | What it does |
|---|---|
| **Daily check-ins** | 10–20 second mood MCQ / micro-quiz, designed to actually get completed |
| **Deep conversations** | Occasional longer, open-ended chats for richer language/tone signal |
| **Academic context** | Pulls attendance, deadlines, exam results from the college app as supporting (not primary) signal |
| **Pattern detection** | Builds a personal baseline per student; flags when chat tone *and* academic data dip together |
| **Tiered response** | Stage 1: bot nudge → Stage 2: optional anonymous peer connection → Stage 3: human escalation to proctor + counsellors |

## Key Features

- 💬 Single conversational interface for detection, nudging, and escalation
- ⏱️ Low-friction daily check-ins + occasional deep conversations
- 📊 Academic data (deadlines, attendance, exam results) used as supporting context, not a separate dashboard
- 🧠 Per-student personal baseline pattern detection (not generic averages)
- 🌱 Stage 1: concrete, actionable wellbeing nudges (not a generic "are you okay?")
- 🤝 Stage 2: optional, anonymous peer-to-peer matching (secondary feature)
- 🚨 Stage 3: human escalation to proctor + curated counsellor/doctor list
- 🔒 Privacy-first design: opt-in, explainable flags, data minimization, human-in-the-loop

## How It Works (Data Flow)

1. **Daily checkpoint** — short, semi-forced mood MCQ or quiz.
2. **Deep conversation (occasional)** — longer, freer chat for richer signal.
3. **Pull context** — sync deadlines, attendance, exam results from the college app.
4. **Detect pattern** — compare chat tone + academic trend against the student's own baseline.
5. **Alert + nudge** — bot delivers a small, concrete wellbeing suggestion.
6. **Offer peer support** — optional, anonymous connection to a similarly-patterned student.
7. **Escalate** — if the pattern keeps worsening, alert the proctor and hand off a counsellor/doctor list.

## Tech Stack (Suggested)

| Component | Tech |
|---|---|
| Chatbot UI | React Native / Flutter (embedded in existing college app) |
| Conversation engine | Rule-based flow (daily check-ins) + LLM-based flow (deep conversations) |
| NLP / sentiment | Lightweight sentiment & tone analysis on open-text replies |
| Backend | Node.js or Python (FastAPI) |
| Data ingestion | Scheduled sync / webhook from college website/app APIs |
| Pattern engine | Per-student baseline model, flags combined chat + academic dips |
| Database | PostgreSQL (encrypted at rest for chat logs & sensitive fields) |
| Peer matching (secondary) | Rule-based anonymous pattern-similarity matcher |
| Escalation routing | Notifies proctor + surfaces college-affiliated counsellor list |

## Privacy & Trust

MindTrail treats trust as a core design constraint:

- **Opt-in only** — stress tracking is never default-on.
- **Explainable flags** — students can always see *why* a nudge or escalation happened.
- **Data minimization** — raw scores stay private by default; only aggregate, anonymized trends reach administrators unless a severe-risk threshold is hit.
- **Human-in-the-loop** — proctor/counsellor escalation only triggers at Stage 3, after sustained worsening.

## Project Status

- **MVP (hackathon demo):** mock college-app data + working daily chatbot + rule-based scoring and escalation flow.
- **Next steps:** pilot with a single department, refine baseline/scoring thresholds using real anonymized data, and formalize the counsellor handoff SLA with campus mental health services.

## Roadmap

- [ ] Mock data layer for deadlines / attendance / exam results
- [ ] Daily check-in chatbot flow (rule-based)
- [ ] Deep conversation flow (LLM-based)
- [ ] Sentiment/tone analysis on open-text chat
- [ ] Per-student baseline + pattern detection engine
- [ ] Stage 1 nudge delivery
- [ ] Stage 2 anonymous peer matching (optional)
- [ ] Stage 3 proctor + counsellor escalation routing
- [ ] Privacy controls: opt-in flow, explainable flags, data minimization

## Disclaimer

MindTrail is a support and escalation tool, not a diagnostic or clinical product. It is designed to surface early signals and connect students to human professionals — it does not replace licensed mental health care.

See [PRD.md](./PRD.md) for the full product requirements.

## Run the website

The responsive frontend is served by the FastAPI application, so only one development server is required:

```powershell
.venv\Scripts\Activate.ps1
uvicorn api.app.main:app --reload
```

Open `http://127.0.0.1:8000/` for the website or `http://127.0.0.1:8000/docs` for the API documentation. If Uvicorn was already running before the frontend was added, stop it with `Ctrl+C` and start it again.

Forty fictional username/password accounts and 180 days of synthetic history (7,200 records) are available in [`data/demo/mindtrail_demo_6_months.xlsx`](./data/demo/mindtrail_demo_6_months.xlsx). The same records are exported to [`data/ml/wellbeing_6_months_40_users.csv`](./data/ml/wellbeing_6_months_40_users.csv) for reproducible ML training. See [`docs/DEMO_DATA.md`](./docs/DEMO_DATA.md) for credentials and safety limits.

The dashboard includes a compact PyTorch trend classifier trained on rolling seven-day signals. It was trained on an RTX 5060 with eight users held out for testing. Its output is a synthetic-data demo indicator, never a diagnosis or an automated care decision. Training details are in [`docs/ML_MODEL.md`](./docs/ML_MODEL.md).
