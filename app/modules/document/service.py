"""
Purpose: Business logic for Document Service.
Handles document storage, retrieval, and metadata management using Supabase Storage.
"""

import os
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from supabase import create_client, Client


load_dotenv()


class DocumentService:
    """
    Manages document operations with Supabase Storage.

    Parameters:
    - supabase_url (str): Supabase project URL
    - supabase_key (str): Supabase API key
    - bucket_name (str): Storage bucket name
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
    ):
        """
        Initialize Document Service with Supabase connection.

        Side Effects:
        - Creates Supabase client connection
        - Sets default bucket name from environment or parameter
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        self.bucket_name = bucket_name or os.getenv("SUPABASE_BUCKET", "user-files")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and Key must be provided")

        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """
        Ensure the storage bucket exists, create if not.

        Side Effects:
        - Creates bucket in Supabase Storage if it doesn't exist
        """
        try:
            buckets = self.client.storage.list_buckets()
            bucket_names = [b.name for b in buckets]

            if self.bucket_name not in bucket_names:
                self.client.storage.create_bucket(
                    self.bucket_name, options={"public": True}
                )
        except Exception as e:
            print(f"Bucket check/creation warning: {e}")

    def upload_document(
        self,
        filename: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Upload a document to Supabase Storage.

        Parameters:
        - filename (str): Name of the file
        - content (str): Text content of the document
        - metadata (Optional[Dict]): Additional metadata

        Return Value:
        - Dict: Upload result with document_id, filename, size, public_url, created_at

        Side Effects:
        - Uploads file to Supabase Storage
        - Stores metadata in PostgreSQL table
        """
        # Generate unique document ID
        content_bytes = content.encode("utf-8")
        doc_hash = hashlib.sha256(content_bytes).hexdigest()[:16]
        doc_id = f"{doc_hash}_{filename}"

        # Upload to storage
        path = f"{doc_id}"
        self.client.storage.from_(self.bucket_name).upload(
            path,
            content_bytes,
            file_options={"content-type": "text/plain", "upsert": "true"},
        )

        # Get public URL
        public_url = self.client.storage.from_(self.bucket_name).get_public_url(path)

        # Store metadata in database (align with file_metadata schema: bucket_name, object_name, ...)
        metadata_record = {
            "bucket_name": self.bucket_name,
            "object_name": path,
            "size": len(content_bytes),
            "content_type": "text/plain",
            "public_url": public_url,
            "last_modified": datetime.utcnow().isoformat(),
        }

        try:
            self.client.table("file_metadata").upsert(metadata_record).execute()
        except Exception as e:
            print(f"Metadata storage warning: {e}")

        return {
            "document_id": doc_id,
            "filename": filename,
            "size": len(content_bytes),
            "public_url": public_url,
            "created_at": datetime.utcnow(),
        }

    def get_document_content(self, document_id: str) -> Optional[str]:
        """
        Retrieve document content from Supabase Storage.

        Parameters:
        - document_id (str): Unique document identifier

        Return Value:
        - Optional[str]: Document content as text, or None if not found

        Side Effects:
        - Downloads file from Supabase Storage
        """
        try:
            result = self.client.storage.from_(self.bucket_name).download(document_id)
            return result.decode("utf-8")
        except Exception as e:
            print(f"Document retrieval error: {e}")
            return None

    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document metadata from database.

        Parameters:
        - document_id (str): Unique document identifier

        Return Value:
        - Optional[Dict]: Document metadata, or None if not found
        """
        try:
            result = (
                self.client.table("file_metadata")
                .select("*")
                .eq("object_name", document_id)
                .execute()
            )
            if result.data:
                row = result.data[0]
                # Derive filename from object_name (format: "<hash>_<filename>")
                filename = (
                    document_id.split("_", 1)[1] if "_" in document_id else document_id
                )
                created_at = row.get("created_at")
                updated_at = row.get("last_modified") or created_at
                return {
                    "document_id": document_id,
                    "filename": filename,
                    "size": row.get("size") or 0,
                    "content_type": row.get("content_type") or "text/plain",
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "metadata": {},
                }
            return None
        except Exception as e:
            print(f"Metadata retrieval error: {e}")
            return None

    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all documents with pagination.

        Parameters:
        - limit (int): Maximum number of documents to return
        - offset (int): Number of documents to skip

        Return Value:
        - List[Dict]: List of document metadata
        """
        try:
            result = (
                self.client.table("file_metadata")
                .select("*")
                .range(offset, offset + limit - 1)
                .execute()
            )
            rows = result.data or []
            documents = []
            for row in rows:
                object_name = row.get("object_name") or ""
                filename = (
                    object_name.split("_", 1)[1] if "_" in object_name else object_name
                )
                created_at = row.get("created_at")
                updated_at = row.get("last_modified") or created_at
                documents.append(
                    {
                        "document_id": object_name,
                        "filename": filename,
                        "size": row.get("size") or 0,
                        "content_type": row.get("content_type") or "text/plain",
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "metadata": {},
                    }
                )
            return documents
        except Exception as e:
            print(f"Document listing error: {e}")
            return []

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from storage and database.

        Parameters:
        - document_id (str): Unique document identifier

        Return Value:
        - bool: True if deletion successful, False otherwise

        Side Effects:
        - Removes file from Supabase Storage
        - Deletes metadata record from database
        """
        try:
            # Delete from storage
            self.client.storage.from_(self.bucket_name).remove([document_id])

            # Delete metadata
            self.client.table("file_metadata").delete().eq(
                "object_name", document_id
            ).execute()

            return True
        except Exception as e:
            print(f"Document deletion error: {e}")
            return False


# ============================================================================
# Pipeline Utilities (Backend-compatible functions for LangGraph integration)
# ============================================================================


def chunk_documents(
    docs: List,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: List[str] = None,
):
    """
    Purpose: Split input Documents into smaller chunks for downstream embedding and retrieval.

    This utility function chunks documents using RecursiveCharacterTextSplitter,
    following the backend pattern for pipeline usage.

    Parameters:
    - docs (List[Document]): Input documents to split.
    - chunk_size (int): Max characters per chunk.
    - chunk_overlap (int): Overlap in characters between consecutive chunks.
    - separators (Optional[List[str]]): Custom separators to guide splitting. Defaults to sensible values.

    Return Value:
    - List[Document]: Chunked documents with metadata preserved.

    Side Effects:
    - None.

    Examples:
    >>> from langchain_core.documents import Document
    >>> chunks = chunk_documents([Document(page_content="a" * 3000)])
    >>> len(chunks) >= 2
    True
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
    )
    return splitter.split_documents(docs)


def load_text_file(path: str) -> List:
    """
    Purpose: Load a text file and return as a list of Documents.

    This utility function loads text content from a file and wraps it in a
    LangChain Document object for pipeline processing.

    Parameters:
    - path (str): Path to text file.

    Return Value:
    - List[Document]: List containing a single Document with the file contents.

    Side Effects:
    - Reads file from disk.

    Examples:
    >>> # docs = load_text_file("input.txt")
    >>> # len(docs) == 1
    True
    """
    from langchain_core.documents import Document

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    return [Document(page_content=content, metadata={"source": path})]
