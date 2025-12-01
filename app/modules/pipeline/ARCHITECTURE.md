# Pipeline Module - Architecture Overview

## Module Structure

The pipeline module now follows the same architectural pattern as other modules in the application:

```
app/modules/pipeline/
├── __init__.py          # Module exports
├── models.py            # Pydantic request/response models
├── service.py           # Business logic and LangGraph orchestration
├── router.py            # FastAPI endpoints (HTTP layer)
└── README.md            # API usage documentation
```

## File Responsibilities

### `models.py` - Data Models
**Purpose**: Define Pydantic models for request validation and response serialization.

**Models**:
- `OrganisationUploadRequest` - Document upload request
- `OrganisationUploadResponse` - Upload processing result
- `CustomerQueryRequest` - Query request with parameters
- `CustomerQueryResponse` - Query result
- `HealthCheckResponse` - Health check status

**Best Practice**: All models include:
- Field validation with Pydantic
- Type hints
- Default values
- Comprehensive docstrings

### `service.py` - Business Logic
**Purpose**: Encapsulate all business logic and LangGraph workflow execution.

**Class**: `PipelineService`

**Methods**:
- `process_organisation_document()` - Process document from content
- `process_organisation_file()` - Process document from file path
- `query_documents()` - Synchronous query execution
- `stream_query()` - Streaming query execution (for real-time responses)

**Key Features**:
- Proper error handling with meaningful exceptions
- Resource cleanup (temporary files)
- Validation of inputs
- Separated from HTTP concerns

### `router.py` - API Endpoints
**Purpose**: Define HTTP endpoints and handle web-specific concerns.

**Endpoints**:
- `GET /health` - Health check
- `POST /organisations/upload` - Upload document (JSON)
- `POST /organisations/upload-file` - Upload document (File)
- `POST /customer/query` - Query documents

**Responsibilities**:
- HTTP request/response handling
- Status code management
- Error translation to HTTP exceptions
- Delegates business logic to service layer

### `__init__.py` - Module Exports
**Purpose**: Define public API of the module.

**Exports**:
- Router for FastAPI integration
- Service class for direct usage
- All Pydantic models for type checking

## Architectural Benefits

### 1. Separation of Concerns
```python
# Models - What data looks like
class OrganisationUploadRequest(BaseModel):
    bucket_name: str
    content: str

# Service - What logic to execute
class PipelineService:
    def process_organisation_document(...):
        # Business logic here

# Router - How to expose via HTTP
@router.post("/organisations/upload")
async def upload_document(request: OrganisationUploadRequest):
    return pipeline_service.process_organisation_document(...)
```

### 2. Testability
Each layer can be tested independently:
- **Models**: Test validation and serialization
- **Service**: Test business logic with mocks
- **Router**: Test HTTP endpoints with TestClient

### 3. Reusability
Service layer can be used:
- From API endpoints (router.py)
- From CLI scripts
- From Celery tasks
- From other modules

### 4. Maintainability
- Clear file organization
- Each file has a single responsibility
- Easy to locate and modify code

## Comparison with Other Modules

### Document Module
```
document/
├── models.py           ✅ Pydantic models
├── service.py          ✅ DocumentService class
├── router.py           ✅ API endpoints
└── __init__.py         ✅ Exports
```

### Pipeline Module (Now)
```
pipeline/
├── models.py           ✅ Pydantic models
├── service.py          ✅ PipelineService class
├── router.py           ✅ API endpoints
└── __init__.py         ✅ Exports
```

## Usage Examples

### Direct Service Usage
```python
from app.modules.pipeline import PipelineService

service = PipelineService()

# Process a document
result = service.process_organisation_document(
    filename="doc.txt",
    content="Document content...",
    bucket_name="my-org",
)

print(f"Created {len(result['chunks'])} chunks")
```

### API Usage
```bash
# Upload document
curl -X POST "http://localhost:8000/api/v1/pipeline/organisations/upload-file" \
  -F "file=@document.txt" \
  -F "bucket_name=my-org"

# Query documents
curl -X POST "http://localhost:8000/api/v1/pipeline/customer/query" \
  -H "Content-Type: application/json" \
  -d '{
    "bucket_name": "my-org",
    "question": "What is this about?"
  }'
```

### Import in Other Modules
```python
# Type-safe imports
from app.modules.pipeline import (
    PipelineService,
    OrganisationUploadRequest,
    CustomerQueryRequest,
)

# Use service directly
pipeline = PipelineService()
result = pipeline.query_documents(
    bucket_name="docs",
    question="What is RAG?",
)
```

## Migration Notes

### What Changed
1. **Moved models** from `router.py` → `models.py`
2. **Created service layer** in `service.py`
3. **Simplified router** to delegate to service
4. **Updated exports** in `__init__.py`

### What Stayed the Same
- API endpoints remain unchanged
- Request/response formats identical
- LangGraph workflows unchanged
- All functionality preserved

### Benefits
✅ **Consistent** with other modules  
✅ **Testable** individual components  
✅ **Reusable** service layer  
✅ **Maintainable** clear structure  
✅ **Type-safe** with proper exports
