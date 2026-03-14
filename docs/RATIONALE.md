# Rationale for Open Agent Capsule (OAC)

## Technical Context
As agentic systems evolve, maintaining a consistent state across different models and harnesses is a core technical challenge. Currently, an agent's persona, operating procedures, and memory are often trapped in proprietary configurations or model-specific blobs.

**OAC defines a canonical format for agent state**, allowing the intelligence (the Capsule) to exist independently of the specific execution harness.

---

## 1. Harness Portability
When an agent's state is stored in a standardized, file-first format, it can be moved between different model providers and execution tools without manual reconfiguration. OAC adapters automate the translation of this state into whatever native format a specific harness requires.

## 2. Verified Configuration
Maintaining the integrity of an agent's operating rules is critical. OAC treats the agent's "brain" as a versioned artifact. Every change must pass automated evaluation gates and be cryptographically signed (HMAC or SSH) before it is promoted. This ensures that the agent's behavior is derived from a known, verified source.

## 3. Context Pruning
Loading an entire agent memory into a single prompt is inefficient and introduces noise. OAC uses structural indexing and selective hydration to ensure that an agent only receives the specific records relevant to its current task. This increases response reliability and reduces unnecessary data processing.

---

## Conclusion
Agents require a durable, portable state to be useful across different environments. OAC provides the infrastructure to make that state manageable and transparent.
