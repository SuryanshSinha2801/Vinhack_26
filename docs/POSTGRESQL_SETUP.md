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

On the first start, SQLAlchemy creates the implemented tables and imports the fictional workbook seed history if the `daily_checkins` table is empty. Excel is not used for subsequent submissions.

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

Use a managed PostgreSQL instance, TLS, backups, restricted database credentials, proper Alembic migrations, and encrypted handling of sensitive wellbeing fields before using real student data. The current automatic table creation and fictional seed import are intended for the hackathon MVP.
