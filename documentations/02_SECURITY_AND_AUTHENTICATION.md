# 02 — Security, Cryptography & Access Control Architecture

## 1. Executive Summary

Enterprise logistics applications handle sensitive commercial intelligence: customer addresses, door access codes, high-value cargo routes, and real-time personnel GPS coordinates.

Greencore enforces a **zero-trust, invite-only security model** built on modern cryptographic standards. Public self-registration is eliminated by design. Authentication utilizes memory-hard **Argon2id** password hashing, short-lived **JSON Web Tokens (JWT)** with cryptographic rotation, and **server-side role re-verification** on every privileged request.

---

## 2. Core Cryptographic Architecture

```mermaid
flowchart TD
    subgraph PasswordHandling["Password Hashing Engine"]
        PlainPwd["Plaintext Password<br/>(Entered by User)"]
        Argon2id["Argon2id Hasher<br/>• Memory-hard (m=65536, t=3, p=4)<br/>• Cryptographic Salt per User<br/>• Side-channel & GPU resistant"]
        PasswordHash[("Stored Argon2id Hash<br/>in admin_users / drivers")]
        PlainPwd --> Argon2id --> PasswordHash
    end

    subgraph TokenEngine["Dual-Token Architecture"]
        LoginRequest["POST /auth/login"]
        TokenGen["Token Generator"]
        AccessToken["Access Token (JWT)<br/>• Valid for 15 Minutes<br/>• Contains user ID, role, type<br/>• Signed with HMAC-SHA256"]
        RefreshToken["Refresh Token<br/>• Cryptographically Random Hex<br/>• Stored as SHA-256 Hash in DB<br/>• Valid for 7 Days (Revocable)"]
        
        LoginRequest --> TokenGen
        TokenGen --> AccessToken
        TokenGen --> RefreshToken
    end

    subgraph Revocation["Server-Side Revocation Gate"]
        Deactivate["Driver Deactivated<br/>or Admin Suspended"]
        RevokeDB["DELETE FROM refresh_tokens<br/>WHERE user_id = :id"]
        InstantLockout["Next Token Refresh FAILS<br/>Active sessions terminated"]
        
        Deactivate --> RevokeDB --> InstantLockout
    end
```

---

## 3. The Dual-Token Lifecycle (Access vs. Refresh)

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client (Web / Mobile)
    participant API as FastAPI Auth Router
    participant DB as Supabase PostgreSQL

    Note over Client,API: Phase 1: Authentication
    Client->>API: POST /auth/login { email, password }
    API->>DB: Query user by email
    DB-->>API: User record + stored password_hash
    API->>API: Verify password with Argon2id
    API->>API: Generate 15-min Access Token (JWT)
    API->>API: Generate 7-day Refresh Token (random hex)
    API->>DB: INSERT into refresh_tokens (token_hash, expires_at, user_id)
    API-->>Client: 200 OK { access_token, refresh_token, expires_in: 900, user }

    Note over Client,API: Phase 2: Normal API Requests (15-minute window)
    Client->>API: GET /routes (Authorization: Bearer <access_token>)
    API->>API: Decode JWT & verify HMAC-SHA256 signature
    API-->>Client: 200 OK (Data returned without hitting refresh table)

    Note over Client,API: Phase 3: Token Expiration & Silent Rotation
    Client->>API: Request fails with 401 Unauthorized (JWT Expired)
    Client->>API: POST /auth/refresh { refresh_token }
    API->>DB: SELECT FROM refresh_tokens WHERE token_hash = :hash AND revoked = false
    alt Token Valid & Unexpired
        API->>API: Issue new 15-min Access Token
        API-->>Client: 200 OK { access_token, expires_in: 900 }
    else Token Revoked / User Deactivated
        API-->>Client: 401 Unauthorized (Session Expired — Force Logout)
    end
