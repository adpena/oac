# Learning loop

The full loop is:

```text
hydrate -> work natively -> ingest -> candidate bundle -> propose -> eval -> promote -> snapshot
```

## What is implemented in the starter

Implemented now:

- hydrate
- ingest
- deterministic candidate reports
- explicit proposal records with canonical destinations and diffs
- structural eval gate
- reversible promotion with backups
- deterministic local snapshots

Still future work:

- semantic or task-quality evals
- learned ranking or promotion scoring
- signed releases and remote registry flow
- multi-writer sync and policy-aware merge

## Intended promotion destinations

- stable rule -> canonical procedure/behavior record
- stable preference -> semantic memory
- repeatable workflow -> skill or workflow record
- specialist prompt -> canonical procedures/agents record
- ephemeral session detail -> stay episodic or be dropped
- target-local config or hook logic -> remain deferred until explicitly abstracted

## Hard rule

No direct uncontrolled write-back from a running harness into the canonical capsule.
Every durable change should become a typed candidate before proposal or promotion.
