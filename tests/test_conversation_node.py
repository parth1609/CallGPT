import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock dependencies before importing pipeline
sys.modules["pinecone"] = MagicMock()
sys.modules["supabase"] = MagicMock()
sys.modules["psycopg2"] = MagicMock()
sys.modules["psycopg2.extras"] = MagicMock()
sys.modules["psycopg2.pool"] = MagicMock()

from app.pipeline import node_save_conversation, RAGState


class TestConversationNode(unittest.TestCase):
    @patch("app.pipeline.ConversationService")
    def test_save_conversation_no_thread_id(self, mock_service_cls):
        """Test that nothing happens if thread_id is missing"""
        state = RAGState(question="hello", answer="hi")
        # No thread_id in state

        result = node_save_conversation(state)

        # Service should not be instantiated
        mock_service_cls.assert_not_called()
        self.assertEqual(result, {})

    @patch("app.pipeline.ConversationService")
    def test_save_conversation_existing_thread(self, mock_service_cls):
        """Test saving to an existing thread"""
        # Setup mock
        mock_service = mock_service_cls.return_value
        mock_service.get_thread.return_value = {"id": "thread-123"}  # Thread exists

        state = RAGState(
            thread_id="thread-123",
            question="What is X?",
            answer="X is Y",
            bucket_name="docs",
        )

        result = node_save_conversation(state)

        # Verify interactions
        mock_service.get_thread.assert_called_with("thread-123")
        mock_service.create_thread.assert_not_called()

        # Check calls to add_message
        self.assertEqual(mock_service.add_message.call_count, 2)

        # Verify user message saved
        mock_service.add_message.assert_any_call("thread-123", "user", "What is X?", {})
        # Verify assistant message saved
        mock_service.add_message.assert_any_call(
            "thread-123", "assistant", "X is Y", {}
        )

        mock_service.close.assert_called_once()
        self.assertEqual(result, {})

    @patch("app.pipeline.ConversationService")
    def test_save_conversation_new_thread(self, mock_service_cls):
        """Test creating a new thread if it doesn't exist"""
        # Setup mock
        mock_service = mock_service_cls.return_value
        mock_service.get_thread.return_value = None  # Thread does not exist

        state = RAGState(
            thread_id="new-thread", question="Hi", answer="Hello", bucket_name="docs"
        )

        result = node_save_conversation(state)

        # Verify thread creation
        mock_service.get_thread.assert_called_with("new-thread")
        mock_service.create_thread.assert_called_with(metadata={"bucket_name": "docs"})

        # Verify messages saved
        self.assertEqual(mock_service.add_message.call_count, 2)

        mock_service.close.assert_called_once()

    @patch("app.pipeline.ConversationService")
    def test_save_conversation_error_handling(self, mock_service_cls):
        """Test that exceptions are caught and don't break the pipeline"""
        # Setup mock to raise exception
        mock_service = mock_service_cls.return_value
        mock_service.get_thread.side_effect = Exception("Database error")

        state = RAGState(thread_id="thread-123")

        # Should not raise exception
        result = node_save_conversation(state)

        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
