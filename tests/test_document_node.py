import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock pinecone and supabase before importing app modules
sys.modules["pinecone"] = MagicMock()
sys.modules["supabase"] = MagicMock()

from app.modules.pipeline.pipeline import document_service_node, RAGState
from langchain_core.documents import Document


class TestDocumentServiceNode(unittest.TestCase):
    @patch("app.modules.pipeline.pipeline.DocumentService")
    @patch("app.modules.pipeline.pipeline.load_text_file")
    def test_document_service_node(self, mock_load, mock_service_cls):
        # Setup mocks
        mock_doc = Document(
            page_content="test content",
            metadata={"source": "test.txt", "filename": "test.txt"},
        )
        mock_load.return_value = [mock_doc]

        mock_service_instance = mock_service_cls.return_value
        mock_service_instance.upload_document.return_value = {
            "document_id": "123",
            "filename": "test.txt",
            "size": 12,
            "public_url": "http://example.com/test.txt",
            "created_at": "2023-01-01",
        }

        # Input - bucket_name is now in state, not a parameter
        state = RAGState(
            bucket_name="test-bucket",
            uploaded_file_path="path/to/test.txt",
            filename="test.txt",
        )

        # Execute
        result = document_service_node(state)

        # Verify
        mock_service_cls.assert_called_with(bucket_name="test-bucket")
        mock_load.assert_called_with("path/to/test.txt")
        mock_service_instance.upload_document.assert_called_with(
            filename="test.txt",
            content="test content",
            metadata={"source": "test.txt", "filename": "test.txt"},
        )

        self.assertEqual(result["content"], "test content")
        self.assertEqual(result["filename"], "test.txt")
        self.assertIn("metadata", result)
        print("Test passed successfully!")


if __name__ == "__main__":
    unittest.main()
