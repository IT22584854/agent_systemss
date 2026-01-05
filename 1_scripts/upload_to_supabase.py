import os
from supabase import create_client
from openai import OpenAI

# Initialize
supabase = create_client("YOUR_URL", "YOUR_KEY")
client = OpenAI(api_key="YOUR_OPENAI_KEY")

def get_embedding(text):
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def chunk_text(text, size=1000):
    """Splits huge files into smaller pieces so search is accurate."""
    return [text[i:i+size] for i in range(0, len(text), size)]

def upload_all_markdowns():
    md_dir = "0_raw_data/markdown"
    
    for filename in os.listdir(md_dir):
        with open(os.path.join(md_dir, filename), 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Identify metadata
            lang = "sinhala" if "sin" in filename.lower() else "english"
            # Split the huge file into chunks
            chunks = chunk_text(content)
            
            print(f"Uploading {filename} in {len(chunks)} chunks...")
            
            for i, chunk in enumerate(chunks):
                embedding = get_embedding(chunk)
                data = {
                    "content": chunk,
                    "language": lang,
                    "style": "formal",
                    "metadata": {"source": filename, "chunk": i},
                    "embedding": embedding
                }
                supabase.table("documents").insert(data).execute()

if __name__ == "__main__":
    upload_all_markdowns()