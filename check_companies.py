import os
import httpx
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

# Clean URL
url = url.strip().rstrip("/")

headers = {"apikey": key, "Authorization": f"Bearer {key}"}

try:
    with httpx.Client() as client:
        response = client.get(f"{url}/rest/v1/companies?select=*", headers=headers)
        response.raise_for_status()
        data = response.json()

        if data:
            print(f"✅ Found {len(data)} companies in database:")
            for row in data:
                print(
                    f"- '{row.get('company_name')}' | Number: '{row.get('exotel_number')}' | Bucket: '{row.get('bucket_name')}'"
                )
        else:
            print("❌ No companies found in the 'companies' table.")
except Exception as e:
    print(f"❌ Error querying Supabase: {e}")
