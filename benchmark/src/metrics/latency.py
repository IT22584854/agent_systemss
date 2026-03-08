import time

# User enters question
t_user_entered = time.time()

# --- Translation (if applicable) ---
translated_question = translate_to_english(user_question)

# --- Agent Request ---
t_agent_start = time.time()
agent_response = get_agent_response(translated_question)
t_agent_end = time.time()
agent_latency = t_agent_end - t_agent_start

# --- Evaluation ---
t_eval_start = time.time()
score, grade = evaluate_agent_response(agent_response)
t_eval_end = time.time()
eval_latency = t_eval_end - t_eval_start

# --- Total Latency ---
t_response_received = time.time()
total_latency = t_response_received - t_user_entered

print(f"Agent Latency: {agent_latency:.3f}s")
print(f"Evaluation Latency: {eval_latency:.3f}s")
print(f"Total Latency: {total_latency:.3f}s")
