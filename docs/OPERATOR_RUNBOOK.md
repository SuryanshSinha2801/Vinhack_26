# MindTrail operator runbook (Windows PowerShell)

This guide is for an authorized person operating the MindTrail hackathon website from the terminal on this PC.

## 1. Important locations

| Item | Location |
|---|---|
| Project | `C:\codes\Vinhack_26` |
| Python environment | `C:\codes\Vinhack_26\.venv` |
| Local configuration | `C:\codes\Vinhack_26\.env` |
| PostgreSQL tools | `C:\Program Files\PostgreSQL\17\bin` |
| Local website | `http://127.0.0.1:8000` |
| API documentation | `http://127.0.0.1:8000/docs` |

The `.env` file contains private local configuration. Never paste it into chat, screenshots, presentations, issues, or GitHub. Never commit database passwords, JWT secrets, AI keys, or service-role keys.

## 2. Open the project terminal

Open PowerShell and run:

```powershell
cd C:\codes\Vinhack_26
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

The prompt should begin with `(.venv)`.

## 3. Start MindTrail

Check that PostgreSQL is running:

```powershell
Get-Service postgresql-x64-17
```

If its status is not `Running`, start it from an administrator PowerShell:

```powershell
Start-Service postgresql-x64-17
```

Start the website:

```powershell
cd C:\codes\Vinhack_26
.\.venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn api.app.main:app --reload --host 127.0.0.1 --port 8000
```

Keep this terminal open. Open the website at `http://127.0.0.1:8000`.

For a local production-style run without automatic reload:

```powershell
uvicorn api.app.main:app --host 127.0.0.1 --port 8000
```

## 4. Stop MindTrail

In the terminal running Uvicorn, press:

```text
Ctrl+C
```

If a Cloudflare tunnel is running in another terminal, press `Ctrl+C` there too. Stopping Uvicorn takes the website offline locally. Stopping only the tunnel removes public access but leaves the local website running.

## 5. Confirm the service is healthy

