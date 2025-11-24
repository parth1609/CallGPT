import asyncio
import os
import sys
import random
import time
from typing import List
from dotenv import load_dotenv
from pinecone import Pinecone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service import RetrievalService

# Mock the embedding service call since it's not running
async def mock_get_query_embedding(self, query: str, model_name: str = None) -> List[float]:
    print(f"[Mock] Generating embedding for query: '{query}'")
    # Return a fixed random vector for consistency in this test
    random.seed(42)
    return [random.uniform(-1.0, 1.0) for _ in range(384)]

async def run_test():
    print("--- Starting Retrieval Service Test ---")
    
    # 1. Load Environment
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(env_path)
    
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("Error: PINECONE_API_KEY not found.")
        return

    # 2. Determine Index Name
    bucket_name = os.getenv("SUPABASE_BUCKET")
    if not bucket_name:
        print("Warning: SUPABASE_BUCKET not set in .env.")
        # List indexes to help user
        pc = Pinecone(api_key=api_key)
        indexes = pc.list_indexes()
        index_names = [i.name for i in indexes]
        print(f"Available indexes: {index_names}")
        
        if index_names:
            bucket_name = index_names[0]
            print(f"Auto-selecting first index for test: {bucket_name}")
            os.environ["SUPABASE_BUCKET"] = bucket_name
        else:
            print("Error: No Pinecone indexes found. Please create one.")
            return
    else:
        print(f"Using index from SUPABASE_BUCKET: {bucket_name}")

    # 3. Insert Test Data
    print("\n--- Step 1: Inserting Test Data ---")
    try:
        pc = Pinecone(api_key=api_key)
        index = pc.Index(bucket_name)
        
        # Check index stats
        print(f"Index stats before: {index.describe_index_stats()}")

        # Generate same vector as mock embedding
        random.seed(42)
        test_vector = [random.uniform(-1.0, 1.0) for _ in range(384)]
        
        test_id = "test_doc_001"
        index.upsert(vectors=[{
            "id": test_id,
            "values": test_vector,
            "metadata": {"content": "This is a test document to verify retrieval."}
        }])
        print(f"Upserted test document with ID: {test_id}")
        
        # Wait for consistency
        print("Waiting 10 seconds for index update...")
        time.sleep(10)
        
        # Verify insertion by fetching
        fetch_res = index.fetch(ids=[test_id])
        if test_id in fetch_res.vectors:
            print(f"Verified: Document {test_id} exists in index.")
        else:
            print(f"Warning: Document {test_id} not found in index after upsert.")

    except Exception as e:
        print(f"Error inserting data: {e}")
        return

    # 4. Initialize Service and Search
    print("\n--- Step 2: Testing Retrieval ---")
    try:
        # Patch the method
        RetrievalService._get_query_embedding = mock_get_query_embedding
        
        service = RetrievalService()
        print("RetrievalService initialized.")
        
        query = "test query"
        print(f"Searching for: '{query}'")
        # Lower threshold to see if that's the issue
        results = await service.similarity_search(query, k=1, threshold=0.0)
        
        print("\n--- Search Results ---")
        for res in results:
            print(f"ID: {res.get('id')}")
            print(f"Score: {res.get('similarity')}")
            print(f"Content: {res.get('content')}")
            
        if results:
            print("\nSUCCESS: Retrieved test document!")
        else:
            print("\nFAILURE: No results found.")
            
        await service.close()
        
    except Exception as e:
        print(f"Error during retrieval test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
