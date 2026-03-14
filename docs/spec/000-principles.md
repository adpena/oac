# Principles

1. **Files are canonical.**
   Markdown, YAML, and JSON are the source of truth.

2. **Adapters are bidirectional compilers.**
   They hydrate native surfaces and ingest native edits back into typed candidates.

3. **Native projections stay native.**
   OpenClaw should look like OpenClaw. Claude Code should look like Claude Code.

4. **Ownership must be explicit.**
   Managed files, managed sections, imported files, and sidecars are different things.

5. **Learning is gated and collaborative.**
   Native edits become candidate bundles first, then proposals, then eval-gated promotion. Multi-writer conflicts are explicitly detected and resolved via merge policies.

6. **Runtime state is not portable by accident.**
   Secrets, auth, caches, and machine-local state are never silently captured in the shared capsule. Ingest explicitly filters for durable knowledge.
