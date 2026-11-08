-- SP6 – Database schema: Orders (ORD) and Reports & Audit (RPT)
-- SQLite. Tables users, items, projects, and stock_transactions are defined by their owning pages.

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------------ Orders

CREATE TABLE orders (
    order_id          INTEGER PRIMARY KEY,
    item_id           INTEGER NOT NULL REFERENCES items(item_id),
    quantity_ordered  INTEGER NOT NULL CHECK (quantity_ordered > 0),
    quantity_received INTEGER NOT NULL DEFAULT 0
                      CHECK (quantity_received >= 0 AND quantity_received <= quantity_ordered),
    vendor            TEXT,
    status            TEXT    NOT NULL DEFAULT 'REQUESTED'
                      CHECK (status IN ('REQUESTED', 'ORDERED', 'PARTIALLY_ARRIVED', 'ARRIVED', 'CANCELLED')),
    requested_by      INTEGER NOT NULL REFERENCES users(user_id),
    received_by       INTEGER          REFERENCES users(user_id),
    requested_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ordered_at        DATETIME,
    arrived_at        DATETIME
);

-- One open order per item.
CREATE UNIQUE INDEX ux_orders_one_open_per_item
    ON orders(item_id)
    WHERE status IN ('REQUESTED', 'ORDERED', 'PARTIALLY_ARRIVED');

CREATE INDEX ix_orders_status       ON orders(status);
CREATE INDEX ix_orders_requested_at ON orders(requested_at);

-- ------------------------------------------------------------------ Reports

CREATE TABLE report_templates (
    template_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE
);

CREATE TABLE template_checklist_items (
    checklist_item_id INTEGER PRIMARY KEY,
    template_id       INTEGER NOT NULL REFERENCES report_templates(template_id) ON DELETE CASCADE,
    position          INTEGER NOT NULL,
    text              TEXT    NOT NULL,
    UNIQUE (template_id, position)
);

-- One table for Report, DailyReport, and MonthlySummaryReport.
CREATE TABLE reports (
    report_id   INTEGER PRIMARY KEY,
    report_type TEXT    NOT NULL CHECK (report_type IN ('DAILY', 'MONTHLY')),
    title       TEXT    NOT NULL,
    author_id   INTEGER NOT NULL REFERENCES users(user_id),
    project_id  TEXT             REFERENCES projects(project_id),
    template_id INTEGER          REFERENCES report_templates(template_id),
    shift       TEXT,
    month       INTEGER CHECK (month BETWEEN 1 AND 12),
    year        INTEGER,
    status      TEXT    NOT NULL DEFAULT 'SUBMITTED'
                CHECK (status IN ('SUBMITTED', 'REVIEWED', 'REJECTED', 'PASSED')),
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (report_type = 'DAILY'   OR (month IS NOT NULL AND year IS NOT NULL)),
    CHECK (report_type = 'MONTHLY' OR (month IS NULL AND year IS NULL))
);

-- One monthly summary per month.
CREATE UNIQUE INDEX ux_reports_one_summary_per_month
    ON reports(month, year)
    WHERE report_type = 'MONTHLY';

CREATE INDEX ix_reports_status  ON reports(status);
CREATE INDEX ix_reports_project ON reports(project_id);

CREATE TABLE report_answers (
    answer_id         INTEGER PRIMARY KEY,
    report_id         INTEGER NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE,
    checklist_item_id INTEGER NOT NULL REFERENCES template_checklist_items(checklist_item_id),
    value             TEXT,
    UNIQUE (report_id, checklist_item_id)
);

CREATE TABLE report_reviewers (
    report_id   INTEGER NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE,
    reviewer_id INTEGER NOT NULL REFERENCES users(user_id),
    decision    TEXT CHECK (decision IN ('REVIEWED', 'REJECTED', 'PASSED')),
    comment     TEXT,
    reviewed_at DATETIME,
    PRIMARY KEY (report_id, reviewer_id)
);

-- ------------------------------------------------------------------ Audit

CREATE TABLE audit_records (
    record_id   INTEGER PRIMARY KEY,
    user_id     INTEGER  NOT NULL REFERENCES users(user_id),
    action      TEXT     NOT NULL,
    entity_type TEXT     NOT NULL,   -- e.g. 'Order', 'Report', 'Item'
    entity_id   TEXT     NOT NULL,   -- ID in that table; no foreign key by design
    old_value   TEXT,
    new_value   TEXT,
    timestamp   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status      TEXT
);

CREATE INDEX ix_audit_entity    ON audit_records(entity_type, entity_id);
CREATE INDEX ix_audit_user      ON audit_records(user_id);
CREATE INDEX ix_audit_timestamp ON audit_records(timestamp);

-- Audit records are never changed or removed.
CREATE TRIGGER trg_audit_no_update BEFORE UPDATE ON audit_records
BEGIN
    SELECT RAISE(ABORT, 'Audit records cannot be edited or deleted.');
END;

CREATE TRIGGER trg_audit_no_delete BEFORE DELETE ON audit_records
BEGIN
    SELECT RAISE(ABORT, 'Audit records cannot be edited or deleted.');
END;
