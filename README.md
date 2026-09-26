# greencore — Monorepo Root

A transport driver and route management platform.

## Structure

```
greencore/
├── apps/
│   ├── driver/           # React Native / Expo driver app
│   └── admin/            # Next.js admin dashboard
├── services/
│   └── api/              # FastAPI backend
├── packages/
│   └── shared-types/     # Shared TypeScript types
├── infra/                # IaC / deployment config
└── docs/                 # Spec & state files (managed outside Git)
```

## Getting Started

See `docs/GREENCORE_DOCUMENTATION.md` for the full spec.

### Backend (API)

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill in secrets
alembic upgrade head
uvicorn app.main:app --reload
```