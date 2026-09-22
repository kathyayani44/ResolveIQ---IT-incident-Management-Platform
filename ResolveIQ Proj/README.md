# ResolveIQ

ResolveIQ is an IT incident management platform that helps teams ingest, classify, investigate, and resolve incidents. It combines a FastAPI backend, a React dashboard, retrieval-augmented generation (RAG), and integrations for Jira and Supabase.

## Features

- Incident creation, normalization, and status tracking
- AI-assisted incident classification, root-cause analysis, and resolution suggestions
- Knowledge-base retrieval using local vector data and Qdrant
- Human approval workflow for proposed resolutions
- Jira incident ingestion and synchronization
- REST API with automatic Swagger and ReDoc documentation
- React and Vite frontend for interacting with the platform

## Project Structure

```text
ResolveIQ Proj/
├── app/                 # FastAPI application, agents, routes, and services
├── database/            # Database schema
├── data/                # Cached incidents, knowledge chunks, and vector data
├── frontend_app/        # React/Vite frontend
├── scripts/             # Data and retrieval utilities
├── src/                 # Embedding, retrieval, and vector-store modules
├── tests/               # Backend test suite
├── requirements.txt     # Python dependencies
└── README.md
```

## Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer and npm
- Git

## Backend Setup

From the `ResolveIQ Proj` directory, create and activate a virtual environment:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in `ResolveIQ Proj` if you want to use external services. The application can start with the default settings, while integrations and AI features require their corresponding keys:

```env
ENVIRONMENT=development

# Optional Jira integration
JIRA_DOMAIN=
JIRA_BASE_URL=
JIRA_EMAIL=
JIRA_API_TOKEN=
JIRA_WEBHOOK_SECRET=

# Optional Supabase integration
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Optional LLM providers
GROQ_API_KEY=
GEMINI_API_KEY=
```

Do not commit `.env` files or API keys to GitHub.

Start the backend:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

Useful endpoints:

- Health check: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Frontend Setup

Open a second terminal and run:

```bash
cd frontend_app
npm install
npm run dev
```

Vite will print the local frontend URL, normally `http://localhost:5173`.

For a production build:

```bash
npm run build
npm run preview
```

## Running Tests

From the `ResolveIQ Proj` directory, with the virtual environment activated:

```bash
pytest
```

