"""
Purpose: Business logic for Conversation Service.
Manages conversation threads and message history using PostgreSQL.
"""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv
from uuid import uuid4


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
        
        # Create connection pool
        self.pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=self.database_url,
        )
        
        self._initialize_schema()
    
    def _initialize_schema(self):
        """
        Initialize database schema if not exists.
        
        Side Effects:
        - Creates threads, messages, and checkpoints tables
        """
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                # Create threads table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS threads (
                        id TEXT PRIMARY KEY,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW(),
                        metadata JSONB DEFAULT '{}'::jsonb
                    )
                """)
                
                # Create messages table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        thread_id TEXT REFERENCES threads(id) ON DELETE CASCADE,
                        role VARCHAR(20) NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        metadata JSONB DEFAULT '{}'::jsonb
                    )
                """)
                
                # Create index on thread_id for faster queries
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_thread_id 
                    ON messages(thread_id)
                """)
                
                conn.commit()
        finally:
            self.pool.putconn(conn)
    
    def create_thread(self, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new conversation thread.
        
        Parameters:
        - metadata: Optional metadata for the thread
        
        Returns:
        - Dict with thread information
        """
        thread_id = str(uuid4())
        conn = self.pool.getconn()
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO threads (id, metadata)
                    VALUES (%s, %s)
                    RETURNING id, created_at, updated_at, metadata
                    """,
                    (thread_id, Json(metadata or {}))
                )
                result = cur.fetchone()
                conn.commit()
                return dict(result)
        finally:
            self.pool.putconn(conn)
    
    def get_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get thread by ID"""
        conn = self.pool.getconn()
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, created_at, updated_at, metadata FROM threads WHERE id = %s",
                    (thread_id,)
                )
                result = cur.fetchone()
                return dict(result) if result else None
        finally:
            self.pool.putconn(conn)
    
    def list_threads(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all threads with pagination"""
        conn = self.pool.getconn()
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, created_at, updated_at, metadata 
                    FROM threads 
                    ORDER BY updated_at DESC 
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset)
                )
                results = cur.fetchall()
                return [dict(r) for r in results]
        finally:
            self.pool.putconn(conn)
    
    def delete_thread(self, thread_id: str) -> bool:
        """
        Delete a thread and all its messages.
        
        Parameters:
        - thread_id: Thread ID to delete
        
        Returns:
        - True if deleted, False if not found
        """
        conn = self.pool.getconn()
        
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM threads WHERE id = %s", (thread_id,))
                deleted = cur.rowcount > 0
                conn.commit()
                return deleted
        finally:
            self.pool.putconn(conn)
    
    def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add a message to a thread.
        
        Parameters:
        - thread_id: Thread ID
        - role: Message role ('user' or 'assistant')
        - content: Message content
        - metadata: Optional message metadata
        
        Returns:
        - Dict with message information
        """
        message_id = str(uuid4())
        conn = self.pool.getconn()
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Insert message
                cur.execute(
                    """
                    INSERT INTO messages (id, thread_id, role, content, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, thread_id, role, content, created_at, metadata
                    """,
                    (message_id, thread_id, role, content, Json(metadata or {}))
                )
                result = cur.fetchone()
                
                # Update thread updated_at
                cur.execute(
                    "UPDATE threads SET updated_at = NOW() WHERE id = %s",
                    (thread_id,)
                )
                
                conn.commit()
                return dict(result)
        finally:
            self.pool.putconn(conn)
    
    def get_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a thread"""
        conn = self.pool.getconn()
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, thread_id, role, content, created_at, metadata 
                    FROM messages 
                    WHERE thread_id = %s 
                    ORDER BY created_at ASC
                    """,
                    (thread_id,)
                )
                results = cur.fetchall()
                return [dict(r) for r in results]
        finally:
            self.pool.putconn(conn)
    
    def get_thread_preview(self, thread_id: str, max_length: int = 50) -> Dict[str, Any]:
        """
        Get a preview of a thread (first user message).
        
        Parameters:
        - thread_id: Thread ID
        - max_length: Maximum length of preview text
        
        Returns:
        - Dict with preview information
        """
        conn = self.pool.getconn()
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get first user message
                cur.execute(
                    """
                    SELECT content, created_at 
                    FROM messages 
                    WHERE thread_id = %s AND role = 'user' 
                    ORDER BY created_at ASC 
                    LIMIT 1
                    """,
                    (thread_id,)
                )
                first_msg = cur.fetchone()
                
                # Get message count
                cur.execute(
                    "SELECT COUNT(*) as count FROM messages WHERE thread_id = %s",
                    (thread_id,)
                )
                count_result = cur.fetchone()
                
                # Get thread updated_at
                cur.execute(
                    "SELECT updated_at FROM threads WHERE id = %s",
                    (thread_id,)
                )
                thread_result = cur.fetchone()
                
                preview = "New conversation"
                last_updated = datetime.utcnow()
                
                if first_msg:
                    content = first_msg["content"]
                    preview = content[:max_length] + ("..." if len(content) > max_length else "")
                
                if thread_result:
                    last_updated = thread_result["updated_at"]
                
                return {
                    "thread_id": thread_id,
                    "preview": preview,
                    "message_count": count_result["count"] if count_result else 0,
                    "last_updated": last_updated,
                }
        finally:
            self.pool.putconn(conn)
    
    def close(self):
        """Close connection pool"""
        if self.pool:
            self.pool.closeall()
