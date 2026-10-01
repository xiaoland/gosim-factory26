CREATE TABLE local_subscriptions (
    work_item_node_id TEXT NOT NULL REFERENCES work_items(node_id),
    member_login TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
    source TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    PRIMARY KEY(work_item_node_id,member_login)
) STRICT;
INSERT INTO local_subscriptions(work_item_node_id,member_login,source,changed_at)
SELECT l.node_id,l.desired_member_login,'assignment',w.observed_at
FROM local_items l JOIN work_items w ON w.node_id=l.node_id
WHERE l.desired_member_login IS NOT NULL;
INSERT OR IGNORE INTO local_subscriptions(work_item_node_id,member_login,source,changed_at)
SELECT c.work_item_node_id,a.member_login,'comment',c.created_at
FROM local_comments c JOIN agent_instances ai ON ai.agent_id=c.writer_group
JOIN assignments a ON a.assignment_id=ai.assignment_id
WHERE a.member_login IS NOT NULL;

CREATE TABLE local_activity (
    ordinal INTEGER PRIMARY KEY AUTOINCREMENT,
    work_item_node_id TEXT NOT NULL REFERENCES work_items(node_id),
    occurred_at TEXT NOT NULL,
    actor_login TEXT NOT NULL,
    action TEXT NOT NULL,
    source_comment INTEGER REFERENCES local_comments(comment_id),
    detail TEXT NOT NULL
) STRICT;
CREATE INDEX local_activity_item ON local_activity(work_item_node_id,ordinal);

ALTER TABLE local_comments ADD COLUMN system_author TEXT;
ALTER TABLE events ADD COLUMN recipient_revision INTEGER;
ALTER TABLE local_run ADD COLUMN root_idle_since TEXT;
ALTER TABLE local_run ADD COLUMN root_check_comment INTEGER REFERENCES local_comments(comment_id);
