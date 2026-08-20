# Enterprise RAG Platform

A production-ready, multi-tenant Retrieval-Augmented Generation (RAG) platform. It allows users to securely upload documents, process them into embeddings, and query them using an LLM-powered chat interface.

## 🚀 Features

- **Document Ingestion**: Upload PDF, TXT, MD, and DOCX files.
- **Asynchronous Processing**: Background document chunking and vector embedding via Celery.
- **Multi-Tenant Isolation**: Strict isolation ensuring users can only access and query their own documents.
- **Vector Search**: High-performance semantic search using Qdrant.
- **Modern Frontend**: A reactive Next.js UI using Tailwind CSS and shadcn/ui.
- **Rate Limiting**: Granular Redis-backed rate limiting to protect API endpoints.
- **Security**: HttpOnly secure cookie-based authentication.

## 🛠 Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) - High-performance Python web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Async PostgreSQL ORM
- [Celery](https://docs.celeryq.dev/) - Distributed task queue
- [Qdrant](https://qdrant.tech/) - Vector database
- [Redis](https://redis.io/) - Rate limiting and Celery broker
- [OpenAI](https://openai.com/) - LLM Generation (Async)

**Frontend**
- [Next.js](https://nextjs.org/) (App Router) - React framework
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first styling
- [shadcn/ui](https://ui.shadcn.com/) - Accessible UI components
- [Playwright](https://playwright.dev/) - End-to-End Testing

## ⚙️ Getting Started

### Prerequisites

- [Docker & Docker Compose](https://www.docker.com/)
- [Node.js](https://nodejs.org/) (v18+)

### 1. Environment Setup

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Ensure you set your `OPENAI_API_KEY` in the `.env` file.

### 2. Start the Backend

Start the PostgreSQL database, Redis, Qdrant, Celery worker, and FastAPI server using Docker Compose:

```bash
docker compose up --build
```

The backend API will be available at `http://localhost:8000`.
You can view the interactive API documentation at `http://localhost:8000/api/v1/docs`.

### 3. Start the Frontend

In a new terminal window, navigate to the frontend directory, install dependencies, and start the development server:

```bash
cd frontend
npm install
npm run dev
```

The frontend application will be available at `http://localhost:3000`.

## 🧪 Testing

**Backend Tests (Pytest)**
```bash
docker compose exec backend sh -c "PYTHONPATH=/app /opt/venv/bin/pytest"
```

**Frontend E2E Tests (Playwright)**
```bash
cd frontend
npx playwright test
```

## 📝 License

MIT License
