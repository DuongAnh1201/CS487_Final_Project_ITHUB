-- SP6 – Database schema: Classrooms & Schedules (CLS) and Issue Logs (ISS)
-- SQLite. Tables users, items, locations and audit_records are defined by their owning pages
-- (AST-USR-schema.sql, ORD-RPT-schema.sql). Load order: AST-USR -> ORD-RPT -> CLS-ISS.
-- Dates and times are ISO-8601 TEXT. IDs use AUTOINCREMENT, so they are never reused (BR-01).
-- Nothing is ever deleted (BR-02): deactivation, removal, cancellation and final statuses replace deletes.

PRAGMA foreign_keys = ON;

-- =================================================================== Classrooms & Schedules (CLS)

CREATE TABLE classrooms (
    classroom_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id             INTEGER NOT NULL UNIQUE REFERENCES locations(location_id),   -- one classroom per Location (BR-18)
    capacity                INTEGER NOT NULL CHECK (capacity > 0),
    room_type               TEXT    NOT NULL CHECK (room_type IN ('LECTURE','COMPUTER_LAB')),
    is_active               INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    closed_for_maintenance  INTEGER NOT NULL DEFAULT 0 CHECK (closed_for_maintenance IN (0,1)),
    closed_reason           TEXT,
    last_checked_at         TEXT,                                                        -- NULL = never checked (BR-20)
    created_by              INTEGER NOT NULL REFERENCES users(user_id),
    created_at              TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_by              INTEGER REFERENCES users(user_id),
    updated_at              TEXT,
    version                 INTEGER NOT NULL DEFAULT 1,
    CHECK ((closed_for_maintenance = 0 AND closed_reason IS NULL)
        OR (closed_for_maintenance = 1 AND closed_reason IS NOT NULL AND length(trim(closed_reason)) > 0))
);
CREATE INDEX idx_classrooms_active ON classrooms(is_active);

CREATE TABLE room_equipment (
    room_equipment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    classroom_id       INTEGER NOT NULL REFERENCES classrooms(classroom_id),
    item_id            INTEGER NOT NULL REFERENCES items(item_id),
    seat_label         TEXT,
    condition          TEXT    NOT NULL DEFAULT 'WORKING'
                       CHECK (condition IN ('WORKING','FAULTY','UNDER_REPAIR','OUT_OF_SERVICE','MISSING')),
    installed_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    installed_by       INTEGER NOT NULL REFERENCES users(user_id),
    removed_at         TEXT,                                                             -- NULL = still installed
    removed_by         INTEGER REFERENCES users(user_id),
    updated_by         INTEGER REFERENCES users(user_id),
    updated_at         TEXT,
    version            INTEGER NOT NULL DEFAULT 1,
    CHECK ((removed_at IS NULL AND removed_by IS NULL) OR (removed_at IS NOT NULL AND removed_by IS NOT NULL)),
    CHECK (removed_at IS NULL OR removed_at >= installed_at)
);
-- An item is installed in at most one room at a time (BR-18).
CREATE UNIQUE INDEX uq_room_equipment_one_room_per_item ON room_equipment(item_id) WHERE removed_at IS NULL;
-- A seat label is used once per room among installed items.
CREATE UNIQUE INDEX uq_room_equipment_seat ON room_equipment(classroom_id, seat_label)
    WHERE removed_at IS NULL AND seat_label IS NOT NULL;
CREATE INDEX idx_room_equipment_classroom ON room_equipment(classroom_id, removed_at);

CREATE TABLE room_checks (
    check_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    classroom_id  INTEGER NOT NULL REFERENCES classrooms(classroom_id),
    checked_by    INTEGER NOT NULL REFERENCES users(user_id),
    checked_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    notes         TEXT
);
CREATE INDEX idx_room_checks_classroom ON room_checks(classroom_id, checked_at);

CREATE TABLE room_check_results (
    result_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    check_id            INTEGER NOT NULL REFERENCES room_checks(check_id),
    room_equipment_id   INTEGER NOT NULL REFERENCES room_equipment(room_equipment_id),
    observed_condition  TEXT    NOT NULL
                        CHECK (observed_condition IN ('WORKING','FAULTY','UNDER_REPAIR','OUT_OF_SERVICE','MISSING')),
    comment             TEXT,
    UNIQUE (check_id, room_equipment_id)
);

