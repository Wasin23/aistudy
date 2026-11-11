"""
2D simulation — world, resources, minds.
Server imports Sim2D and calls sim.step() each tick.
"""

import random
from collections import deque

SENSE_BANDWIDTH  = 50
ENERGY_START     = 1000.0
ENERGY_PER_MOVE  = 5.0
ENERGY_PER_FIGHT = 10.0

STRENGTH_MIN = 0.1
STRENGTH_MAX = 1.0

# ── World ──────────────────────────────────────────────────────────────────────

GRID_W      = 46
GRID_H      = 46
N_MINDS     = 1
N_RESOURCES = 5
HARVEST_TICKS  = 12
HARVEST_HEALTH = 30.0
HARVEST_ENERGY = 200.0

HEALTH_TOP = 50.0   # noncritical buffer
HEALTH_MID = 35.0
HEALTH_BOT = 15.0   # critical core
SIGHT_LENGTH = 15
SIGHT_WIDTH  = 1

T_PLAIN    = 0
T_FERTILE  = 1
T_HARSH    = 2
T_RESOURCE = 3   # pseudo-terrain written to sight when a resource is visible

SMELL_RANGE    = 20
_TERRAIN_TOUCH = {T_PLAIN: 0.0, T_FERTILE: 0.5, T_HARSH: 1.0}

TERRAIN = [
    {"color": "#0d0d0f", "label": "plain"},
    {"color": "#0a130a", "label": "fertile"},
    {"color": "#160808", "label": "harsh"},
]

MIND_COLORS = ["#ff5050", "#44ddff", "#55ff99", "#ffaa33", "#cc55ff"]
FACE_DIRS   = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


_NC = "ABCDEFGHJKLMNPQRSTUVWXYZ"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _gen_name():
    return "".join(random.choices(_NC, k=3))



_SIGHT_AXES = {
    "N":  {"fwd": ( 0, -1), "perp": ( 1,  0)},
    "NE": {"fwd": ( 1, -1), "perp": ( 1,  1)},
    "E":  {"fwd": ( 1,  0), "perp": ( 0,  1)},
    "SE": {"fwd": ( 1,  1), "perp": ( 1, -1)},
    "S":  {"fwd": ( 0,  1), "perp": ( 1,  0)},
    "SW": {"fwd": (-1,  1), "perp": ( 1,  1)},
    "W":  {"fwd": (-1,  0), "perp": ( 0,  1)},
    "NW": {"fwd": (-1, -1), "perp": ( 1, -1)},
}


def _visible_cells(mx, my, facing):
    ax      = _SIGHT_AXES[facing]
    fwd     = ax["fwd"]
    perp    = ax["perp"]
    is_diag = fwd[0] != 0 and fwd[1] != 0
    scale   = 2 if is_diag else 1
    out     = {(mx % GRID_W, my % GRID_H)}
    rng     = SIGHT_LENGTH + 2
    for rdy in range(-rng, rng + 1):
        for rdx in range(-rng, rng + 1):
            if rdx == 0 and rdy == 0:
                continue
            fwd_dot  = rdx * fwd[0]  + rdy * fwd[1]
            perp_dot = abs(rdx * perp[0] + rdy * perp[1])
            if fwd_dot < 1 or fwd_dot > SIGHT_LENGTH * scale:
                continue
            if perp_dot > SIGHT_WIDTH * scale:
                continue
            out.add(((mx + rdx) % GRID_W, (my + rdy) % GRID_H))
    return list(out)


def _mdist(x1, y1, x2, y2):
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    return min(dx, GRID_W - dx) + min(dy, GRID_H - dy)


def generate_world():
    seeds = []
    for _ in range(20):
        roll = random.random()
        t = T_PLAIN if roll < 0.60 else (T_FERTILE if roll < 0.85 else T_HARSH)
        seeds.append((random.uniform(0, GRID_W), random.uniform(0, GRID_H), t))
    world = []
    for y in range(GRID_H):
        row = []
        for x in range(GRID_W):
            min_d = float("inf")
            t = T_PLAIN
            for sx, sy, st in seeds:
                d = (x - sx) ** 2 + (y - sy) ** 2
                if d < min_d:
                    min_d = d
                    t = st
            row.append(t)
        world.append(row)
    return world


# ── Resource ───────────────────────────────────────────────────────────────────

class Resource:
    def __init__(self):
        self.x = random.randrange(GRID_W)
        self.y = random.randrange(GRID_H)
        self.harvesting       = None
        self.harvest_progress = 0
        self.flash            = 0

    def relocate(self):
        self.x                = random.randrange(GRID_W)
        self.y                = random.randrange(GRID_H)
        self.harvesting       = None
        self.harvest_progress = 0
        self.flash            = 8

    def to_dict(self):
        return {
            "x": self.x, "y": self.y,
            "harvest_progress": self.harvest_progress,
            "flash": self.flash,
        }


# ── Boar ──────────────────────────────────────────────────────────────────────

