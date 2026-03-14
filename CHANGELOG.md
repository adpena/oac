# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-03-14

### Added
- Multi-writer sync with merge policies and conflict resolution
- Stable record IDs for robust long-term provenance tracking
- MCP discovery surface for record retrieval (`oac serve-mcp`)
- Incremental ingest with content fingerprinting
- Lexical and structural indexing (`oac index`, `oac structural-index`)
- Deterministic snapshot packaging with HMAC-SHA256 and SSH-Ed25519 signing
- Adapter Conformance Kit (`oac ack`)
- Performance benchmarks in test suite

### Changed
- Proposal bundles now include conflict metadata for multi-writer scenarios
- Improved error messages across all CLI commands

## [0.2.0] - 2026-03-01

### Added
- Proposal and promotion engine with reversible operations
- Structural and semantic evaluation gates (`oac eval`)
- Ingest paths for all 5 primary targets (Codex, Claude Code, OpenClaw, OpenCode, Gemini)
- Typed candidate bundles with ownership tracking
- Backup and revert system for promotions

## [0.1.0] - 2026-02-15

### Added
- Canonical capsule format specification (manifest.yaml, record kinds)
- Adapter model with bidirectional hydrate/ingest
- Bundled profiles for 7 targets
- CLI foundation (`oac validate`, `oac hydrate`, `oac targets`)
- Example capsule (`examples/hello-capsule/`)
- Normative specification documents (13 specs)
