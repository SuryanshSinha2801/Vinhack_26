# Adaptive check-in personalization

## Goal

MindTrail changes the optional part of each daily check-in so the questions stay relevant to the signed-in student. The feature monitors non-clinical wellbeing signals; it does not diagnose a mental disorder or replace a validated clinical assessment.

## Fixed safety and tracking core

Every form always asks about mood, stress, energy, desired support, immediate safety, follow-up preference, trend-personalization consent, and privacy acknowledgement. Personalization can never hide the immediate-help question or its deterministic support path.

## Ranked focus areas

The curator reads at most the latest 14 history records and scores four areas:

- `sleep`: low average sleep or a downward sleep trend
- `academic`: higher stress or an upward stress trend
- `connection`: lower connectedness or a downward connection trend
- `support`: lower mood and energy

The two highest-ranked areas supply the day's additional questions. Examples include sleep duration and quality, study pressure, social connection, useful support types, and optional context.

## Consent and cold start

If the student previously selected `No` for trend-based suggestions, the curator ignores their history and uses a deterministic rotating question mix. New users receive the same rotating cold-start behavior until history is available. The response explains whether recent history was used.

## Request flow

1. The authenticated frontend requests `GET /v1/checkins/today`.
2. The backend checks whether the student already submitted today.
3. The curator ranks focus areas and returns 10–13 questions plus personalization metadata.
4. The frontend renders only the returned IDs and types.
5. On submission, the backend rebuilds the same daily form and validates its required questions.
6. A successful submission updates date-wise history and can affect the next day's ranking.

## Safety boundaries

- The algorithm reports wellbeing patterns, not mental-health diagnoses.
- The immediate-help question remains fixed and bypasses ML/ranking logic.
- A positive immediate-help response opens the deterministic support interface.
- The dashboard ML output and question curator are separate; neither silently makes referral or treatment decisions.
- The current Excel implementation is for fictional hackathon data only.
