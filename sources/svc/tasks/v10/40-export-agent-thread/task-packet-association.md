# Task-Packet Association

## Why lexical association

An exported thread can contain several tasks, historical paths, quoted examples,
and arbitrary tool output. Semantic inference would make evidence selection
unreviewable. The first protocol therefore treats each textual `tasks/...` match as
evidence, not as a claim of ownership.

## Proposed Algorithm

1. Traverse only user/assistant message-like record content in provider order;
   do not mine arbitrary tool arguments, tool outputs, shell output, or opaque
   reasoning. Record bounded lexical candidates plus source line, record type,
   field path, and exact matched path—not the surrounding message body.
2. Parse a candidate as a relative POSIX-style path. Reject absolute paths,
   `..`, NULs, unsupported encodings, and paths that resolve outside the current
   repository's physical `tasks/` directory.
3. Resolve a candidate to either a task packet file or a packet directory. A
   directory must contain `packet.md`; its complete subtree becomes the smallest
   copy unit.
4. De-duplicate by physical repository-relative packet root while retaining every
   occurrence's provenance in the manifest.
5. Copy every valid root with archive-safe paths and hashes through streaming,
   descriptor-bound reads. A missing, invalid, unsafe, or resource-bounded
   candidate remains a provenance warning in the manifest; it cannot silently
   expand the archive or discard the raw thread evidence.

Several packet roots are expected in a long-lived thread. Including all valid,
provenanced roots is more honest than pretending one is “the” packet. A future
explicit include/exclude surface may narrow this set, but must retain the complete
candidate ledger.

## Integrity and Privacy

The exporter must not follow symlinks out of the selected packet tree, and it must
not modify task files. A manifest entry should distinguish a referenced packet
that is missing locally from a validated packet copied into the archive. This
keeps the archived evidence honest when a task packet was deleted as disposable
work state.
