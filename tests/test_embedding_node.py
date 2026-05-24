import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock pinecone and supabase before importing app modules
sys.modules["pinecone"] = MagicMock()
sys.modules["supabase"] = MagicMock()

from app.modules.pipeline.pipeline import embedding_node, RAGState


class TestEmbeddingNode(unittest.TestCase):
    @patch("app.modules.pipeline.pipeline.EmbeddingService")
    def test_embedding_node(self, mock_service_cls):
        # Setup mocks
        mock_service_instance = mock_service_cls.return_value

        # Mock chunk_and_embed return value (chunks, embeddings, model_name, total_chunks)
        mock_embeddings = [[0.1, 0.2], [0.3, 0.4]]
        mock_chunks = ["chunk1", "chunk2"]
        mock_service_instance.chunk_and_embed.return_value = (
            mock_chunks,
            mock_embeddings,
            "test-model",
            2,
        )

        # Input
        state = RAGState(
            content="test content",
            chunk_size=100,
            chunk_overlap=10,
            embeddings_model="test-model",
        )

        # Execute
        try:
            result = embedding_node(state)

            # Verify
            mock_service_instance.chunk_and_embed.assert_called_with(
                text="test content",
                chunk_size=100,
                chunk_overlap=10,
                model_name="test-model"
            )

            self.assertEqual(result["embeddings"], mock_embeddings)
            self.assertEqual(result["dimension"], 2)  # 2 chunks
            print("Test passed successfully!")

        except Exception as e:
            print(f"Test failed with error: {e}")
            raise e


if __name__ == "__main__":
    unittest.main()
