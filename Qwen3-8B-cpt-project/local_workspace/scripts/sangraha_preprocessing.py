import re
import os
import unicodedata
from datasets import load_dataset, Dataset
import pyarrow as pa
import pyarrow.parquet as pq

# =================CONFIGURATION=================
SOURCE_DATASET = "ai4bharat/sangraha"
SOURCE_SUBSET = "verified" 
LANG_CODE = "tam"
OUTPUT_DIR = "processed_data/sangraha_tamil_clean"
HF_REPO_ID = "Azri-Muhsin/sangraha-tamil-cleaned" 
BATCH_SIZE = 10_000 
# ===============================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_text_sillama_style(text):
    """
    Applies SiLlama-style cleaning rules adapted for Tamil:
    1. Unicode Normalization (NFC)
    2. Remove HTML tags if any present
    3. Script Identification (Must be primarily Tamil)
    4. Length filtering
    5. Agressively filtering noise phrases
    """
    if not isinstance(text, str):
        return None
    
    # 1. Unicode Normalization
    text = unicodedata.normalize('NFC', text)

    # 5. Noise Filtering
    if re.search(r'home screen|amazon card |Click here', text, flags=re.IGNORECASE):
        return None
    
    # 2. Heuristic Cleaning (Remove HTML & Excessive Whitespace)
    text = re.sub(r'<.*?>', '', text) # Remove HTML tags
    text = re.sub(r'^ - ', '', text)  # Remove leading hyphens
    text = re.sub(r'\s+', ' ', text).strip() # Collapse whitespace
    
    
    # 3. Filter Short/Empty Sentences (< 20 chars)
    if len(text) < 20:
        return None
        
    # 4. Script Filtering 
    # Check if a significant portion of the text is actually Tamil.
    # Tamil Unicode Block: U+0B80 to U+0BFF
    tamil_char_count = len(re.findall(r'[\u0B80-\u0BFF]', text))
    total_char_count = len(text.replace(" ", ""))
    
    if total_char_count == 0:
        return None
        
    # Keep only if > 50% of characters are Tamil 
    if (tamil_char_count / total_char_count) < 0.5:
        return None

    return text

def process_and_upload():
    print(f"Loading {SOURCE_DATASET} (verified/{LANG_CODE}) in streaming mode...")
    
    # Sangraha structure requires pointing to data_dir for specific language to avoid downloading all 22 langs
    # Note: If 'verified/tam' fails, we fallback to streaming 'verified' and filtering.

    dataset = load_dataset(
            SOURCE_DATASET, 
            data_dir=f"verified/{LANG_CODE}", 
            split="train", 
            streaming=True
    )


    buffer = []
    chunk_counter = 0
    total_processed = 0
    
    # Schema for Parquet (Simple text column)
    schema = pa.schema([('text', pa.string())])
    
    print("Starting processing...")
    
    for i, sample in enumerate(dataset):
        # Extract text (handle different column names if necessary)
        raw_text = sample.get('text', sample.get('content', ''))
        
        cleaned_text = clean_text_sillama_style(raw_text)
        
        if cleaned_text:
            buffer.append({'text': cleaned_text})
            
        # Flush to disk every BATCH_SIZE
        if len(buffer) >= BATCH_SIZE:
            chunk_filename = os.path.join(OUTPUT_DIR, f"part-{chunk_counter}.parquet")
            
            # Convert buffer to PyArrow Table
            table = pa.Table.from_pylist(buffer, schema=schema)
            pq.write_table(table, chunk_filename)
            
            print(f"Saved chunk {chunk_counter} ({len(buffer)} rows) to {chunk_filename}")
            buffer = []
            chunk_counter += 1
            total_processed += BATCH_SIZE
            
    # Flush remaining buffer
    if buffer:
        chunk_filename = os.path.join(OUTPUT_DIR, f"part-{chunk_counter}.parquet")
        table = pa.Table.from_pylist(buffer, schema=schema)
        pq.write_table(table, chunk_filename)
        print(f"Saved final chunk {chunk_counter} ({len(buffer)} rows).")

    print(f"Processing complete! Total estimated rows: {total_processed + len(buffer)}")
    
    # Upload to Hub
    print(f"Uploading to Hugging Face Hub: {HF_REPO_ID}...")
    
    # We load the local folder as a dataset to push it easily
    final_dataset = load_dataset("parquet", data_files=f"{OUTPUT_DIR}/*.parquet")
    final_dataset.push_to_hub(HF_REPO_ID, private=False) # Set private=False if you want it public
    
    print("Upload Complete! ✨")

if __name__ == "__main__":
    process_and_upload()