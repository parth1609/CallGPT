
import sys
import os
from unittest.mock import MagicMock

# Add app to path
sys.path.append(os.getcwd())

from unittest.mock import MagicMock, patch

# Mock pinecone before importing app modules that depend on it
sys.modules["pinecone"] = MagicMock()
sys.modules["supabase"] = MagicMock()

from app.pipeline import document_service_node, RAGState

def test_node():
    print("Testing document_service_node...")
    
    # Mock file object
    class MockUploadedFile:
        def __init__(self):
            self.name = "test.txt"
            self.type = "text/plain"
            self._content = b"Hello world content"
            
        def read(self):
            return self._content

    mock_file = MockUploadedFile()
    state = RAGState()

    # We expect this to fail because upload_file doesn't exist on DocumentService
    # But we also need to make sure DocumentService doesn't fail on init due to missing creds if they aren't set.
    # Let's try to run it. If it fails on init, we'll know.
    
    try:
        result = document_service_node(state, mock_file)
        print("Result:", result)
    except Exception as e:
        print(f"Caught expected error: {e}")

if __name__ == "__main__":
    test_node()
