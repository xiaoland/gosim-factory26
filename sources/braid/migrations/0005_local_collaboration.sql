ALTER TABLE local_items ADD COLUMN parent_issue TEXT REFERENCES local_items(node_id);
ALTER TABLE local_comments ADD COLUMN reply_to INTEGER REFERENCES local_comments(comment_id);
ALTER TABLE local_comments ADD COLUMN thread_root INTEGER REFERENCES local_comments(comment_id);
ALTER TABLE local_comments ADD COLUMN resolved_through INTEGER REFERENCES local_comments(comment_id);
ALTER TABLE local_comments ADD COLUMN hide_reason TEXT;
UPDATE local_comments SET thread_root=comment_id;
CREATE INDEX local_comment_threads ON local_comments(thread_root,comment_id);
CREATE TABLE local_comment_reactions (
    comment_id INTEGER NOT NULL REFERENCES local_comments(comment_id),
    actor TEXT NOT NULL,
    expression TEXT NOT NULL CHECK(length(trim(expression))>0),
    PRIMARY KEY(comment_id,actor,expression)
) STRICT;
