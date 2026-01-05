import json
from supabase import create_client

# Setup
supabase = create_client("https://amiyreckqotozjxyhxld.supabase.co", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFtaXlyZWNrcW90b3pqeHloeGxkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzUzNTU0NSwiZXhwIjoyMDgzMTExNTQ1fQ.Jo6SO0Eif1BNkvhr7wHYrOswRCzywXnK-pepwKHLIjI")

def export_to_jsonl():
    # --- CHANGE FILENAME HERE ---
    output_file = "medical_research_dataset_v1.jsonl" 
    # ----------------------------

    print(f"📡 Fetching data from Supabase...")
    response = supabase.table("medical_research").select("*").execute()
    rows = response.data

    if not rows:
        print("❌ No data found!")
        return
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for row in rows:
            # Cleaning the data to ensure it's a proper List/Dict and not a String
            chat_ml_data = json.loads(row['chat_ml']) if isinstance(row['chat_ml'], str) else row['chat_ml']
            ner_data = json.loads(row['ner_data']) if isinstance(row['ner_data'], str) else row['ner_data']
            
            entry = {
                "source": row['file_name'],
                "language": row['language_style'],
                "messages": chat_ml_data, 
                "ner": ner_data
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f"✅ DONE! File created: {output_file}")
    print(f"📦 Total entries: {len(rows)}")

if __name__ == "__main__":
    export_to_jsonl()
