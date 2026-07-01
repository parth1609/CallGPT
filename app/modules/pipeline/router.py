"""
Purpose: FastAPI router for Pipeline orchestration using LangGraph workflows.
Exposes the organisation and customer pipelines as REST API endpoints.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from typing import Optional

from .models import (
    OrganisationUploadRequest,
    OrganisationUploadResponse,
    CustomerQueryRequest,
    CustomerQueryResponse,
    HealthCheckResponse,
)
from .service import PipelineService
from datetime import datetime
import os


router = APIRouter(tags=["Pipeline"])

# Initialize service
pipeline_service = PipelineService()


# ============================================================================
# Health Check Endpoint
# ============================================================================


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint for pipeline service.

    Return Value:
    - HealthCheckResponse: Service status and timestamp
    """
    return HealthCheckResponse(
        status="healthy",
        service="pipeline_module",
        timestamp=datetime.utcnow(),
    )


# ============================================================================
# Organisation Pipeline Endpoints
# ============================================================================


@router.post(
    "/organisations/upload",
    response_model=OrganisationUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_organisation_document_json(request: OrganisationUploadRequest):
    """
    Upload and process organisation document through LangGraph pipeline (JSON).

    Pipeline Flow:
    START → document_load → embedding → vectorstore → END

    Parameters:
    - request: OrganisationUploadRequest with document data

    Return Value:
    - OrganisationUploadResponse: Processing result with chunk count

    Side Effects:
    - Uploads document to Supabase storage
    - Generates embeddings
    - Stores vectors in Pinecone
    """
    try:
        # Process document through service layer
        result = pipeline_service.process_organisation_document(
            filename=request.filename,
            content=request.content,
            bucket_name=request.bucket_name,
            embeddings_model=request.embeddings_model,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            metadata=request.metadata,
        )

        return OrganisationUploadResponse(
            status="success",
            message="Document processed successfully through pipeline",
            filename=result.get("filename", request.filename),
            bucket_name=request.bucket_name,
            chunks_created=len(result.get("chunks", [])),
            metadata=result.get("metadata"),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline processing failed: {str(e)}",
        )


# ============================================================================
# Company Lookup Endpoint
# ============================================================================


@router.get("/company/by-email")
async def get_company_by_email(email: str):
    """
    Look up the company (and its bucket_name) associated with a user's email.
    Used by the frontend to auto-populate the Bucket/Index field for the
    currently logged-in Clerk user.

    Parameters:
    - email: The user's email address (from Clerk)

    Return Value:
    - Dict with company_id, company_name, bucket_name
    """
    try:
        # Try direct PostgreSQL first (most reliable, bypasses RLS)
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            import psycopg

            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    # Ensure email column exists (safe migration)
                    cur.execute("""
                        DO $$ BEGIN
                            ALTER TABLE companies ADD COLUMN IF NOT EXISTS email TEXT;
                        EXCEPTION WHEN others THEN NULL;
                        END $$;
                    """)
                    conn.commit()

                    cur.execute(
                        "SELECT id, company_name, bucket_name FROM companies WHERE email = %s LIMIT 1;",
                        (email,),
                    )
                    row = cur.fetchone()
                    if row:
                        return {
                            "company_id": str(row[0]),
                            "company_name": row[1],
                            "bucket_name": row[2],
                        }
            return {"bucket_name": None, "message": "No company found for this email"}

        # Fallback: try Supabase client
        from supabase import create_client

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = (
            os.getenv("SUPABASE_API_KEY")
            or os.getenv("SUPABASE_SERVICE_KEY")
            or os.getenv("SUPABASE_KEY")
        )

        if not supabase_url or not supabase_key:
            return {"bucket_name": None, "message": "No database connection available"}

        client = create_client(supabase_url, supabase_key)
        response = (
            client.table("companies")
            .select("id, company_name, bucket_name")
            .eq("email", email)
            .limit(1)
            .execute()
        )

        if response.data and len(response.data) > 0:
            row = response.data[0]
            return {
                "company_id": row["id"],
                "company_name": row.get("company_name", ""),
                "bucket_name": row["bucket_name"],
            }

        return {"bucket_name": None, "message": "No company found for this email"}

    except Exception as e:
        # Don't crash — just return null bucket so the field stays empty
        return {"bucket_name": None, "message": f"Lookup failed: {str(e)}"}


@router.post(
    "/organisations/upload-file",
    response_model=OrganisationUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_organisation_document_file(
    file: UploadFile = File(...),
    bucket_name: str = "organisations",
    embeddings_model: str = "text-embedding-3-small",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    user_email: Optional[str] = None,
):
    """
    Upload and process organisation document through LangGraph pipeline (File Upload).

    Pipeline Flow:
    START → document_load → embedding → vectorstore → END

    Parameters:
    - file: Uploaded file (multipart/form-data)
    - bucket_name: Supabase bucket and Pinecone index name
    - embeddings_model: Model to use for embeddings
    - chunk_size: Size of text chunks
    - chunk_overlap: Overlap between chunks
    - user_email: Clerk user's email to link company to user account

    Return Value:
    - OrganisationUploadResponse: Processing result with chunk count

    Side Effects:
    - Uploads document to Supabase storage
    - Generates embeddings
    - Stores vectors in Pinecone
    """
    try:
        # Read uploaded file content
        content = await file.read()
        text_content = content.decode("utf-8", errors="ignore")

        # Process through service layer
        result = pipeline_service.process_organisation_document(
            filename=file.filename,
            content=text_content,
            bucket_name=bucket_name,
            embeddings_model=embeddings_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            metadata={"user_email": user_email} if user_email else None,
        )

        return OrganisationUploadResponse(
            status="success",
            message="Document processed successfully through pipeline",
            filename=result.get("filename", file.filename),
            bucket_name=bucket_name,
            chunks_created=len(result.get("chunks", [])),
            metadata=result.get("metadata"),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline processing failed: {str(e)}",
        )


# ============================================================================
# Customer Query Pipeline Endpoints
# ============================================================================


@router.post(
    "/customer/query",
    response_model=CustomerQueryResponse,
    status_code=status.HTTP_200_OK,
)
async def query_documents(request: CustomerQueryRequest):
    """
    Query documents through customer pipeline (synchronous).

    Pipeline Flow:
    START → vectorstore → answer → save_conversation → END

    Parameters:
    - request: CustomerQueryRequest with query parameters

    Return Value:
    - CustomerQueryResponse: Answer and metadata

    Side Effects:
    - Queries Pinecone vector store
    - Generates LLM response
    - Saves conversation to database
    """
    try:
        # Query through service layer
        result = await pipeline_service.query_documents(
            bucket_name=request.bucket_name,
            question=request.question,
            embeddings_model=request.embeddings_model,
            llm_model=request.llm_model,
            temperature=request.temperature,
            search_type=request.search_type,
            k=request.k,
            fetch_k=request.fetch_k,
            lambda_mult=request.lambda_mult,
            thread_id=request.thread_id,
        )

        return CustomerQueryResponse(
            answer=result.get("answer", ""),
            question=request.question,
            thread_id=result.get("thread_id"),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {type(e).__name__}: {str(e)}",
        )
