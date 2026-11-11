# Rules

## Health

A mind has 100 health split into three sections: top (50), mid (35), bot (15).
Healing fills top first, then mid, then bot. Damage drains top first, then mid, then bot.

## Energy

A mind starts with 1000 energy. Energy is fat storage — it depletes through use and is replenished by eating.
Each sense write costs 1 energy. Walking costs `ENERGY_PER_MOVE`. Fighting costs `ENERGY_PER_FIGHT`.

## Strength

Strength is a multiplier from 0.1 to 1.0, starting at 1.0.
Damage reduces it proportionally. Healing restores it proportionally.
Strength scales movement speed and fight odds.

## Senses

A mind has five senses: sight, hearing, touch, smell, taste.
Each is a stream — a sliding window of up to 50 values. The world writes via `use_sense()`; oldest values are pushed out. The mind reads but does not write them.

### What the world writes each tick

- **Touch** — terrain underfoot as a float: plain=0.0, fertile=0.5, harsh=1.0. One write per tick.
- **Smell** — strongest resource signal within 20 cells: `1/(1+dist)`. Zero if nothing nearby. One write per tick.
- **Sight** — up to 3 writes per tick: one `(terrain_type, distance)` tuple for the nearest cell of each terrain type in the vision cone.
- **Hearing** — one ambient baseline write per tick at intensity 0.1. Additional `("mind", proximity)` writes for each other mind in view.
- **Taste** — one write per tick while standing on a resource cell: value is `harvest_progress / HARVEST_TICKS` (rises from 0 to 1 as harvest completes). Silent otherwise.

## Effectors

A mind has three motor outputs: walk, fight, forage.
Walk costs `ENERGY_PER_MOVE * strength`. Fight costs `ENERGY_PER_FIGHT * strength`. Forage signals intent to the world.

## PNS

The peripheral nervous system sits between body and CNS.
It tracks five neurotransmitters (0.0–1.0): dopamine, serotonin, norepinephrine, cortisol, endorphin.

- **Dopamine** — learned anticipation. Driven by the association layer's expected health outcome for the current sense pattern. High when current senses predict gain; low when they predict loss or nothing.
- **Serotonin** — learned contentment. Driven by a rolling average of recent expected outcomes. Rises with sustained positive history; falls with sustained negative or volatile history.
- **Norepinephrine** — hardcoded reflex. Driven by damage rate and sense overwhelm. Fast spike, fast decay.
- **Cortisol** — hardcoded integrator. Driven by sustained low health or low energy. Slow to rise, slow to fall.
- **Endorphin** — hardcoded reflex. Driven by exertion and recovery after damage. Relief signal.

Intensity is the balance of activating (norepinephrine + cortisol) vs suppressing (serotonin + endorphin) transmitters.
Mode is binary and hardcoded: rest-and-digest below threshold, fight-or-flight above.
The CNS reads neurotransmitters, intensity, and mode — never raw body state directly.

## Association Layer

Lives inside the PNS. Implements Pavlovian learning between sense patterns and health outcomes.

Each tick it:
1. Snapshots the five sense streams into a 7-tuple: `(touch, smell, taste, sight_plain, sight_fertile, sight_harsh, hearing)` — each bucketed low/mid/high (0/1/2).
2. Queues the snapshot with the current health value, to be resolved 10 ticks later.
3. On resolution: computes `health_now - health_then`, normalizes to 0–1, and updates the table entry for that snapshot via exponential moving average (α=0.1).
4. Looks up the current snapshot's expected outcome from the table (defaults to 0.5 until seen).

The expected outcome drives dopamine directly. A 20-tick rolling average of expected outcomes drives serotonin.

## CNS

The central nervous system reads PNS state only — never body or senses directly.
It maintains a short-term memory (deque of recent PNS snapshots) and a long-term transition table mapping PNS state → most likely next PNS state.
Each tick it measures surprise (how wrong the last prediction was) and updates the transition table.
