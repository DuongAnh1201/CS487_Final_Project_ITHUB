# Use Cases – IT Inventory Tracker

## 1. Actors

| Actor | Type | Description |
|---|---|---|
| **IT Administrator** | Primary | Manages all assets, licenses, users, and locations. Has full access. |
| **IT Technician** | Primary | Handles day-to-day asset operations: check-in/out, status updates, repairs. |
| **Employee** | Primary | Receives assets; can view assets assigned to them and request equipment. |
| **Manager / Auditor** | Primary | Views reports and audit history; read-only access. |
| **System Scheduler** | Secondary | Time-based trigger for automated checks (e.g., license expiry alerts). |

---

## 2. Use Case Summary

| ID | Use Case | Primary Actor(s) | Priority |
|---|---|---|---|
| UC-01 | Log In | All human actors | P1 |
| UC-02 | Add Asset | IT Admin | P1 |
| UC-03 | Update Asset | IT Admin, IT Technician | P1 |
| UC-04 | Retire Asset | IT Admin | P2 |
| UC-05 | Check Out Asset | IT Technician | P1 |
| UC-06 | Check In Asset | IT Technician | P1 |
| UC-07 | Search / Filter Assets | All human actors | P1 |
| UC-08 | Manage Software License | IT Admin | P2 |
| UC-09 | Receive License Expiry Alert | System Scheduler → IT Admin | P3 |
| UC-10 | Manage Locations | IT Admin | P2 |
| UC-11 | View My Assets | Employee | P2 |
| UC-12 | Request Equipment | Employee | P3 |
| UC-13 | View Audit History | IT Admin, Manager / Auditor | P2 |
| UC-14 | Generate Report | IT Admin, Manager / Auditor | P2 |

---

## 3. Use Case Descriptions

### UC-01: Log In
- **Actor:** Any human actor
- **Precondition:** User has an account.
- **Main Flow:**
  1. User enters username and password.
  2. System validates credentials.
  3. System loads the menu based on the user's role.
- **Alternate Flow:**
  - 2a. Invalid credentials → system shows an error; after 5 failed attempts the account is locked.
- **Postcondition:** User is authenticated with role-based permissions.

---

### UC-02: Add Asset
- **Actor:** IT Administrator
- **Precondition:** Admin is logged in.
- **Main Flow:**
  1. Admin selects "Add Asset."
  2. Admin chooses asset type (Laptop, Monitor, Network Device, Peripheral, etc.).
  3. System displays fields for that type.
  4. Admin enters details: serial number, model, manufacturer, purchase date, cost, warranty end, location.
  5. System validates input and checks that the serial number is unique.
  6. System creates the asset with status **Available** and generates an asset tag.
  7. System records the action in the audit log.
- **Alternate Flows:**
  - 5a. Duplicate serial number → system rejects and shows the existing asset.
  - 5b. Missing required field → system highlights the field and asks for input.
- **Postcondition:** New asset exists with status **Available**.

---

### UC-03: Update Asset
- **Actor:** IT Administrator, IT Technician
- **Precondition:** Asset exists and is not retired.
- **Main Flow:**
  1. User searches for the asset (UC-07).
  2. User edits allowed fields (location, condition, notes, status such as **In Repair**).
  3. System validates and saves changes.
  4. System records old and new values in the audit log.
- **Alternate Flow:**
  - 2a. Technician attempts to edit a restricted field (e.g., cost) → system denies.
- **Postcondition:** Asset is updated; change is logged.

---

### UC-04: Retire Asset
- **Actor:** IT Administrator
- **Precondition:** Asset exists and is not currently checked out.
- **Main Flow:**
  1. Admin selects an asset and chooses "Retire."
  2. Admin selects a reason (End of Life, Lost, Damaged, Sold, Recycled).
  3. System sets status to **Retired** and records the retirement date.
  4. System records the action in the audit log.
- **Alternate Flow:**
  - 1a. Asset is checked out → system blocks retirement until it is checked in (UC-06).
- **Postcondition:** Asset is retired and excluded from active inventory; its history remains.

---

### UC-05: Check Out Asset
- **Actor:** IT Technician
- **Precondition:** Asset status is **Available**; employee exists.
- **Main Flow:**
  1. Technician searches for the asset.
  2. Technician selects the employee receiving it.
  3. Technician sets an optional expected return date.
  4. System creates an **Assignment** record (asset, employee, date, technician).
  5. System changes asset status to **Checked Out**.
  6. System records the action in the audit log.
