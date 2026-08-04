"""
Example script demonstrating how to use the get_thread_history function
to retrieve conversation history from PostgreSQL checkpointer.
"""

import os
from dotenv import load_dotenv

# IMPORTANT: Add the project root to path to import modules
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent  # Go up from tests/ to CallGPT/
sys.path.insert(0, str(project_root))

# Import customer pipeline and get_thread_history from pipeline.py
from app.modules.pipeline.pipeline import customer, get_thread_history


load_dotenv()


def main():
    """
    Example usage of get_thread_history function.
    Replace 'your_specific_thread_id' with an actual thread ID from your database.
    """
    # Example thread ID - replace with your actual thread ID
    thread_id = "5b38ffdb-bab1-46cc-99a9-4b986938dec2"

    print(f"Retrieving history for thread: {thread_id}\n")
    print("=" * 80)

    try:
        # Retrieve the conversation history
        messages = get_thread_history(thread_id)

        # Print the conversation
        print(f"\nFound {len(messages)} messages:\n")
        for i, msg in enumerate(messages, 1):
            print(f"[{i}] {msg['type']}: {msg['content']}")
            print("-" * 80)

        # print(messages)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
