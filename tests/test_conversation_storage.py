"""
Test script to verify that conversations are being stored in PostgreSQL.
This will create a test conversation and then retrieve it to confirm persistence.
"""

import os
from dotenv import load_dotenv
from uuid import uuid4

# IMPORTANT: Add the project root to path to import modules
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.modules.pipeline.pipeline import customer, get_thread_history

load_dotenv()


def test_conversation_storage():
    """Test that conversations are being stored in PostgreSQL"""

    print("=" * 80)
    print("TESTING CONVERSATION STORAGE")
    print("=" * 80)

    # Create a test thread
    test_thread_id = str(uuid4())
    print(f"\n1. Created test thread: {test_thread_id}")

    # Prepare test state
    state = {
        "question": "What is Python?",
        "thread_id": test_thread_id,
        "bucket_name": "test-bucket",
        "embeddings_model": "sentence-transformers/all-MiniLM-L6-v2",
        "llm_model": "openai/gpt-oss-120b",
        "temperature": 0.5,
        "k": 4,
        "search_type": "similarity_search",
        "use_reranker": False,
        "fetch_k": 20,
        "reranker_model": "bge-reranker-v2-m3",
        "messages": [],
    }

    print("\n2. Running customer pipeline with test question...")

    try:
        # Run the customer pipeline (this should store the conversation)
        config = {"configurable": {"thread_id": test_thread_id}}

        # Stream through the pipeline
        for event in customer.stream(state, config=config, stream_mode="updates"):
            if "answer" in event:
                chunk = event["answer"]
                if "answer" in chunk:
                    print(f"   Answer received: {chunk['answer'][:100]}...")

        print("\n3. ✅ Pipeline execution completed")

        # Now try to retrieve the conversation history
        print(f"\n4. Retrieving conversation history for thread: {test_thread_id}")

        messages = get_thread_history(test_thread_id)

        if messages:
            print(f"\n5. ✅ SUCCESS! Found {len(messages)} messages in database:")
            print("-" * 80)
            for i, msg in enumerate(messages, 1):
                print(f"   [{i}] {msg['type']}: {msg['content'][:100]}...")
            print("-" * 80)
            print("\n✅ CONVERSATION IS BEING STORED SUCCESSFULLY!")
        else:
            print("\n5. ❌ FAILURE! No messages found in database")
            print("   This means conversations are NOT being persisted")
            print("\n   Possible causes:")
            print("   - DATABASE_URL not set correctly")
            print("   - Checkpointer not initialized properly")
            print("   - Database tables not created")

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_conversation_storage()
