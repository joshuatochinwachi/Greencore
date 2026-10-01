# Greencore Admin Dashboard (`apps/admin`)

Operations web dashboard built with Next.js (App Router), TypeScript, and custom Greencore design system (Section 18).

## Backend Connection

This dashboard connects directly to the production FastAPI backend deployed on Railway:
- **API URL:** `https://greencore-production.up.railway.app`
- **Swagger UI:** `https://greencore-production.up.railway.app/docs`
- **Health Check:** `https://greencore-production.up.railway.app/health`

Configured via `NEXT_PUBLIC_API_URL` in `.env.local`.

## Features Built (Phase 1)

1. **Operations Dispatch Dashboard (`/`)**
   - Live KPI cards: Registered drivers, active routes, total drops, nightly allocation status.
   - Real-time Railway API status indicator (with `/health` ping).
   - Quick navigation into roster, routes, allocations, and CSV import.

2. **Driver Fleet Management (`/drivers`)**
   - Full driver roster with role filters (`van`, `7_5t`, `class1`, `class2`) and status filters.
   - Live search by driver name, email, or licence number.
   - Driver registration modal with vehicle role qualification.
   - Driver edit modal with audit logging.
   - Deactivation modal with mandatory operational reason (revokes all active JWT tokens per Section 14.2).

3. **Routes & Drops Portfolio (`/routes`)**
   - Route list with dynamic sequence ordering and drop count monitoring.
   - Detailed drop view: customer name, account number, postcode, address, special instructions, required vehicle class.
   - "New Route" creation modal.
   - "Add Drop" modal with automatic sequence numbering.
   - "Move Drop" modal with conflict warning check (`vehicle_class_mismatch`, `capacity_exceeded`) and forced override per Section 15.7 & 17.4.

4. **Nightly Route Allocations Workspace (`/allocations`)**
   - Date-based allocation matrix (defaults to tomorrow's date with quick day toggles).
   - Driver x route assignment grid with real-time duplicate driver warnings.
   - "Confirm & Send Notifications" modal publishing assignments and triggering driver push alerts per Section 6.1 & 14.4.

5. **Route Card CSV Import Wizard (`/import`)**
   - 3-step wizard: Upload -> Column Mapping -> Commit.
   - Intelligent auto-matching of detected CSV columns.
   - Acceptance criteria Section 17.6 verification: Partial-success commit reporting individual failed rows with specific reasons without discarding valid drops.

6. **Authentication & Session (`/login`)**
   - Enterprise login card with seed super admin auto-fill helper (`admin@test.greencore.app`).
   - JWT access & refresh token storage and route guarding.

## Running Locally

```bash
cd apps/admin
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000).