```

---

## 4. Role-Based Access Control (RBAC) Matrix

To prevent privilege escalation, all admin endpoints enforce **server-side role re-verification**. The role declared in a JWT is never trusted blindly; the endpoint middleware queries the live database record to ensure permissions have not been downgraded or revoked mid-session.

| Feature / Resource | `super_admin` | `operations_manager` | `route_manager` | `payroll_hr` | `read_only` | `driver` (Field) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Manage Admin Users & Roles** | ✅ Full | ❌ Denied | ❌ Denied | ❌ Denied | ❌ Denied | ❌ Denied |
| **Driver Fleet Management (CRUD)** | ✅ Full | ✅ Full | ❌ Denied | 👁️ View only | 👁️ View only | ❌ Denied |
| **Driver Account Deactivation** | ✅ Full | ✅ Full | ❌ Denied | ❌ Denied | ❌ Denied | ❌ Denied |
| **Route & Drop Sequence Editing** | ✅ Full | ✅ Full | ✅ Full | ❌ Denied | 👁️ View only | ❌ Denied |
| **Route Conflict Override (`force`)** | ✅ Full | ✅ Full | ✅ Full | ❌ Denied | ❌ Denied | ❌ Denied |
| **Nightly Route Allocation Matrix** | ✅ Full | ✅ Full | ❌ Denied | ❌ Denied | 👁️ View only | ❌ Denied |
| **Confirm & Broadcast Notifications**| ✅ Full | ✅ Full | ❌ Denied | ❌ Denied | ❌ Denied | ❌ Denied |
| **CSV Route Card Import** | ✅ Full | ✅ Full | ✅ Full | ❌ Denied | ❌ Denied | ❌ Denied |
| **View Live GPS Location Map** | ✅ Full | ✅ Full | ✅ Full | ❌ **403 Forbidden** | ❌ Denied | ❌ Denied |
| **Driver Time Tracking & Timesheets** | ✅ Full | ✅ Full | ❌ Denied | ✅ Full | 👁️ View only | 👁️ Own only |
| **System Audit Log Inspection** | ✅ Full | 👁️ View only | ❌ Denied | 👁️ View only | 👁️ View only | ❌ Denied |

> **Privacy Hardening Note (Section 17.3):** Admins with the `payroll_hr` role are explicitly returned an HTTP 403 Forbidden on live location endpoints, rather than an empty map. An empty map is indistinguishable from "no active drivers" and conceals the privacy boundary from automated verification.

---

## 5. Invite-Only Onboarding & Credential Creation

In enterprise fleet operations, open public signups represent an unacceptable attack surface. Greencore implements **closed, invite-only onboarding** for both administrative staff and field drivers:

```mermaid
sequenceDiagram
    autonumber
    participant SuperAdmin as Super Admin (Dashboard)
    participant API as FastAPI Backend
    participant DB as PostgreSQL Database
    participant Driver as New Driver / Staff Member

    SuperAdmin->>API: POST /auth/invite { email, full_name, role, depot_id }
    API->>API: Verify caller has super_admin or ops_manager role
    API->>API: Generate 128-bit cryptographic invite token
    API->>DB: INSERT into invite_tokens (token_hash, email, role, expires_at: 72h)
    API-->>SuperAdmin: 201 Created { invite_id, expires_at }
    
    Note over API,Driver: Secure delivery via corporate email or SMS
    Driver->>API: POST /auth/register { invite_token, password, phone }
    API->>DB: SELECT FROM invite_tokens WHERE token_hash = :hash AND is_used = false
    
    alt Token Valid & Unexpired
        API->>API: Validate password complexity (min 8 chars, mixed case, symbols)
        API->>API: Hash password with Argon2id
        API->>DB: INSERT into drivers (or admin_users)
        API->>DB: UPDATE invite_tokens SET is_used = true
        API-->>Driver: 201 Created { driver_id, status: "active" }
    else Token Expired or Reused
        API-->>Driver: 400 Bad Request (Invalid or expired invitation)
    end
```

---

## 6. Immediate Session Revocation on Deactivation

When an employee departs or a contractor is suspended, simply setting `status = 'inactive'` in the database is insufficient if active JWT access tokens or refresh tokens remain circulating.

Greencore implements **atomic session termination**:
1. Admin triggers `POST /drivers/{id}/deactivate` with a mandatory reason.
2. The database updates `status = 'inactive'`.
3. In the exact same database transaction, all rows in `refresh_tokens` belonging to that user ID are deleted.
4. When the user's mobile app or browser attempts to refresh its 15-minute token, the server rejects the request with HTTP 401 Unauthorized, forcibly logging out the client immediately.
5. The action is permanently recorded in `audit_log_entries`.

---

## 7. Conference & Interview Talking Points

> **Why Argon2id over bcrypt or PBKDF2?**  
> *"Argon2id was the winner of the Password Hashing Competition (PHC). Unlike bcrypt, which is susceptible to FPGA and ASIC acceleration attacks due to low memory footprint, Argon2id is memory-hard. It requires configurable RAM allocations to compute, neutralizing GPU-accelerated dictionary attacks."*

> **How does Greencore balance offline field requirements with token revocation?**  
> *"We use short-lived 15-minute JWT access tokens paired with server-revocable 7-day refresh tokens. This ensures low-latency verification on active routes without hitting the database for every single drop update, while capping the rogue token window at 15 minutes if a driver's credentials are revoked."*
