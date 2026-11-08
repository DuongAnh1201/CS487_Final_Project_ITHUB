PRAGMA foreign_keys = ON;

CREATE TABLE users (
    user_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name             TEXT    NOT NULL,
    school_email          TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    school_id             TEXT    NOT NULL UNIQUE,
    password_hash         TEXT    NOT NULL,
    role                  TEXT    NOT NULL CHECK (role IN ('ADMIN','STUDENT_ASSISTANT')),
    status                TEXT    NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','LOCKED','DEACTIVATED')),
    failed_attempts       INTEGER NOT NULL DEFAULT 0 CHECK (failed_attempts >= 0),
    locked_until          TEXT,
    must_change_password  INTEGER NOT NULL DEFAULT 1 CHECK (must_change_password IN (0,1)),
    access_end_date       TEXT,
    last_login_at         TEXT,
    created_by            INTEGER REFERENCES users(user_id),
    created_at            TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_by            INTEGER REFERENCES users(user_id),
    updated_at            TEXT,
    CHECK (status <> 'LOCKED' OR locked_until IS NOT NULL)
);

CREATE TABLE sessions (
    session_id        TEXT    PRIMARY KEY,
    user_id           INTEGER NOT NULL REFERENCES users(user_id),
    started_at        TEXT    NOT NULL DEFAULT (datetime('now')),
    last_activity_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    ended_at          TEXT
);
CREATE INDEX idx_sessions_user ON sessions(user_id);

CREATE TABLE locations (
    location_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    building     TEXT    NOT NULL,
    room         TEXT    NOT NULL,
    area         TEXT    NOT NULL DEFAULT '',
    is_active    INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    UNIQUE (building, room, area)
);

CREATE TABLE categories (
    category_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    is_consumable  INTEGER NOT NULL DEFAULT 0 CHECK (is_consumable IN (0,1))
);

CREATE TABLE items (
    item_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_tag          TEXT    NOT NULL UNIQUE,
    item_kind          TEXT    NOT NULL DEFAULT 'ASSET' CHECK (item_kind IN ('ASSET','CONSUMABLE')),
    category_id        INTEGER NOT NULL REFERENCES categories(category_id),
    location_id        INTEGER NOT NULL REFERENCES locations(location_id),
    model              TEXT    NOT NULL,
    manufacturer       TEXT,
    serial_number      TEXT    UNIQUE,
    status             TEXT    NOT NULL DEFAULT 'AVAILABLE' CHECK (status IN ('AVAILABLE','ON_LOAN','DAMAGED','LOST','RETIRED')),
    purchase_date      TEXT,
    warranty_end_date  TEXT,
    notes              TEXT,
    created_by         INTEGER NOT NULL REFERENCES users(user_id),
    created_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_by         INTEGER REFERENCES users(user_id),
    updated_at         TEXT,
    version            INTEGER NOT NULL DEFAULT 1,
    CHECK (warranty_end_date IS NULL OR purchase_date IS NULL OR warranty_end_date >= purchase_date),
    CHECK (item_kind = 'ASSET' OR status IN ('AVAILABLE','RETIRED'))
);
CREATE INDEX idx_items_category ON items(category_id);
CREATE INDEX idx_items_location ON items(location_id);
CREATE INDEX idx_items_status   ON items(status);
CREATE INDEX idx_items_model    ON items(model);

CREATE TABLE consumables (
    item_id            INTEGER PRIMARY KEY REFERENCES items(item_id),
    quantity_on_hand   INTEGER NOT NULL DEFAULT 0 CHECK (quantity_on_hand >= 0),
    reorder_threshold  INTEGER NOT NULL DEFAULT 0 CHECK (reorder_threshold >= 0)
);

CREATE TABLE stock_transactions (
    transaction_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id         INTEGER NOT NULL REFERENCES consumables(item_id),
    type            TEXT    NOT NULL CHECK (type IN ('STOCK_IN','STOCK_OUT')),
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    recipient       TEXT,
    order_id        INTEGER REFERENCES orders(order_id),
    performed_by    INTEGER NOT NULL REFERENCES users(user_id),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    CHECK (type = 'STOCK_IN'  OR recipient IS NOT NULL),
    CHECK (type = 'STOCK_OUT' OR recipient IS NULL)
);
CREATE INDEX idx_stock_tx_item ON stock_transactions(item_id, created_at);

CREATE TABLE borrowers (
    borrower_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id    TEXT    NOT NULL UNIQUE,
    name         TEXT    NOT NULL,
    email        TEXT    COLLATE NOCASE,
    type         TEXT    NOT NULL CHECK (type IN ('STUDENT','FACULTY','STAFF'))
);

