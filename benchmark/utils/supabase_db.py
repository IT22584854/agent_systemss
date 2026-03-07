# import os
# from supabase import create_client, Client
# from dotenv import load_dotenv

# load_dotenv()

# # .strip() is critical here to remove hidden spaces/newlines from .env
# url = os.getenv("SUPABASE_URL", "").strip()
# key = os.getenv("SUPABASE_KEY", "").strip()

# # Ensure the URL doesn't have a trailing slash
# if url.endswith("/"):
#     url = url[:-1]

# # Initialize with explicit error checking
# try:
#     supabase: Client = create_client(url, key)
# except Exception as e:
#     print(f"Failed to initialize Supabase Client: {e}")

# def store_evaluation(db_row: dict):
#     try:
#         # Check if table exists/connection is alive
#         response = supabase.table("evaluations").insert(db_row).execute()
#         return response
#     except Exception as e:
#         # Detailed error logging
#         print(f"Supabase Insert Error: {e}")
#         return None
    

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def store_evaluation(db_row: dict):
    """
    Uses standard REST calls to bypass SDK-level networking conflicts.
    """
    url = os.getenv("SUPABASE_URL", "").strip().rstrip('/')
    key = os.getenv("SUPABASE_KEY", "").strip()

    if not url or not key:
        print("❌ Supabase Error: Missing Credentials")
        return None

    # Supabase REST API endpoint for your table
    endpoint = f"{url}/rest/v1/evaluations"
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    try:
        # Standardize all numeric values to basic floats
        payload = {k: (float(v) if isinstance(v, (float, int)) else str(v)) for k, v in db_row.items()}
        
        # Perform a standard POST request
        response = requests.post(endpoint, headers=headers, json=payload, timeout=10)
        
        if response.status_code in [200, 201]:
            print("✅ Successfully logged to Supabase via REST API")
        else:
            print(f"❌ Supabase REST Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Network Error: {e}")

    return None