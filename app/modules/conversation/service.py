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
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector_async
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
            raise ValueError("DATABASE_URL must be provided")
        
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
                (thread_id,)
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
                (thread_id,)
            )
            rows = await result.fetchall()
            return [dict(row) for row in rows]
    
    async def create_thread(self, 
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
                (thread_id, json.dumps(metadata or {}))
            )
            row = await result.fetchone()
            return dict(row)

    async def add_thread_message(
        self, 
        thread_id: str, 
        message_id: str,
        index: int,
        message_type: str,
        content: str
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
                (message_id, thread_id, index, message_type, content)
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
                rows  = await result.fetchall()
                if not rows:
                    return [] 
                thread_ids = [row['thread_id'] for row in rows[:limit]]

                import asyncio
                task = [self.get_thread_messages(tid) for tid in thread_ids]

                messages = await asyncio.gather(*task)
                return [msg for msg in messages]



           


async def main():
    """Main function to test the ConversationService with dummy messages."""
    
    # Sample conversation data matching the JSON structure
    sample_data = {
        "threads": [
            {
                "thread_id": "1828b29e-ca3a-41a1-a5ed-4fb58e07b168",
                "conversation": [
                    {"index": 0, "type": "HumanMessage", "content": "my name is yash", "message_id": "ae2c0e2e-10b1-4bc7-853c-1cc18a455f7b"},
                    {"index": 1, "type": "AIMessage", "content": "Hello Yash, nice to meet you! How can I help you today?", "message_id": "3907ed85-c7f8-4375-94a4-5dc7a54af8d3"},
                    {"index": 2, "type": "HumanMessage", "content": "what is iran trap? acknowledge with my name.", "message_id": "2c046eb9-e4a9-478f-9d81-ebf1192dd510"},
                    {"index": 3, "type": "AIMessage", "content": "Sure thing, Yash. I'm sorry, but I don't have information on an 'Iran trap'.", "message_id": "cecd4a9e-6b11-4b2d-8ad7-330f600a7b84"},
                ]
            },
            {
                "thread_id": "41300162-73fa-4365-aa94-de6a4a927e01",
                "conversation": [
                    {"index": 0, "type": "HumanMessage", "content": "this is parth", "message_id": "3e4bb05d-1c5c-4f77-b673-68d5e675dbc3"},
                    {"index": 1, "type": "AIMessage", "content": "I'm sorry, could you provide more detail?", "message_id": "380c33f6-86d9-4d71-bc48-9afbc74e6ce9"},
                    {"index": 2, "type": "HumanMessage", "content": "tell me about USA", "message_id": "3969687a-0d7c-4b2b-9853-ce82376fab5d"},
                    {"index": 3, "type": "AIMessage", "content": "The United States is portrayed as having overwhelming military advantages.", "message_id": "e738793e-2fdf-4250-8fb8-5a9e17ae06d7"},
                ]
            }
        ]
    }
    
    # Initialize the conversation service
    conversation_service = ConversationService()
    
    try:
        # Open the connection pool
        await conversation_service.open()
        print("Connection pool opened.")
        
        # Process each thread
        # for thread_data in sample_data["threads"]:
        #     thread_id = thread_data["thread_id"]
            
        #     # Create the thread
        #     thread = await conversation_service.create_thread(
        #         metadata={"title": f"Conversation {thread_id}"}
        #     )
        #     print(f"\nCreated thread: {thread['thread_id']}")
            
        #     # Add each message to the thread
        #     for msg in thread_data["conversation"]:
        #         message = await conversation_service.add_thread_message(
        #             thread_id=thread["thread_id"],
        #             message_id=msg["message_id"],
        #             index=msg["index"],
        #             message_type=msg["type"],
        #             content=msg["content"]
        #         )
        #         print(f"  Added [{msg['type']}] index={msg['index']}: {msg['content'][:40]}...")
        
        # print("\nAll messages stored successfully!")

        # Get a thread
        # thread_id = "b6ec7284-d7bb-4c97-8bb9-64dd4950cc42"
        # thread = await conversation_service.get_thread(thread_id=thread_id)
        # print(f"\nThread: {thread}")
        
        # # Get messages for the thread
        # messages = await conversation_service.get_thread_messages(thread_id=thread_id)
        # print(f"\nMessages ({len(messages)} total):")
        # for msg in messages:
        #     print(f"  [{msg['index']}] {msg['type']}: {msg['content'][:50]}...")



        # get all thread message
        # messages = await conversation_service.list_threads()
        # # Print each thread's messages
        # for idx, thread_msgs in enumerate(messages, start=1):
        #     print(f"Thread {idx} messages:")
        #     for msg in thread_msgs:
        #         print(msg)
    
    finally:
        # Always close the connection pool
        await conversation_service.close()
        print("Connection pool closed.")


# if __name__ == "__main__":
#     # Use SelectorEventLoop for Windows compatibility with psycopg
#     selector = selectors.SelectSelector()
#     loop = asyncio.SelectorEventLoop(selector)
#     asyncio.set_event_loop(loop)
#     try:
#         loop.run_until_complete(main())
#     finally:
#         loop.close()