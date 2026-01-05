import os
import json
import time
import re
from openai import OpenAI
from supabase import create_client
from tqdm import tqdm

# 1. Configuration
client = OpenAI(api_key="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")
supabase = create_client("https://amiyreckqotozjxyhxld.supabase.co", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFtaXlyZWNrcW90b3pqeHloeGxkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzUzNTU0NSwiZXhwIjoyMDgzMTExNTQ1fQ.Jo6SO0Eif1BNkvhr7wHYrOswRCzywXnK-pepwKHLIjI")

def is_garbage(text):
    """Very lenient: Only skips if the file is basically empty."""
    if len(text.strip()) < 50: 
        return True
    return False

def process_to_supabase(file_path, file_name, index):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        if is_garbage(text):
            return "SKIP_GARBAGE"

        # Logic for Language Quota
        if index < 100:
            target_lang, style_key = "Professional English", "english"
        elif index < 150:
            target_lang, style_key = "Pure Sinhala (Spoken)", "sinhala_script"
        elif index < 200:
            target_lang, style_key = "Pure Tamil (Spoken)", "tamil_script"
        elif index < 300:
            target_lang, style_key = "Sinhala-English Code-Mixed", "sinhala_code"
        else:
            target_lang, style_key = "Tamil-English Code-Mixed", "tamil_code"

        prompt = f"""
        Return a JSON object with 'ner' and 'chatml'.
        1. 'ner': List Medications/Conditions found. If none, return [].
        2. 'chatml': A 4-turn medical conversation in {target_lang}. 
           Format: [{{"role": "user", "content": "..."}}, {{"role": "assistant", "content": "..."}}]
        
        TEXT: {text[:3000]}
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a medical data engineer. Always return valid JSON."},
                      {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        data = json.loads(response.choices[0].message.content)

        # Upload if chatml exists
        if data.get('chatml'):
            supabase.table("medical_research").insert({
                "file_name": file_name,
                "language_style": style_key,
                "chat_ml": data['chatml'],
                "ner_data": data.get('ner', []),
                "raw_text": text[:500]
            }).execute()
            return "SUCCESS"
        
        return "SKIP_AI_EMPTY"

    except Exception as e:
        if "429" in str(e):
            print("⏳ Rate limit hit, sleeping 10 seconds...")
            time.sleep(10)
        return f"ERROR: {e}"

# 2. Execution Loop
INPUT_DIR = r"D:\Medical_OCR_Research\2_processed"
all_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".md")]

if not all_files:
    print("❌ ERROR: No .md files found in " + INPUT_DIR)
else:
    success_count = 0
    file_index = 0 
    pbar = tqdm(total=400, desc="Overall Progress")
    
    while success_count < 400:
        current_file = all_files[file_index % len(all_files)]
        
        result = process_to_supabase(
            os.path.join(INPUT_DIR, current_file), 
            current_file, 
            success_count
        )
        
        if result == "SUCCESS":
            success_count += 1
            pbar.update(1)
            # Short print so you see it working
            print(f" ✅ [{success_count}/400] Saved {current_file}")
        elif result == "SKIP_GARBAGE":
            pass # Keep it quiet for garbage
        else:
            print(f" ⚠️ {result} for {current_file}")
        
        file_index += 1
        time.sleep(0.3)

    pbar.close()
    print("🎉 MISSION ACCOMPLISHED. 400 ROWS IN SUPABASE.")