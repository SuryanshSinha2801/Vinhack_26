# Demo data

The active local demo workbook is `data/demo/mindtrail_demo_6_months.xlsx`.

It contains 40 fictional accounts and 180 days of synthetic wellbeing history (7,200 records). The backend reads every populated row in the `Demo Users` sheet at startup and seeds missing local accounts. Passwords are hashed before being stored in the local SQLite authentication database.

## Demo credentials

The workbook contains reproducible fictional credentials for disposable local test databases only. Production mode refuses to run the demo seed command. Before exposing a previously seeded database, run `python -m scripts.rotate_local_security`; replacement credentials are written only to the Git-ignored `data/private/rotated_demo_credentials.csv` file.

Credentials formerly printed in this document must be considered public and must never be accepted by an internet-accessible deployment.

## Workbook sheets

- `Overview`: record counts, limitations, and the aggregate recent trend.
- `Demo Users`: 40 fictional usernames and demo passwords.
- `15-Day History`: retained for compatibility; now contains 180 days of synthetic mood, stress, sleep, energy, connectedness, and support-response records.
- `Check-in Submissions`: append-only audit records for check-ins saved through the website.

No row represents a real person. The synthetic scores are not clinical measurements and must not be used for diagnosis or decision-making.