CREATE TABLE schedule_imports (
    import_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name      TEXT    NOT NULL,
    imported_by    INTEGER NOT NULL REFERENCES users(user_id),
    imported_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    rows_accepted  INTEGER NOT NULL DEFAULT 0 CHECK (rows_accepted >= 0),
    rows_rejected  INTEGER NOT NULL DEFAULT 0 CHECK (rows_rejected >= 0)
);

-- One row per rejected CSV row (1NF instead of a JSON list).
CREATE TABLE schedule_import_errors (
    error_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    import_id   INTEGER NOT NULL REFERENCES schedule_imports(import_id),
    row_number  INTEGER NOT NULL CHECK (row_number > 0),
    reason      TEXT    NOT NULL,
    UNIQUE (import_id, row_number)
);

CREATE TABLE schedule_entries (
    entry_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    classroom_id     INTEGER NOT NULL REFERENCES classrooms(classroom_id),
    import_id        INTEGER REFERENCES schedule_imports(import_id),                     -- NULL for manual entries
    course_code      TEXT    NOT NULL CHECK (length(trim(course_code)) > 0),
    course_title     TEXT    NOT NULL CHECK (length(trim(course_title)) > 0),
    instructor_name  TEXT    NOT NULL CHECK (length(trim(instructor_name)) > 0),
    day_of_week      TEXT    NOT NULL CHECK (day_of_week IN ('MON','TUE','WED','THU','FRI','SAT','SUN')),
    start_time       TEXT    NOT NULL CHECK (start_time GLOB '[0-2][0-9]:[0-5][0-9]' AND start_time < '24:00'),
    end_time         TEXT    NOT NULL CHECK (end_time   GLOB '[0-2][0-9]:[0-5][0-9]' AND end_time   < '24:00'),
    term_start       TEXT    NOT NULL CHECK (date(term_start) IS NOT NULL),
    term_end         TEXT    NOT NULL CHECK (date(term_end)   IS NOT NULL),
    status           TEXT    NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','CANCELLED')),
    source           TEXT    NOT NULL CHECK (source IN ('IMPORT','MANUAL')),
    created_by       INTEGER NOT NULL REFERENCES users(user_id),
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_by       INTEGER REFERENCES users(user_id),
    updated_at       TEXT,
    version          INTEGER NOT NULL DEFAULT 1,
    CHECK (end_time > start_time),
    CHECK (term_end >= term_start),
    CHECK ((source = 'IMPORT' AND import_id IS NOT NULL) OR (source = 'MANUAL' AND import_id IS NULL))
);
-- Overlap checks and timetables (BR-19, US-CLS-08).
CREATE INDEX idx_schedule_room_day ON schedule_entries(classroom_id, day_of_week, status);

-- =================================================================== Issue Logs (ISS)

