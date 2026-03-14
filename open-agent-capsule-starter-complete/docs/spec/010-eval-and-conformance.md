# Eval and conformance

## Starter eval goal

The starter eval is deliberately structural.
It proves that the capsule can still load and that each enabled target can still complete a hydrate + ingest round-trip.

It does **not** pretend to be a semantic quality benchmark.

## Eval steps

1. validate the manifest
2. reload the canonical capsule
3. optionally stage promotable proposal changes into a temporary copy
4. hydrate every selected enabled target
5. ingest each hydrated target back into typed candidates
6. fail the run if any step raises or produces an invalid state

## Conformance command

`oac conformance` is the same structural mechanism without a proposal bundle.
It is the starter's way of proving that adapters still compose with the canonical capsule contract.

## Why this matters

This gate is intentionally humble, but it forces the project to keep:

- adapter outputs deterministic enough to round-trip
- canonical paths valid after promotion
- review and promotion separated from native execution

## What still needs to grow

- semantic eval slices by canonical kind
- target-specific regression suites
- performance budgets and benchmark baselines
- policy-aware selective eval for large capsules
