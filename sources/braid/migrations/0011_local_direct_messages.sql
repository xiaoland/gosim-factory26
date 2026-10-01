ALTER TABLE events ADD COLUMN recipient_login TEXT;
CREATE TABLE local_comment_delivery (
    comment_id INTEGER NOT NULL REFERENCES local_comments(comment_id),
    recipient_login TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('queued','delivered','unreachable','self')),
    reason TEXT,
    event_id TEXT REFERENCES events(event_id),
    PRIMARY KEY(comment_id,recipient_login)
) STRICT;
