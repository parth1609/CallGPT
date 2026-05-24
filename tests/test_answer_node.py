import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock pinecone and supabase BEFORE importing app.pipeline
sys.modules["pinecone"] = MagicMock()
sys.modules["supabase"] = MagicMock()

from app.modules.pipeline.pipeline import node_answer, RAGState
from langchain_core.documents import Document


class TestAnswerNode(unittest.IsolatedAsyncioTestCase):
    @patch("app.modules.pipeline.pipeline.get_retrieval_service")  # Mock get_retrieval_service in pipeline
    @patch("app.modules.pipeline.pipeline.get_llm_service")  # Mock get_llm_service in pipeline
    @patch("app.modules.pipeline.pipeline.get_groq_llm")
    @patch("app.modules.pipeline.pipeline.get_qa_prompt")
    async def test_node_answer(
        self, mock_get_prompt, mock_get_llm, mock_get_llm_service, mock_get_retrieval_service
    ):
        # Setup RetrievalService mock
        mock_retriever_service = mock_get_retrieval_service.return_value

        # Mock _get_query_embedding method
        mock_retriever_service._get_query_embedding.return_value = [0.1, 0.2, 0.3]

        # Mock similarity_search to return a mock retriever
        mock_retriever = MagicMock()
        mock_retriever_service.similarity_search.return_value = mock_retriever

        # Mock retrieve method is no longer needed since similarity_search returns results directly
        mock_retriever_service.similarity_search.return_value = [{"content": "Answer is in context 1", "metadata": {"source": "test1"}}, {"content": "Answer is in context 2", "metadata": {"source": "test2"}}]

        # Mock prompt
        mock_prompt = mock_get_prompt.return_value
        mock_prompt.format_messages.return_value = [MagicMock(content="test message")]

        # Mock LLM streaming response
        mock_llm = mock_get_llm.return_value
        
        async def mock_stream_chat_async(*args, **kwargs):
            yield {"content": "Hello", "finish_reason": None}
            yield {"content": " World", "finish_reason": "stop"}
            
        mock_llm_service = mock_get_llm_service.return_value
        mock_llm_service.stream_chat_async = mock_stream_chat_async

        # Setup state
        state = RAGState(
            bucket_name="test-index",
            question="What is the answer?",
            messages=[],
            search_type="similarity_search",
            k=4,
            embeddings_model="sentence-transformers/all-MiniLM-L6-v2",
            llm_model="openai/gpt-oss-120b",
            temperature=0.1,
        )

        # Execute
        results = [chunk async for chunk in node_answer(state)]

        # Verify mocks were called
        mock_get_retrieval_service.assert_called_once_with(index_name="test-index")
        mock_retriever_service._get_query_embedding.assert_called_once_with(
            "What is the answer?", model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        mock_retriever_service.similarity_search.assert_called_once_with(
            query="What is the answer?",
            k=4,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            use_reranker=False,
            query_embedding=[0.1, 0.2, 0.3],
        )



        # Check results
        self.assertTrue(len(results) > 0, "Should have at least one result")

        # Verify final answer
        final_result = results[-1]
        self.assertIn("answer", final_result)
        self.assertEqual(final_result["answer"], "Hello World")

        # Verify messages in final result
        self.assertIn("messages", final_result)
        messages = final_result["messages"]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].content, "What is the answer?")
        self.assertEqual(messages[1].content, "Hello World")

        print("Test passed successfully!")


if __name__ == "__main__":
    unittest.main()
