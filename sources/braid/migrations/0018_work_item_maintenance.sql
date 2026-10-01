CREATE TABLE local_maintenance_receipts (
    operation_id TEXT PRIMARY KEY,
    work_item_node_id TEXT NOT NULL REFERENCES work_items(node_id),
    writer_agent TEXT NOT NULL REFERENCES agent_instances(agent_id),
    writer_turn TEXT NOT NULL REFERENCES turns(turn_id),
    source_digest TEXT NOT NULL,
    result_digest TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    source_json TEXT NOT NULL,
    receipt_json TEXT NOT NULL,
    committed_at TEXT NOT NULL
) STRICT;
