# ResolveIQ Backend

ResolveIQ backend service built with FastAPI.

## Project Structure

```
ResolveIQ/
├── app/
│   ├── agents/
│   │   ├── classification/
│   │   ├── kb/
│   │   ├── rag/
│   │   ├── rca/
│   │   ├── resolution/
│   │   ├── revision/
│   │   └── sop/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   ├── graph/
│   │   └── nodes/
│   ├── integrations/
│   │   ├── jira/
│   │   └── supabase/
│   ├── schemas/
│   ├── services/
│   └── utils/
├── database/
├── scripts/
└── tests/
```

## Getting Started

### Prerequisites
- Python 3.10+

### Installation

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Server

Start the FastAPI development server with Uvicorn:

```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`.

- Health check endpoint: `http://127.0.0.1:8000/health`
- Interactive API docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Alternative API docs (ReDoc): `http://127.0.0.1:8000/redoc`

### Running Tests

Execute pytest:

```bash
pytest
```