class Boar:
    ENERGY_MAX      = 200.0
    ENERGY_REGEN    = 1.5    # per tick while wandering
    ENERGY_PER_MOVE = 6.0    # per tick while chasing
    NOTICE_RADIUS   = 8
    ABANDON_RADIUS  = 14
    DAMAGE_PER_TICK = 5.0
    WANDER_CHANCE   = 0.15

    def __init__(self):
        self.x      = random.randrange(GRID_W)
        self.y      = random.randrange(GRID_H)
        self.energy = self.ENERGY_MAX
        self.state  = "wandering"
        self.target = None

    def step(self, minds):
        events = []

        # find target
        target_mind = next((m for m in minds if m.id == self.target), None)

        # state transitions
        if self.state == "wandering":
            for m in minds:
                if _mdist(self.x, self.y, m.x, m.y) <= self.NOTICE_RADIUS:
                    self.state  = "chasing"
                    self.target = m.id
                    target_mind = m
                    events.append(f"BOAR noticed M{m.id}({m.name}) dist={_mdist(self.x,self.y,m.x,m.y)}")
                    break
        elif self.state == "chasing":
            if target_mind is None:
                self.state, self.target = "wandering", None
            else:
                dist = _mdist(self.x, self.y, target_mind.x, target_mind.y)
                if dist > self.ABANDON_RADIUS:
                    self.state, self.target = "wandering", None
                    events.append(f"BOAR gave up on M{target_mind.id} dist={dist}")

        # movement
        if self.state == "chasing" and target_mind and self.energy > 0:
            dx = target_mind.x - self.x
            dy = target_mind.y - self.y
            if dx >  GRID_W / 2: dx -= GRID_W
            if dx < -GRID_W / 2: dx += GRID_W
            if dy >  GRID_H / 2: dy -= GRID_H
            if dy < -GRID_H / 2: dy += GRID_H
            sx = 1 if dx > 0 else (-1 if dx < 0 else 0)
            sy = 1 if dy > 0 else (-1 if dy < 0 else 0)
            self.x = (self.x + sx) % GRID_W
            self.y = (self.y + sy) % GRID_H
            self.energy = max(0.0, self.energy - self.ENERGY_PER_MOVE)
            if self.energy == 0:
                events.append(f"BOAR exhausted at ({self.x},{self.y})")
        elif self.state == "wandering":
            if random.random() < self.WANDER_CHANCE:
                dx, dy = random.choice([(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)])
                self.x = (self.x + dx) % GRID_W
                self.y = (self.y + dy) % GRID_H
            self.energy = min(self.ENERGY_MAX, self.energy + self.ENERGY_REGEN)

        # damage and hearing on contact
        for m in minds:
            if m.x == self.x and m.y == self.y:
                m.damage(self.DAMAGE_PER_TICK)
                m.use_sense("hearing", ("boar_contact", 1.0))
                events.append(f"BOAR hits M{m.id}({m.name}) hp={m.health:.0f}")

        # hearing warning for minds in notice range
        for m in minds:
            d = _mdist(self.x, self.y, m.x, m.y)
            if 0 < d <= self.NOTICE_RADIUS:
                m.use_sense("hearing", ("boar", 1.0 / (1.0 + d)))

        return events

    def to_dict(self):
        return {
            "x":      self.x,
            "y":      self.y,
            "state":  self.state,
            "energy": round(self.energy, 1),
        }


# ── PNS ───────────────────────────────────────────────────────────────────────

FIGHT_OR_FLIGHT_THRESHOLD = 0.6
CNS_STM_SIZE              = 20    # short-term memory ticks

ASSOCIATION_DELAY = 10    # ticks between sense snapshot and outcome check
ASSOCIATION_ALPHA = 0.20  # EMA learning rate for outcome table
TASTE_ALPHA       = 0.25  # immediate reinforcement rate when eating


# ── Association Layer ─────────────────────────────────────────────────────────

class AssociationLayer:
    """
    Pavlovian association memory inside PNS.
    Snapshots sense state each tick, defers outcome measurement by
    ASSOCIATION_DELAY ticks, then learns: this sense pattern → that health change.
    Drives dopamine (current expectation) and serotonin (stable history).
    """

    def __init__(self):
        self._table      = {}                # sense_snap → EMA outcome (0..1)
        self._pending    = []                # (tick_due, sense_snap, health_then)
        self.expected    = 0.35
        self._recent     = deque(maxlen=20)  # history of expected values
        self.last_snap   = None              # snapshot taken this tick
        self.last_updates = []              # (snap, outcome, new_val) for entries resolved this tick

    def _sense_snap(self, body):
        def b(v):
            return 0 if v < 0.33 else (1 if v < 0.66 else 2)

        tv = list(body.touch)
        touch = (sum(tv) / len(tv)) if tv else 0.0

        sv = list(body.smell)
        smell = max(sv) if sv else 0.0

        taste = list(body.taste)[-1] if body.taste else 0.0

        sight_vals = [v for v in body.sight if isinstance(v, tuple) and len(v) == 2]
        by_terrain = {T_PLAIN: [], T_FERTILE: [], T_HARSH: [], T_RESOURCE: []}
        for t, d in sight_vals:
            if t in by_terrain:
                by_terrain[t].append(1.0 / (1.0 + d))
        def avg(lst): return (sum(lst) / len(lst)) if lst else 0.0
        sight_plain    = avg(by_terrain[T_PLAIN])
        sight_fertile  = avg(by_terrain[T_FERTILE])
        sight_harsh    = avg(by_terrain[T_HARSH])
        sight_resource = avg(by_terrain[T_RESOURCE])

        hearing = min(1.0, len(body.hearing) / 10.0)

        return (b(touch), b(smell), b(taste),
                b(sight_plain), b(sight_fertile), b(sight_harsh),
                b(sight_resource), b(hearing))

    def tick(self, body, tick):
        total      = HEALTH_TOP + HEALTH_MID + HEALTH_BOT
        health_now = body.health
        snap_now   = self._sense_snap(body)
        self.last_snap    = snap_now
        self.last_updates = []

        # Immediate reinforcement: taste directly signals eating progress now
        taste_now = list(body.taste)[-1] if body.taste else 0.0
        if taste_now > 0.0:
            curr = self._table.get(snap_now, 0.5)
            self._table[snap_now] = curr * (1 - TASTE_ALPHA) + 0.85 * TASTE_ALPHA

        remaining = []
        for tick_due, old_snap, health_then in self._pending:
            if tick >= tick_due:
                delta   = (health_now - health_then) / total  # −1..1
                outcome = delta * 0.5 + 0.5                   # normalize to 0..1
                prev    = self._table.get(old_snap, 0.5)
                new_val = prev * (1.0 - ASSOCIATION_ALPHA) + outcome * ASSOCIATION_ALPHA
                self._table[old_snap] = new_val
                self.last_updates.append((old_snap, round(outcome, 3), round(new_val, 3)))
            else:
                remaining.append((tick_due, old_snap, health_then))
        self._pending = remaining

        self._pending.append((tick + ASSOCIATION_DELAY, snap_now, health_now))

        self.expected = self._table.get(snap_now, 0.35)
        self._recent.append(self.expected)

    @property
    def dopamine_drive(self):
        return self.expected

    @property
    def serotonin_drive(self):
        if not self._recent:
            return 0.5
        return sum(self._recent) / len(self._recent)