CREATE TABLE issues (
    issue_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    classroom_id       INTEGER NOT NULL REFERENCES classrooms(classroom_id),
    room_equipment_id  INTEGER REFERENCES room_equipment(room_equipment_id),            -- optional PC / monitor (BR-21)
    category           TEXT    NOT NULL CHECK (category IN ('HARDWARE','SOFTWARE','NETWORK','ROOM_FACILITY','OTHER')),
    severity           TEXT    NOT NULL CHECK (severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    description        TEXT    NOT NULL CHECK (length(trim(description)) > 0),
    status             TEXT    NOT NULL DEFAULT 'OPEN'
                       CHECK (status IN ('OPEN','ASSIGNED','IN_PROGRESS','RESOLVED','CLOSED','DUPLICATE','REJECTED')),
    reporter_name      TEXT    NOT NULL CHECK (length(trim(reporter_name)) > 0),
    reporter_type      TEXT    NOT NULL CHECK (reporter_type IN ('STUDENT','FACULTY','STAFF')),
    reporter_contact   TEXT,
    created_by         INTEGER NOT NULL REFERENCES users(user_id),
    created_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    assigned_to        INTEGER REFERENCES users(user_id),
    target_date        TEXT    NOT NULL,                                                 -- created_at + 1/3/7/14 days (BR-22)
    resolution_notes   TEXT,
    resolved_by        INTEGER REFERENCES users(user_id),
    resolved_at        TEXT,
    duplicate_of_id    INTEGER REFERENCES issues(issue_id),
    is_repeat_problem  INTEGER NOT NULL DEFAULT 0 CHECK (is_repeat_problem IN (0,1)),     -- FR-ISS-08
    updated_by         INTEGER REFERENCES users(user_id),
    updated_at         TEXT,
    version            INTEGER NOT NULL DEFAULT 1,
    CHECK (target_date >= date(created_at)),
    -- From ASSIGNED onward somebody is responsible.
    CHECK (status NOT IN ('ASSIGNED','IN_PROGRESS','RESOLVED','CLOSED') OR assigned_to IS NOT NULL),
    -- Resolution fields are filled exactly when the issue is RESOLVED or CLOSED (BR-23).
    CHECK ((status IN ('RESOLVED','CLOSED')
                AND resolution_notes IS NOT NULL AND length(trim(resolution_notes)) > 0
                AND resolved_by IS NOT NULL AND resolved_at IS NOT NULL)
        OR (status NOT IN ('RESOLVED','CLOSED')
                AND resolution_notes IS NULL AND resolved_by IS NULL AND resolved_at IS NULL)),
    -- A DUPLICATE always points to its original, and only a DUPLICATE does.
    CHECK ((status = 'DUPLICATE') = (duplicate_of_id IS NOT NULL)),
    CHECK (duplicate_of_id IS NULL OR duplicate_of_id <> issue_id)
);
-- Filtered issue list under 2 s for 5,000 issues (NFR-ISS-02).
CREATE INDEX idx_issues_status        ON issues(status);
CREATE INDEX idx_issues_classroom     ON issues(classroom_id);
CREATE INDEX idx_issues_equipment     ON issues(room_equipment_id);
CREATE INDEX idx_issues_created_at    ON issues(created_at);
CREATE INDEX idx_issues_assigned      ON issues(assigned_to, status);
CREATE INDEX idx_issues_duplicate_of  ON issues(duplicate_of_id);
CREATE INDEX idx_issues_open_target   ON issues(target_date) WHERE status IN ('OPEN','ASSIGNED','IN_PROGRESS');

-- Append-only history (NFR-ISS-04): a status change has old/new status, a comment has only text.
CREATE TABLE issue_updates (
    update_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id    INTEGER NOT NULL REFERENCES issues(issue_id),
    user_id     INTEGER NOT NULL REFERENCES users(user_id),
    old_status  TEXT CHECK (old_status IN ('OPEN','ASSIGNED','IN_PROGRESS','RESOLVED','CLOSED','DUPLICATE','REJECTED')),
    new_status  TEXT CHECK (new_status IN ('OPEN','ASSIGNED','IN_PROGRESS','RESOLVED','CLOSED','DUPLICATE','REJECTED')),
    comment     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (
        -- comment line
        (old_status IS NULL AND new_status IS NULL AND comment IS NOT NULL AND length(trim(comment)) > 0)
        -- creation line
     OR (old_status IS NULL AND new_status IS 'OPEN')
        -- status change line
     OR (old_status IS NOT NULL AND new_status IS NOT NULL AND old_status <> new_status)
    )
);
CREATE INDEX idx_issue_updates_issue ON issue_updates(issue_id, created_at);

-- =================================================================== Triggers: no deletes (BR-02)

CREATE TRIGGER trg_classrooms_no_delete       BEFORE DELETE ON classrooms       BEGIN SELECT RAISE(ABORT, 'Classrooms are deactivated, not deleted (BR-02)'); END;
CREATE TRIGGER trg_room_equipment_no_delete   BEFORE DELETE ON room_equipment   BEGIN SELECT RAISE(ABORT, 'Equipment is removed (removed_at), not deleted (BR-02)'); END;
CREATE TRIGGER trg_schedule_entries_no_delete BEFORE DELETE ON schedule_entries BEGIN SELECT RAISE(ABORT, 'Schedule entries are cancelled, not deleted (BR-02)'); END;
CREATE TRIGGER trg_issues_no_delete           BEFORE DELETE ON issues           BEGIN SELECT RAISE(ABORT, 'Issues are closed, not deleted (BR-02)'); END;

-- Append-only tables
CREATE TRIGGER trg_room_checks_no_update      BEFORE UPDATE ON room_checks            BEGIN SELECT RAISE(ABORT, 'Room checks are append-only'); END;
CREATE TRIGGER trg_room_checks_no_delete      BEFORE DELETE ON room_checks            BEGIN SELECT RAISE(ABORT, 'Room checks are append-only'); END;
CREATE TRIGGER trg_check_results_no_update    BEFORE UPDATE ON room_check_results     BEGIN SELECT RAISE(ABORT, 'Room check results are append-only'); END;
CREATE TRIGGER trg_check_results_no_delete    BEFORE DELETE ON room_check_results     BEGIN SELECT RAISE(ABORT, 'Room check results are append-only'); END;
CREATE TRIGGER trg_imports_no_delete          BEFORE DELETE ON schedule_imports       BEGIN SELECT RAISE(ABORT, 'Schedule imports are kept for history'); END;
CREATE TRIGGER trg_import_errors_no_update    BEFORE UPDATE ON schedule_import_errors BEGIN SELECT RAISE(ABORT, 'Import errors are append-only'); END;
CREATE TRIGGER trg_import_errors_no_delete    BEFORE DELETE ON schedule_import_errors BEGIN SELECT RAISE(ABORT, 'Import errors are append-only'); END;
CREATE TRIGGER trg_issue_updates_no_update    BEFORE UPDATE ON issue_updates          BEGIN SELECT RAISE(ABORT, 'Issue history cannot be edited (NFR-ISS-04)'); END;
CREATE TRIGGER trg_issue_updates_no_delete    BEFORE DELETE ON issue_updates          BEGIN SELECT RAISE(ABORT, 'Issue history cannot be deleted (NFR-ISS-04)'); END;

-- =================================================================== Triggers: CLS rules

-- Equipment can only be installed in an active classroom, and only an ASSET that is not
-- retired, lost or on loan (SP4 §11.1). The Desktop/Monitor category check stays in ClassroomManager.
CREATE TRIGGER trg_room_equipment_active_room BEFORE INSERT ON room_equipment
WHEN (SELECT is_active FROM classrooms WHERE classroom_id = NEW.classroom_id) = 0
BEGIN SELECT RAISE(ABORT, 'Choose a different active classroom.'); END;

CREATE TRIGGER trg_room_equipment_valid_item BEFORE INSERT ON room_equipment
WHEN (SELECT item_kind FROM items WHERE item_id = NEW.item_id) <> 'ASSET'
  OR (SELECT status    FROM items WHERE item_id = NEW.item_id) IN ('RETIRED','LOST','ON_LOAN')
BEGIN SELECT RAISE(ABORT, 'Only assets that are not retired, lost or on loan can be installed (BR-18)'); END;

-- A removed equipment record is history and cannot change; it cannot move to another room either
-- (a move is remove + new record).
CREATE TRIGGER trg_room_equipment_removed_read_only BEFORE UPDATE ON room_equipment
WHEN OLD.removed_at IS NOT NULL
BEGIN SELECT RAISE(ABORT, 'Removed equipment records are read-only'); END;

CREATE TRIGGER trg_room_equipment_no_move BEFORE UPDATE OF classroom_id, item_id ON room_equipment
WHEN NEW.classroom_id <> OLD.classroom_id OR NEW.item_id <> OLD.item_id
BEGIN SELECT RAISE(ABORT, 'A move closes this record and opens a new one'); END;

-- A classroom cannot be deactivated while it has installed equipment or future classes (BR-18).
CREATE TRIGGER trg_classrooms_deactivate_equipment BEFORE UPDATE OF is_active ON classrooms
WHEN NEW.is_active = 0 AND OLD.is_active = 1
 AND EXISTS (SELECT 1 FROM room_equipment WHERE classroom_id = NEW.classroom_id AND removed_at IS NULL)
BEGIN SELECT RAISE(ABORT, 'Remove the installed equipment first.'); END;

CREATE TRIGGER trg_classrooms_deactivate_classes BEFORE UPDATE OF is_active ON classrooms
WHEN NEW.is_active = 0 AND OLD.is_active = 1
 AND EXISTS (SELECT 1 FROM schedule_entries
             WHERE classroom_id = NEW.classroom_id AND status = 'ACTIVE' AND term_end >= date('now'))
BEGIN SELECT RAISE(ABORT, 'This classroom has future classes.'); END;

-- Each result must be for equipment installed in the room being checked.
CREATE TRIGGER trg_check_results_same_room BEFORE INSERT ON room_check_results
WHEN (SELECT classroom_id FROM room_equipment WHERE room_equipment_id = NEW.room_equipment_id)
  <> (SELECT classroom_id FROM room_checks    WHERE check_id = NEW.check_id)
BEGIN SELECT RAISE(ABORT, 'Equipment is not in the checked classroom'); END;

-- A room check updates the classroom's last-checked date, so the overdue flag clears (BR-20).
CREATE TRIGGER trg_room_checks_apply AFTER INSERT ON room_checks
BEGIN
    UPDATE classrooms
    SET last_checked_at = NEW.checked_at
    WHERE classroom_id = NEW.classroom_id
      AND (last_checked_at IS NULL OR last_checked_at < NEW.checked_at);
END;

-- Schedule entries only for active classrooms.
CREATE TRIGGER trg_schedule_active_room BEFORE INSERT ON schedule_entries
WHEN (SELECT is_active FROM classrooms WHERE classroom_id = NEW.classroom_id) = 0
BEGIN SELECT RAISE(ABORT, 'Classroom is not active'); END;

-- No overlapping ACTIVE classes in the same room, day and term (BR-19). Safety net for ScheduleManager.
CREATE TRIGGER trg_schedule_no_overlap_insert BEFORE INSERT ON schedule_entries
WHEN NEW.status = 'ACTIVE' AND EXISTS (
    SELECT 1 FROM schedule_entries s
    WHERE s.classroom_id = NEW.classroom_id AND s.day_of_week = NEW.day_of_week AND s.status = 'ACTIVE'
      AND s.term_start <= NEW.term_end AND NEW.term_start <= s.term_end
      AND s.start_time <  NEW.end_time AND NEW.start_time <  s.end_time)
BEGIN SELECT RAISE(ABORT, 'Schedule entry overlaps another class (BR-19)'); END;

CREATE TRIGGER trg_schedule_no_overlap_update BEFORE UPDATE ON schedule_entries
WHEN NEW.status = 'ACTIVE' AND EXISTS (
    SELECT 1 FROM schedule_entries s
    WHERE s.entry_id <> NEW.entry_id
      AND s.classroom_id = NEW.classroom_id AND s.day_of_week = NEW.day_of_week AND s.status = 'ACTIVE'
      AND s.term_start <= NEW.term_end AND NEW.term_start <= s.term_end
      AND s.start_time <  NEW.end_time AND NEW.start_time <  s.end_time)
BEGIN SELECT RAISE(ABORT, 'Schedule entry overlaps another class (BR-19)'); END;

-- A cancelled entry stays cancelled (kept for history).
CREATE TRIGGER trg_schedule_cancelled_read_only BEFORE UPDATE ON schedule_entries
WHEN OLD.status = 'CANCELLED'
BEGIN SELECT RAISE(ABORT, 'Cancelled schedule entries are read-only'); END;

-- =================================================================== Triggers: ISS rules

-- New issues start OPEN, in an active classroom (FR-ISS-01).
CREATE TRIGGER trg_issues_start_open BEFORE INSERT ON issues
WHEN NEW.status <> 'OPEN'
BEGIN SELECT RAISE(ABORT, 'New issues start as OPEN'); END;

CREATE TRIGGER trg_issues_active_room BEFORE INSERT ON issues
WHEN (SELECT is_active FROM classrooms WHERE classroom_id = NEW.classroom_id) = 0
BEGIN SELECT RAISE(ABORT, 'Classroom is not active'); END;

-- The item, if any, must be installed in the chosen classroom (BR-21).
CREATE TRIGGER trg_issues_equipment_in_room BEFORE INSERT ON issues
WHEN NEW.room_equipment_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM room_equipment
    WHERE room_equipment_id = NEW.room_equipment_id
      AND classroom_id = NEW.classroom_id AND removed_at IS NULL)
