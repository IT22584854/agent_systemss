import os
import json
from openai import OpenAI

# 1. Setup Client
client = OpenAI(api_key="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")

def generate_multiturn_row(content, language, style):
    system_instruction = "You are a helpful Health Information Guide for the Sri Lankan Ministry of Health."
    
    # Precise prompt to force 4-turn logic
    prompt = f"""
    Generate a 4-turn medical conversation based on the provided text.
    
    FORMAT: Output ONLY a JSON object with a 'messages' key containing 4 message objects.
    Each object must have 'role' and 'content' keys. 
    Role must be either 'user' or 'assistant'.
    
    STRUCTURE:
    - turn 1 (user): Initial health question.
    - turn 2 (assistant): Detailed answer using proper terms.
    - turn 3 (user): Practical follow-up (e.g. food, side effects, timing).
    - turn 4 (assistant): Final advice.

    LANGUAGE & STYLE: {language} ({style})
    LINGUISTIC RULE: Use natural spoken grammar (Janawahara). 
    If style is 'mixed', use common Sri Lankan Singlish/Tamilish.

    TEXT CONTENT:
    {content[:3000]}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" } # Forces valid JSON
        )
        
        raw_json = json.loads(response.choices[0].message.content)
        
        # --- THE AZRI FIX: Strict Re-labeling ---
        # This ensures role names are lowercase and correct regardless of AI output
        final_messages = [{"role": "system", "content": system_instruction}]
        
        for i, msg in enumerate(raw_json['messages'][:4]):
            # i=0 (user), i=1 (assistant), i=2 (user), i=3 (assistant)
            role = "user" if i % 2 == 0 else "assistant"
            final_messages.append({
                "role": role, 
                "content": msg['content']
            })
            
        return {"messages": final_messages}
    except Exception as e:
        print(f"Row failed: {e}")
        return None

# 2. Main Execution Logic
def main():
    # Azri's required counts
    configs = [
        {"lang": "English", "style": "formal", "count": 100},
        {"lang": "Sinhala", "style": "formal spoken", "count": 100},
        {"lang": "Tamil", "style": "formal spoken", "count": 100},
        {"lang": "Sinhala", "style": "romanized-mixed", "count": 50},
        {"lang": "Tamil", "style": "romanized-mixed", "count": 50}
    ]

    output_file = "3_datasets/medical_training_400.jsonl"
    processed_dir = "2_processed" # Where your Crawl4AI markdown files are
    files = [f for f in os.listdir(processed_dir) if f.endswith(".md")]

    with open(output_file, "w", encoding="utf-8") as f:
        file_idx = 0
        for config in configs:
            print(f"🚀 Generating {config['count']} rows for {config['lang']} ({config['style']})...")
            for i in range(config['count']):
                # Rotate through your 145 files
                with open(os.path.join(processed_dir, files[file_idx % len(files)]), "r", encoding="utf-8") as md:
                    content = md.read()
                
                row = generate_multiturn_row(content, config['lang'], config['style'])
                if row:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                
                file_idx += 1
                if (i+1) % 10 == 0:
                    print(f"  - Progress: {i+1}/{config['count']}")

    print(f"✅ Finished! Dataset saved to {output_file}")

if __name__ == "__main__":
    main()