class PNS:
    """
    Peripheral nervous system. Reads body state, produces neurotransmitter levels,
    derives intensity and mode. CNS reads from here — never from the body directly.
    """

    MODES = ("rest_and_digest", "fight_or_flight")

    def __init__(self, body):
        self.body = body

        # ── Neurotransmitters (0.0 – 1.0) ────────────────────────────────────
        self.dopamine       = 0.3   # anticipation, drive, seeking
        self.serotonin      = 0.5   # contentment, stability, calm
        self.norepinephrine = 0.0   # alertness, urgency
        self.cortisol       = 0.0   # sustained stress
        self.endorphin      = 0.0   # pain suppression, relief

        # ── Derived ───────────────────────────────────────────────────────────
        self.intensity = 0.0                  # 0.0 – 1.0, gain on all signals
        self.mode      = "rest_and_digest"    # binary, hardcoded threshold

        self._prev_health  = body.health
        self._prev_energy  = body.energy
        self._prev_delta   = 0.0
        self._stress_ticks = 0
        self._prev_mode    = "rest_and_digest"
        self._tick         = 0
        self._assoc        = AssociationLayer()

    def tick(self):
        self._tick += 1
        body = self.body

        # ── Read body ─────────────────────────────────────────────────────────
        current_health    = body.health
        self.health_delta = current_health - self._prev_health
        self._prev_health = current_health

        health_ratio = current_health / (HEALTH_TOP + HEALTH_MID + HEALTH_BOT)
        energy_ratio = min(1.0, body.energy / ENERGY_START)

        # sense activity: how full are the streams (0.0–1.0)
        sense_activity = (
            len(body.sight) + len(body.hearing) +
            len(body.touch) + len(body.smell) + len(body.taste)
        ) / (SENSE_BANDWIDTH * 5)

        # damage rate: how fast health is dropping (0.0–1.0)
        damage_rate = max(0.0, min(1.0, -self.health_delta / 15.0))

        # exertion: action energy only (walk/fight), not sense drain
        total_spent   = max(0.0, self._prev_energy - body.energy)
        action_spent  = max(0.0, total_spent - body.last_sense_cost)
        exertion      = min(1.0, action_spent / ENERGY_PER_FIGHT)
        self._prev_energy = body.energy

        # stress accumulator for cortisol
        if health_ratio < 0.3 or energy_ratio < 0.2:
            self._stress_ticks += 1
        else:
            self._stress_ticks = max(0, self._stress_ticks - 5)

        # ── Association layer: sense snapshot → deferred health outcome ─────────
        self._assoc.tick(body, self._tick)

        # ── Dopamine: learned anticipation from sense→outcome associations ──────
        self.dopamine = max(0.0, min(1.0, self.dopamine * 0.9 + self._assoc.dopamine_drive * 0.1))

        # ── Serotonin: learned contentment from stable outcome history ──────────
        self.serotonin = max(0.0, min(1.0, self.serotonin * 0.95 + self._assoc.serotonin_drive * 0.05))

        # ── Norepinephrine: alarm — damage rate + sense overwhelm ─────────────
        norepi_drive = damage_rate * 0.7 + max(0.0, sense_activity - 0.7) * 0.3
        self.norepinephrine = max(0.0, min(1.0, self.norepinephrine * 0.8 + norepi_drive * 0.2))

        # ── Cortisol: sustained stress — slow integrator ──────────────────────
        cortisol_drive = min(1.0, self._stress_ticks / 50.0)
        self.cortisol = max(0.0, min(1.0, self.cortisol * 0.97 + cortisol_drive * 0.03))

        # ── Endorphin: exertion + recovery after damage ───────────────────────
        recovery = max(0.0, self.health_delta / 10.0) if self._prev_delta < 0 else 0.0
        endorphin_drive = exertion * 0.6 + recovery * 0.4
        self.endorphin = max(0.0, min(1.0, self.endorphin * 0.85 + endorphin_drive * 0.15))
        self._prev_delta = self.health_delta

        # ── Intensity: activating vs suppressing balance ──────────────────────
        activating  = (self.norepinephrine + self.cortisol) / 2
        suppressing = (self.serotonin + self.endorphin) / 2
        self.intensity = max(0.0, min(1.0, activating - suppressing + 0.5))

        # ── Mode: hardcoded threshold ─────────────────────────────────────────
        self.mode = (
            "fight_or_flight" if self.intensity >= FIGHT_OR_FLIGHT_THRESHOLD
            else "rest_and_digest"
        )

    def to_dict(self):
        assoc_table = sorted(
            [{"snap": list(k), "val": round(v, 3)} for k, v in self._assoc._table.items()],
            key=lambda x: -x["val"],
        )
        return {
            "dopamine":       round(self.dopamine,       3),
            "serotonin":      round(self.serotonin,      3),
            "norepinephrine": round(self.norepinephrine, 3),
            "cortisol":       round(self.cortisol,       3),
            "endorphin":      round(self.endorphin,      3),
            "intensity":      round(self.intensity,      3),
            "mode":           self.mode,
            "assoc_entries":  len(self._assoc._table),
            "assoc_expected": round(self._assoc.expected, 3),
            "assoc_table":    assoc_table,
        }