BEGIN SELECT RAISE(ABORT, 'Item is not installed in this classroom.'); END;

CREATE TRIGGER trg_issues_location_fixed BEFORE UPDATE OF classroom_id, room_equipment_id ON issues
WHEN NEW.classroom_id <> OLD.classroom_id
  OR COALESCE(NEW.room_equipment_id, -1) <> COALESCE(OLD.room_equipment_id, -1)
BEGIN SELECT RAISE(ABORT, 'Classroom and item of an issue cannot be changed'); END;

-- Only the allowed status moves (BR-23, SP4 §9.3). Role checks stay in IssueController.
CREATE TRIGGER trg_issues_transition BEFORE UPDATE OF status ON issues
WHEN NEW.status <> OLD.status AND NOT (
       (OLD.status = 'OPEN'        AND NEW.status IN ('ASSIGNED','REJECTED','DUPLICATE'))
    OR (OLD.status = 'ASSIGNED'    AND NEW.status IN ('IN_PROGRESS','REJECTED','DUPLICATE'))
    OR (OLD.status = 'IN_PROGRESS' AND NEW.status = 'RESOLVED')
    OR (OLD.status = 'RESOLVED'    AND NEW.status IN ('IN_PROGRESS','CLOSED')))
BEGIN SELECT RAISE(ABORT, 'This status change is not allowed.'); END;

