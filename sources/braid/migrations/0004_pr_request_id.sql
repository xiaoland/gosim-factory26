ALTER TABLE local_items ADD COLUMN request_id TEXT;
CREATE UNIQUE INDEX local_items_request_id ON local_items(request_id);
