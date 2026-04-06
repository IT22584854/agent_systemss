-- Export final-answer rows for evaluation from agent turn logs.
-- Usage from repo root (PowerShell):
-- sqlite3 agents/data/evaluation_logs.db ".read benchmark/scripts/export_agent_turn_logs.sql"

.headers on
.mode csv
.once benchmark/outputs/agent_turn_logs_final_answers.csv
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
