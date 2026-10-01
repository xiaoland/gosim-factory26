# Analysis fixture corpus

These sanitized fixtures preserve the native JSONL shapes needed by the analysis
contract. Codex covers a root/child delegation and cumulative token samples. Pi
covers a branched v3 session, compaction usage, and a fork linked through
`parentSession`. The manually calculated facts in `oracle.json` are independent
of the implementation under test.

Source formats were checked against OpenAI Codex rollout protocol and Pi session
v3 on 2026-09-19. The corpus deliberately excludes Pi subagent extensions.
