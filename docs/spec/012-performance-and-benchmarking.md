# Performance and benchmarking

## Monitoring cost

OAC includes a built-in benchmark suite to monitor the computational and I/O cost of core operations.
Run benchmarks with:
```bash
make benchmark
```
This measures the average time for `hydrate`, `ingest`, and `eval` across all enabled targets using the example capsule.

## Optimization strategies

### Incremental I/O

Both hydration and ingestion are optimized for large-scale capsules:
- **Incremental Hydration:** Uses `write_if_changed` to only touch files that have actually been modified in the capsule.
- **Incremental Ingest:** Uses a persistent `--state` file to track record fingerprints, scanning only new or changed native files.

### Selective hydration

For large capsules or focused development, the `hydrate` command supports a `--kind` filter. This allows hydrating only a specific subset of the capsule (e.g. just `identity.persona`), reducing projection time.

### Fast discovery

Derived indexes provide O(1) or O(log N) lookup for records:
- `index`: Full-text keyword mapping.
- `structural-index`: Fast metadata lookup by kind, tag, or record ID.
