# GREENCORE
## Transport Driver & Route Management Platform
### Product, Technical & Implementation Documentation — v1.0

**Prepared by:** Joshua Nwachukwu

**Date:** August 2026

**Status:** Draft for client review — pending sign-off on scope, phasing and open questions (Section 12)

---

## How to read this document

This document serves two audiences at once:

- **Sections 1–2** are written for the founder/client: what Greencore does, why, and what it costs in time and money to get there.
- **Sections 3–11** are written as a build specification precise enough that a developer can implement each module without needing to ask "what did they mean by this."

If you only read one section before the kickoff call, read **Section 12 (Open Questions)**. Nothing in Phase 1 should start until those are answered.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Requirements Document (PRD)](#2-product-requirements-document-prd)
3. [Technical Requirements Document (TRD)](#3-technical-requirements-document-trd)
4. [System Architecture](#4-system-architecture)
5. [UI/UX Design](#5-uiux-design)
6. [App & System Flows](#6-app--system-flows)
7. [Backend API Design](#7-backend-api-design)
8. [Database Schema](#8-database-schema)
9. [Security & Data Protection](#9-security--data-protection)
10. [Implementation Plan & Phasing](#10-implementation-plan--phasing)
11. [Risks & Assumptions](#11-risks--assumptions)
12. [Open Questions Requiring Client Decisions](#12-open-questions-requiring-client-decisions)
13. [Appendix](#13-appendix)
14. [API Contracts (Request/Response Examples)](#14-api-contracts-requestresponse-examples)
15. [Full Enum Reference](#15-full-enum-reference)
16. [Environment & Configuration Specification](#16-environment--configuration-specification)
17. [Acceptance Criteria](#17-acceptance-criteria)
18. [Design Tokens (Starter Set)](#18-design-tokens-starter-set)
19. [Seed / Test Data](#19-seed--test-data)

---

## 1. Executive Summary

Greencore replaces paper route cards, radio chatter, and end-of-day guesswork with a single system that tells a driver exactly where to go and in what order, and tells the office exactly what happened.

At its core, Greencore is two connected applications sharing one backend:

- **Greencore Driver** (iOS + Android, React Native) — the app a driver opens at 6am to see their route, drive it, mark drops complete, and log off.
- **Greencore Admin** (responsive web dashboard) — where operations staff build routes, allocate them to drivers, watch live progress, and see what went wrong.

The system is built so that after the initial rollout, **no developer is needed to run day-to-day operations** — routes, drops, drivers, and schedules are all editable from the admin dashboard.

This document proposes building it in four phases (Section 10), starting with a genuinely usable Phase 1 in 8–12 weeks rather than attempting the full spec at once.

---

## 2. Product Requirements Document (PRD)

### 2.1 Problem Statement

The client currently manages driver routes and delivery instructions through static route cards with no digital record of:
- What was actually delivered, when, and by whom
- Why a delivery failed
- Where a driver is during their shift
- How long a driver actually worked

This creates operational blind spots (no proof of delivery, no live visibility, no audit trail) and makes route changes slow and error-prone (every change requires manually reprinting or re-communicating a route card).

### 2.2 Goals

- Give drivers a single, simple app to see their route, complete drops, and log hours.
- Give operations staff a dashboard to build, edit, and allocate routes without developer involvement.
- Capture proof of delivery and failure reasons for every drop.
- Track driver working time accurately and defensibly (with an audit trail on amendments).
- Track live location **only** during an active shift, with clear, defensible privacy boundaries.
- Preserve and digitise the existing route card data as the seed dataset.

### 2.3 Non-Goals (explicitly out of scope for v1)

- Customer-facing tracking (e.g. "your delivery is 10 minutes away" links) — not in the original spec, flag as a possible Phase 5.
- Payroll integration — hours are tracked and exportable, but Greencore does not run payroll.
- Full fleet maintenance/telematics (OBD integration, fuel cards) — vehicle *records* only, not vehicle *telemetry*.
- Customer order intake / e-commerce — Greencore assumes drops already exist as data; it does not generate orders.

### 2.4 Personas

| Persona | Needs |
|---|---|
| **Driver** | Simple, low-friction app usable one-handed, in a cab, with poor signal. Needs to know: where next, what to do there, how am I doing today. |
| **Operations Manager** | Needs to allocate ~20-50 drivers to routes every evening/morning, fast, and be alerted immediately when something goes wrong on the road. |
| **Route Manager** | Needs to edit drop-level detail (instructions, sequence, customer data) without touching driver accounts or payroll. |
| **Payroll/HR Admin** | Needs accurate, tamper-evident hours data, but should not need live location access. |
| **Super Admin (client's IT/ops lead)** | Needs full visibility and the ability to grant/restrict access to everyone else. |

### 2.5 Feature Set by Priority

**Must have (Phase 1–2, "MVP that replaces the paper route card"):**
- Driver auth (invite-only), profile, roles
- Route & drop database, with CSV/Excel import mapped from existing route cards
- Admin route builder, editor, and nightly allocation workflow
- Driver home screen, route view with map + ordered drops
- Drop detail view (instructions, access notes, contact)
- Delivery completion with status + optional photo/signature
- Failed delivery / exception reasons
- Start/End Work with hours tracking
- Push notifications for route allocation and shift reminders

**Should have (Phase 2–3):**
- Live location during active shift only, with admin live map
- Offline mode for route data and delivery completion
- Driver-to-driver chat (visibility-scoped, see Section 9.4) + admin announcements
- Route optimisation (true VRP, not manual sorting)
- Audit log for admin changes
- Role-based admin permissions

**Could have (Phase 3–4):**
- Vehicle management + defect reporting
- Incident/emergency reporting
- Driver schedule / two-week calendar
- Reporting & analytics exports

**Won't have in v1 (see 2.3):**
- Customer tracking links, payroll processing, telematics/OBD

### 2.6 Success Metrics

- 100% of drops have a recorded completion status (delivered/failed) with timestamp — replacing "we think it was delivered."
- Route allocation time drops from [current manual process time — **needs client input**] to under 15 minutes for a full day's routes.
- Zero unexplained gaps in driver hours records (every entry is either raw or a flagged, audited amendment).
- Admin can add, move, or resequence a drop without contacting the developer, from day one of Phase 1.

---

## 3. Technical Requirements Document (TRD)

### 3.1 Recommended Stack

| Layer | Choice | Why |
|---|---|---|
| Driver app | **React Native + Expo** | Matches your existing shipped stack (HollowScan is RN/Expo on iOS + Google Play) — reuse of build pipeline, EAS config, and your own operational knowledge. Single codebase for iOS + Android. |
| Admin dashboard | **Next.js (React, web)** | Shares component/design patterns with the driver app if desired (React Native Web is optional, not required); fast to iterate, easy for the client's team to eventually self-host or extend. |
| Backend API | **FastAPI (Python)** | Matches your HollowScan backend — you already operate this in production. Async support matters here for live-location websocket load. |
| Primary database | **PostgreSQL + PostGIS extension** | Relational integrity for drivers/routes/drops/deliveries, and PostGIS gives you real geospatial queries (nearest drop, geofencing, distance) instead of doing lat/lng math in application code. |
| Realtime (chat, live location) | **WebSockets (FastAPI native) or Supabase Realtime** | You already use Supabase on HollowScan — if hosting Postgres on Supabase, its Realtime channels can carry live location and chat with less custom infrastructure. |
| File storage (POD photos, signatures, defect photos) | **S3-compatible object storage** (AWS S3, Cloudflare R2, or Supabase Storage) | Signed URLs, cheap at scale, keeps binary data out of Postgres. |
| Push notifications | **Firebase Cloud Messaging (FCM) + APNs via FCM** | You already have FCM V1 working in production on HollowScan. |
| Mapping / geocoding / routing | See 3.2 — **not hard-coded**, abstracted behind an internal `RoutingProvider` interface | Client requirement #36: must be swappable later. |
| Route optimisation (VRP) | **Google Route Optimization API (Cloud Fleet Routing) or OR-Tools (self-hosted)** | Distance Matrix/Directions API alone cannot solve multi-stop VRP with constraints — see 11.2 for the risk this carries. |
| Background jobs (nightly allocation, notification sends) | **Celery + Redis, or FastAPI background tasks + a scheduler (APScheduler/cron)** | Needed for route optimisation runs and bulk notification sends. |
| Hosting | **Railway (backend, matching HollowScan) + Vercel (admin dashboard) + Supabase (DB/storage)** | Consistent with your current operational footprint; low DevOps overhead for a small team. |

### 3.2 Mapping Provider Decision

Per the client's own requirement (#36 in the original spec): do not hard-code a single provider. Build a `RoutingProvider` interface with methods:

```
geocode(address) -> {lat, lng, confidence}
distance_matrix(origin, [destinations]) -> [{distance, duration}]
optimize_route(depot, [drops], constraints) -> [ordered drop sequence]
directions(origin, destination) -> polyline
```

Implement one concrete provider first (recommend **Google Maps Platform**, since it has the strongest UK postcode geocoding and an actual route-optimization product), but the interface means switching to Mapbox or HERE later is a provider-class swap, not a rewrite. **Confirm pricing tier with the client before committing** — Directions, Distance Matrix, Geocoding and Route Optimization are billed separately and this can get expensive at 30+ stops × dozens of drivers × daily runs.

### 3.3 Offline-First Strategy

- Driver app pulls the full day's route (drops, instructions, sequence) at shift start and caches it locally (SQLite via `expo-sqlite` or WatermelonDB).
- Delivery completions, failures, and defect reports write to local storage first, tagged with a client-generated UUID and timestamp, then sync via a queue when connectivity returns.
- Conflict resolution rule: **server never overwrites a driver's completed delivery record** — if the same drop somehow has two completion events (rare, e.g. device swap mid-route), the earliest timestamp wins and the second is logged as a duplicate for admin review, not silently dropped.
- The driver UI must show a persistent "Offline — will sync" banner, not a silent failure.

### 3.4 Non-Functional Requirements

- Driver app must be usable on a 3-year-old mid-range Android device with a 4G/patchy connection.
- Admin dashboard must load a day's full route allocation view (assume up to ~50 drivers, ~2,000 drops) in under 3 seconds.
- Live location updates: 15-30 second interval (not continuous streaming) to balance responsiveness against battery drain and API/data cost — **confirm acceptable interval with client**.
- All timestamps stored in UTC, displayed in the driver/admin's local time (Europe/London, accounting for BST).

---

## 4. System Architecture

```mermaid
flowchart TB
    subgraph Clients
        DA["Driver App<br/>(React Native / Expo)<br/>iOS + Android"]
        AD["Admin Dashboard<br/>(Next.js, web)"]
    end

    subgraph Edge
        API["FastAPI Backend<br/>REST + WebSocket"]
    end

    subgraph Core
        AUTH["Auth Service<br/>(JWT + refresh tokens)"]
        ROUTE["Routing Engine<br/>(RoutingProvider interface)"]
        NOTIF["Notification Service"]
        JOBS["Background Jobs<br/>(Celery + Redis)"]
    end

    subgraph Data
        PG[("PostgreSQL + PostGIS")]
        REDIS[("Redis<br/>cache + queue")]
        S3[("Object Storage<br/>POD photos, signatures")]
    end

    subgraph External
        MAPS["Mapping Provider<br/>(Google Maps Platform)"]
        VRP["Route Optimization API<br/>(Cloud Fleet Routing / OR-Tools)"]
        FCM["FCM / APNs<br/>Push Notifications"]
    end

    DA <-->|REST + WS| API
    AD <-->|REST + WS| API
    API --> AUTH
    API --> ROUTE
    API --> NOTIF
    API --> JOBS
    API <--> PG
    API <--> REDIS
    API <--> S3
    ROUTE --> MAPS
    ROUTE --> VRP
    NOTIF --> FCM
    JOBS --> PG
    JOBS --> NOTIF
```

### 4.1 Module Boundaries

- **Auth Service** — driver/admin login, invite-only account creation, JWT issuance, role-based permission checks. No admin permission logic lives in the frontend; every sensitive endpoint re-checks role server-side.
- **Routing Engine** — the only module allowed to call external mapping/VRP APIs. All geocoding, distance calculation, and optimisation requests pass through here so the provider can be swapped without touching business logic elsewhere.
- **Notification Service** — single choke point for all push notifications, so every notification is logged (client requirement: "notifications should be logged so admin can see an important notification was issued").
- **Background Jobs** — nightly route optimisation runs, bulk notification sends, scheduled shift reminders, offline-sync reconciliation sweeps.

### 4.2 Real-Time Data Flows

Two independent real-time channels, kept separate so a chat outage never affects location tracking or vice versa:

1. **Location channel** — driver app pushes a location ping every 15-30s *only while on an active shift*; admin dashboard subscribes to a live map channel scoped to the routes/drivers that admin's role permits.
2. **Chat/notification channel** — driver chat messages and admin announcements, scoped per Section 9.4 visibility rules.

---

## 5. UI/UX Design

### 5.1 Design Principles

1. **One-thumb operable.** Every primary driver action (start work, mark delivered, open next drop) must be reachable with one thumb on a phone mounted in a cab.
2. **No typing where a tap will do.** Failed-delivery reasons, statuses, and checklist items are all selectable, not typed. Notes fields are optional, never required to proceed.
3. **Big, high-contrast, glanceable.** Drivers check this screen in daylight, in a moving vehicle (parked), often with gloves on. Minimum touch target 48dp, minimum body text 16sp.
4. **Never block on network.** Every driver-facing action must work (and visibly queue) when offline.
5. **Admin is dense, driver is sparse.** The admin dashboard is a data-management tool — normal desktop information density is fine there. The driver app is not.

### 5.2 Driver App — Screen Inventory

| Screen | Purpose | Key elements |
|---|---|---|
| Landing | Entry point | Logo, Sign In, Forgot Password, Support contact. No public sign-up (invite-only). |
| Sign In | Auth | Email + password, biometric unlock toggle (Phase 2+) |
| Home | Daily overview | Today's route summary, START WORK button, drop counter, hours-today, nav to Route/Chat/Hours/Schedule |
| Route View | Core screen | Full-screen map, numbered drop pins, route line, current position, "Next Drop" card pinned to bottom |
| Drop Detail | Per-drop info | Customer, account number, address, instructions, access notes, contact, photos (if any), "Navigate" button, "Mark as Delivered" / "Report Issue" |
| Delivery Completion | Proof of delivery | Status selector, optional photo capture, optional signature pad, notes field |
| Failed Delivery | Exception capture | Reason selector (chip list), notes, photo, auto-captured time/location |
| My Hours | Time tracking | Today's timer, this week's daily breakdown, running total |
| Driver Chat | Peer comms | Message list scoped per Section 9.4, safety banner when vehicle-moving state detected |
| My Schedule | Two-week calendar | Working days, day off, allocated route if published, shift start time |
| Incident Report | Safety/emergency | Type selector, short description, photo, location, clear "this is not 999" disclaimer |
| Settings | Account | Profile, notification prefs, location-tracking status indicator, log out |

### 5.3 Admin Dashboard — Screen Inventory

| Section | Purpose |
|---|---|
| Dashboard (home) | Today's snapshot: drivers working/not working, routes allocated/unallocated, deliveries completed/outstanding/failed, live map widget, alerts feed |
| Drivers | CRUD driver profiles, roles, vehicle assignment, active/inactive toggle |
| Routes | View/create/edit routes, drop-level editor, drag-to-resequence, "Optimise Route" action, search |
| Route Import | CSV/Excel upload wizard with column-mapping step |
| Allocation | Nightly/date-based allocation workspace: driver × route grid, conflict warnings, "Send Route Notifications" confirmation modal |
| Live Map | Full-screen live view of on-shift drivers, filterable by route/depot |
| Hours & Timesheets | Per-driver daily/weekly hours, amendment tool with mandatory reason + audit trail |
| Deliveries | Completed/failed/outstanding lists, POD viewer, exception review queue |
| Chat & Announcements | Moderation view of driver chat, compose admin announcement (broadcast scoping) |
| Vehicles | Vehicle records, MOT/insurance/service dates, defect report inbox |
| Reports | Exportable analytics (CSV/Excel/PDF) |
| Audit Log | Searchable log of all admin changes |
| Admin Users & Permissions | Manage admin accounts and role assignments (Super Admin only) |

### 5.4 Design System Notes

- Establish a token set (colour, spacing, type scale) shared conceptually between the RN driver app and the Next.js admin — doesn't need to be one shared library in v1, but should look like one product family.
- Status colours should be consistent everywhere: green = delivered/complete, amber = in progress/partial, red = failed/issue, grey = not started/inactive.
- Greencore brand assets (logo, colours) to be placed in `apps/driver/assets/` and `apps/admin/public/` — confirm exact brand palette and logo files before high-fidelity UI work starts.


---

## 6. App & System Flows

### 6.1 Nightly Route Allocation → Driver Shift (end-to-end)

```mermaid
sequenceDiagram
    participant Admin
    participant Dashboard
    participant API
    participant DB
    participant Push as FCM/APNs
    participant Driver
    participant App as Driver App

    Admin->>Dashboard: Open Allocation for tomorrow's date
    Dashboard->>API: GET available drivers + unallocated routes
    API->>DB: query
    DB-->>API: drivers, routes, conflicts
    API-->>Dashboard: render allocation grid
    Admin->>Dashboard: Assign Route to Driver (x N)
    Dashboard->>API: PATCH assignments (draft)
    Admin->>Dashboard: Confirm "Send Route Notifications to 24 drivers"
    Dashboard->>API: POST /allocations/confirm
    API->>DB: persist assignments, log to audit log
    API->>Push: send "Route Allocated" notification per driver
    Push-->>App: notification delivered
    Driver->>App: Opens app, views tomorrow's route
    Note over Driver,App: Next morning
    Driver->>App: Presses START WORK
    App->>API: POST /shifts/start (location permission check)
    API->>DB: create shift record, start hours timer
    App->>App: cache today's route + drops locally (offline-first)
```

### 6.2 Delivery Completion (including offline path)

```mermaid
flowchart TD
    A[Driver opens Drop Detail] --> B{Delivery outcome}
    B -->|Success| C[Mark as Delivered]
    B -->|Problem| D[Report Issue / Failed Delivery]
    C --> E[Optional: photo / signature]
    D --> F[Select reason + optional photo/notes]
    E --> G{Online?}
    F --> G
    G -->|Yes| H[POST /deliveries — sync immediately]
    G -->|No| I[Write to local queue with UUID + timestamp]
    I --> J["Show 'Offline — will sync' banner"]
    J --> K[Connectivity restored]
    K --> L[Background sync flushes queue to API]
    H --> M[Drop counter updates: Drops 18/32]
    L --> M
    M --> N[Admin dashboard reflects update in near real-time]
```

### 6.3 Live Location Tracking — Start/Stop Boundary

```mermaid
stateDiagram-v2
    [*] --> Off: App installed, not on shift
    Off --> RequestingPermission: Driver presses START WORK
    RequestingPermission --> Off: Permission denied
    RequestingPermission --> Tracking: Permission granted
    Tracking --> Tracking: Ping every 15-30s while shift active
    Tracking --> Off: Driver presses END WORK
    Tracking --> Off: Shift auto-closed (e.g. max hours exceeded, admin override)
    note right of Tracking
        Location is NEVER collected
        outside an active shift.
        Admin cannot see location
        once a shift has ended,
        unless a separately disclosed
        historical-tracking policy exists.
    end note
```

### 6.4 Admin Route Editing With Conflict Warnings

```mermaid
flowchart TD
    A[Admin selects drop] --> B[Edit: move / resequence / reassign route]
    B --> C{System validation}
    C -->|Vehicle/licence mismatch| D[Warn: driver's vehicle class cannot serve this drop]
    C -->|Route capacity exceeded| E[Warn: route now exceeds configured drop/time limit]
    C -->|Duplicate drop detected| F[Warn: this account/postcode already exists on another active route today]
    C -->|Time window conflict| G[Warn: delivery window overlaps existing commitment]
    C -->|No conflicts| H[Save change]
    D --> I[Admin confirms override or cancels]
    E --> I
    F --> I
    G --> I
    I -->|Confirm| H
    H --> J[Write audit log entry: who / what / before / after / when]
    H --> K[If route already allocated + notified: trigger 'Route Changed' push]
```


---

## 7. Backend API Design

REST + JSON over HTTPS, plus two WebSocket channels (location, chat). Auth via short-lived JWT access token + refresh token. Every endpoint below enforces role checks server-side (never trust the client's role claim alone — re-verify against the DB on each request).

### 7.1 Auth

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/auth/login` | Email + password → access + refresh token |
| POST | `/auth/refresh` | Refresh token → new access token |
| POST | `/auth/logout` | Invalidate refresh token |
| POST | `/auth/invite` | Admin-only: creates invite, driver sets password on first login |
| POST | `/auth/password-reset/request` | |
| POST | `/auth/password-reset/confirm` | |

### 7.2 Drivers

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/drivers` | Admin: list, filterable by role/status/depot |
| POST | `/drivers` | Admin: create (invite flow) |
| GET | `/drivers/{id}` | |
| PATCH | `/drivers/{id}` | |
| POST | `/drivers/{id}/deactivate` | Soft-delete; revokes active sessions |
| GET | `/drivers/{id}/hours` | Weekly/daily hours summary |
| GET | `/drivers/me` | Driver's own profile (self-service) |

### 7.3 Routes & Drops

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/routes` | List/search (postcode, account number, customer, route ID) |
| POST | `/routes` | Create route |
| GET | `/routes/{id}` | Includes ordered drop list |
| PATCH | `/routes/{id}` | Edit route metadata (depot, start/end point) |
| POST | `/routes/{id}/drops` | Add drop to route |
| PATCH | `/routes/{id}/drops/{dropId}` | Edit drop (instructions, sequence, address, etc.) |
| DELETE | `/routes/{id}/drops/{dropId}` | Remove drop |
| POST | `/routes/{id}/drops/{dropId}/move` | Move drop to another route |
| POST | `/routes/{id}/optimise` | Trigger VRP optimisation; returns proposed sequence for admin approval |
| POST | `/routes/import` | Step 1: upload CSV/Excel, returns parsed columns |
| POST | `/routes/import/map` | Step 2: confirm column mapping, commit import |

### 7.4 Allocation

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/allocations?date=` | Grid of drivers × routes for a given date |
| POST | `/allocations` | Assign route to driver for a date (draft) |
| POST | `/allocations/confirm` | Confirm + trigger notification send, writes audit log |

### 7.5 Shifts, Hours & Location

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/shifts/start` | Begins shift, starts hours timer, opens location channel |
| POST | `/shifts/end` | Ends shift, closes location channel, finalises hours entry |
| POST | `/shifts/{id}/break/start` | |
| POST | `/shifts/{id}/break/end` | |
| PATCH | `/shifts/{id}/amend` | Admin-only, requires reason, writes audit log |
| WS | `/ws/location` | Driver publishes location while shift active; admin subscribes scoped to permitted routes |

### 7.6 Deliveries

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/deliveries` | Record completion/failure; accepts client-generated UUID for offline dedupe |
| GET | `/deliveries?route_id=&date=` | Admin view |
| POST | `/deliveries/{id}/proof` | Upload photo/signature (multipart → S3, returns signed URL reference) |

### 7.7 Chat & Notifications

| Method | Endpoint | Notes |
|---|---|---|
| WS | `/ws/chat` | Scoped per visibility rules (Section 9.4) |
| POST | `/announcements` | Admin: broadcast to all/route/depot/vehicle-category |
| GET | `/notifications/log` | Admin: audit of sent notifications |

### 7.8 Vehicles, Incidents, Audit

| Method | Endpoint | Notes |
|---|---|---|
| GET/POST | `/vehicles` | |
| POST | `/vehicles/{id}/defects` | Driver-submitted defect report |
| POST | `/incidents` | Driver-submitted incident report |
| GET | `/audit-log` | Filterable, admin-only, read-only |


---

## 8. Database Schema

PostgreSQL with PostGIS enabled for `geography`/`geometry` columns on any lat/lng field.

```mermaid
erDiagram
    DRIVER ||--o{ SHIFT : works
    DRIVER ||--o{ DRIVER_VEHICLE_ASSIGNMENT : assigned
    VEHICLE ||--o{ DRIVER_VEHICLE_ASSIGNMENT : assigned
    DRIVER ||--o{ ALLOCATION : receives
    ROUTE ||--o{ ALLOCATION : allocated_via
    ROUTE ||--o{ DROP : contains
    DROP ||--o{ DELIVERY : results_in
    SHIFT ||--o{ DELIVERY : recorded_during
    SHIFT ||--o{ LOCATION_PING : generates
    DRIVER ||--o{ CHAT_MESSAGE : sends
    DRIVER ||--o{ INCIDENT_REPORT : files
    DRIVER ||--o{ DEFECT_REPORT : files
    VEHICLE ||--o{ DEFECT_REPORT : concerns
    ADMIN_USER ||--o{ AUDIT_LOG_ENTRY : creates
    ADMIN_USER ||--o{ ANNOUNCEMENT : sends

    DRIVER {
        uuid id PK
        string full_name
        string email
        string phone
        string photo_url
        enum role "van, 7_5t, class1, class2"
        string licence_number
        enum status "active, inactive"
        uuid depot_id FK
        timestamptz created_at
    }

    VEHICLE {
        uuid id PK
        string registration
        enum vehicle_type
        string weight_class
        date mot_due
        date insurance_due
        date service_due
        enum status "active, in_repair, retired"
    }

    ROUTE {
        uuid id PK
        string route_name "e.g. LONDON 01"
        uuid depot_id FK
        geography start_point
        geography end_point
        enum status "active, inactive"
        int max_drops "nullable, admin-configurable capacity limit — powers route_capacity_exceeded check"
        timestamptz created_at
    }

    DROP {
        uuid id PK
        uuid route_id FK
        int sequence
        string account_number
        string customer_name
        string address
        string postcode
        geography location
        text delivery_instructions
        text access_instructions
        text tray_instructions
        jsonb opening_hours
        string contact_phone
        boolean fixed_position
        uuid must_precede_drop_id FK "nullable, sequencing constraint"
        enum required_vehicle_class "nullable, e.g. class1_hgv — used by vehicle_class_mismatch check"
        enum status "not_started, en_route, arrived, delivered, partial, failed, closed, no_access, other"
    }

    ALLOCATION {
        uuid id PK
        date shift_date
        uuid driver_id FK
        uuid route_id FK
        uuid vehicle_id FK
        time planned_start
        enum status "draft, confirmed, notified"
        timestamptz confirmed_at
    }

    SHIFT {
        uuid id PK
        uuid driver_id FK
        uuid allocation_id FK
        timestamptz start_time
        timestamptz end_time
        jsonb breaks "array of start/end pairs"
        interval total_working_time
        boolean amended
        text amendment_reason
        uuid amended_by FK "nullable, admin_user"
    }

    DELIVERY {
        uuid id PK
        uuid drop_id FK
        uuid shift_id FK
        uuid driver_id FK
        enum status
        timestamptz completed_at
        geography completed_location
        string proof_photo_url
        string signature_url
        text failure_reason
        text notes
        uuid client_uuid "for offline dedupe"
    }

    LOCATION_PING {
        uuid id PK
        uuid shift_id FK
        geography location
        timestamptz recorded_at
    }

    CHAT_MESSAGE {
        uuid id PK
        uuid sender_driver_id FK
        text content
        string photo_url
        enum scope "route, depot, global"
        timestamptz created_at
        boolean reported
    }

    ANNOUNCEMENT {
        uuid id PK
        uuid sent_by FK
        text content
        enum target_type "all, driver, route, depot, vehicle_category"
        jsonb target_ids
        timestamptz sent_at
    }

    INCIDENT_REPORT {
        uuid id PK
        uuid driver_id FK
        enum incident_type
        text description
        string photo_url
        geography location
        timestamptz reported_at
    }

    DEFECT_REPORT {
        uuid id PK
        uuid driver_id FK
        uuid vehicle_id FK
        enum defect_type
        text description
        string photo_url
        timestamptz reported_at
        enum status "open, acknowledged, resolved"
    }

    ADMIN_USER {
        uuid id PK
        string full_name
        string email
        enum permission_role "super_admin, ops_manager, route_manager, payroll_hr, read_only"
    }

    AUDIT_LOG_ENTRY {
        uuid id PK
        uuid admin_user_id FK
        string entity_type
        uuid entity_id
        jsonb before_value
        jsonb after_value
        timestamptz created_at
    }
```

### 8.1 Notes on the schema

- `DROP.location` uses PostGIS `geography(Point, 4326)` — enables real distance queries (nearest drop, drops within X metres) rather than storing lat/lng as plain floats.
- `DROP.must_precede_drop_id` and `fixed_position` implement the client's requirement that admins can pin drops or force ordering constraints even when the VRP optimiser is used.
- `DROP.required_vehicle_class` and `ROUTE.max_drops` are what the `vehicle_class_mismatch` and `route_capacity_exceeded` conflict warnings (Section 15.7, checked in Section 17.4) actually validate against — these two fields were missing from an earlier draft of this schema and are required before the route-editing conflict checks can be implemented at all.
- `LOCATION_PING` rows are only ever inserted while a `SHIFT` has no `end_time` — enforce this at the application layer, not just by convention, and set a retention policy (Section 9) to auto-purge old pings.
- `DELIVERY.client_uuid` is generated on-device at the moment of completion (even offline) so the sync process can safely dedupe if a completion is retried after reconnecting.
- Every table touched by an admin action needs a corresponding `AUDIT_LOG_ENTRY` write — implement this as a single reusable service function, not repeated per-endpoint, to guarantee nothing is missed.


---

## 9. Security & Data Protection

### 9.1 Authentication & Access Control

- Invite-only account creation for drivers — no public sign-up endpoint exists at all (removes an entire class of account-abuse risk).
- Passwords hashed with bcrypt/argon2, never stored or logged in plaintext.
- JWT access tokens short-lived (15 min); refresh tokens long-lived but revocable server-side (needed for "deactivate account when driver leaves").
- All admin endpoints re-verify `permission_role` server-side against current DB state on every request — never trust a cached/client-supplied role.
- Rate limiting on `/auth/login` and `/auth/password-reset/*` to prevent brute force and credential stuffing.
- Optional Phase 2+: SMS/email 2FA, biometric app unlock (local device biometric, not server-side biometric storage).

### 9.2 Transport & Storage Security

- TLS 1.2+ enforced on all API traffic; no plaintext HTTP endpoints, including internal service-to-service calls.
- POD photos/signatures stored in S3-compatible storage with private buckets; access only via short-lived signed URLs, never public bucket URLs.
- Database encryption at rest (standard on Supabase/RDS/managed Postgres — confirm with hosting provider).
- Secrets (API keys, DB credentials) in environment variables / a secrets manager, never committed to source control. **Note for you specifically:** you've already had one FCM credential rotation forced by a GitHub secret exposure on HollowScan — bake a pre-commit secret scanner (e.g. `gitleaks`) into this repo from day one so it doesn't happen twice.

### 9.3 Location Data — Specific Controls

This is the highest-sensitivity data category in the app and needs controls beyond "we'll be careful":

- Location collection is technically impossible to trigger outside an active shift — enforced by only accepting `/ws/location` pings tied to a `shift_id` with no `end_time`, not just by the app choosing not to send them.
- Configurable retention period for `LOCATION_PING` data (e.g. 90 days), after which a scheduled job purges it. **Client must decide this number** — see Section 12.
- Admin live-map access scoped by `permission_role` — Payroll/HR role, per the client's own admin-permissions section, should **not** see live location by default.
- A documented lawful basis for processing employee location data must exist before launch (likely "legitimate interests" or contractual necessity under UK GDPR) — **this is a legal decision, not a technical one; recommend the client's employment lawyer or DPO sign off before Phase 2 (live tracking) ships.**
- Drivers can see, in-app, whether tracking is currently active (client requirement, already in original spec — implemented as a persistent status indicator, not just a settings toggle).

### 9.4 Driver-to-Driver Visibility (client's added requirement)

The client's instruction was: drivers should see other drivers' info and routes, but not location or other sensitive info. Implemented as:

| Data | Visible to other drivers? |
|---|---|
| Driver name, on which route today | Yes |
| Route drop count / progress (e.g. "18/32") | Yes, if this is genuinely needed — **recommend confirming with client whether this is necessary at all; see pushback in the summary above** |
| Full drop-level detail (customer name, account number, delivery instructions) on **another driver's** route | **No — not exposed**, even though the client's instruction is ambiguous on this point. Recommend restricting "see other drivers' routes" to route name/progress only, not drop-level customer data, unless the client explicitly confirms otherwise in writing. |
| Live GPS location | No, never, for peer drivers |
| Contact/phone number | No, unless explicitly required for chat coordination — chat is pseudonymous by display name only |
| Hours worked, pay-relevant data | No |

This is flagged as an **open question for the client** (Section 12) rather than a silent implementation decision, because "routes" is ambiguous between "which route are they on" and "the full contents of that route."

Before implementing any version of this, ask the client what operational problem it's solving (e.g. shift coverage, drivers coordinating on the road) rather than building "full visibility" by default — the answer changes whether this is a name/progress display or something closer to shared customer data, and the latter is a real exposure worth pushing back on if the underlying need doesn't actually require it.

### 9.5 Audit & Accountability

- Every admin write to driver/route/hours data produces an `AUDIT_LOG_ENTRY` (who, what, before, after, when) — read-only, no admin role (including Super Admin) can delete audit entries.
- Hours amendments require a mandatory reason field before saving — enforced at the API layer, not just the UI.

### 9.6 Application-Level Hardening Checklist

- Input validation and parameterised queries everywhere (ORM-enforced) — no raw SQL string interpolation, eliminates SQL injection class of bugs.
- File upload validation: enforce content-type and size limits on POD photos/signatures/defect photos server-side, not just client-side; scan or at minimum re-encode uploaded images to strip embedded metadata/EXIF (which can contain GPS data you don't want retained twice).
- CSV/Excel import (route data) treated as untrusted input — validate every row, reject malformed rows with a clear error report rather than partial silent imports.
- CORS locked to known admin dashboard origins; driver app auth via bearer token, not cookies, avoiding CSRF surface entirely on mobile.
- Dependency scanning (Dependabot/Snyk) on both the FastAPI backend and the RN/Next.js frontends.
- Before launch: a third-party penetration test scoped to auth, location data access, and the admin permission boundaries specifically — this is the app's highest-risk surface and worth paying for a real test rather than relying on internal review alone.


---

## 10. Implementation Plan & Phasing

Realistic estimates assume one focused full-stack developer (you), with the client providing route card data and timely decisions on Section 12. Ranges reflect the swing between "client decisions come fast" and "client decisions are slow."

**Before presenting the phase breakdown below, state the Phase 1 range out loud as 8-12 weeks, not less.** The week-by-week estimates in this section are a build-time floor assuming no delays; verbally quoting the upper end protects against the client anchoring on the fastest possible number and treating any slippage as a missed deadline.

### Phase 0 — Foundations (1-2 weeks)
- Confirm all Section 12 open questions
- Repo setup, CI/CD, environments (dev/staging/prod), secret scanning
- Auth service, base DB schema, admin permission model
- Brand assets integrated (logo, palette)

### Phase 1 — Core System (6-9 weeks build time; quote 8-12 weeks to the client)
- Driver auth, profile, roles
- Route/Drop database + CSV/Excel import + column-mapping wizard
- Admin: route builder/editor, search, nightly allocation workflow + confirmation flow
- Driver: home screen, route view (map + ordered drops), drop detail
- Basic push notifications (route allocated, shift reminder)
- **Exit criteria:** admin can build a route from imported data and a driver can view it on their phone, end to end, with zero developer intervention after go-live for a standard route change.

### Phase 2 — Driver Operations (6-8 weeks)
- Start/End Work + hours tracking + weekly summary
- Delivery completion + proof of delivery (photo/signature)
- Failed delivery / exception reporting
- Live location (shift-scoped) + admin live map
- Offline mode (route caching, offline delivery completion, sync)
- **Exit criteria:** a full day's route can be driven and completed with the phone in airplane mode for stretches, syncing cleanly on reconnect.

### Phase 3 — Communication & Management (5-7 weeks)
- Driver chat (scoped per 9.4) + admin announcements + moderation
- Incident reporting
- Vehicle management + defect reporting
- Audit log (admin-facing)
- Admin role-based permissions (beyond a single admin account)
- Excel/CSV/PDF exports

### Phase 4 — Advanced Automation (ongoing, post-launch)
- True VRP route optimisation (vs. manually-ordered import)
- Automated exception alerts, workload balancing
- Analytics dashboard
- Multi-depot / multi-tenant support if the business expands (Section 12 Q: is this needed at all in v1?)

### 10.1 What "done" looks like for a sellable v1 (client can run it unaided)

> Admin: create driver → import/build route → allocate route → confirm & notify.
> Driver: receive notification → view route → start work → drive optimally-ordered drops → open each drop → read instructions → navigate → complete or fail delivery → finish route → end work → see hours.
> Admin afterward: see completed/failed deliveries → see hours → review the day → make the next day's changes without calling the developer.

That loop, uninterrupted, is Phase 1 + Phase 2. Everything in Phase 3-4 makes it better, not functional.

---

## 11. Risks & Assumptions

### 11.1 Assumptions

- The client will supply real route card data (or representative samples) before Phase 1 import work begins — without this, the import wizard is being built and tested against guesswork.
- Drivers have company-issued or personal smartphones capable of running a modern RN app (iOS 15+ / Android 10+ recommended baseline — confirm).
- The client has, or will obtain, a mapping provider account (Google Maps Platform or equivalent) with billing set up — this is a client cost, not bundled into your dev fee.

### 11.2 Key Risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| **Route optimisation is harder than it looks** | VRP with fixed positions, vehicle constraints, and time windows is a genuinely hard problem; a naive "nearest neighbour" implementation will produce visibly bad routes drivers won't trust | Use a proven VRP API/library (Section 3.1) rather than building an optimiser from scratch; treat Phase 4 optimisation as its own mini-project, not a bolt-on |
| **Mapping/VRP API costs scale with usage** | 30+ stops × many drivers × daily = real ongoing cost | Get a cost estimate from the client's expected volume before committing to a provider; build the `RoutingProvider` abstraction so cost isn't a lock-in risk |
| **Location tracking legal exposure** | Employee GPS tracking without proper basis/notice is a genuine UK employment-law and GDPR risk for the client | Recommend client legal/DPO sign-off before Phase 2 ships; document the lawful basis in writing as part of delivery |
| **Offline sync edge cases** | Duplicate/lost delivery records erode trust in the whole system fast | Client-generated UUIDs + earliest-timestamp-wins rule (Section 3.3); test explicitly with real connectivity drop scenarios, not just simulated |
| **Scope creep from a very long spec** | The original document is comprehensive to the point of enterprise-TMS scope; treating all of it as "v1" risks an endless build with no shippable milestone | Hold the line on Phase 1/2 exit criteria (Section 10.1) as the actual deliverable for the deposit/kickoff conversation |
| **Driver adoption** | If the app is slower or more annoying than the paper route card, drivers will resist it | Prioritise the "one-thumb, no typing" UX principles (Section 5.1) from the first usable build, and pilot with a small group of drivers before full rollout |

---

## 12. Open Questions Requiring Client Decisions

These need answers before or during Phase 0 — several of them change the database schema or architecture if answered differently, so getting them late is expensive.

1. Which mapping/routing provider, and who is paying for and holding that account?
2. What does "drivers see other drivers' routes" actually mean — route name/progress only, or full drop-level detail? (Recommend: name/progress only — see 9.4.)
3. What is the location data retention period, and who (by role) is allowed to view historical (not live) location?
4. Single depot or multiple depots in v1? Any near-term plan to run this for more than one transport company (multi-tenant)?
5. iOS and Android both required for launch, or Android-first (client's own drivers' devices — worth surveying)?
6. What is the actual current manual process time for route allocation, to set a real success-metric baseline (Section 2.6)?
7. Live-location ping interval — is 15-30s acceptable, or does the client want tighter/looser for cost reasons?
8. Who has final say on "must precede" / "fixed position" drop overrides — is that Route Manager level or does it need Super Admin?
9. What's the expected data volume (number of drivers, routes, drops/day) at launch and in 12 months — sizes the DB/infra decisions now rather than later.
10. Does the client have an existing employment-law/DPO contact who needs to review the location-tracking policy before Phase 2, or does Josh need to flag this as a gap for them to fill?
11. Proof of delivery: is a signature legally/contractually required, or is a photo sufficient? (Affects whether a signature-capture component is built at all.)
12. What exact route card format/spreadsheet structure exists today — needed to finalise the CSV import column-mapping wizard (client to supply sample files).

---

## 13. Appendix

### 13.1 Glossary

- **VRP (Vehicle Routing Problem):** the class of optimisation problem behind "find the best order to visit N stops given vehicle and time constraints" — harder than simple point-to-point directions.
- **POD (Proof of Delivery):** the photo/signature/notes captured confirming a drop was completed.
- **Offline-first:** an architecture where the app is fully usable without connectivity, syncing changes when a connection becomes available, rather than requiring connectivity to function.
- **PostGIS:** a PostgreSQL extension adding native geospatial data types and queries.

### 13.2 Suggested Repository Structure

```
greencore/
├── apps/
│   ├── driver/           # React Native / Expo app
│   └── admin/            # Next.js dashboard
├── services/
│   └── api/               # FastAPI backend
├── packages/
│   └── shared-types/       # Shared TypeScript types (drop, route, delivery, etc.)
├── infra/                 # IaC / deployment config
└── docs/
    └── GREENCORE_DOCUMENTATION.md   # this file
```

### 13.3 Source Document

This documentation was produced from the founder-supplied specification (route/driver management app requirements, delivered as a text document) plus the additional verbal requirement that drivers should see other drivers' routes but not their location or other sensitive information. Section 9.4 documents how that requirement was interpreted and flags where it needs client confirmation.

---

## 14. API Contracts (Request/Response Examples)

> **Before an agent builds against these:** the field values below (enums, defaults) reflect the spec as written. Anywhere Section 12 is still unanswered, the shapes are correct but a specific value (e.g. which `failure_reason` list, ping interval) should be treated as a default to confirm, not a client-approved final decision. All requests require `Authorization: Bearer <access_token>` unless noted.

### 14.1 Auth

**POST `/auth/login`**
```json
// Request
{ "email": "driver@example.com", "password": "string" }

// Response 200
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 900,
  "user": {
    "id": "b7e1...uuid",
    "type": "driver",
    "full_name": "John Smith",
    "role": "class1"
  }
}

// Response 401
{ "error": "invalid_credentials", "message": "Email or password is incorrect." }
```

**POST `/auth/refresh`**
```json
// Request
{ "refresh_token": "eyJ..." }

// Response 200
{ "access_token": "eyJ...", "expires_in": 900 }
```

**POST `/auth/invite`** (admin, `ops_manager` or `super_admin` only)
```json
// Request
{ "email": "newdriver@example.com", "full_name": "Jane Doe", "role": "van", "depot_id": "d4a2...uuid" }

// Response 201
{ "invite_id": "inv_01H...", "status": "pending", "expires_at": "2026-09-06T00:00:00Z" }
```

### 14.2 Drivers

**GET `/drivers?status=active&role=class1&depot_id=`**
```json
// Response 200
{
  "data": [
    {
      "id": "b7e1...uuid",
      "full_name": "John Smith",
      "email": "john@example.com",
      "phone": "+447700900000",
      "photo_url": "https://.../photo.jpg",
      "role": "class1",
      "licence_number": "SMITH901234JD9AB",
      "status": "active",
      "depot_id": "d4a2...uuid",
      "vehicle_id": "v991...uuid",
      "created_at": "2026-01-15T08:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 50,
  "total": 1
}
```

**PATCH `/drivers/{id}`**
```json
// Request (partial update — only send changed fields)
{ "role": "class2", "status": "active" }

// Response 200 — full updated driver object, same shape as GET above
```

**POST `/drivers/{id}/deactivate`**
```json
// Request
{ "reason": "Left the company 2026-08-30" }

// Response 200
{ "id": "b7e1...uuid", "status": "inactive", "deactivated_at": "2026-08-30T09:00:00Z" }
// Side effect: all refresh tokens for this driver are revoked immediately.
```

### 14.3 Routes & Drops

**GET `/routes/{id}`**
```json
// Response 200
{
  "id": "r001...uuid",
  "route_name": "LONDON 01",
  "depot_id": "d4a2...uuid",
  "start_point": { "lat": 51.5074, "lng": -0.1278 },
  "end_point": { "lat": 51.5074, "lng": -0.1278 },
  "status": "active",
  "drops": [
    {
      "id": "dr001...uuid",
      "sequence": 1,
      "account_number": "123456",
      "customer_name": "ABC Shop",
      "address": "12 Example Road, London",
      "postcode": "AB1 2CD",
      "location": { "lat": 51.51, "lng": -0.12 },
      "delivery_instructions": "Deliver trays to rear of shop",
      "access_instructions": "Loading bay behind building, ring bell",
      "tray_instructions": "Stack 2 high max",
      "opening_hours": { "mon_fri": "08:00-18:00", "sat": "09:00-13:00", "sun": "closed" },
      "contact_phone": "+442012345678",
      "fixed_position": false,
      "must_precede_drop_id": null,
      "required_vehicle_class": null,
      "status": "not_started"
    }
  ]
}
```

**POST `/routes/{id}/drops`**
```json
// Request
{
  "account_number": "654321",
  "customer_name": "New Customer Ltd",
  "address": "5 High Street",
  "postcode": "EF3 4GH",
  "delivery_instructions": "Front door delivery",
  "sequence": 5
}

// Response 201 — full drop object, same shape as above, with geocoded `location` populated server-side from `postcode`/`address`
```

**POST `/routes/{id}/drops/{dropId}/move`**
```json
// Request
{ "target_route_id": "r007...uuid", "sequence": 3 }

// Response 200
{ "moved": true, "warnings": ["vehicle_class_mismatch"] }
// warnings is an array of enum values from Section 15.6 — empty array if no conflicts.
// A non-empty warnings array does NOT block the move; the admin dashboard shows it and requires an explicit confirm click before this endpoint is called with `"force": true`.
```

**POST `/routes/{id}/optimise`**
```json
// Request
{ "respect_fixed_positions": true, "vehicle_id": "v991...uuid" }

// Response 200 — proposed order only, NOT auto-applied
{
  "proposed_sequence": ["dr003...", "dr001...", "dr005..."],
  "estimated_distance_km": 41.2,
  "estimated_duration_minutes": 96,
  "provider": "google_route_optimization"
}
// Admin must call PATCH on the route to accept this sequence — optimisation never silently overwrites the live route.
```

**POST `/routes/import`**
```json
// Request: multipart/form-data, file field named "file" (.csv or .xlsx)

// Response 200
{
  "import_id": "imp_01H...",
  "detected_columns": ["Account No", "Customer", "Postcode", "Notes", "Route"],
  "row_count": 342,
  "sample_rows": [ { "Account No": "123456", "Customer": "ABC Shop", "Postcode": "AB1 2CD" } ]
}
```

**POST `/routes/import/map`**
```json
// Request
{
  "import_id": "imp_01H...",
  "column_mapping": {
    "Account No": "account_number",
    "Customer": "customer_name",
    "Postcode": "postcode",
    "Notes": "delivery_instructions",
    "Route": "route_name"
  }
}

// Response 200
{ "imported": 340, "failed": 2, "errors": [ { "row": 88, "reason": "invalid_postcode" }, { "row": 210, "reason": "missing_customer_name" } ] }
// Import is row-level partial-success by design — never all-or-nothing, per Section 9.6.
```

### 14.4 Allocation

**GET `/allocations?date=2026-08-31`**
```json
// Response 200
{
  "date": "2026-08-31",
  "drivers": [ { "id": "b7e1...uuid", "full_name": "John Smith", "role": "class1", "already_scheduled": false } ],
  "routes": [ { "id": "r001...uuid", "route_name": "LONDON 01", "drop_count": 32, "allocated": false } ]
}
```

**POST `/allocations/confirm`**
```json
// Request
{
  "date": "2026-08-31",
  "assignments": [
    { "driver_id": "b7e1...uuid", "route_id": "r001...uuid", "vehicle_id": "v991...uuid", "planned_start": "06:00" }
  ]
}

// Response 200
{ "confirmed": 24, "notifications_sent": 24, "audit_log_entry_id": "aud_01H..." }
```

### 14.5 Shifts & Location

**POST `/shifts/start`**
```json
// Request
{ "allocation_id": "alloc_01H...", "location_permission_granted": true }

// Response 201
{ "shift_id": "sh_01H...", "start_time": "2026-08-31T06:02:14Z", "status": "active" }

// Response 403 (permission not granted)
{ "error": "location_permission_required", "message": "Location permission must be granted to start a shift." }
```

**WS `/ws/location`** (driver → server, sent every 15-30s while `shift.status == active`)
```json
{ "shift_id": "sh_01H...", "lat": 51.512, "lng": -0.121, "recorded_at": "2026-08-31T06:15:00Z" }
```

**POST `/shifts/{id}/amend`** (admin only)
```json
// Request
{ "start_time": "2026-08-31T06:00:00Z", "reason": "Driver forgot to press Start Work; confirmed via depot sign-in sheet" }

// Response 200 — reason is mandatory; a 400 is returned if omitted
{ "shift_id": "sh_01H...", "amended": true, "amendment_reason": "...", "amended_by": "admin_01H..." }
```

### 14.6 Deliveries

**POST `/deliveries`**
```json
// Request
{
  "client_uuid": "c3f8b2a0-...-generated-on-device",
  "drop_id": "dr001...uuid",
  "shift_id": "sh_01H...",
  "status": "delivered",
  "completed_at": "2026-08-31T07:22:10Z",
  "completed_location": { "lat": 51.51, "lng": -0.12 },
  "notes": null
}

// Response 201
{ "id": "del_01H...", "status": "delivered", "duplicate_of": null }

// If client_uuid already exists server-side (offline retry):
// Response 200
{ "id": "del_01H...", "status": "delivered", "duplicate_of": null, "note": "already recorded, no new row created" }
```

**POST `/deliveries/{id}/proof`**
```json
// Request: multipart/form-data — fields: "photo" and/or "signature"

// Response 200
{ "proof_photo_url": "https://.../signed-url...", "signature_url": null }
```

### 14.7 Chat & Announcements

**WS `/ws/chat`** (scoped per Section 9.4 — server enforces scope, not client)
```json
// Outbound (driver → server)
{ "content": "M25 closed near junction 10.", "scope": "route" }

// Inbound (server → subscribed clients)
{
  "id": "msg_01H...",
  "sender_driver_id": "b7e1...uuid",
  "sender_name": "John Smith",
  "content": "M25 closed near junction 10.",
  "scope": "route",
  "created_at": "2026-08-31T07:30:00Z"
}
```

**POST `/announcements`** (admin)
```json
// Request
{ "content": "M25 delays expected tomorrow morning.", "target_type": "route", "target_ids": ["r001...uuid"] }

// Response 201
{ "id": "ann_01H...", "sent_at": "2026-08-31T18:00:00Z", "recipients_notified": 3 }
```

### 14.8 Standard Error Shape

All error responses use this shape, so an agent building error handling only needs one parser:
```json
{ "error": "machine_readable_code", "message": "Human-readable explanation.", "field_errors": { "postcode": "Invalid UK postcode format" } }
```
`field_errors` is present only on 422 validation failures; omitted otherwise.

---

## 15. Full Enum Reference

Every enum referenced elsewhere in this document, spelled out completely, so nothing is left to inference.

**15.1 `driver.role`**
`van`, `7_5t`, `class1`, `class2` — extensible; adding a new role is a data change (new row in a `driver_roles` lookup table if roles need to be admin-manageable) not a code change if implemented as a lookup table rather than a hard enum. **Recommend a lookup table over a native DB enum for this specific field**, since the original spec explicitly says roles should be expandable later.

**15.2 `driver.status`**
`active`, `inactive`

**15.3 `vehicle.status`**
`active`, `in_repair`, `retired`

**15.4 `vehicle.vehicle_type`**
`van`, `7_5t`, `class1_hgv`, `class2_hgv` — mirrors driver roles for eligibility matching.

**15.5 `route.status`**
`active`, `inactive`

**15.6 `drop.status`**
`not_started`, `en_route`, `arrived`, `delivered`, `partial`, `failed`, `closed` (customer closed), `no_access`, `other`

**15.7 Route-edit conflict warning codes** (returned in `warnings[]`, Section 14.3)
`vehicle_class_mismatch`, `route_capacity_exceeded`, `duplicate_drop`, `time_window_conflict`

**15.8 `delivery.status`**
Same value set as `drop.status` (15.6) — a delivery record's status is what gets written back onto the drop.

**15.9 `delivery.failure_reason`** (required when `status` is `failed`, `partial`, `closed`, `no_access`, or `other`)
`shop_closed`, `no_access`, `loading_bay_unavailable`, `road_closed`, `customer_refused`, `wrong_address`, `vehicle_issue`, `product_unavailable`, `other`

**15.10 `allocation.status`**
`draft`, `confirmed`, `notified`

**15.11 `chat_message.scope`**
`route` (drivers on the same route today), `depot` (drivers based at the same depot), `global` (all active drivers) — server resolves scope membership at send time from current shift/allocation data, not a stored group.

**15.12 `announcement.target_type`**
`all`, `driver`, `route`, `depot`, `vehicle_category`

**15.13 `admin_user.permission_role`**
`super_admin`, `ops_manager`, `route_manager`, `payroll_hr`, `read_only` — exact permission matrix (which role can hit which endpoint) needs to be finalised as a literal table before Phase 3; Section 5.3's screen inventory maps roughly to this but isn't yet an enforceable permission matrix.

**15.14 `incident_report.incident_type`**
`accident`, `road_closure`, `vehicle_breakdown`, `serious_delay`, `dangerous_location`, `delivery_problem`, `emergency`

**15.15 `defect_report.defect_type`**
`tyre`, `warning_light`, `brakes`, `lights`, `damage`, `other`

**15.16 `defect_report.status`**
`open`, `acknowledged`, `resolved`

**15.17 `notification.type`** (for the notification log, Section 4.1)
`route_allocated`, `shift_reminder`, `route_changed`, `admin_announcement`

---

## 16. Environment & Configuration Specification

> Values below are starting recommendations, not final — anything marked `[CONFIRM]` depends on a Section 12 answer.

### 16.1 Repository & Package Naming

- Repo: `greencore` (monorepo, structure per Section 13.2)
- Driver app package/bundle ID: `com.greencore.driver` `[CONFIRM — client may want their own reverse-domain, e.g. com.clientname.greencore]`
- Admin dashboard: no bundle ID (web), deployed as `admin.greencore.app` or client's own subdomain `[CONFIRM]`
- API service name: `greencore-api`

### 16.2 Environment Variables (backend, `services/api/.env`)

```
# Database
DATABASE_URL=postgresql://user:pass@host:5432/greencore
REDIS_URL=redis://host:6379

# Auth
JWT_SECRET=<generate, never commit>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Object storage
S3_BUCKET=greencore-uploads
S3_REGION=eu-west-2
S3_ACCESS_KEY_ID=<secret>
S3_SECRET_ACCESS_KEY=<secret>

# Mapping / routing provider
MAPS_PROVIDER=google  # [CONFIRM per Section 12 Q1]
GOOGLE_MAPS_API_KEY=<secret>
ROUTE_OPTIMIZATION_PROVIDER=google_cloud_fleet_routing  # [CONFIRM]

# Push notifications
FCM_SERVICE_ACCOUNT_JSON=<secret, mount as file not env var>

# Location tracking
LOCATION_PING_INTERVAL_SECONDS=20  # [CONFIRM per Section 12 Q7]
LOCATION_DATA_RETENTION_DAYS=90    # [CONFIRM per Section 12 Q3]

# App environment
ENVIRONMENT=development  # development | staging | production
LOG_LEVEL=info
```

### 16.3 Environment Variables (driver app, `apps/driver/.env`)

```
EXPO_PUBLIC_API_BASE_URL=https://api.greencore.app
EXPO_PUBLIC_WS_BASE_URL=wss://api.greencore.app
EXPO_PUBLIC_SENTRY_DSN=<optional, error tracking>
```

### 16.4 Environment Variables (admin dashboard, `apps/admin/.env.local`)

```
NEXT_PUBLIC_API_BASE_URL=https://api.greencore.app
NEXT_PUBLIC_WS_BASE_URL=wss://api.greencore.app
NEXTAUTH_SECRET=<generate, never commit>
```

### 16.5 Minimum Versions

- Node.js: 20 LTS
- Python: 3.12 (FastAPI backend)
- PostgreSQL: 15+ (PostGIS 3.4+)
- React Native: latest stable via Expo SDK 52+ (confirm against current SDK at build start, this drifts)
- iOS deployment target: 15.0+
- Android minSdkVersion: 29 (Android 10)

### 16.6 Secret Handling (ties to Section 9.2)

- `gitleaks` pre-commit hook enabled from the first commit, per your own HollowScan incident.
- No secret listed above is ever committed, including in `.env.example` files — those files list variable *names* only, with placeholder values like `<secret>`.

---

## 17. Acceptance Criteria

Given/When/Then criteria for the features most likely to be built wrong if left to inference. This is not exhaustive for every screen — it targets the places where "looks done" and "is done" diverge.

### 17.1 Route Allocation & Notification
- **Given** an admin has assigned routes to 24 drivers in draft state, **when** they click "Send Route Notifications," **then** the system shows a confirmation modal stating the exact recipient count before any notification is sent.
- **Given** the admin confirms, **when** notifications are dispatched, **then** an audit log entry and a notification log entry are created for every recipient, even if the push itself fails to deliver (delivery failure is logged, not silently dropped).

### 17.2 Delivery Completion — Offline
- **Given** a driver is offline, **when** they mark a drop as delivered, **then** the completion is saved locally with a `client_uuid` and the drop counter updates immediately in the UI without waiting for network.
- **Given** that same offline completion, **when** connectivity returns, **then** it syncs automatically without any user action, and the "Offline — will sync" banner clears only after a successful sync confirmation from the server, not optimistically.
- **Given** a `client_uuid` that already exists server-side (duplicate sync attempt), **when** the sync runs, **then** no second delivery row is created and the response indicates `duplicate_of: null` with the original record's data (Section 14.6).

### 17.3 Live Location Boundary
- **Given** a driver has not pressed "Start Work," **when** the app is open in the foreground or background, **then** zero location pings are sent — this must be true even if OS-level location permission is "always allow."
- **Given** a driver presses "End Work," **when** the shift closes, **then** the location WebSocket connection is closed server-side within the same request, not left open until the client disconnects.
- **Given** an admin with `payroll_hr` permission role, **when** they open the Live Map, **then** they see no driver location data (Section 9.3) — the endpoint returns 403, not an empty map (an empty map is indistinguishable from "no one's working" and hides the permission boundary from testing).

### 17.4 Route Edit Conflict Warnings
- **Given** an admin moves a drop to a route served by a Van-class vehicle when the drop requires Class 1 access, **when** they attempt to save, **then** the system returns `vehicle_class_mismatch` in `warnings[]` and does not apply the change until the admin explicitly re-submits with `force: true`.
- **Given** any successful route edit (with or without an overridden warning), **when** the change is saved, **then** exactly one `AUDIT_LOG_ENTRY` is created recording the before and after state of the changed fields only, not the entire route object.

### 17.5 Driver Visibility Scope (Section 9.4)
- **Given** two drivers on different routes, **when** Driver A views the driver list or chat participant list, **then** Driver A sees Driver B's name and current route name/progress only — no customer names, account numbers, or delivery instructions from Driver B's route are retrievable through any driver-facing endpoint.
- **Given** Driver A is not on shift, **when** Driver B looks at the live map (if a driver-facing version exists) or driver list, **then** Driver A's location is never present, regardless of Driver A's shift history that day.

### 17.6 CSV/Excel Import
- **Given** an uploaded route file with 342 rows where 2 rows have invalid postcodes, **when** the import is committed, **then** 340 rows import successfully and 2 are reported individually with row number and reason (Section 14.3) — the entire import never fails because of a subset of bad rows.

---

## 18. Design Tokens (Starter Set)

**These are placeholder values, not the client's brand.** Swap immediately once Greencore's actual logo and palette are supplied (per your note that you'll add these to the public folder). Their purpose here is to stop an agent from inventing an unrelated visual identity in the meantime.

```
// Color — semantic, not brand (map brand colors onto these once supplied)
--color-primary: #1B5E3A        /* placeholder "green" per company name — replace with actual brand green */
--color-primary-dark: #123D26
--color-surface: #FFFFFF
--color-surface-alt: #F4F6F5
--color-text-primary: #10221A
--color-text-secondary: #5B6B63
--color-border: #DDE3E0

// Status colors — fixed regardless of brand, per Section 5.4 consistency rule
--color-status-success: #1E8E3E   /* delivered / complete */
--color-status-warning: #F2A900   /* in progress / partial */
--color-status-danger:  #D32F2F   /* failed / issue */
--color-status-neutral: #8A8F8C   /* not started / inactive */

// Spacing scale (px, 4pt base grid)
--space-1: 4px
--space-2: 8px
--space-3: 12px
--space-4: 16px
--space-5: 24px
--space-6: 32px
--space-7: 48px

// Type scale — driver app minimum sizes per Section 5.1
--font-size-body: 16px
--font-size-body-driver-min: 16px   /* never go below this in driver-facing UI */
--font-size-heading-sm: 20px
--font-size-heading-md: 24px
--font-size-heading-lg: 32px

// Touch targets
--touch-target-min: 48px            /* per Section 5.1, non-negotiable on driver app */

// Radius
--radius-sm: 6px
--radius-md: 12px
--radius-full: 999px
```

---

## 19. Seed / Test Data

Minimal seed set for local development and automated tests — enough to exercise the full Phase 1/2 loop end to end without real client data.

```json
{
  "depots": [
    { "id": "d4a2b1c0-0000-0000-0000-000000000001", "name": "North London Depot" }
  ],
  "admin_users": [
    { "id": "adm-0000-0000-0000-000000000001", "full_name": "Test Admin", "email": "admin@test.greencore.app", "permission_role": "super_admin" }
  ],
  "vehicles": [
    { "id": "v991-0000-0000-0000-000000000001", "registration": "AB12 CDE", "vehicle_type": "class1_hgv", "status": "active" }
  ],
  "drivers": [
    { "id": "b7e1-0000-0000-0000-000000000001", "full_name": "Test Driver One", "email": "driver1@test.greencore.app", "role": "class1", "status": "active", "depot_id": "d4a2b1c0-0000-0000-0000-000000000001", "vehicle_id": "v991-0000-0000-0000-000000000001" }
  ],
  "routes": [
    {
      "id": "r001-0000-0000-0000-000000000001",
      "route_name": "TEST ROUTE 01",
      "depot_id": "d4a2b1c0-0000-0000-0000-000000000001",
      "status": "active",
      "drops": [
        { "id": "dr01-0000-0000-0000-000000000001", "sequence": 1, "account_number": "TEST001", "customer_name": "Test Customer A", "postcode": "AB1 2CD", "delivery_instructions": "Front door", "status": "not_started" },
        { "id": "dr02-0000-0000-0000-000000000002", "sequence": 2, "account_number": "TEST002", "customer_name": "Test Customer B", "postcode": "EF3 4GH", "delivery_instructions": "Rear loading bay, ring bell", "status": "not_started" }
      ]
    }
  ]
}
```

Use this as a fixtures file (`fixtures/seed.json`) loaded by a `make seed` / `scripts/seed.py` script, not hand-typed into migrations — keeps it re-runnable and safe to reset in CI.

---


*End of document.*