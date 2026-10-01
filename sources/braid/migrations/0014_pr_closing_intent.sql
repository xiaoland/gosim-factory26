-- Existing prepared merges have no frozen closing declaration; do not infer one on recovery.
ALTER TABLE local_merges ADD COLUMN closing_issues TEXT NOT NULL DEFAULT '[]';