-- Final issues (CLOSED, REJECTED, DUPLICATE) are locked. Only the repeat-problem flag on an
-- original may still be set when a new duplicate is linked to it.
CREATE TRIGGER trg_issues_final_locked BEFORE UPDATE OF
    status, category, severity, description, reporter_name, reporter_type, reporter_contact,
    assigned_to, target_date, resolution_notes, resolved_by, resolved_at, duplicate_of_id ON issues
WHEN OLD.status IN ('CLOSED','REJECTED','DUPLICATE')
BEGIN SELECT RAISE(ABORT, 'This issue is closed and cannot be changed.'); END;

-- Duplicates link to the root original, never to another duplicate (SP4 §9.4).
CREATE TRIGGER trg_issues_duplicate_root BEFORE UPDATE OF duplicate_of_id ON issues
WHEN NEW.duplicate_of_id IS NOT NULL
 AND (SELECT status FROM issues WHERE issue_id = NEW.duplicate_of_id) = 'DUPLICATE'
BEGIN SELECT RAISE(ABORT, 'Choose the original issue.'); END;

-- No comments on final issues (SP4 §11.1).
CREATE TRIGGER trg_issue_updates_no_comment_on_final BEFORE INSERT ON issue_updates
WHEN NEW.new_status IS NULL
 AND (SELECT status FROM issues WHERE issue_id = NEW.issue_id) IN ('CLOSED','REJECTED','DUPLICATE')