From a second PowerShell terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/health | ConvertTo-Json -Depth 5
```

Expected result: `status` is `ok`.

Check that the home page responds:

```powershell
(Invoke-WebRequest http://127.0.0.1:8000/).StatusCode
```

Expected result: `200`.

For a brand-new empty demo database, import fictional seed data once:

```powershell
python -m scripts.seed_demo_data
```

Do not run seed imports against a database intended for real student records.

## 6. Demo login

Use one of the fictional demo accounts documented in `docs\DEMO_DATA.md`. For example:

```text
Username: arjun01
Password: Trail@Arjun26
```

These accounts are for demonstrations only. Do not reuse their passwords elsewhere.

## 7. PostgreSQL access

The application database connection is configured by `APP_DATABASE_URL` in `.env`.

Open PostgreSQL interactively without placing a password in command history:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h 127.0.0.1 -U mindtrail -d mindtrail -W
```

Useful read-only commands inside `psql`:

```sql
\dt
SELECT COUNT(*) AS users FROM users;
SELECT COUNT(*) AS checkins FROM daily_checkins;
SELECT checkin_date, COUNT(*)
FROM daily_checkins
GROUP BY checkin_date
ORDER BY checkin_date DESC
LIMIT 14;
SELECT u.username, d.checkin_date, d.mood, d.stress, d.sleep_hours
FROM daily_checkins d
JOIN users u ON u.id = d.user_id
ORDER BY d.checkin_date DESC
LIMIT 20;
\q
```

Wellbeing answers are sensitive. Only inspect individual rows when authorized and necessary. Prefer counts and aggregate queries during demonstrations.

## 8. Confirm one check-in per day

Run:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h 127.0.0.1 -U mindtrail -d mindtrail -W -c "SELECT user_id, checkin_date, COUNT(*) FROM daily_checkins GROUP BY user_id, checkin_date HAVING COUNT(*) > 1;"
```

The query should return zero rows. PostgreSQL also enforces the unique `(user_id, checkin_date)` constraint.

## 9. Run automated checks

Stop the public tunnel before maintenance. From the project directory:

```powershell
cd C:\codes\Vinhack_26
.\.venv\Scripts\Activate.ps1
python -m pytest -q
node --check frontend\app.js
git diff --check
```

Do not run tests against a production database containing real student information. Use a separate test database for any deployment beyond the hackathon demo.

The repository's test bootstrap overrides `APP_DATABASE_URL` before importing the application, creates a temporary SQLite database, and removes it after the test session. Tests therefore do not write users or check-ins into the configured PostgreSQL database.

## 10. Install or update Python dependencies

```powershell
cd C:\codes\Vinhack_26
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
alembic upgrade head
```

Restart Uvicorn after dependency or `.env` changes.

## 11. Make the local website temporarily public

First run MindTrail locally on port 8000. In a second terminal:

```powershell
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:8000
```

Cloudflare prints a temporary `https://...trycloudflare.com` address. Share only the newly printed address.

To remove public access, press `Ctrl+C` in the Cloudflare terminal. A temporary tunnel URL should be treated as public while the tunnel process is running. Changing Uvicorn's port does not revoke an already running tunnel; stop the tunnel process.

Before opening a tunnel:

- Confirm `.env`, API keys, database tools, and local files are not served by the frontend.
- Use fictional demo data only.
- Do not expose Swagger `/docs` for a real deployment.
- Do not share database or administrator credentials.

## 12. Find what is using port 8000

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess
```

Inspect the process before stopping it:

```powershell
Get-Process -Id <PID>
```

If it is the MindTrail Uvicorn process and its original terminal is unavailable:

```powershell
Stop-Process -Id <PID>
```

Never stop an unfamiliar process without inspecting it first.

## 13. Database backup

Create a private backup directory:

```powershell
New-Item -ItemType Directory -Force C:\codes\Vinhack_26\data\private\backups
```

Create a PostgreSQL custom-format backup. The command asks for the database password:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" -h 127.0.0.1 -U mindtrail -d mindtrail -W -F c -f "C:\codes\Vinhack_26\data\private\backups\mindtrail.backup"
```

The `data\private` directory is ignored by Git. Backups can contain sensitive information; do not upload them to GitHub or send them through ordinary messaging.

## 14. Database restore

Restoring overwrites or adds database state and must only be performed by an authorized operator after confirming the target database. Stop Uvicorn first and take a fresh backup.

To restore into an empty replacement database:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" -h 127.0.0.1 -U mindtrail -d mindtrail -W --clean --if-exists "C:\codes\Vinhack_26\data\private\backups\mindtrail.backup"
```

Do not run this command casually: `--clean` removes database objects before restoring them.

## 15. Git status, update, and push

Inspect before changing anything:

```powershell
cd C:\codes\Vinhack_26
git status --short
git branch --show-current
git remote -v
git log -5 --oneline
```

Pull code only when the worktree is understood and local changes are protected:

```powershell
git pull --ff-only origin main
```

Before committing:

```powershell
python -m pytest -q
node --check frontend\app.js
git diff --check
git diff
```

Stage explicit files instead of using `git add .`, because the project folder may contain private workbook changes and unrelated files:

```powershell
git add -- path\to\file1 path\to\file2
git diff --cached
git commit -m "Describe the change"
git push -u origin main
git ls-remote origin refs/heads/main
```

Never commit `.env`, `.data`, `data\private`, database backups, real check-in exports, or credentials. Never force-push without the repository owner's explicit approval.

## 16. Common problems

### Port 8000 is already in use

Another server is already listening. Use the port-inspection commands in section 12, or temporarily run:

```powershell
uvicorn api.app.main:app --reload --host 127.0.0.1 --port 8127
```

### `cloudflared` is not recognized

Use its full path:

```powershell
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" --version
```

### `psql` is not recognized

Use its full path:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" --version
```

### PostgreSQL connection fails

Check the service:

```powershell
Get-Service postgresql-x64-17
Test-NetConnection 127.0.0.1 -Port 5432
```

Then confirm `APP_DATABASE_URL` exists in `.env`. Do not print the complete value during a screen share.

### Environment activation is blocked

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Frontend looks stale

Restart Uvicorn and hard-refresh the browser with `Ctrl+F5`.

## 17. Safe operating rules

- MindTrail is a non-diagnostic hackathon prototype, not a clinical system.
- Use fictional data for demonstrations.
- Keep raw answers private and show aggregate information whenever possible.
- Stop the public tunnel immediately after a demo.
- Back up the database before schema work or restoration.
- Never delete users, check-ins, or backups without confirming the exact target and authorization.
- Never expose `.env`, JWT secrets, AI keys, database passwords, or PostgreSQL administrator credentials.
- Record operational changes in Git, but never commit runtime data.

## 18. Normal daily operator sequence

```powershell
cd C:\codes\Vinhack_26
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
Get-Service postgresql-x64-17
alembic upgrade head
uvicorn api.app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. When finished, stop any Cloudflare tunnel first, then stop Uvicorn with `Ctrl+C`.
