ALTER TABLE local_items ADD COLUMN base_ref TEXT;
ALTER TABLE local_items ADD COLUMN draft INTEGER NOT NULL DEFAULT 0 CHECK(draft IN (0,1));
UPDATE local_items
SET base_ref=(SELECT delivery_ref FROM local_run),
    draft=CASE WHEN ready_commit IS NULL THEN 1 ELSE 0 END
WHERE node_id IN (SELECT node_id FROM work_items WHERE kind='pr');
ALTER TABLE local_merges ADD COLUMN base_ref TEXT;
ALTER TABLE local_merges ADD COLUMN head_ref TEXT;
UPDATE local_merges
SET base_ref=(SELECT base_ref FROM local_items WHERE node_id=pr_node_id),
    head_ref=(SELECT head_ref FROM local_items WHERE node_id=pr_node_id);
