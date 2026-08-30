# GREENCORE
## Transport Driver & Route Management Platform
### Proposal — August 2026

**Prepared by:** Joshua Nwachukwu

---

## The Problem

Right now, routes and delivery instructions live on paper route cards. That means:

- No record of what was actually delivered, when, or by whom
- No visibility into why a delivery failed
- No live picture of where drivers are during a shift
- No accurate, defensible record of hours worked
- Every route change means manually reprinting or re-communicating a card

Greencore replaces all of this with one connected system.

## What Greencore Does

Two connected apps, one backend:

- **Greencore Driver** (iOS + Android) — a driver opens it at the start of a shift, sees their route in the right order with full delivery instructions, marks each drop complete or flags a problem, and logs their hours.
- **Greencore Admin** (web dashboard) — operations staff build and edit routes, allocate them to drivers every evening or morning, watch live progress during the day, and see exactly what happened afterward.

After the initial build, **your team runs this without needing a developer** — adding drivers, editing routes, and allocating work is all done from the dashboard.

## What You Get

- Every drop has a recorded outcome — delivered, failed, or an exception — with a timestamp and, where needed, a photo or signature as proof.
- Route allocation goes from a manual daily task to a few minutes of work on a dashboard, with a confirmation step before drivers are notified.
- Accurate hours tracking, with any correction logged and traceable — no silent edits.
- Live location visibility while a driver is on shift, and only while on shift — this is a deliberate privacy boundary, not a limitation.
- A searchable digital record of every route, replacing the paper route cards, imported directly from your existing data.

## How It's Built

Built as a modern mobile app (React Native, so it runs natively on both iOS and Android from one codebase) and a web dashboard, backed by a proper database with real mapping and route-optimisation technology — not a spreadsheet with a map bolted on.

Full technical detail — architecture, database design, API specification, and security approach — is available in the accompanying technical documentation, `GREENCORE_DOCUMENTATION.md`, for your team's own record or for any developer who needs it.

## Delivery Plan

| Phase | What's delivered | Estimate |
|---|---|---|
| **Foundations** | Environment setup, brand integration, core data model | 1-2 weeks |
| **Phase 1 — Core System** | Route database, import from your existing route cards, admin route builder, driver app with route view and drop detail, route allocation and notifications | **8-12 weeks** |
| **Phase 2 — Driver Operations** | Hours tracking, delivery completion and proof, failed-delivery reporting, live location, offline mode | 6-8 weeks |
| **Phase 3 — Communication & Management** | Driver chat, admin announcements, incident reporting, vehicle records, audit log, admin permissions | 5-7 weeks |
| **Phase 4 — Advanced Automation** | Full route optimisation, automated alerts, analytics, and further features as the business grows | Ongoing, post-launch |

**Phase 1 alone delivers a working system your team can run day-to-day** — building a route from your data, allocating it, and a driver completing it end-to-end on their phone.

## What We Need From You Before Kickoff

A short list of decisions and materials, so nothing gets built on a guess:

- Confirmation of a mapping/routing provider account (we recommend Google Maps Platform)
- Sample route card data or spreadsheets, in whatever format you currently use
- Confirmation of how much visibility drivers should have into each other's routes
- A decision on how long location data should be kept, and who should be able to see historical (not live) location
- Confirmation on whether one depot or multiple depots need to be supported
- Sign-off from your legal/HR contact on the location-tracking policy, given this involves tracking employees' location during work hours

These are covered in full in Section 12 of the technical documentation.

## Next Steps

1. Review this proposal and the accompanying technical documentation.
2. Confirm the open decisions above.
3. Agree scope and deposit for Phase 1.
4. Kickoff.

---

*Full technical specification, database schema, API design, and security detail available on request in [GREENCORE_DOCUMENTATION](./GREENCORE_DOCUMENTATION.md).*
