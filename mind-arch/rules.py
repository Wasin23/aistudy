"""
Hidden from all minds. Server applies these; minds infer them from outcomes.

Phase 2: 6-position, 10-value stream (10^6 = 1,000,000 possible patterns).
Rules are computed on demand via deterministic hash — nothing stored per pattern.
Each mind's identity is a (salt, biome_profile) pair.
  - biome  = pattern[0]  (0-9), sets the environmental prior
  - salt   = random int, differentiates per-pattern noise between minds
  - effect = biome_profile[biome] + hash_noise(pattern, salt)
"""

import hashlib
import itertools
import random

N_POSITIONS = 6
N_VALUES    = 10   # digits 0–9
N_BIOMES    = 10   # biome = pattern[0], so 10 possible biomes

FIGHT_PATTERNS = list(itertools.product(range(2), repeat=4))  # 16 binary, unchanged

# ── Biome profile shape ───────────────────────────────────────────────────────
N_JACKPOT = 2   # biomes that earn well
N_DECENT  = 0   # biomes that earn a little
N_HOSTILE = 8   # biomes that hurt  (80% of patterns are hostile)

NOISE_RANGE = 5  # hash % 5 → {0,1,2,3,4}, shifted by 2 → {-2,-1,0,+1,+2}

# ── Drift config ──────────────────────────────────────────────────────────────
DRIFT_THRESHOLD = 30
DRIFT_PROB      = 0.003

# ── Fight drift config (unchanged) ───────────────────────────────────────────
FIGHT_DRIFT_PROB  = 0.15
FIGHT_DRIFT_RANGE = (-6, 6)


def _hash_noise(pattern, salt):
    """Deterministic per-(pattern, salt) noise. Returns int in [0, NOISE_RANGE)."""
    data = f"{pattern}:{salt}"
    h    = int(hashlib.md5(data.encode(), usedforsecurity=False).hexdigest()[:8], 16)
    return h % NOISE_RANGE


def compute_effect(pattern, salt, biome_profile):
    """Hidden rule effect for a pattern given a mind's salt + biome profile."""
    biome = pattern[0]
    base  = biome_profile[biome]
    noise = _hash_noise(pattern, salt) - (NOISE_RANGE // 2)
    return base + noise


def get_biome(pattern):
    """Biome is always the first digit of the pattern."""
    return pattern[0]


def generate_random_rules(rng=None):
    """
    Generate a unique rule identity for one mind.
    Returns (salt, biome_profile).
    biome_profile maps biome index (0-9) → base effect value.
    2 jackpot biomes, 3 decent, 5 hostile — shuffled randomly.
    """
    if rng is None:
        rng = random

    salt   = rng.randint(0, 10 ** 9)
    biomes = list(range(N_BIOMES))
    rng.shuffle(biomes)

    biome_profile = {}
    for rank, b in enumerate(biomes):
        if rank < N_JACKPOT:
            biome_profile[b] = rng.randint(8, 12)
        elif rank < N_JACKPOT + N_DECENT:
            biome_profile[b] = rng.randint(1, 5)
        else:
            biome_profile[b] = rng.randint(-10, -5)

    return salt, biome_profile


def generate_random_fight_rules(rng=None):
    """16 binary fight patterns, hidden per mind. Unchanged from Phase 1."""
    if rng is None:
        rng = random
    n_jackpots   = rng.randint(2, 4)
    jackpot_pats = rng.sample(FIGHT_PATTERNS, n_jackpots)
    jackpots     = {p: rng.randint(5, 9) for p in jackpot_pats}
    effects      = {}
    for p in FIGHT_PATTERNS:
        effects[p] = jackpots[p] if p in jackpots else rng.randint(-7, 3)
    return effects


def drift_biome(biome_profile, rng=None):
    """Shift one random biome's base value. Returns (biome, old, new)."""
    if rng is None:
        rng = random
    biome = rng.choice(list(biome_profile.keys()))
    old   = biome_profile[biome]
    delta = rng.choice([-3, -2, -1, 1, 2, 3])
    new   = max(-12, min(14, old + delta))
    biome_profile[biome] = new
    return biome, old, new


def fight_drift_one(effects, rng=None):
    """Shift one random fight rule. Returns (pattern, old, new)."""
    if rng is None:
        rng = random
    pattern = rng.choice(FIGHT_PATTERNS)
    old     = effects[pattern]
    new     = rng.randint(*FIGHT_DRIFT_RANGE)
    while new == old:
        new = rng.randint(*FIGHT_DRIFT_RANGE)
    effects[pattern] = new
    return list(pattern), old, new
