# ResShare - Decentralized File Sharing Application with AI Chatbot

ResShare is a decentralized file sharing application that allows users to securely store, share, and manage their files using Resilient DB technology. The application now features an **AI-powered chatbot** that can answer questions about your uploaded documents using Retrieval-Augmented Generation (RAG).

## Features

### Core Features
- User Authentication (Sign up, Login, Logout)
- File Upload and Download
- Folder Creation and Management
- File Sharing between Users
- Secure File Storage using IPFS
- User Account Management

### AI Document Assistant
- **Intelligent Document Q&A**: Ask questions about your uploaded files
- **Multi-format Support**: Works with PDF, DOCX, and TXT files
- **Semantic Search**: Finds relevant information across all your documents
- **Privacy-First**: Your data stays isolated and secure
- **Source Attribution**: See which documents were used to answer your questions

## Tech Stack

- **Frontend**: React.js with Material-UI
- **Backend**: Python Flask
- **Storage**: ResilientDB for Metadata storage, IPFS for File Storage, QDrant for Vector Storage
- **Authentication**: Session-based authentication
- **AI/ML**: 
  - Local BGE small en v1.5 via FastEmbed for embedding generation
  - Qdrant for persistent vector search
  - Local Qwen via a llama.cpp chat-completions endpoint for response generation
  - LangChain for text processing

## Prerequisites

- Python 3.10+
- Node.js 16+ and npm
- uv (preferred)
- IPFS daemon running locally
- Qdrant (started automatically by Docker Compose)
- A separately started local llama.cpp server for generated responses (see `local_finetuning/README.md`)

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/ExpoLab-App/ResShare.git
cd ResShare
```

2. **Install backend dependencies:**
```bash
cd backend
uv sync
```

3. **Install frontend dependencies:**
```bash
cd frontend
npm install
cd ..
```

4. **Set up AI features:**
```bash
# Host-run backend; Compose defaults to host.docker.internal instead
export LOCAL_LLM_BASE_URL="http://127.0.0.1:8081/v1"
export LOCAL_LLM_MODEL="resshare-local"
```

## Running the Application

1. **Start the backend, IPFS services, and Qdrant:**
Start the ResShare fine-tuned model in a separate terminal:
```bash
bash local_finetuning/serve.sh
```

Then start the application stack:
```bash
docker compose up --build
```

To run IPFS, IPFS Cluster, Qdrant, Flask, and React as separate local processes,
follow the [manual local development guide](docs/development.md).

2. **Start the frontend development server:**
```bash
cd frontend
npm start
```

The application will be available at:
- Frontend: http://localhost:5997
- Backend API: http://localhost:5000

## Using the AI Chatbot

### Getting Started with AI
1. **Upload Documents**: Upload PDF, DOCX, or TXT files through the normal file upload process
2. **Navigate to AI Chat**: Click the "AI Chat" button in the navigation bar
3. **Ask Questions**: Type questions about your documents and get intelligent responses

### Example Queries
- "What are the main findings in my research paper?"
- "Summarize the key points from my meeting notes"
- "What does my contract say about payment terms?"
- "Find information about project deadlines"

### Supported File Types for AI
- **PDF**: Research papers, reports, contracts
- **DOCX**: Word documents, meeting notes, proposals  
- **TXT**: Plain text files, code documentation, notes

### AI Features
- **Smart Chunking**: Documents are intelligently split into semantic chunks
- **Vector Search**: Uses advanced embeddings to find relevant content
- **Source Attribution**: Shows which files and sections were used for answers
- **Privacy Preserved**: Each user's AI data is completely isolated

## Configuration

### Local AI Configuration
FastEmbed downloads BGE small en v1.5 on first use and runs embeddings locally.
Generation requires a separately started local chat server. See
[the local fine-tuning runbook](local_finetuning/README.md) for model setup.

`RAG_COLLECTION` defaults to `resshare_bge_small_en_v15_v1` (384 dimensions).
Existing Gemini vectors remain in `resshare_vectors` and cannot be reused.
Old uploads need reindexing before local retrieval can find them; statistics
count only metadata matching the local model and collection. Follow the
[index migration checklist](local_finetuning/PLAN.md#index-migration-and-rollback)
before cutting over an existing deployment.

The backend bounds the prompt to 6,000 UTF-8 bytes and output to 512 tokens for
an 8K context server. Sources reflect only whole chunks actually sent to the
model. Retrieval/model failures return HTTP 503/502 rather than a successful
answer. No server is started automatically.

## Usage

### Standard File Operations
1. Create a new account using the sign-up feature
2. Log in to your account
3. Create folders to organize your files
4. Upload files to your folders
5. Share files with other users
6. Download shared files from other users

### AI-Powered Features
1. **Upload Text Documents**: Upload PDF, DOCX, or TXT files
2. **Wait for Processing**: Files are automatically processed for AI search
3. **Ask Questions**: Use the AI Chat interface to query your documents
4. **Get Intelligent Answers**: Receive responses with source attribution
5. **Explore Knowledge Base**: View statistics about your indexed documents
## Architecture

### RAG Pipeline
```
File Upload → Text Extraction → Chunking → Embedding → Vector DB Storage
                                                            ↓
User Query → Query Embedding → Vector Search → Context → LLM → Response
```

### Components
- **Text Extractors**: PDF (PyPDF2), DOCX (python-docx), TXT (UTF-8)
- **Chunking**: LangChain RecursiveCharacterTextSplitter
- **Embeddings**: FastEmbed BAAI/bge-small-en-v1.5, 384 dimensions
- **Vector DB**: Qdrant with authenticated per-user payload filtering
- **LLM**: Local OpenAI-compatible chat endpoint, shared grounded prompt and non-thinking mode
