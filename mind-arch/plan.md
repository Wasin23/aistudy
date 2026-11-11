# Body

## Effectors (motor outputs)
- **Walk** — move one cell. Costs `ENERGY_PER_MOVE`. Speed scaled by strength multiplier.
- **Fight** — engage a target. Costs `ENERGY_PER_FIGHT`. Outcome odds scaled by strength multiplier.
- **Forage** — attempt to harvest from current cell. No direct energy cost yet.

---

# Feelings (nervous system / proto-emotions)

## Damage signals
- **Pain** — rate of health loss. Fires when health is actively falling. Derivative.
- **Ache** — accumulated damage. Where you are in the health sections, duration under stress. Integral.

## Deficit signals
- **Hunger** — body needs something it isn't getting. Health declining over time with no input.
- **Satiation** — recent positive input. Opposite of hunger.

## Activation signals
- **Arousal** — readiness, alertness. Nervous system lit up. Driven by senses firing.
- **Calm** — low activation. Senses quiet, body stable.
