from transformers import AutoTokenizer

# Load tokenizers
model_1_id = "unsloth/llama-3-8b-bnb-4bit" 
model_2_id = "Qwen/Qwen3-8B-Base" 

try:
    tokenizer_llama = AutoTokenizer.from_pretrained(model_1_id)
    tokenizer_qwen = AutoTokenizer.from_pretrained(model_2_id)
except OSError:
    print(f"⚠️ Warning: Could not find {model_2_id}.")
  

sentences = {
    "English": "The quick brown fox jumps over the lazy dog.",
    "Tamil (Simple)": "எனது பெயர் ஆதித்யா.",
    "Tamil (Complex)": "இலங்கை ஒரு அழகான தீவு நாடு.",
    "Sinhala (Simple)": "මගේ නම ආදිත්‍ය",
    "Sinhala (Complex)": "ශ්‍රී ලංකාව ලස්සන දූපත් රටක්"
}

print(f"\n{'Language':<20} | {'Chars':<5} || {'L-Toks':<7} | {'Q-Toks':<7} || {'L-Eff':<6} | {'Q-Eff':<6}")
print("=" * 80)

for lang, text in sentences.items():
    # --- LLAMA-3 ---
    
    ids_llama = tokenizer_llama.encode(text, add_special_tokens=False)
    count_llama = len(ids_llama)
    
    # --- QWEN ---
    ids_qwen = tokenizer_qwen.encode(text, add_special_tokens=False)
    count_qwen = len(ids_qwen)
    
    # --- Stats ---
    char_count = len(text)
    
    # Efficiency Calculation
    eff_llama = char_count / count_llama if count_llama > 0 else 0
    eff_qwen = char_count / count_qwen if count_qwen > 0 else 0
    
    print(f"{lang:<20} | {char_count:<5} || {count_llama:<7} | {count_qwen:<7} || {eff_llama:.2f}   | {eff_qwen:.2f}")

    # Visual Inspection (verify no garbage)
    print(f"  L-Tokens: {[tokenizer_llama.decode([x]) for x in ids_llama[:5]]}...")
    print(f"  Q-Tokens: {[tokenizer_qwen.decode([x]) for x in ids_qwen[:5]]}...")