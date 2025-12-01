# Pipeline Module - LangGraph API Endpoints

This module exposes your LangGraph workflows as REST API endpoints, making it easy for the frontend to use orchestrated workflows.

## Architecture

```
Frontend → FastAPI Router → LangGraph Pipeline → Service Functions
```

## Organisation Pipeline

**Workflow**: `document_load → embedding → vectorstore → END`

This pipeline processes documents by:
1. Loading and uploading to Supabase
2. Chunking text and generating embeddings
3. Storing vectors in Pinecone

### Endpoints

#### 1. Upload Document (JSON)

**POST** `/api/v1/pipeline/organisations/upload`

```bash
curl -X POST "http://localhost:8000/api/v1/pipeline/organisations/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "bucket_name": "my-organisation",
    "filename": "company-docs.txt",
    "content": "Your document content here...",
    "embeddings_model": "text-embedding-3-small",
    "chunk_size": 500,
    "chunk_overlap": 50,
    "metadata": {
      "department": "engineering",
      "version": "1.0"
    }
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Document processed successfully through pipeline",
  "filename": "company-docs.txt",
  "bucket_name": "my-organisation",
  "chunks_created": 42,
  "metadata": {
    "document_id": "123e4567-e89b-12d3-a456-426614174000"
  }
}
```

#### 2. Upload Document (File)

**POST** `/api/v1/pipeline/organisations/upload-file`

```bash
curl -X POST "http://localhost:8000/api/v1/pipeline/organisations/upload-file?bucket_name=my-org&embeddings_model=text-embedding-3-small" \
  -F "file=@./documents/my-file.txt"
```

**Query Parameters:**
- `bucket_name` (default: "organisations")
- `embeddings_model` (default: "text-embedding-3-small")
- `chunk_size` (default: 500)
- `chunk_overlap` (default: 50)

#### 3. Health Check

**GET** `/api/v1/pipeline/health`

```bash
curl "http://localhost:8000/api/v1/pipeline/health"
```

## Frontend Integration Examples

### JavaScript / React

```javascript
// Upload document with file input
async function uploadDocument(file, bucketName = "my-org") {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(
    `/api/v1/pipeline/organisations/upload-file?bucket_name=${bucketName}`,
    {
      method: 'POST',
      body: formData
    }
  );
  
  const result = await response.json();
  console.log(`Created ${result.chunks_created} chunks`);
  return result;
}

// Upload document with text content
async function uploadDocumentText(content, filename, bucketName = "my-org") {
  const response = await fetch('/api/v1/pipeline/organisations/upload', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      bucket_name: bucketName,
      filename: filename,
      content: content,
      embeddings_model: "text-embedding-3-small",
      metadata: {
        uploaded_at: new Date().toISOString()
      }
    })
  });
  
  return await response.json();
}
```

### Python Client

```python
import requests

def upload_document(filepath: str, bucket_name: str = "my-org"):
    """Upload document through pipeline"""
    with open(filepath, 'rb') as f:
        files = {'file': f}
        params = {
            'bucket_name': bucket_name,
            'embeddings_model': 'text-embedding-3-small'
        }
        response = requests.post(
            'http://localhost:8000/api/v1/pipeline/organisations/upload-file',
            files=files,
            params=params
        )
    return response.json()

# Usage
result = upload_document('./my-document.txt', 'engineering-docs')
print(f"Success! Created {result['chunks_created']} chunks")
```

## Benefits Over Individual Endpoints

### Before (Multiple API Calls):
```javascript
// 1. Upload document
const uploadResult = await fetch('/api/v1/documents/upload-file', {...});

// 2. Generate embeddings
const embedResult = await fetch('/api/v1/embeddings/embed', {...});

// 3. Store in vectorstore
const storeResult = await fetch('/api/v1/vectorstore/upsert', {...});
```

### After (Single Pipeline Call):
```javascript
// All steps in one call!
const result = await fetch('/api/v1/pipeline/organisations/upload-file', {...});
```

**Advantages:**
- ✅ **Simpler frontend code** - One API call instead of orchestrating multiple
- ✅ **Atomic operations** - All steps succeed or fail together
- ✅ **State management** - LangGraph handles workflow state automatically
- ✅ **Error handling** - Centralized error handling in one place
- ✅ **Better performance** - Reduced network round trips

## Testing with Swagger UI

1. Start your FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Open Swagger UI:
   ```
   http://localhost:8000/docs
   ```

3. Navigate to **Pipeline** section to test endpoints interactively

## Error Handling

All endpoints return standard HTTP status codes:

- **201 Created** - Document successfully processed
- **500 Internal Server Error** - Pipeline processing failed

Error response example:
```json
{
  "detail": "Pipeline processing failed: No content available to chunk and embed"
}
```

## Next Steps

You can extend this module by:
1. Adding the customer query pipeline endpoints (for querying documents)
2. Adding status endpoints to check pipeline progress
3. Adding endpoints to list processed documents
4. Adding webhook support for async processing notifications
