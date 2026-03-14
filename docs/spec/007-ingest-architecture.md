# Ingest architecture

## Goal

Ingest should be boring, deterministic, and profile-aware.
It should feel like a compiler pass, not a magical memory vacuum.

## Pipeline

```text
discover paths -> parse native surfaces -> classify into candidate kinds ->
attach ownership/portability/lossiness -> emit candidate bundle hints -> report
```

## Key abstractions

- `IngestPlan` — target-level declarative scan contract
- `IngestRule` — one surface pattern plus parser and candidate metadata
- `IngestCandidate` — typed candidate extracted from a native surface
- `IngestReport` — deterministic result summary with counters and notes

## Why this shape

This keeps the starter:

- composable — every adapter can reuse the same engine
- profile-aware — path overrides affect ingest too
- performant — only declared surfaces are scanned
- honest — read-only targets can say so explicitly
- extensible — future proposal/promotion layers can consume the same report format

## Incremental scanning

Ingest supports optimized scanning via deterministic **fingerprints**.
When an optional `--state` file is provided, OAC tracks the hash of every ingested record. Subsequent runs will only include records that have changed or are new, skipping unchanged files to reduce I/O and proposal noise. This is the primary mechanism for scaling OAC to large memory surfaces.

## Candidate bundle hints

The starter does not write candidate bundle files yet.
It emits stable path hints like:

```text
.oac/candidates/<target>/...
```

That is the seam where proposal records will land next.
