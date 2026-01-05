import os
import json
from openai import OpenAI

client = OpenAI(api_key="YOUR_OPENAI_KEY")

def generate_chatml(content, language, style):
    # This prompt tells GPT exactly how to behave for your leader's requirements
    prompt = f"""
    Using the following medical text, generate a multi-turn conversation (at least 2 turns) in ChatML format.
    
    Language: {language}
    Style: {style}
    Format: JSONL with 'messages' list containing 'role' and 'content'.
    
    Context: {content[:2000]} 
    """
    
    response = client.chat.completions.create(
        model="gpt-4o", # or gpt-3.5-turbo to save costs
        messages=[{"role": "user", "content": prompt}],
        response_format={ "type": "json_object" }
    )
    return response.choices[0].message.content

# Logic to loop through 0_raw_data/markdown and save to dataset.jsonl
# You'll call this for each language/style combo until you hit 300 rows.