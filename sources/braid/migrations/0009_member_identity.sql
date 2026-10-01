ALTER TABLE local_run ADD COLUMN next_member_sequence INTEGER NOT NULL DEFAULT 0 CHECK(next_member_sequence >= 0);
ALTER TABLE local_items ADD COLUMN desired_member_login TEXT;
ALTER TABLE assignments ADD COLUMN member_login TEXT;
CREATE UNIQUE INDEX assignments_member_login
ON assignments(member_login)
WHERE member_login IS NOT NULL;