CREATE TABLE loans (
    loan_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id        INTEGER NOT NULL REFERENCES items(item_id),
    borrower_id    INTEGER NOT NULL REFERENCES borrowers(borrower_id),
    checkout_date  TEXT    NOT NULL,
    due_date       TEXT    NOT NULL,
    return_date    TEXT,
    condition_out  TEXT    NOT NULL CHECK (condition_out IN ('GOOD','FAIR','POOR','DAMAGED')),
    condition_in   TEXT    CHECK (condition_in IN ('GOOD','FAIR','POOR','DAMAGED')),
    notes          TEXT,
    processed_by   INTEGER NOT NULL REFERENCES users(user_id),
    received_by    INTEGER REFERENCES users(user_id),
    extended       INTEGER NOT NULL DEFAULT 0 CHECK (extended IN (0,1)),
    status         TEXT    NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','CLOSED')),
    version        INTEGER NOT NULL DEFAULT 1,
    CHECK (due_date >= checkout_date),
    CHECK (return_date IS NULL OR return_date >= checkout_date),
    CHECK ((status = 'OPEN'   AND return_date IS NULL AND condition_in IS NULL AND received_by IS NULL)
        OR (status = 'CLOSED' AND return_date IS NOT NULL AND condition_in IS NOT NULL AND received_by IS NOT NULL))
);
CREATE UNIQUE INDEX uq_loans_one_open_per_item ON loans(item_id) WHERE status = 'OPEN';
CREATE INDEX idx_loans_borrower_status ON loans(borrower_id, status);
CREATE INDEX idx_loans_open_due ON loans(due_date) WHERE status = 'OPEN';

CREATE TABLE item_incidents (
    incident_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id        INTEGER NOT NULL REFERENCES items(item_id),
    type           TEXT    NOT NULL CHECK (type IN ('LOST','DAMAGED','RETIRED')),
    description    TEXT    NOT NULL,
    incident_date  TEXT    NOT NULL,
    reported_by    INTEGER NOT NULL REFERENCES users(user_id),
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_incidents_item ON item_incidents(item_id);

CREATE TRIGGER trg_users_no_delete       BEFORE DELETE ON users       BEGIN SELECT RAISE(ABORT, 'Users are deactivated, not deleted (BR-02)'); END;
CREATE TRIGGER trg_items_no_delete       BEFORE DELETE ON items       BEGIN SELECT RAISE(ABORT, 'Items are retired, not deleted (BR-02)'); END;
CREATE TRIGGER trg_consumables_no_delete BEFORE DELETE ON consumables BEGIN SELECT RAISE(ABORT, 'Consumables are retired, not deleted (BR-02)'); END;
CREATE TRIGGER trg_loans_no_delete       BEFORE DELETE ON loans       BEGIN SELECT RAISE(ABORT, 'Loans are kept for history (BR-02)'); END;
CREATE TRIGGER trg_borrowers_no_delete   BEFORE DELETE ON borrowers   BEGIN SELECT RAISE(ABORT, 'Borrowers are kept for loan history (BR-02)'); END;

CREATE TRIGGER trg_stock_tx_no_update   BEFORE UPDATE ON stock_transactions BEGIN SELECT RAISE(ABORT, 'Stock transactions are append-only'); END;
CREATE TRIGGER trg_stock_tx_no_delete   BEFORE DELETE ON stock_transactions BEGIN SELECT RAISE(ABORT, 'Stock transactions are append-only'); END;
CREATE TRIGGER trg_incidents_no_update  BEFORE UPDATE ON item_incidents     BEGIN SELECT RAISE(ABORT, 'Incidents are append-only'); END;
CREATE TRIGGER trg_incidents_no_delete  BEFORE DELETE ON item_incidents     BEGIN SELECT RAISE(ABORT, 'Incidents are append-only'); END;

CREATE TRIGGER trg_consumables_kind BEFORE INSERT ON consumables
WHEN (SELECT item_kind FROM items WHERE item_id = NEW.item_id) <> 'CONSUMABLE'
BEGIN SELECT RAISE(ABORT, 'consumables row requires items.item_kind = CONSUMABLE'); END;

CREATE TRIGGER trg_loans_only_assets BEFORE INSERT ON loans
WHEN (SELECT item_kind FROM items WHERE item_id = NEW.item_id) <> 'ASSET'
BEGIN SELECT RAISE(ABORT, 'Consumables are issued, not lent (BR-11)'); END;

CREATE TRIGGER trg_loans_only_available BEFORE INSERT ON loans
WHEN (SELECT status FROM items WHERE item_id = NEW.item_id) <> 'AVAILABLE'
BEGIN SELECT RAISE(ABORT, 'Only Available items can be lent (BR-07)'); END;

CREATE TRIGGER trg_retired_read_only BEFORE UPDATE ON items
WHEN OLD.status = 'RETIRED'
BEGIN SELECT RAISE(ABORT, 'Retired items are read-only (BR-07)'); END;

CREATE TRIGGER trg_stock_apply AFTER INSERT ON stock_transactions
BEGIN
    UPDATE consumables
    SET quantity_on_hand = quantity_on_hand + CASE NEW.type WHEN 'STOCK_IN' THEN NEW.quantity ELSE -NEW.quantity END
    WHERE item_id = NEW.item_id;
END;
