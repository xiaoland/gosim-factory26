ALTER TABLE provider_sessions ADD COLUMN cli_binding_id TEXT;
CREATE UNIQUE INDEX provider_sessions_cli_binding ON provider_sessions(cli_binding_id)
WHERE cli_binding_id IS NOT NULL;
