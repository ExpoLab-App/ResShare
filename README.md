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
- **Storage**: ResilientDB for Metadata storage and IPFS for File Storage
- **Authentication**: Session-based authentication
- **AI/ML**: 
  - Gemini embeddings (`gemini-embedding-001`) and FAISS vector search
  - Gemini 2.5 Flash for answers, with extractive fallback when generation is unavailable
  - LangChain for text chunking

## Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- IPFS daemon running locally
- Google Gemini API key (`GOOGLE_API_KEY` in `.env`) for the AI document chatbot

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/ResilientApp/ResShare.git
cd ResShare
```

2. **Install backend dependencies:**
```bash
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt
```

3. **Install frontend dependencies:**
```bash
cd frontend
npm install
```

4. **Configure environment variables** (from the project root):

```bash
cp env.example .env
# Edit .env: set GOOGLE_API_KEY, FLASK_SECRET_KEY, and other values as needed
```

| Variable | Purpose |
|----------|---------|
| `GOOGLE_API_KEY` | Required for AI chat — document embeddings, search, and Gemini answers |
| `FLASK_SECRET_KEY` | Session signing (use a strong value in production) |
| `FLASK_RUN_PORT` | Backend port (default `5000`; set if port 5000 is already in use) |
| `CORS_ORIGINS` | Extra frontend origins allowed to call the API |
| `KV_SERVICE_URL` | ResilientDB KV endpoint |
| `STORAGE_TYPE` | `memory` (local dev) or `resilientdb` |

For the frontend, point the UI at your backend URL:

```bash
cd frontend
cp .env.example .env.local
# Set REACT_APP_API_BASE_URL to match your backend (e.g. http://localhost:5001 if FLASK_RUN_PORT=5001)
```

> **Note:** Copy `env.example` to `.env` in the **project root** (not `backend/.env`). The app loads `.env` from the directory where you run `python app.py`.

## Running the Application

1. **Start the IPFS daemons:**
```bash
ipfs daemon
ipfs-cluster-service daemon
```
*To install IPFS Cluster Service, please refer to [this link](https://ipfscluster.io/download/)*

2. **Start the backend server:**
```bash
python app.py
```

3. **Start the frontend development server:**
```bash
cd frontend
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
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

### AI chatbot

Set `GOOGLE_API_KEY` in `.env` (see step 4 above). The key powers:

- **Embeddings & search** — Gemini `gemini-embedding-001` indexes your documents into a per-user FAISS store
- **Generated answers** — Gemini 2.5 Flash synthesizes a reply from retrieved chunks

If the generative model is unavailable, the chatbot uses an **extractive fallback**: it returns the most relevant passage from your top-matching file chunk instead of rewriting it (no paraphrasing or summarization).

Without `GOOGLE_API_KEY`, document indexing and AI search will not work.


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
- **Embeddings**: Google Gemini API (gemini-embedding-001) with configurable dimensions (768/1536/3072)
- **Vector DB**: FAISS with per-user isolation
- **LLM**: Gemini 2.5 Flash (optional) or extractive fallback
