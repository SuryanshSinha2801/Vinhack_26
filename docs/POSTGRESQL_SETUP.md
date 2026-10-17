# PostgreSQL setup

MindTrail uses one SQLAlchemy connection for authentication and daily wellbeing records. SQLite is retained as the local zero-setup default. PostgreSQL uses the same models and API behavior.

## 1. Create the local database

Run these commands from PowerShell, adjusting the PostgreSQL `bin` path if needed:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres
```

Then run the following inside `psql`:

```sql
CREATE USER mindtrail WITH PASSWORD 'choose-a-long-local-password';
CREATE DATABASE mindtrail OWNER mindtrail;
\q
```

## 2. Configure MindTrail

Add this line to the local `.env` file. Do not commit the real password.

```dotenv
APP_DATABASE_URL=postgresql+psycopg2://mindtrail:choose-a-long-local-password@localhost:5432/mindtrail
APP_TIMEZONE=Asia/Kolkata
```

`AUTH_DATABASE_URL` remains only as a backward-compatible fallback when `APP_DATABASE_URL` is empty.

## 3. Start the application

```powershell
cd C:\codes\Vinhack_26
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn api.app.main:app --reload --host 127.0.0.1 --port 8000
```

Before the first start, apply the committed schema migration and explicitly import the fictional demo data:

```powershell
alembic upgrade head
python -m scripts.seed_demo_data
uvicorn api.app.main:app --reload --host 127.0.0.1 --port 8000
```

`alembic upgrade head` is safe to run again when checking for pending migrations. The seed command only imports workbook history when `daily_checkins` is empty. Excel is not used for subsequent submissions.

## 4. Verify the data

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U mindtrail -d mindtrail -c "SELECT COUNT(*) AS users FROM users;"
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U mindtrail -d mindtrail -c "SELECT COUNT(*) AS checkins FROM daily_checkins;"
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U mindtrail -d mindtrail -c "SELECT checkin_date, COUNT(*) FROM daily_checkins GROUP BY checkin_date ORDER BY checkin_date DESC LIMIT 14;"
```

The important database rule is:

```sql
UNIQUE (user_id, checkin_date)
```

This guarantees at most one daily check-in for each authenticated user, including when two requests arrive almost simultaneously.

## Production note

Use a managed PostgreSQL instance, TLS, backups, restricted database credentials, reviewed Alembic migrations, and encrypted handling of sensitive wellbeing fields before using real student data. The fictional seed import is intended for the hackathon MVP.

The current migration head is `20261017_04`. To create a timestamped custom-format dump under the ignored `data/private/backups` directory and validate that PostgreSQL can read its catalog:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\backup_postgres.ps1
```

The script intentionally does not save a database password. PostgreSQL may prompt for it. Treat every backup as sensitive and keep it encrypted and outside Git.
