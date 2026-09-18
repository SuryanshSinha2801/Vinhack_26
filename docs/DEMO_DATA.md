# Demo data

The local demo workbook is `data/demo/mindtrail_demo.xlsx`.

It contains five fictional accounts and 15 days of synthetic wellbeing history (75 records). The backend reads the `Demo Users` sheet at startup and seeds missing local accounts. Passwords are hashed before being stored in the local SQLite authentication database.

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

- `Overview`: record counts, limitations, and the aggregate 15-day trend.
- `Demo Users`: fictional usernames and demo passwords.
- `15-Day History`: synthetic mood, stress, sleep, energy, connectedness, and support-response records.

No row represents a real person. The synthetic scores are not clinical measurements and must not be used for diagnosis or decision-making.