# ── CNS ───────────────────────────────────────────────────────────────────────

class CNS:
    """
    Central nervous system. Reads PNS state, builds short and long-term memory,
    extracts transition patterns, predicts next state, measures surprise.
    Does not read body or senses directly.
    """

    def __init__(self, pns):
        self.pns = pns

        # short-term memory: recent PNS snapshots
        self.stm = deque(maxlen=CNS_STM_SIZE)

        # long-term memory: state → {next_state → count}
        # each key is a bucketed PNS signature; value is what followed and how often
        self.ltm = {}

        self.active_concept = None   # current state signature
        self.prediction     = None   # predicted next state
        self.surprise       = 0.0    # how wrong the last prediction was (0.0–1.0)
        self._prev_snap     = None

    def _snapshot(self):
        """Bucket PNS into discrete signature. 3 levels per transmitter + mode."""
        def b(v):
            return 0 if v < 0.33 else (1 if v < 0.66 else 2)
        p = self.pns
        return (
            b(p.dopamine),
            b(p.serotonin),
            b(p.norepinephrine),
            b(p.cortisol),
            b(p.endorphin),
            0 if p.mode == "rest_and_digest" else 1,
        )

    def tick(self):
        snap = self._snapshot()

        # measure surprise against last prediction
        if self.prediction is not None:
            diff = sum(abs(a - b) for a, b in zip(snap, self.prediction))
            self.surprise = diff / (len(snap) * 2)

        # learn: record that prev_snap transitioned to snap
        if self._prev_snap is not None:
            row = self.ltm.setdefault(self._prev_snap, {})
            row[snap] = row.get(snap, 0) + 1

        # predict: from current snap, what most often follows?
        row = self.ltm.get(snap, {})
        if row:
            self.prediction     = max(row, key=row.get)
            self.active_concept = snap
        else:
            self.prediction     = None
            self.active_concept = None

        self.stm.append(snap)
        self._prev_snap = snap

    def to_dict(self):
        return {
            "concepts":       len(self.ltm),
            "surprise":       round(self.surprise, 3),
            "active_concept": list(self.active_concept) if self.active_concept else None,
            "prediction":     list(self.prediction)     if self.prediction     else None,
        }


# ── Motor Cortex ──────────────────────────────────────────────────────────────

class MotorCortex:
    """
    Receives impulses from any source (PNS, lizard brain, CNS).
    Each tick: strongest impulse wins, fires the corresponding effector.
    Has direct access to body strength — strength scales execution, not competition.
    """

    ACTIONS = ("idle", "walk", "fight", "forage")

    def __init__(self, body):
        self.body           = body
        self._impulses      = []
        self.last_action    = "idle"
        self.last_intensity = 0.0
        self.last_source    = None
        self.last_walk      = (0, 0)   # (dx,dy) of last walk; (0,0) if not walk

    def add_impulse(self, action, intensity, source, params=None):
        """Queue an impulse. params carries action-specific data (e.g. dx/dy for walk)."""
        self._impulses.append({
            "action":    action,
            "intensity": max(0.0, min(1.0, intensity)),
            "source":    source,
            "params":    params or {},
        })

    def resolve(self):
        """Pick strongest impulse, fire effector, clear queue. Called once per tick."""
        if not self._impulses:
            self.last_action    = "idle"
            self.last_intensity = 0.0
            self.last_source    = None
            return

        winner = max(self._impulses, key=lambda i: i["intensity"])
        self._impulses = []

        self.last_action    = winner["action"]
        self.last_intensity = winner["intensity"]
        self.last_source    = winner["source"]

        # strength is the execution multiplier — already baked into effector costs
        action = winner["action"]
        params = winner["params"]

        if action == "walk":
            dx = params.get("dx", 0)
            dy = params.get("dy", 0)
            self.last_walk = (dx, dy)
            self.body.walk(dx, dy)
        else:
            self.last_walk = (0, 0)
            if action == "fight":
                self.body.fight()
            elif action == "forage":
                self.body.forage()

    def to_dict(self):
        return {
            "last_action":    self.last_action,
            "last_intensity": round(self.last_intensity, 3),
            "last_source":    self.last_source,
            "pending":        len(self._impulses),
        }


# ── Lizard Brain ──────────────────────────────────────────────────────────────

