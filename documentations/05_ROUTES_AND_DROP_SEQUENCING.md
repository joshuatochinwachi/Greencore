# 05 — Route & Drop Sequencing Engine & Conflict Verification

## 1. Executive Summary

In commercial distribution, a route is not merely an unordered bag of stops; it is a **strictly ordered sequence** of deliveries subject to physical truck constraints, customer delivery time windows, and loading bay physical access limits.

Greencore's Route & Drop Engine manages:
1. **Dynamic Linked Sequence Numbering:** Adding, removing, or shifting stops automatically recalculates contiguous sequence integers (1..N).
2. **Pre-Flight Conflict Verification Engine:** Intercepts route transfer operations to detect vehicle class incompatibilities and route capacity overflows before changes are persisted.
3. **Audited Force Override (Section 17.4):** Allows dispatch managers to override warnings when emergency field operational decisions supersede static constraints.

---

## 2. Dynamic Sequence Renumbering Mechanics

When a drop is moved from sequence position $i$ to position $j$, all intermediate stops must shift predictably without leaving gaps or creating duplicate sequence numbers:

```mermaid
flowchart TD
    subgraph Scenario["Drop Transfer: Stop C (Seq 3) moved to Sequence 1"]
        Original["Initial Sequence:<br/>[1: Stop A] → [2: Stop B] → [3: Stop C] → [4: Stop D]"]
        Remove["Extract Stop C:<br/>[1: Stop A] → [2: Stop B] → [3: Stop D] (Gap closed)"]
        Insert["Shift and Insert at Pos 1:<br/>[1: Stop C] → [2: Stop A] → [3: Stop B] → [4: Stop D]"]
        Original --> Remove --> Insert
    end
```

### 2.1 Resequencing Logic in `services/api/app/services/route.py`:
```python
def resequence_route(db: Session, route_id: uuid.UUID) -> None:
    """Ensures drop sequence numbers are strictly 1..N with zero gaps."""
    drops = (
        db.query(Drop)
        .filter(Drop.route_id == route_id)
        .order_by(Drop.sequence.asc(), Drop.id.asc())
        .all()
    )
    for idx, drop in enumerate(drops, start=1):
        if drop.sequence != idx:
            drop.sequence = idx
    db.flush()
```

---

## 3. Pre-Flight Conflict Detection Engine

Before any drop transfer (`POST /routes/drops/{id}/move`) is saved to the database, it passes through the **Pre-Flight Conflict Detection Pipeline**:

```mermaid
flowchart TD
    StartMove["Move Request Received:<br/>POST /routes/drops/{drop_id}/move<br/>{ target_route_id, sequence, force }"]
    
    CheckCap{"Target Route Drop Count<br/>>= route.max_drops?"}
    WarnCap["Flag Warning:<br/>route_capacity_exceeded"]
    
    CheckVeh{"Drop Required Vehicle Class<br/>Matches Target Route Vehicle?"}
    WarnVeh["Flag Warning:<br/>vehicle_class_mismatch"]
    
    CheckDup{"Customer Account Already<br/>Present on Target Route?"}
    WarnDup["Flag Warning:<br/>duplicate_drop"]
    
    Evaluate{"Any Warnings Flagged?"}
    CheckForce{"Was force: true<br/>supplied in request?"}
    
    Reject["Return 200 OK<br/>{ moved: false, warnings: [...] }<br/>NO DATABASE CHANGES"]
    Apply["Execute Reassignment & Resequence<br/>Record AUDIT_LOG_ENTRY with override note<br/>Return 200 OK { moved: true }"]

    StartMove --> CheckCap
    CheckCap -- Yes --> WarnCap --> CheckVeh
    CheckCap -- No --> CheckVeh
    
    CheckVeh -- Incompatible --> WarnVeh --> CheckDup
    CheckVeh -- Compatible --> CheckDup
    
    CheckDup -- Duplicate Found --> WarnDup --> Evaluate
    CheckDup -- Unique --> Evaluate
    
    Evaluate -- Warnings Exist --> CheckForce
    Evaluate -- Clean (No Warnings) --> Apply
    
    CheckForce -- force == false --> Reject
    CheckForce -- force == true --> Apply
```

---

## 4. Conflict Rules Specification (Section 15.7)

### 4.1 `vehicle_class_mismatch`
- **Condition:** Drop specifies `required_vehicle_class = 'class1_hgv'` (e.g. standard loading bay height or 26-pallet order), but target route is assigned a `van` or `7_5t` vehicle.
- **Risk Avoided:** Dispatching a small van to collect pallets it cannot physically hold or access.

### 4.2 `route_capacity_exceeded`
- **Condition:** Target route has `max_drops = 30`, and currently holds 30 drops. Transferring an additional stop would raise the total to 31.
- **Risk Avoided:** Driver exceeding legal EU Drivers' Hours working time limits (Regulation EC 561/2006).

### 4.3 `duplicate_drop`
- **Condition:** Target route already contains a drop for the exact same customer account number on that delivery day.
- **Risk Avoided:** Multiple drivers showing up at the same customer back-to-back.

---

## 5. End-to-End Conflict Flow Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Admin as Operations Manager (Web Dashboard)
    participant UI as Next.js Routes Page
    participant API as FastAPI Backend
    participant DB as PostgreSQL

    Admin->>UI: Selects Drop #4 -> Move to Route "LONDON EAST 02"
    UI->>API: POST /routes/drops/{drop_id}/move { target_route_id, sequence: 1, force: false }
    API->>DB: Inspect target route vehicle & capacity
    DB-->>API: Target route vehicle is Van, Drop requires Class 1 HGV
    API-->>UI: 200 OK { moved: false, warnings: ['vehicle_class_mismatch'] }
    
    UI->>UI: Display Amber Warning Modal:<br/>"Vehicle Class Mismatch Detected"
    Admin->>UI: Checks "Acknowledge and Force Override" checkbox
    Admin->>UI: Clicks "Confirm Override & Move"
    
    UI->>API: POST /routes/drops/{drop_id}/move { target_route_id, sequence: 1, force: true }
    API->>DB: Transfer drop to target_route_id
    API->>DB: Resequence drops (1..N)
    API->>DB: INSERT into audit_log_entries (entity: 'drop', action: 'move_override', warnings_overridden)
    DB-->>API: Transaction Committed
    API-->>UI: 200 OK { moved: true, warnings: [] }
    UI->>UI: Refresh drop view with success notification
```

---

## 6. Interview & Conference Talking Points

> **Why return HTTP 200 with `{ moved: false, warnings: [...] }` instead of HTTP 400 Bad Request on conflict?**  
> *"In REST design, a 4xx error indicates a malformed or illegal client request. In field logistics dispatch, a conflict warning is not an error — it is business domain feedback. The request was syntactically perfect, but the business engine flagged an operational hazard. Returning 200 with structured warning codes allows the frontend to render an informative modal allowing human supervisors to review and force-override with an audit trail."*

> **How does Greencore guarantee continuous drop sequences without race conditions?**  
> *"Drop resequencing runs inside an atomic PostgreSQL database transaction with `FOR UPDATE` row-level locks on the route. If two dispatchers attempt to move drops within the same route simultaneously, the transactions serialize, guaranteeing continuous sequence numbering without duplicate positions."*
