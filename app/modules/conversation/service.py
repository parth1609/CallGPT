"""
Purpose: Business logic for Conversation Service.
Manages conversation threads and message history using PostgreSQL.
"""

import os
import json
import asyncio
import selectors
from typing import List, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from uuid import uuid4

from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage


load_dotenv()


class ConversationService:
    """Manages conversation threads and messages with PostgreSQL"""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize Conversation Service with PostgreSQL connection pool.

        Parameters:
        - database_url: PostgreSQL connection URL
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")

        if not self.database_url:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                "⚠️ DATABASE_URL not provided. ConversationService will not be functional."
            )
            return  # Don't try to create pool if we don't have URL

        self.pool = AsyncConnectionPool(
            conninfo=self.database_url,
            max_size=15,
            kwargs={
                "autocommit": True,
                "prepare_threshold": None,
                "row_factory": dict_row,
            },
            open=False,  # Don't open automatically
        )

    async def open(self):
        """Open the connection pool."""
        await self.pool.open()

        # checkpointer for retrive the threads from the langgraph inbuild feature
        self.checkpointer = AsyncPostgresSaver(self.pool)
        await self.checkpointer.setup()

    @staticmethod
    def _extract_messages_from_checkpointer(
        checkpointer_instance, thread_id: str
    ) -> List[Dict[str, Any]]:
        """
        Helper function to extract messages from a checkpointer instance.

        Parameters:
        - checkpointer_instance: The PostgresSaver instance
        - thread_id: The thread ID to retrieve

        Returns:
        - List of message dictionaries (without duplicates)
        """
        import logging

        logger = logging.getLogger(__name__)

        # Define the configuration for the specific thread
        config = {"configurable": {"thread_id": thread_id}}

        # Retrieve the full history of checkpoints for that thread
        thread_history = list(checkpointer_instance.list(config))
        logger.debug(f"Found {len(thread_history)} checkpoints for thread {thread_id}")

        # IMPORTANT: Each checkpoint contains the FULL conversation state up to that point
        # So we only need to get messages from the MOST RECENT checkpoint
        # Otherwise we get duplicates!
        messages = []
        if thread_history:
            # Get the most recent checkpoint (first in the list since they're in reverse chronological order)
            latest_checkpoint = thread_history[0]
            checkpoint_messages = latest_checkpoint.checkpoint.get(
                "channel_values", {}
            ).get("messages", [])
            messages = checkpoint_messages

        logger.debug(f"Extracted {len(messages)} total messages from latest checkpoint")

        # Convert messages to dictionary format for easier processing
        result = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                result.append({"type": "User", "content": msg.content})
            elif isinstance(msg, AIMessage):
                result.append({"type": "AI", "content": msg.content})
            else:
                result.append(
                    {"type": msg.__class__.__name__, "content": str(msg.content)}
                )

        return result

    @staticmethod
    def get_thread_history(
        thread_id: str, checkpointer_instance=None, db_uri: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Static method to retrieve conversation history for a specific thread.

        This is the main entry point for getting thread history. It can use either a provided
        checkpointer instance or create a new one from a database URI.

        Parameters:
        - thread_id: The thread ID to retrieve history for
        - checkpointer_instance: Optional PostgresSaver instance to use
        - db_uri: Optional database URI if checkpointer_instance is None

        Returns:
        - List of message dictionaries with 'type' and 'content' keys
        """
        import logging

        logger = logging.getLogger(__name__)

        logger.debug(f"Retrieving thread history for thread_id: {thread_id}")

        # Use provided checkpointer if available
        if checkpointer_instance is not None:
            return ConversationService._extract_messages_from_checkpointer(
                checkpointer_instance, thread_id
            )

        # Otherwise create a temporary checkpointer
        from langgraph.checkpoint.postgres import PostgresSaver

        database_url = db_uri or os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError(
                "DATABASE_URL must be provided or set as environment variable"
            )

        # Create a temporary checkpointer - use contexit t manager to avoid prepared statement issues
        with PostgresSaver.from_conn_string(database_url) as temp_checkpointer:
            return ConversationService._extract_messages_from_checkpointer(
                temp_checkpointer, thread_id
            )

    async def close(self):
        """Close the connection pool."""
        await self.pool.close()

    async def get_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation thread by ID.

        Parameters:
        - thread_id: ID of the thread

        Returns:
        - Dict with thread information if found, None otherwise
        """
        async with self.pool.connection() as conn:
            result = await conn.execute(
                """
                SELECT * FROM threads WHERE thread_id = %s
                """,
                (thread_id,),
            )
            row = await result.fetchone()
            return dict(row) if row else None

    async def get_thread_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a thread.

        Parameters:
        - thread_id: ID of the thread

        Returns:
        - List of message dicts ordered by index
        """
        async with self.pool.connection() as conn:
            result = await conn.execute(
                """
                SELECT messages_id, thread_id, index, type, content, created_at
                FROM messages 
                WHERE thread_id = %s 
                ORDER BY index
                """,
                (thread_id,),
            )
            rows = await result.fetchall()
            return [dict(row) for row in rows]

    async def create_thread(
        self,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new conversation thread.

        Parameters:
        - metadata: Optional metadata for the thread

        Returns:
        - Dict with thread information
        """
        thread_id = str(uuid4())

        async with self.pool.connection() as conn:
            result = await conn.execute(
                """
                INSERT INTO threads (thread_id, metadata)
                VALUES (%s, %s)
                RETURNING thread_id, created_at, updated_at, metadata
                """,
                (thread_id, json.dumps(metadata or {})),
            )
            row = await result.fetchone()
            return dict(row)

    async def add_thread_message(
        self,
        thread_id: str,
        message_id: str,
        index: int,
        message_type: str,
        content: str,
    ) -> Dict[str, Any]:
        """
        Add a message to the thread.

        Parameters:
        - thread_id: ID of the thread
        - message_id: Unique ID for the message
        - index: Position of the message in the conversation
        - message_type: Type of message (HumanMessage, AIMessage, etc.)
        - content: Message content

        Returns:
        - Dict with message information
        """
        async with self.pool.connection() as conn:
            result = await conn.execute(
                """
                INSERT INTO messages (messages_id, thread_id, index, type, content)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING messages_id, thread_id, index, type, content, created_at
                """,
                (message_id, thread_id, index, message_type, content),
            )
            row = await result.fetchone()
            return dict(row)

    async def list_threads(self, limit: int = 100) -> Dict[str, Any]:
        """
        list get the list of all threads
        """
        async with self.pool.connection() as conn:
            result = await conn.execute(
                """
                    SELECT * FROM threads
                    """
            )
            rows = await result.fetchall()
            if not rows:
                return []
            thread_ids = [row["thread_id"] for row in rows[:limit]]

            import asyncio

            task = [self.get_thread_messages(tid) for tid in thread_ids]

            messages = await asyncio.gather(*task)
            return [msg for msg in messages]


# if __name__ == "__main__":
#     # Use SelectorEventLoop for Windows compatibility with psycopg to avoid async error
#     selector = selectors.SelectSelector()
#     loop = asyncio.SelectorEventLoop(selector)
#     asyncio.set_event_loop(loop)
#     try:
#         loop.run_until_complete(main())
#     finally:
#         loop.close()
