param(
    [string]$OutputDirectory = "data/private/backups"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$backupRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot $OutputDirectory))
$privateRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot "data/private"))

if (-not $backupRoot.StartsWith($privateRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Backups must remain under data/private so they cannot be committed."
}

New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupFile = Join-Path $backupRoot "mindtrail-$timestamp.dump"

Write-Host "Creating an encrypted-at-rest location is your responsibility. PostgreSQL may prompt for the database password."
& pg_dump --host localhost --port 5432 --username mindtrail --dbname mindtrail --format custom --file $backupFile
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed with exit code $LASTEXITCODE" }

& pg_restore --list $backupFile | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Backup validation failed with exit code $LASTEXITCODE" }

Write-Host "Validated backup: $backupFile"
