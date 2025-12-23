# Docusaurus RAG Chatbot Backend

This backend service provides a Retrieval-Augmented Generation (RAG) chatbot for Docusaurus-based books. It allows users to ask questions about book content and receive accurate answers based on the book's content without hallucination.

## Features

- **RAG-based Q&A**: Ask questions about book content with answers grounded in actual book content
- **Selected Text Q&A**: Ask questions specifically about selected text on the page
- **Source Citations**: Responses include references to the source documents
- **FastAPI Backend**: Built with FastAPI for high performance and automatic API documentation
- **Cohere Embeddings**: Uses Cohere API for high-quality embeddings
- **Qdrant Vector Storage**: Efficient similarity search with metadata support
- **OpenRouter LLM Integration**: Answers generated via OpenRouter API

## Prerequisites

- Python 3.8+
- API keys for:
  - Cohere API
  - Qdrant Cloud
  - OpenRouter API
  - Neon Postgres (optional, for chat history)

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Set up your book content**:
   - Place your Docusaurus documentation in a `docs/` directory
   - The ingestion script will automatically process `.md` and `.mdx` files

## Usage

### 1. Start the Backend Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 2. Ingest Your Book Content

```bash
python ingest.py
```

This will scan your `docs/` directory, chunk the content, generate embeddings, and store them in Qdrant.

### 3. API Endpoints

- `GET /api/health` - Health check for the service
- `POST /api/chat` - Chat endpoint for asking questions
- `POST /api/search` - Search endpoint for finding relevant content
- `POST /api/selected-text-question` - Endpoint for questions about selected text

### 4. Example API Request

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is this book about?",
    "selected_text": null
  }'
```

## Frontend Integration

To integrate with your Docusaurus site:

1. Add the `ChatbotWidget.jsx` and `ChatbotWidget.css` files to your Docusaurus project
2. Import and use the component in your layout
3. The widget will automatically detect text selection and provide the "Ask about selected text" functionality

## Configuration

The application behavior can be configured through environment variables in `.env`:

- `COHERE_API_KEY` - Your Cohere API key
- `QDRANT_URL` - Your Qdrant Cloud URL
- `QDRANT_API_KEY` - Your Qdrant API key
- `OPENROUTER_API_KEY` - Your OpenRouter API key
- `NEON_DB_URL` - Your Neon Postgres connection string (optional)
- `QDRANT_COLLECTION_NAME` - Name of the Qdrant collection to use (default: "book_chunks")

## Development

### Running Tests

```bash
python test_api.py
```

### API Documentation

Auto-generated API documentation is available at:
- `http://localhost:8000/docs` - Interactive API documentation (Swagger UI)
- `http://localhost:8000/redoc` - Alternative API documentation (ReDoc)

## Architecture

The backend consists of several key services:

- **Embedding Service**: Uses Cohere API to generate document embeddings
- **Vector Service**: Manages storage and retrieval of embeddings in Qdrant
- **LLM Service**: Uses OpenRouter API to generate responses
- **Retrieval Service**: Handles document retrieval and context preparation
- **Database Service**: Manages chat history and session data (if database configured)
- **Validation Service**: Ensures responses are grounded in book content

## Security

- All API keys are stored in environment variables
- No API keys are exposed to the frontend
- Rate limiting can be configured via environment variables
- Input validation is performed on all API endpoints

## Troubleshooting

### Common Issues

1. **API Keys**: Ensure all required API keys are set in the `.env` file
2. **Qdrant Connection**: Verify your Qdrant URL and API key are correct
3. **Content Ingestion**: Make sure your book content is in the `docs/` directory

### Health Check

Use the health endpoint to verify all services are available:
```bash
curl http://localhost:8000/api/health
```

## Performance

- The system is designed to respond to queries within 5 seconds
- Responses are grounded in book content with source citations
- Selected text functionality restricts answers to only the provided text
- Fallback responses are provided when information is not available in the book