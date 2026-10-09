-- A PR reviewer responsibility survives individual frozen-candidate requests.
CREATE TABLE pr_review_sessions (
    pr_node_id TEXT PRIMARY KEY REFERENCES work_items(node_id),
    review_node_id TEXT NOT NULL UNIQUE REFERENCES work_items(node_id),
    current_request_id INTEGER NOT NULL UNIQUE REFERENCES review_requests(request_id)
) STRICT;
