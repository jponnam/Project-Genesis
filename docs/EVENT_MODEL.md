# Event model

Every meaningful simulation change is recorded as a typed **domain event**. Events are the contract between the live engine and offline tooling (replay, inspect, analytics, observatory).

## Lifecycle

1. Systems and executors construct a concrete `DomainEvent` subclass.
2. The event bus publishes it during the tick.
3. `DomainEvent.to_record()` serializes to a JSON-friendly dict.
4. `JsonlEventStore` appends one JSON object per line.
5. Readers use `event_from_record` / `EVENT_TYPE_REGISTRY` to rehydrate typed events.

## Record shape (persistence)

Typical fields on each JSONL line:

| Field | Meaning |
|-------|---------|
| `schema_version` | Event schema version for forward compatibility |
| `event_id` | Stable unique id |
| `tick` | Simulation tick when emitted |
| `event_type` | Registry key (e.g. `agent_born`, `trade_executed`) |
| `payload` | Type-specific fields |
| timestamps / metadata | As defined by the base event contract |

Exact keys are defined in `civitas.domain.events` and verified by round-trip tests.

## Coverage

There are **65** concrete `DomainEvent` types registered for persistence. Categories include:

- Lifecycle: birth, death, population census
- Needs & resources: gather, consume, produce, energy/water/food
- Economy: trade, prices, wealth census (includes Gini / top-share bps)
- Social: relationships, trust, reputation, families, networks
- Governance: laws, votes, institutions, taxes, treasury
- Knowledge: research, innovation, diffusion, teaching, memory
- Built environment: infrastructure, cities, technology unlocks

Bootstrap seed worlds also emit foundational placement events (fire, fire hearth, tax schedule, council, well, settlement).

## What events do *not* give you

- Full final **resource holdings** per agent (only flows and some census snapshots).
- A byte-identical in-memory `World` object without re-running the engine from the same config and seed.
- Guarantees about events from future schema versions without a migration path.

For research, prefer metrics that the analytics engine already derives from the log (see [ANALYTICS.md](ANALYTICS.md)).