BEGIN SELECT RAISE(ABORT, 'This issue is closed. Comments are not allowed.'); END;

-- =================================================================== Views: derived values (not stored)

-- Room status (DD-CLS-02). Only installed items of category 'Desktop' count as PCs.
CREATE VIEW v_classroom_status AS
SELECT c.classroom_id,
       CASE
           WHEN c.closed_for_maintenance = 1                       THEN 'CLOSED'
           WHEN COALESCE(pc.total, 0) = 0 OR pc.working = pc.total THEN 'AVAILABLE'
           WHEN pc.working = 0                                     THEN 'UNUSABLE'
           ELSE 'LIMITED'
       END AS room_status,
       COALESCE(pc.total, 0)   AS pcs_installed,
       COALESCE(pc.working, 0) AS pcs_working
FROM classrooms c
LEFT JOIN (
    SELECT re.classroom_id,
           COUNT(*)                                          AS total,
           SUM(CASE WHEN re.condition = 'WORKING' THEN 1 ELSE 0 END) AS working
    FROM room_equipment re
    JOIN items i      ON i.item_id = re.item_id
    JOIN categories k ON k.category_id = i.category_id
    WHERE re.removed_at IS NULL AND k.name = 'Desktop'
    GROUP BY re.classroom_id
) pc ON pc.classroom_id = c.classroom_id;

-- Active rooms never checked or not checked in the last 7 days (BR-20).
CREATE VIEW v_rooms_check_overdue AS
SELECT classroom_id, last_checked_at
FROM classrooms
WHERE is_active = 1
  AND (last_checked_at IS NULL OR julianday('now') - julianday(last_checked_at) > 7);

-- Unresolved issues past their target date (BR-22).
CREATE VIEW v_issues_overdue AS
SELECT issue_id, classroom_id, severity, status, target_date
FROM issues
WHERE status IN ('OPEN','ASSIGNED','IN_PROGRESS') AND target_date < date('now');

-- Number of reports of a problem = 1 (original) + its duplicates (FR-ISS-08).
CREATE VIEW v_issue_report_counts AS
SELECT o.issue_id, 1 + COUNT(d.issue_id) AS report_count, o.is_repeat_problem
FROM issues o
LEFT JOIN issues d ON d.duplicate_of_id = o.issue_id
WHERE o.status <> 'DUPLICATE'
GROUP BY o.issue_id;
