ALTER TABLE turns ADD COLUMN deferred_reason TEXT;
ALTER TABLE turns ADD COLUMN first_deferred_at TEXT;
ALTER TABLE turns ADD COLUMN last_deferred_at TEXT;
ALTER TABLE turns ADD COLUMN deferred_count INTEGER NOT NULL DEFAULT 0;