- **Alternate Flows:**
  - 1a. Asset is not Available → system shows the current status and holder.
  - 2a. Employee is inactive → system blocks the check-out.
- **Postcondition:** Asset is assigned to the employee.

---

### UC-06: Check In Asset
- **Actor:** IT Technician
- **Precondition:** Asset status is **Checked Out**.
- **Main Flow:**
  1. Technician scans or searches for the asset.
  2. System shows the current assignment.
  3. Technician records the asset's condition (Good, Damaged, Missing Parts).
  4. System closes the assignment with a return date.
  5. System sets status to **Available**.
  6. System records the action in the audit log.
- **Alternate Flow:**
  - 3a. Condition is Damaged → system sets status to **In Repair** instead of Available.
- **Postcondition:** Assignment is closed; asset is back in inventory or in repair.

---

### UC-07: Search / Filter Assets
- **Actor:** All human actors (results limited by role)
- **Main Flow:**
  1. User enters a keyword and/or filters (type, status, location, assigned employee).
  2. System returns matching assets.
  3. User selects an asset to view details.
- **Alternate Flow:**
  - 2a. No results → system shows "No assets found."
- **Postcondition:** None (read-only).

---

### UC-08: Manage Software License
- **Actor:** IT Administrator
- **Main Flow:**
  1. Admin adds or edits a license: product name, vendor, license key, total seats, expiration date.
  2. Admin assigns or unassigns seats to employees or devices.
  3. System updates the count of used and available seats.
  4. System records the action in the audit log.
- **Alternate Flow:**
  - 2a. No seats available → system blocks the assignment and shows the seat count.
- **Postcondition:** License data and seat usage are current.

---

### UC-09: Receive License Expiry Alert
- **Actor:** System Scheduler (trigger), IT Administrator (receiver)
- **Main Flow:**
  1. Scheduler runs a daily check.
  2. System finds licenses expiring within a configured window (default 30 days).
  3. System notifies the IT Administrator.
- **Postcondition:** Admin is aware of upcoming expirations.
- **Design note:** Candidate for the **Observer** pattern.

---

### UC-10: Manage Locations
- **Actor:** IT Administrator
- **Main Flow:**
  1. Admin adds, edits, or deactivates a location (building, room, storage area).
  2. System saves the change.
- **Alternate Flow:**
  - 1a. Location still holds assets → system blocks deactivation.
- **Postcondition:** Location list is updated.

---

### UC-11: View My Assets
- **Actor:** Employee
- **Main Flow:**
  1. Employee opens "My Assets."
  2. System lists the assets and license seats currently assigned to them.
- **Postcondition:** None (read-only).

---

### UC-12: Request Equipment
- **Actor:** Employee
- **Main Flow:**
  1. Employee submits a request (asset type, reason, needed-by date).
  2. System creates a request with status **Pending** and notifies the IT staff.
  3. IT staff approves or rejects the request; if approved, it continues to UC-05.
- **Postcondition:** Request is recorded and tracked.

---

### UC-13: View Audit History
- **Actor:** IT Administrator, Manager / Auditor
- **Main Flow:**
  1. User selects an asset, an employee, or a date range.
  2. System shows the log entries: timestamp, user, action, old value, new value.
- **Postcondition:** None (read-only). Audit entries cannot be edited or deleted.

---

### UC-14: Generate Report
- **Actor:** IT Administrator, Manager / Auditor
- **Main Flow:**
  1. User selects a report type:
     - Inventory by status
     - Assets by location
     - Assets per employee
     - Expiring licenses
     - Warranty expiring
  2. User sets filters or a date range.
  3. System generates the report and displays it or exports it (CSV).
- **Postcondition:** Report is produced.
- **Design note:** Candidate for the **Strategy** pattern (one strategy per report type).

---

## 4. Relationships (for the Use Case Diagram)
- UC-05, UC-06, UC-03, UC-04 **«include»** UC-07 (Search Asset)
- All use cases except UC-01 **«include»** UC-01 (Log In)
- UC-06 **«extend»** UC-03 (the Damaged condition sets the asset to In Repair)
- UC-12 **«extend»** UC-05 (an approved request leads to a check-out)
- **Generalization:** IT Administrator inherits every use case of IT Technician.

---

## 5. Asset Status Lifecycle
```
Available ──check out──▶ Checked Out ──check in──▶ Available
    │                         │
    │                         └──check in (damaged)──▶ In Repair ──fixed──▶ Available
    │
    └──retire──▶ Retired   (also possible from In Repair)
```