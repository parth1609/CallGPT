# 💬 VocaliZ

**VocaliZ** is an intelligent document chat system that helps organizations make their knowledge accessible through conversational AI. Upload your documents, and let your team or customers ask questions in natural language—getting accurate, context-aware answers instantly.

---

## 🌟 What Can VocaliZ Do?

### For Organizations
- **Upload Documents**: Simply upload your text files (manuals, FAQs, policies, knowledge bases, etc.)
- **Automatic Indexing**: The system automatically processes and organizes your documents
- **Instant Accessibility**: Your knowledge becomes searchable and accessible through natural conversation

### For End Users (Customers/Employees)
- **Ask Questions**: Type questions in plain English about your organization's documents
- **Get Instant Answers**: Receive accurate, contextual responses powered by AI
- **Conversation History**: Continue conversations across sessions with automatic memory
- **Source References**: Answers include references to source documents for verification

---

## 🎯 Use Cases

VocaliZ is perfect for:

- **Customer Support**: Let customers find answers from your documentation instantly
- **Employee Onboarding**: New employees can ask questions about company policies and procedures
- **Knowledge Management**: Make organizational knowledge accessible to everyone
- **Technical Documentation**: Help users navigate complex technical manuals
- **FAQ Automation**: Reduce support load by automating common questions

---

## 🚀 Quick Start (For Non-Technical Users)

### Prerequisites
You'll need:
- A computer with Python 3.13 or later installed
- Internet connection
- API keys for required services (your IT team can help with this)

### Installation

1. **Download the project** to your computer

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   - Copy the `.env.example` file and rename it to `.env`
   - Fill in your API keys and configuration (ask your IT administrator if you need help)

4. **Start the system**:

   **Option A: Using the simple interface (Streamlit)**
   ```bash
   make frontend
   ```
   Then open your browser to `http://localhost:8501`

   **Option B: Using the full API**
   ```bash
   make api
   ```
   The API will be available at `http://localhost:8000`

---

## 💡 How to Use

### Uploading Documents (Organization Mode)

1. Open the VocaliZ interface in your browser
2. Switch to **"Org"** mode in the sidebar
3. Configure your settings:
   - **Bucket/Index Name**: Choose a name for your document collection (e.g., "customer-support")
   - **Chunk Size**: Leave default (1000) for best results
   - **Embeddings Model**: Leave default unless advised otherwise
4. Click **"Choose a text file to upload"** and select your document
5. Click **"🚀 Process and Index Document"**
6. Wait for processing to complete—you'll see a success message with details

### Asking Questions (Customer Mode)

1. Switch to **"Customer"** mode in the sidebar
2. Make sure the **Bucket/Index Name** matches the one you uploaded documents to
3. Type your question in the chat box at the bottom
4. Press Enter or click Send
5. The AI will search your documents and provide an answer

### Tips for Best Results
- **Be specific**: Instead of "What is this about?", try "What are the warranty terms for laptops?"
- **Use natural language**: Ask questions like you would ask a person
- **Follow up**: You can ask follow-up questions in the same conversation
- **Check sources**: Review the source information to verify answers

---

## 🏗️ System Architecture

VocaliZ uses a **Retrieval-Augmented Generation (RAG)** architecture:

```
User Question → Document Search → Context Retrieval → AI Answer Generation → Response
```

### Technology Stack
- **Backend Framework**: FastAPI (Python)
- **Frontend**: Streamlit (with additional frontend in development)
- **System Orchestration**: LangChain, LangGraph for orchestration
- **Vector Database**: Pinecone + Supabase
- **Embeddings**: HuggingFace Sentence Transformers
- **LLM**: Groq (configurable)
- **Conversation Storage**: PostgreSQL with persistent memory

---

## 📁 Project Structure

