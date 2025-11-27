import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock pinecone and supabase BEFORE importing app.pipeline
sys.modules['pinecone'] = MagicMock()
sys.modules['supabase'] = MagicMock()

from app.pipeline import node_answer, RAGState
from langchain_core.documents import Document

class TestAnswerNode(unittest.TestCase):
    @patch('app.pipeline.RetrievalService')  # Mock RetrievalService in pipeline
    @patch('app.pipeline.LLMService')  # Mock LLMService in pipeline
    @patch('app.pipeline.get_groq_llm')
    @patch('app.pipeline.get_qa_prompt')
    def test_node_answer(self, mock_get_prompt, mock_get_llm, MockLLMService, MockRetrievalService):
        # Setup RetrievalService mock
        mock_retriever_service = MockRetrievalService.return_value
        
        # Mock _get_query_embedding method
        mock_retriever_service._get_query_embedding.return_value = [0.1, 0.2, 0.3]
        
        # Mock similarity_search to return a mock retriever
        mock_retriever = MagicMock()
        mock_retriever_service.similarity_search.return_value = mock_retriever
        
        # Mock retrieve method to return documents
        mock_doc1 = Document(page_content="Answer is in context 1", metadata={"source": "test1"})
        mock_doc2 = Document(page_content="Answer is in context 2", metadata={"source": "test2"})
        mock_retriever_service.retrieve.return_value = [mock_doc1, mock_doc2]
        
        # Mock prompt
        mock_prompt = mock_get_prompt.return_value
        mock_prompt.format_messages.return_value = [MagicMock(content="test message")]
        
        # Mock LLM streaming response
        mock_llm = mock_get_llm.return_value
        chunk1 = MagicMock()
        chunk1.content = "Hello"
        chunk2 = MagicMock()
        chunk2.content = " World"
        
        mock_llm.stream.return_value = iter([chunk1, chunk2])
        
        # Setup state
        state = RAGState(
            bucket_name="test-index",
            question="What is the answer?",
            messages=[],
            search_type="similarity_search",
            k=4,
            embeddings_model="sentence-transformers/all-MiniLM-L6-v2",
            llm_model="openai/gpt-oss-120b",
            temperature=0.1
        )
        
        # Execute
        gen = node_answer(state)
        results = list(gen)
        
        # Verify mocks were called
        MockRetrievalService.assert_called_once_with(index_name="test-index")
        mock_retriever_service._get_query_embedding.assert_called_once_with("What is the answer?")
        mock_retriever_service.similarity_search.assert_called_once_with(
            query="What is the answer?",
            k=4,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2"
        )
        mock_retriever_service.retrieve.assert_called_once_with(mock_retriever, "What is the answer?")
        mock_get_llm.assert_called_once()
        
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

if __name__ == '__main__':
    unittest.main()

