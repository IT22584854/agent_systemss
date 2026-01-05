import os
import json
import time
from openai import OpenAI
from tqdm import tqdm

# Use your OpenAI Key here
client = OpenAI(api_key="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")

def generate_multiturn_row(content, language, style):
    system_instruction = "You are a helpful Health Information Guide for the Sri Lankan Ministry of Health."
    
    prompt = f"""
    Using the medical text provided, generate a 4-turn conversation in JSON format.
    LANGUAGE: {language}
    STYLE: {style}

    LINGUISTIC RULES:
    1. Use natural, spoken {language} (Janawahara). 
    2. For Sinhala/Tamil, avoid robotic government-style endings. 
    3. Keep medical terms in English where appropriate for Sri Lankan hospitals.

    JSON STRUCTURE:
    Return a JSON object with a 'messages' key containing 4 items (user, assistant, user, assistant).

    TEXT: {content[:3000]}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # <--- THE "BIG" MODEL (Not Mini)
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" } 
        )
        raw_json = json.loads(response.choices[0].message.content)
        final_messages = [{"role": "system", "content": system_instruction}]
        for i, msg in enumerate(raw_json['messages'][:4]):
            role = "user" if i % 2 == 0 else "assistant"
            final_messages.append({"role": role, "content": msg['content']})
        return {"messages": final_messages}
    except Exception as e:
        print(f"⚠️ Row failed: {e}")
        return None

def main():
    processed_dir = r"D:\Medical_OCR_Research\2_processed" 
    output_file = r"D:\Medical_OCR_Research\3_datasets\medical_training_final.jsonl"
    
    files = [f for f in os.listdir(processed_dir) if f.endswith(".md")]
    configs = [
        {"lang": "Sinhala", "style": "formal spoken", "count": 100},
        {"lang": "Tamil", "style": "formal spoken", "count": 100},
        {"lang": "English", "style": "formal", "count": 100},
        {"lang": "Sinhala", "style": "romanized code-mixed", "count": 50},
        {"lang": "Tamil", "style": "romanized code-mixed", "count": 50}
    ]

    with open(output_file, "w", encoding="utf-8") as f:
        global_file_idx = 0
        for config in configs:
            print(f"🚀 Generating {config['lang']}...")
            success_count = 0
            while success_count < config['count']:
                source_path = os.path.join(processed_dir, files[global_file_idx % len(files)])
                with open(source_path, "r", encoding="utf-8") as md:
                    content = md.read()
                row = generate_multiturn_row(content, config['lang'], config['style'])
                if row:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    success_count += 1
                global_file_idx += 1
                time.sleep(0.1) 

    print(f"🎉 DONE: {output_file}")

if __name__ == "__main__":
    main()