```
CallGPT/
├── app/
│   ├── core/                 # Core configuration and settings
│   ├── modules/              # Main application modules
│   │   ├── conversation/     # Conversation management
│   │   ├── document/         # Document processing
│   │   ├── embedding/        # Text embeddings
│   │   ├── llm/              # Language model integration
│   │   ├── pipeline/         # RAG pipeline orchestration
│   │   ├── retrieval/        # Document retrieval
│   │   └── vectorstore/      # Vector database operations
│   └── main.py               # FastAPI application entry point
├── tests/                    # Test files
├── streamlit_app.py          # Streamlit UI
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
├── Makefile                  # Convenient commands
└── README.md                 # This file
```

---

## 🔧 Configuration

The system is configured through environment variables in the `.env` file:

| Variable | Purpose | Required |
|----------|---------|----------|
| `GROQ_API_KEY` | API key for Groq LLM | ✅ Yes |
| `SUPABASE_URL` | Supabase project URL | ✅ Yes |
| `SUPABASE_SERVICE_KEY` | Supabase service key | ✅ Yes |
| `SUPABASE_BUCKET` | Default storage bucket name | ✅ Yes |
| `PINECONE_API_KEY` | Pinecone vector database key | ✅ Yes |
| `DATABASE_URL` | PostgreSQL connection string | ✅ Yes |
| `LLM_MODEL` | Which AI model to use | Optional |
| `EMBEDDING_MODEL` | Which embedding model to use | Optional |

---

## 📊 Features

### Current Features
- ✅ Multi-format document upload and processing
- ✅ Intelligent text chunking and embedding
- ✅ Vector similarity search
- ✅ Conversational AI with context awareness
- ✅ Persistent conversation history
- ✅ Multi-tenant support (different buckets/indexes)
- ✅ Configurable retrieval parameters
- ✅ Two-stage retrieval with reranking option
- ✅ Streaming responses for better UX
- ✅ REST API for integration

### Frontend Status
> **Note**: A new, enhanced frontend is currently being developed by another team member. The current Streamlit interface is fully functional and will be replaced once the new frontend is merged.

---

## 🔌 API Endpoints

The FastAPI backend provides RESTful endpoints:

### Health Check
```
GET /health
```

### Organization Endpoints
```
POST /api/v1/pipeline/organisations/upload-file
POST /api/v1/pipeline/organisations/upload
```

### Customer Endpoints
```
POST /api/v1/pipeline/customer/query
```

### Module-Specific Endpoints
- `/api/v1/embeddings/*` - Embedding operations
- `/api/v1/retrieval/*` - Document retrieval
- `/api/v1/llm/*` - Language model operations
- `/api/v1/conversations/*` - Conversation management
- `/api/v1/documents/*` - Document operations
- `/api/v1/vectorstore/*` - Vector storage operations

Full API documentation is available at `http://localhost:8000/docs` when running the API server.

---

 

Individual module tests:
```bash
pytest tests/test_document_node.py
pytest tests/test_embedding_node.py
pytest tests/test_vectorstore_node.py
pytest tests/test_answer_node.py
```

---

## 📝 Makefile Commands

For convenience, common tasks are available through the Makefile:

```bash
make install    # Install all dependencies
make api        # Start the FastAPI backend server
make frontend   # Start the Streamlit frontend
make format     # Format code with Ruff
make lint       # Lint code with Flake8
```

---

## 🔐 Security Considerations

- **API Keys**: Never commit your `.env` file to version control
- **Service Keys**: Use Supabase service keys only on the backend, never expose them to clients
- **Access Control**: Implement proper authentication and authorization for production use
- **Data Privacy**: Be mindful of what documents you upload and who has access

---

## 🤝 Support & Contributing

### Getting Help
- Check the documentation in each module's README
- Review the architecture documentation in `app/modules/pipeline/ARCHITECTURE.md`
- Contact your system administrator or IT team

### For Developers
See the **Developer Guide** section below for detailed technical information.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

---

# 👨‍💻 Developer Guide

