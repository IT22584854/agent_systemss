from datasets import load_dataset


dataset = load_dataset(
    "ai4bharat/sangraha", 
    data_dir="verified/tam", 
    split="train", 
    streaming=True
)

# Shuffle (Pseudo-random)
shuffled_dataset = dataset.shuffle(buffer_size=1000, seed=42)

print("Displaying 3 random entries from Sangraha (Tamil)...\n")

for i, sample in enumerate(shuffled_dataset.take(3)):
    print(f"--- Sample {i+1} ---")
    text_preview = sample.get('text', 'No text found')[:500] # Truncate text to 500 chars so it doesn't flood terminal 
    print(f"ID: {sample.get('id', 'N/A')}")
    print(f"URL: {sample.get('url', 'N/A')}")
    print(f"Content: {text_preview}...\n")