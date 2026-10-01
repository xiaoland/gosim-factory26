-- work_items is rebuilt with foreign_keys disabled outside the transaction by apply_one.
CREATE TABLE work_items_new (
    node_id TEXT PRIMARY KEY,
    repository_node_id TEXT NOT NULL REFERENCES repositories(node_id),
    kind TEXT NOT NULL CHECK (kind IN ('issue', 'pr', 'review')),
    number INTEGER NOT NULL CHECK (number > 0),
    state TEXT NOT NULL,
    context_revision TEXT,
    observed_at TEXT NOT NULL,
    UNIQUE (repository_node_id, kind, number)
) STRICT;
INSERT INTO work_items_new SELECT * FROM work_items;
DROP TABLE work_items;
ALTER TABLE work_items_new RENAME TO work_items;

CREATE TABLE review_requests (
    request_id INTEGER PRIMARY KEY CHECK(request_id > 0),
    node_id TEXT NOT NULL UNIQUE REFERENCES work_items(node_id),
    pr_node_id TEXT NOT NULL REFERENCES work_items(node_id),
    issue_node_id TEXT NOT NULL REFERENCES work_items(node_id),
    request_key TEXT NOT NULL UNIQUE,
    requester_member TEXT NOT NULL,
    requester_agent TEXT REFERENCES agent_instances(agent_id),
    requester_turn TEXT REFERENCES turns(turn_id),
    base_ref TEXT NOT NULL,
    head_ref TEXT NOT NULL,
    base_commit TEXT NOT NULL,
    head_commit TEXT NOT NULL,
    head_tree TEXT NOT NULL,
    requirements_revision INTEGER NOT NULL,
    requirements_body TEXT NOT NULL,
    requirements_digest TEXT NOT NULL CHECK(length(requirements_digest)=64),
    responsibility TEXT NOT NULL CHECK(responsibility IN ('issue_owner','assigned_reviewer')),
    responsibility_revision INTEGER NOT NULL DEFAULT 1 CHECK(responsibility_revision > 0),
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','completed','cancelled')),
    verdict TEXT CHECK(verdict IN ('approved','changes_requested','inconclusive')),
    conclusion_body TEXT,
    evidence TEXT NOT NULL DEFAULT '[]',
    conclusion_member TEXT,
    conclusion_agent TEXT REFERENCES agent_instances(agent_id),
    conclusion_turn TEXT REFERENCES turns(turn_id),
    checkout_commit TEXT,
    checkout_tree TEXT,
    checkout_dirty TEXT,
    cancelled_reason TEXT,
    created_at TEXT NOT NULL,
    concluded_at TEXT,
    CHECK((status='completed' AND verdict IS NOT NULL AND conclusion_body IS NOT NULL) OR (status!='completed' AND verdict IS NULL))
) STRICT;
CREATE INDEX review_requests_pr ON review_requests(pr_node_id,request_id);
CREATE INDEX review_requests_issue ON review_requests(issue_node_id,status,request_id);
CREATE TABLE review_checkouts (
    request_id INTEGER NOT NULL REFERENCES review_requests(request_id),
    responsibility_revision INTEGER NOT NULL,
    issue_assignment_revision INTEGER NOT NULL,
    path TEXT NOT NULL UNIQUE,
    origin TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    tree_sha TEXT NOT NULL,
    member_login TEXT NOT NULL,
    agent_id TEXT REFERENCES agent_instances(agent_id),
    created_at TEXT NOT NULL,
    PRIMARY KEY(request_id,responsibility_revision,issue_assignment_revision)
) STRICT;
ALTER TABLE local_merges ADD COLUMN review_request_id INTEGER REFERENCES review_requests(request_id);
