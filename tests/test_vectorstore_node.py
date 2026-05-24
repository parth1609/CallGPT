import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock pinecone and supabase
sys.modules["pinecone"] = MagicMock()
sys.modules["supabase"] = MagicMock()
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock pinecone and supabase
sys.modules["pinecone"] = MagicMock()
sys.modules["supabase"] = MagicMock()

from app.modules.pipeline.pipeline import node_vectorstore, RAGState
from langchain_core.documents import Document


class TestVectorStoreNode(unittest.TestCase):
    @patch("app.modules.pipeline.pipeline.VectorStoreService")
    def test_node_vectorstore(self, MockVectorStoreService):
        # Setup
        mock_service = MockVectorStoreService.return_value
        mock_service._sanitize_metadata.return_value = [{"source": "test"}]

        state = RAGState(
            bucket_name="Test-Index",
            chunks=[Document(page_content="test", metadata={"source": "test"})],
            embeddings=[[0.1, 0.2]],
            metadata={"source": "test"},
            dimension=2,
        )

        # Execute
        node_vectorstore(state)

        # Verify
        # Verify it calls upsert_vectors with correct arguments
        mock_service.upsert_vectors.assert_called_with(
            chunks=["test"],
            embeddings=[[0.1, 0.2]],
            index_name="test-index",
            metadata=[{"source": "test"}],
        )


if __name__ == "__main__":
    unittest.main()
