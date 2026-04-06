param(
    [string]$DbPath = "agents/data/evaluation_logs.db",
    [string]$OutPath = "benchmark/outputs/agent_turn_logs_final_answers.csv"
)

$ErrorActionPreference = "Stop"

$sqlite = Get-Command sqlite3 -ErrorAction SilentlyContinue
if (-not $sqlite) {
    throw "sqlite3 not found. Install sqlite3 or add it to PATH."
}

if (-not (Test-Path $DbPath)) {
    throw "Database not found: $DbPath"
}

$outDir = Split-Path -Parent $OutPath
if ($outDir -and -not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$query = @"
.headers on
.mode csv
.once $OutPath
SELECT
  session_id,
  turn_index,
  user_message,
  assistant_message,
  active_agent,
  rag_query,
  is_clarification,
  is_final_answer,
  created_at,
  responded_at,
  latency_ms
FROM agent_turn_logs
WHERE is_final_answer = 1
ORDER BY created_at;
"@

& $sqlite.Source $DbPath $query
Write-Host "Export complete: $OutPath"

