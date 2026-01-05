import json

def convert_to_chatml(user_msg, assistant_msg, system_prompt="You are a helpful medical assistant."):
    """Formats a single Q&A into the ChatML structure Azri requested."""
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_msg}
        ]
    }

# This is what you will save to your .jsonl file
# Example for a Code-mixed row:
row = convert_to_chatml(
    user_msg="Mata doctor hambawenna appointment ekak ganna puluwanda?", # Code-mixed/Singlish
    assistant_msg="Ow, obata online ho dura kathanaya magin appointment ekak laba gatha haka." # Formal Sinhala response
)

with open("dataset.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps(row) + "\n")