class LizardBrain:
    """
    Hardcoded reflex layer. Reads PNS, pushes impulses to motor cortex.
    No learning. Fires below the CNS — CNS can override with a stronger impulse.
    """

    _DIRS = [(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]

    def __init__(self, pns, motor_cortex, body):
        self.pns           = pns
        self.motor_cortex  = motor_cortex
        self.body          = body
        self._last_smell   = 0.0
        self._last_seek_dir = None

    def tick(self):
        p  = self.pns
        mc = self.motor_cortex

        sv = list(self.body.smell)
        current_smell = max(sv) if sv else 0.0

        # Forage: on food right now, and not being actively threatened
        on_food = self.body.taste and list(self.body.taste)[-1] > 0
        if on_food and p.norepinephrine < 0.3:
            mc.add_impulse("forage", 0.9, "lizard_forage")

        # Flee: norepinephrine spike — something alarming, move fast
        if p.norepinephrine > 0.3:
            dx, dy = random.choice(self._DIRS)
            mc.add_impulse("walk", p.norepinephrine, "lizard_flee", {"dx": dx, "dy": dy})

        # Seek: low dopamine — chemotaxis toward increasing smell, else random wander
        if p.dopamine < 0.55:
            smell_rising = current_smell > self._last_smell + 0.005
            if smell_rising and self._last_seek_dir is not None and random.random() < 0.75:
                dx, dy = self._last_seek_dir
            else:
                dx, dy = random.choice(self._DIRS)
            self._last_seek_dir = (dx, dy)
            mc.add_impulse("walk", 1.0 - p.dopamine, "lizard_seek", {"dx": dx, "dy": dy})

        # Stress: sustained cortisol — escape current situation
        if p.cortisol > 0.3:
            dx, dy = random.choice(self._DIRS)
            mc.add_impulse("walk", p.cortisol, "lizard_stress", {"dx": dx, "dy": dy})

        self._last_smell = current_smell


# ── World Model ───────────────────────────────────────────────────────────────

class WorldModel:
    """
    CNS-level transition model.
    Learns (sense_snap, walk_dir) → value of next state by observing what snap
    results from each (snap, action) pair and scoring it against the association table.
    At planning time, fires the direction predicted to lead to the best next state,
    but only when it beats the current state by PLAN_THRESHOLD — so it doesn't
    override lizard reflexes unless it actually knows something useful.
    Persists across deaths alongside the association table.
    """
    ALPHA          = 0.15
    PLAN_THRESHOLD = 0.03
    _DIRS = [(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]

    def __init__(self, assoc):
        self._assoc       = assoc
        self._table       = {}      # (snap, (dx,dy)) → EMA of resulting next-state value
        self._prev_snap   = None
        self._prev_action = None
        self.best_dir     = None
        self.best_val     = 0.0

    def tick(self, curr_snap, last_walk_dir, motor_cortex):
        # Update: observe that (prev_snap, prev_action) led to curr_snap
        if self._prev_snap is not None and self._prev_action is not None:
            curr_value = self._assoc._table.get(curr_snap, 0.35)
            key = (self._prev_snap, self._prev_action)
            prev = self._table.get(key, 0.35)
            self._table[key] = prev * (1 - self.ALPHA) + curr_value * self.ALPHA

        # Plan: find direction predicted to yield the best next-state value
        curr_value = self._assoc._table.get(curr_snap, 0.35)
        best_val   = curr_value + self.PLAN_THRESHOLD
        best_dir   = None
        for d in self._DIRS:
            predicted = self._table.get((curr_snap, d))
            if predicted is not None and predicted > best_val:
                best_val = predicted
                best_dir = d

        self.best_dir = best_dir
        self.best_val = best_val

        if best_dir is not None:
            dx, dy = best_dir
            motor_cortex.add_impulse("walk", best_val, "cns_seek", {"dx": dx, "dy": dy})

        self._prev_snap   = curr_snap
        self._prev_action = last_walk_dir

    def reset_state(self):
        """Called on death — forgets where it was, keeps what it learned."""
        self._prev_snap   = None
        self._prev_action = None
        self.best_dir     = None
        self.best_val     = 0.0

    _DIR_LABEL = {
        (0,-1):"N",(1,-1):"NE",(1,0):"E",(1,1):"SE",
        (0,1):"S",(-1,1):"SW",(-1,0):"W",(-1,-1):"NW",
    }

    def to_dict(self):
        wm_table = sorted(
            [{"snap": list(snap), "dir": self._DIR_LABEL.get(d, str(d)), "val": round(v, 3)}
             for (snap, d), v in self._table.items()],
            key=lambda x: -x["val"],
        )
        return {
            "entries":  len(self._table),
            "best_val": round(self.best_val, 3),
            "planning": self.best_dir is not None,
            "table":    wm_table,
        }


# ── Mind ───────────────────────────────────────────────────────────────────────

class Mind:
    def __init__(self, mid):
        self.id    = mid
        self.name  = _gen_name()
        self.color = MIND_COLORS[mid]
        self.x     = random.randrange(GRID_W)
        self.y     = random.randrange(GRID_H)
        self.health_top    = HEALTH_TOP
        self.health_mid    = HEALTH_MID
        self.health_bot    = HEALTH_BOT
        self.deaths        = 0
        self.strikes       = 3
        self.harvests      = 0
        self.harvest_flash = 0
        self.facing        = random.choice(FACE_DIRS)
        self.seen_minds    = {}

        # ── Energy & strength ─────────────────────────────────────────────────
        self.energy          = ENERGY_START
        self._sense_cost     = 0
        self.last_sense_cost = 0
        self.strength        = STRENGTH_MAX

        # ── Senses (written by the world via use_sense()) ─────────────────────
        self._init_senses()

        # ── PNS → CNS → Motor Cortex ──────────────────────────────────────────
        self.pns          = PNS(self)
        self.cns          = CNS(self.pns)
        self.motor_cortex = MotorCortex(self)
        self.lizard_brain = LizardBrain(self.pns, self.motor_cortex, self)
        self.world_model  = WorldModel(self.pns._assoc)

    def _init_senses(self):
        self.sight   = deque(maxlen=SENSE_BANDWIDTH)
        self.hearing = deque(maxlen=SENSE_BANDWIDTH)
        self.touch   = deque(maxlen=SENSE_BANDWIDTH)
        self.smell   = deque(maxlen=SENSE_BANDWIDTH)
        self.taste   = deque(maxlen=SENSE_BANDWIDTH)

    def use_sense(self, sense, value):
        """World calls this to push a value into a sense stream. Costs 1 energy."""
        getattr(self, sense).append(value)
        self._sense_cost += 1

    def drain_energy(self):
        """Called once per tick after all sense writes. Deducts accumulated cost."""
        self.last_sense_cost = self._sense_cost
        self.energy          = max(0.0, self.energy - self._sense_cost)
        self._sense_cost     = 0

    @property
    def health(self):
        return self.health_top + self.health_mid + self.health_bot

    def heal(self, amount):
        """Fill top first, then mid, then bot. Restores strength proportionally."""
        total = HEALTH_TOP + HEALTH_MID + HEALTH_BOT
        for attr, cap in [("health_top", HEALTH_TOP), ("health_mid", HEALTH_MID), ("health_bot", HEALTH_BOT)]:
            current = getattr(self, attr)
            add = min(amount, cap - current)
            setattr(self, attr, current + add)
            amount -= add
            if amount <= 0:
                break
        self.strength = min(STRENGTH_MAX, self.strength + amount / total)

    def damage(self, amount):
        """Drain top first, then mid, then bot. Reduces strength proportionally."""
        total = HEALTH_TOP + HEALTH_MID + HEALTH_BOT
        self.strength = max(STRENGTH_MIN, self.strength - amount / total)
        for attr in ["health_top", "health_mid", "health_bot"]:
            current = getattr(self, attr)
            take = min(amount, current)
            setattr(self, attr, current - take)
            amount -= take
            if amount <= 0:
                break

    # ── Effectors (PNS drives these) ──────────────────────────────────────────

    def walk(self, dx, dy):
        """Move one cell. Costs energy scaled by strength."""
        if dx != 0 or dy != 0:
            self.update_facing(self.x + dx, self.y + dy)
        self.x = (self.x + dx) % GRID_W
        self.y = (self.y + dy) % GRID_H
        self.energy = max(0.0, self.energy - ENERGY_PER_MOVE * self.strength)

    def fight(self):
        """Engage target. Costs energy. Strength scales win odds."""
        self.energy = max(0.0, self.energy - ENERGY_PER_FIGHT * self.strength)

    def forage(self):
        """Signal intent to harvest from current cell. Resolved by the world."""
        pass

    def choose_move(self, world, resources):
        return (self.x, self.y)

    def update_facing(self, dest_x, dest_y):
        dx = dest_x - self.x
        dy = dest_y - self.y
        if dx >  GRID_W / 2: dx -= GRID_W
        if dx < -GRID_W / 2: dx += GRID_W
        if dy >  GRID_H / 2: dy -= GRID_H
        if dy < -GRID_H / 2: dy += GRID_H
        if   dx > 0 and dy < 0: self.facing = "NE"
        elif dx > 0 and dy > 0: self.facing = "SE"
        elif dx < 0 and dy < 0: self.facing = "NW"
        elif dx < 0 and dy > 0: self.facing = "SW"
        elif dx > 0:             self.facing = "E"
        elif dx < 0:             self.facing = "W"
        elif dy > 0:             self.facing = "S"
        elif dy < 0:             self.facing = "N"

    def _full_health(self):
        self.health_top = HEALTH_TOP
        self.health_mid = HEALTH_MID
        self.health_bot = HEALTH_BOT

    def soft_reset(self):
        """Body dies, brain survives. Keeps association table and CNS ltm."""
        self.deaths      += 1
        self.x            = random.randrange(GRID_W)
        self.y            = random.randrange(GRID_H)
        self.facing       = random.choice(FACE_DIRS)
        self._full_health()
        self.energy          = ENERGY_START
        self._sense_cost     = 0
        self.last_sense_cost = 0
        self.strength        = STRENGTH_MAX
        self._init_senses()
        # reset neurotransmitter values but keep learned association table and CNS ltm
        self.pns._prev_health  = self.health
        self.pns._prev_energy  = self.energy
        self.pns._prev_delta   = 0.0
        self.pns._stress_ticks = 0
        self.pns.dopamine       = 0.3
        self.pns.serotonin      = 0.5
        self.pns.norepinephrine = 0.0
        self.pns.cortisol       = 0.0
        self.pns.endorphin      = 0.0
        self.pns.intensity      = 0.0
        self.pns.mode           = "rest_and_digest"
        self.pns._prev_mode     = "rest_and_digest"
        self.cns.stm.clear()
        self.cns.prediction     = None
        self.cns.active_concept = None
        self.cns.surprise       = 0.0
        self.world_model.reset_state()

    def lose_strike(self):
        self.strikes -= 1
        self.x        = random.randrange(GRID_W)
        self.y        = random.randrange(GRID_H)
        self._full_health()

    def respawn(self):
        self.deaths  += 1
        self.strikes  = 3
        self.x        = random.randrange(GRID_W)
        self.y        = random.randrange(GRID_H)
        self._full_health()
        self.facing      = random.choice(FACE_DIRS)
        self.name        = _gen_name()
        self.energy          = ENERGY_START
        self._sense_cost     = 0
        self.last_sense_cost = 0
        self.strength        = STRENGTH_MAX
        self._init_senses()
        self.pns          = PNS(self)
        self.cns          = CNS(self.pns)
        self.motor_cortex = MotorCortex(self)
        self.lizard_brain = LizardBrain(self.pns, self.motor_cortex, self)
        self.world_model  = WorldModel(self.pns._assoc)

    def to_dict(self):
        return {
            "id":            self.id,
            "name":          self.name,
            "color":         self.color,
            "x":             self.x,
            "y":             self.y,
            "facing":        self.facing,
            "energy":        round(self.energy, 1),
            "strength":      round(self.strength, 3),
            "health":        round(self.health, 1),
            "health_top":    round(self.health_top, 1),
            "health_mid":    round(self.health_mid, 1),
            "health_bot":    round(self.health_bot, 1),
            "harvests":      self.harvests,
            "deaths":        self.deaths,
            "strikes":       self.strikes,
            "harvest_flash": self.harvest_flash,
            "seen_minds":    list(self.seen_minds.values()),
            "pns":           self.pns.to_dict(),
            "cns":           self.cns.to_dict(),
            "wm":            self.world_model.to_dict(),
            "motor":         self.motor_cortex.to_dict(),
            "senses": {
                "sight":   len(self.sight),
                "hearing": len(self.hearing),
                "touch":   len(self.touch),
                "smell":   len(self.smell),
                "taste":   len(self.taste),
            },
        }


# ── Sim2D ──────────────────────────────────────────────────────────────────────

class Sim2D:
    def __init__(self):
        self.tick      = 0
        self.world     = generate_world()
        self.minds     = [Mind(i) for i in range(N_MINDS)]
        self.resources = [Resource() for _ in range(N_RESOURCES)]
        self.boar      = Boar()
        self._send_world = True

    def step(self):
        self.tick += 1
        events = []
        W      = self.world

        # 1. Sight
        for m in self.minds:
            m.seen_minds = {}
            vis = set(_visible_cells(m.x, m.y, m.facing))
            for o in self.minds:
                if o.id != m.id and (o.x, o.y) in vis:
                    m.seen_minds[o.id] = {
                        "x": o.x, "y": o.y,
                        "color": o.color, "name": o.name,
                        "health": round(o.health, 1),
                    }

        # 2. Boar
        events.extend(self.boar.step(self.minds))

        # 3. Move
        for m in self.minds:
            dest = m.choose_move(W, self.resources)
            m.update_facing(dest[0], dest[1])
            m.x, m.y = dest

        # 4. World → sense streams
        for m in self.minds:
            # Touch
            touch_val = _TERRAIN_TOUCH[W[m.y][m.x]]
            m.use_sense("touch", touch_val)

            # Smell
            smell_val = 0.0
            for r in self.resources:
                d = _mdist(m.x, m.y, r.x, r.y)
                if d <= SMELL_RANGE:
                    smell_val = max(smell_val, 1.0 / (1.0 + d))
            m.use_sense("smell", smell_val)

            # Sight
            vis = _visible_cells(m.x, m.y, m.facing)
            vis_set = set(vis)
            nearest_by_terrain = {}
            for cx, cy in vis:
                t = W[cy][cx]
                d = _mdist(m.x, m.y, cx, cy)
                if t not in nearest_by_terrain or d < nearest_by_terrain[t]:
                    nearest_by_terrain[t] = d
            for t, d in nearest_by_terrain.items():
                m.use_sense("sight", (t, d))
            # Resource sight: write T_RESOURCE for nearest visible resource cell
            nearest_res_dist = None
            for r in self.resources:
                if (r.x, r.y) in vis_set:
                    d = _mdist(m.x, m.y, r.x, r.y)
                    if nearest_res_dist is None or d < nearest_res_dist:
                        nearest_res_dist = d
            if nearest_res_dist is not None:
                m.use_sense("sight", (T_RESOURCE, nearest_res_dist))

            # Hearing
            m.use_sense("hearing", ("ambient", 0.1))
            for oinfo in m.seen_minds.values():
                d = _mdist(m.x, m.y, oinfo["x"], oinfo["y"])
                m.use_sense("hearing", ("mind", 1.0 / (1.0 + d)))

            # Taste: always write so buffer reflects current tick (0.0 when not on food)
            taste_val = 0.0
            for r in self.resources:
                if r.x == m.x and r.y == m.y:
                    taste_val = r.harvest_progress / HARVEST_TICKS
                    break
            m.use_sense("taste", taste_val)

            sight_strs = [f"({TERRAIN[t]['label']},{d})" for t, d in nearest_by_terrain.items()]
            events.append(
                f"SENSE  M{m.id}({m.name})  "
                f"touch={touch_val:.2f}  smell={smell_val:.2f}  "
                f"sight=[{','.join(sight_strs)}]  "
                f"hearing={1+len(m.seen_minds)}w  "
                f"taste={'none' if taste_val is None else f'{taste_val:.2f}'}"
            )

        # 5. Drain sense energy → PNS → CNS → motor cortex
        for m in self.minds:
            sense_cost = m._sense_cost
            m.drain_energy()
            if m.energy == 0:
                m.damage(1.0)
            events.append(
                f"DRAIN  M{m.id}({m.name})  cost={sense_cost} energy={m.energy:.0f} hp={m.health:.0f}"
            )

            m.pns.tick()

            p = m.pns
            events.append(
                f"PNS    M{m.id}({m.name})  "
                f"dopa={p.dopamine:.2f} sero={p.serotonin:.2f} "
                f"norepi={p.norepinephrine:.2f} cort={p.cortisol:.2f} endo={p.endorphin:.2f} | "
                f"intensity={p.intensity:.2f} mode={p.mode}"
            )
            events.append(
                f"ASSOC  M{m.id}({m.name})  "
                f"snap={p._assoc.last_snap}  "
                f"expected={p._assoc.expected:.3f}  entries={len(p._assoc._table)}"
            )
            for snap, outcome, val in p._assoc.last_updates:
                events.append(
                    f"ASSOC_LEARN  M{m.id}({m.name})  "
                    f"snap={snap}  outcome={outcome:.3f} → {val:.3f}"
                )

            # log mode flip
            if m.pns.mode != m.pns._prev_mode:
                events.append(
                    f"MODE  M{m.id}({m.name})  "
                    f"{m.pns._prev_mode} → {m.pns.mode}  "
                    f"intensity={m.pns.intensity:.2f}"
                )
            m.pns._prev_mode = m.pns.mode

            m.cns.tick()
            m.lizard_brain.tick()

            # World model: directed impulse if it knows a better direction
            curr_snap = m.pns._assoc.last_snap
            m.world_model.tick(curr_snap, m.motor_cortex.last_walk, m.motor_cortex)
            if m.world_model.best_dir is not None:
                events.append(
                    f"WM     M{m.id}({m.name})  "
                    f"dir={m.world_model.best_dir}  "
                    f"val={m.world_model.best_val:.3f}  "
                    f"entries={len(m.world_model._table)}"
                )

            # log new concept crystallized
            prev_concepts = getattr(m.cns, '_prev_concepts', 0)
            if len(m.cns.ltm) > prev_concepts:
                events.append(
                    f"CONCEPT M{m.id}({m.name})  "
                    f"total={len(m.cns.ltm)}  "
                    f"surprise={m.cns.surprise:.3f}"
                )
            m.cns._prev_concepts = len(m.cns.ltm)

            m.motor_cortex.resolve()

            # log any non-idle action
            if m.motor_cortex.last_action != "idle":
                events.append(
                    f"ACTION M{m.id}({m.name})  "
                    f"{m.motor_cortex.last_action}  "
                    f"intensity={m.motor_cortex.last_intensity:.2f}  "
                    f"src={m.motor_cortex.last_source}"
                )

        # 4. Harvest
        for r in self.resources:
            on_cell = [m for m in self.minds if m.x == r.x and m.y == r.y]
            if not on_cell:
                r.harvesting      = None
                r.harvest_progress = 0
                continue
            harvester = next((m for m in on_cell if m.id == r.harvesting), on_cell[0])
            if r.harvesting != harvester.id:
                r.harvesting      = harvester.id
                r.harvest_progress = 0
            r.harvest_progress += 1
            if r.harvest_progress >= HARVEST_TICKS:
                harvester.heal(HARVEST_HEALTH)
                harvester.energy = min(ENERGY_START, harvester.energy + HARVEST_ENERGY)
                harvester.harvests  += 1
                harvester.harvest_flash = 10
                events.append(
                    f"HARVEST M{harvester.id}({harvester.name})"
                    f"  at ({r.x},{r.y})  hp={harvester.health:.0f}  en={harvester.energy:.0f}"
                )
                r.relocate()

        # 6. Death check
        for m in self.minds:
            if m.health <= 0:
                m.soft_reset()
                events.append(
                    f"DEATH  M{m.id}({m.name})  deaths={m.deaths}  "
                    f"assoc_kept={len(m.pns._assoc._table)}  concepts_kept={len(m.cns.ltm)}"
                )

        # 7. World drift
        world_changed = False
        if random.random() < 0.003:
            x   = random.randrange(GRID_W)
            y   = random.randrange(GRID_H)
            old = W[y][x]
            nw  = random.randrange(3)
            if nw != old:
                W[y][x] = nw
                events.append(f"DRIFT ({x},{y})  {TERRAIN[old]['label']}→{TERRAIN[nw]['label']}")
                world_changed = True

        # 8. Flash decay
        for r in self.resources:
            if r.flash > 0: r.flash -= 1
        for m in self.minds:
            if m.harvest_flash > 0: m.harvest_flash -= 1

        # 9. Snap
        if self.tick % 10 == 0:
            for m in self.minds:
                p = m.pns
                events.append(
                    f"SNAP  M{m.id}({m.name}) "
                    f"hp={m.health:.0f}({m.health_top:.0f}/{m.health_mid:.0f}/{m.health_bot:.0f}) "
                    f"en={m.energy:.0f} str={m.strength:.2f} | "
                    f"dopa={p.dopamine:.2f} sero={p.serotonin:.2f} "
                    f"norepi={p.norepinephrine:.2f} cort={p.cortisol:.2f} endo={p.endorphin:.2f} | "
                    f"intensity={p.intensity:.2f} mode={p.mode} | "
                    f"assoc={len(p._assoc._table)} exp={p._assoc.expected:.2f} | "
                    f"concepts={len(m.cns.ltm)} surprise={m.cns.surprise:.3f}"
                )

        state = {
            "type":      "tick",
            "tick":      self.tick,
            "minds":     [m.to_dict() for m in self.minds],
            "resources": [r.to_dict() for r in self.resources],
            "boar":      self.boar.to_dict(),
            "events":    events,
        }
        if self._send_world or world_changed:
            state["world"] = W
            self._send_world = False
        return state
