ALTER TABLE local_run ADD COLUMN default_issue_profile TEXT;
ALTER TABLE local_run ADD COLUMN default_pr_profile TEXT;
ALTER TABLE local_items ADD COLUMN desired_profile_id TEXT;
ALTER TABLE local_items ADD COLUMN assignment_revision INTEGER NOT NULL DEFAULT 1 CHECK(assignment_revision > 0);
ALTER TABLE assignments ADD COLUMN assignment_revision INTEGER NOT NULL DEFAULT 1 CHECK(assignment_revision > 0);
