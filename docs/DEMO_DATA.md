# Demo data

The active local demo workbook is `data/demo/mindtrail_demo_6_months.xlsx`.

It contains 40 fictional accounts and 180 days of synthetic wellbeing history (7,200 records). The backend reads every populated row in the `Demo Users` sheet at startup and seeds missing local accounts. Passwords are hashed before being stored in the local SQLite authentication database.

## Demo credentials

| Username | Password | Display name |
| --- | --- | --- |
| `arjun01` | `Trail@Arjun26` | Arjun |
| `meera02` | `Trail@Meera26` | Meera |
| `kabir03` | `Trail@Kabir26` | Kabir |
| `anaya04` | `Trail@Anaya26` | Anaya |
| `rohan05` | `Trail@Rohan26` | Rohan |

These credentials are intentionally public and must only be used for local demonstrations. They are not suitable for production or real student accounts.

## Workbook sheets

- `Overview`: record counts, limitations, and the aggregate recent trend.
- `Demo Users`: 40 fictional usernames and demo passwords.
- `15-Day History`: retained for compatibility; now contains 180 days of synthetic mood, stress, sleep, energy, connectedness, and support-response records.
- `Check-in Submissions`: append-only audit records for check-ins saved through the website.

No row represents a real person. The synthetic scores are not clinical measurements and must not be used for diagnosis or decision-making.
