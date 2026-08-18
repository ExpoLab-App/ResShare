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
  - Google Gemini for embeddings
  - Qdrant for persistent vector search
  - Gemini 2.5 Flash or an extractive fallback for response generation
  - LangChain for text processing

## Prerequisites

- Python 3.10+
- Node.js 16+ and npm
- uv (preferred)
- IPFS daemon running locally
- Qdrant (started automatically by Docker Compose)
- Gemini API key for document embedding and generated responses

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
# Required for document embeddings and generated answers
export GOOGLE_API_KEY="your-gemini-api-key-here"
```

## Running the Application

1. **Start the backend, IPFS services, and Qdrant:**
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

### Gemini Configuration
Document embedding requires a Gemini API key. The same key enables generated
answers; without it, indexing fails while the uploaded file remains available.

```bash
export GOOGLE_API_KEY="your-key-here"
```

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
- **Vector DB**: Qdrant with authenticated per-user payload filtering
- **LLM**: Gemini 2.5 Flash (optional) or extractive fallback
