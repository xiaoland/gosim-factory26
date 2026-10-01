CREATE TABLE local_run (
    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    run_id TEXT NOT NULL,
    repository TEXT NOT NULL,
    delivery_ref TEXT NOT NULL,
    lifecycle TEXT NOT NULL DEFAULT 'running',
    delivery_commit TEXT
) STRICT;
CREATE TABLE local_items (
    node_id TEXT PRIMARY KEY REFERENCES work_items(node_id),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    revision INTEGER NOT NULL DEFAULT 1,
    state_reason TEXT,
    head_ref TEXT,
    ready_commit TEXT,
    request_comment TEXT UNIQUE
) STRICT;
CREATE TABLE local_comments (
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_item_node_id TEXT NOT NULL REFERENCES work_items(node_id),
    body TEXT,
    lifecycle TEXT NOT NULL CHECK(lifecycle IN ('visible','hidden','deleted')),
    writer_group TEXT,
    writer_turn TEXT,
    revision INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
) STRICT;
CREATE TABLE local_merges (
    pr_node_id TEXT PRIMARY KEY REFERENCES local_items(node_id),
    base_commit TEXT NOT NULL,
    head_commit TEXT NOT NULL,
    merge_commit TEXT,
    lifecycle TEXT NOT NULL CHECK(lifecycle IN ('prepared','applied','conflict')),
    error TEXT,
    writer_group TEXT,
    writer_turn TEXT,
    writer_node TEXT
) STRICT;
ALTER TABLE events ADD COLUMN writer_group TEXT;
ALTER TABLE events ADD COLUMN writer_turn TEXT;
