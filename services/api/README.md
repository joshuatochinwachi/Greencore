# services/api — Greencore FastAPI Backend

## Setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env    # fill in real values

# Start Postgres + Redis (from repo root):
cd ../../infra
docker compose up -d
cd ../services/api

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

## Structure

```
services/api/
├── app/
│   ├── main.py               # FastAPI app factory
│   ├── config.py             # Settings (pydantic-settings)
│   ├── database.py           # SQLAlchemy engine + session
│   ├── dependencies.py       # Shared FastAPI dependencies (get_db, get_current_user)
│   ├── models/               # SQLAlchemy ORM models (one file per table group)
│   ├── schemas/              # Pydantic request/response schemas
│   ├── routers/              # FastAPI routers (one per domain)
│   ├── services/             # Business logic (auth, notifications, audit)
│   └── migrations/           # Alembic migrations (auto-generated)
├── tests/
├── alembic.ini
├── requirements.txt
└── .env.example
```