## Introduction for Developers

CallGPT follows a **modular monolith architecture** with clear separation of concerns. The application is built using FastAPI for the backend, with a pipeline-based approach using LangGraph for RAG orchestration.

### Architecture Principles

1. **Modular Design**: Each module (document, embedding, retrieval, etc.) is self-contained
2. **Layered Architecture**: Clear separation between models, services, and routers
3. **Type Safety**: Extensive use of Pydantic models and Python type hints
4. **Testability**: Each layer can be tested independently
5. **Scalability**: Designed for easy horizontal scaling and service extraction

### Module Structure

Each module follows a consistent pattern:
```
module_name/
├── __init__.py          # Public API exports
├── models.py            # Pydantic request/response models
├── service.py           # Business logic
├── router.py            # FastAPI endpoints
└── README.md            # Module-specific documentation
```

### Tech Stack Details

- **FastAPI**: Async web framework for high-performance APIs
- **LangChain/LangGraph**: LLM orchestration and workflow management
- **Pydantic**: Data validation and settings management
- **PostgreSQL**: Conversation storage and checkpointing
- **Pinecone**: Vector similarity search
- **Supabase**: Vector storage and file management
- **Sentence Transformers**: Text embeddings
- **Groq**: LLM inference

### Getting Started (Developers)

1. **Clone and install**:
   ```bash
   git clone <repository-url>
   cd CallGPT
   uv add -r requirements.txt  # Using uv for faster installs
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Fill in your API keys and configuration
   ```

3. **Database setup**:
   ```bash
   # Ensure PostgreSQL is running and DATABASE_URL is set
   # Tables are created automatically by LangGraph checkpointer
   ```

4. **Run development servers**:
   ```bash
   # Terminal 1 - Backend
   make api
   
   # Terminal 2 - Frontend
   make frontend
   ```

### Key Design Patterns

#### 1. State Management with LangGraph
The RAG pipeline is implemented as a state graph:
```python
class RAGState(TypedDict):
    question: str
    messages: Annotated[Sequence[BaseMessage], add_messages]
    context: List[Document]
    answer: str
    # ... more fields
```

#### 2. Service Layer Pattern
Business logic is isolated in service classes:
```python
class PipelineService:
    def process_organisation_document(self, ...):
        # Pure business logic
        
    def query_documents(self, ...):
        # Pure business logic
```

#### 3. Dependency Injection
Settings and configuration are injected via Pydantic:
```python
from app.core.config import settings

# Use settings anywhere
api_key = settings.GROQ_API_KEY
```

#### 4. Checkpointing for Persistence
LangGraph checkpointer provides conversation memory:
```python
customer = customer_pipeline.compile(checkpointer=checkpointer)

# Conversations are automatically saved with thread_id
result = customer.invoke(state, config={"configurable": {"thread_id": thread_id}})
```

### Development Workflow

1. **Create a new feature**:
   - Add models in `models.py`
   - Implement business logic in `service.py`
   - Expose via API in `router.py`
   - Write tests in `tests/`

2. **Code quality**:
   ```bash
   make format  # Auto-format with Ruff
   make lint    # Check code quality
   pytest       # Run tests
   ```

 

**Streaming responses**:
```python
# Use LangGraph streaming
for event in graph.stream(state, stream_mode="updates"):
    yield event
```

**Database operations**:
```python
# Conversations are auto-saved via checkpointer
# Access with thread_id in config
config = {"configurable": {"thread_id": thread_id}}
state = graph.get_state(config)
```
 
### Deployment Considerations

- **Environment variables**: Use secrets management in production
- **Database**: Ensure PostgreSQL has sufficient resources
- **Scaling**: Consider containerization with Docker
- **Monitoring**: Add logging, metrics, and alerting
- **API rate limits**: Implement rate limiting for production

---

**Built with ❤️ by parth1609**

*Last Updated: January 2026*
