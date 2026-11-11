import random
from collections import deque
from itertools import permutations as _perms, product as _product

_NAME_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ'  # no I/O to avoid 1/0 confusion

def _gen_name():
    return ''.join(random.choices(_NAME_CHARS, k=3))

PANIC_THRESHOLD   = 25.0
BUFFER_SIZE       = 200
SENSITIVITY       = 0.5
META_WEIGHT       = 5
DRIVE_WINDOW      = 40

TRANSFER_OPTIONS   = [5, 10, 15, 20, 25]  # amounts a mind may choose to transfer
RESOURCE_REGEN     = 2.5   # resources → health per tick (passive healing)
RESOURCE_DECAY     = 0.97  # resources shrink 3% per tick — prevents runaway accumulation

SIGNAL_PATTERNS  = list(_product(range(2), repeat=4))  # 16 4-bit signals
_FIGHT_PATTERNS  = SIGNAL_PATTERNS                      # same set, different context


def _unique_perms(pattern):
    return list(set(_perms(pattern)))


def _features(pattern):
    p      = pattern
    s      = sum(p)
    rhythm = sum(abs(p[i+1] - p[i]) for i in range(len(p) - 1))
    return [
        ("biome",     p[0]),               # first digit = biome = primary structure signal
        ("last",      p[-1]),
        ("sum",       s),
        ("max_val",   max(p)),
        ("min_val",   min(p)),
        ("val_range", max(p) - min(p)),
        ("rhythm",    rhythm),
    ]


class MetaLearner:
    """Feature-level score estimator for unseen patterns (intuition layer)."""

    def __init__(self):
        self._feats = {}

    def rebuild(self, learned):
        self._feats = {}
        for pattern, v in learned.items():
            if v["count"] <= 0:
                continue
            score = v["total"] / v["count"]
            for feat in _features(pattern):
                if feat not in self._feats:
                    self._feats[feat] = {"total": 0.0, "count": 0}
                self._feats[feat]["total"] += score
                self._feats[feat]["count"] += 1

    def estimate(self, pattern):
        feats = _features(pattern)
        ests, wts = [], []
        for f in feats:
            if f in self._feats and self._feats[f]["count"] > 0:
                ests.append(self._feats[f]["total"] / self._feats[f]["count"])
                wts.append(self._feats[f]["count"])
        if not ests:
            return None
        return sum(e * w for e, w in zip(ests, wts)) / sum(wts)

    def top_features(self, n=10):
        out = []
        for (name, val), v in self._feats.items():
            if v["count"] > 0:
                out.append({
                    "feature": f"{name}={val}",
                    "avg":     round(v["total"] / v["count"], 2),
                    "count":   v["count"],
                })
        return sorted(out, key=lambda x: abs(x["avg"]), reverse=True)[:n]


class Mind:
    def __init__(self):
        self.health        = 100.0
        self._last_delta   = 0.0
        self._buffer       = deque(maxlen=BUFFER_SIZE)
        self.learned       = {}   # (pattern_tuple, ctx) → {"total": float, "count": int}
        self._meta         = MetaLearner()
        self._meta_fight   = MetaLearner()
        self.name          = _gen_name()
        self.drive         = 0.5
        self._drive_buf    = deque(maxlen=DRIVE_WINDOW)
        self._drive_gained = 0.0
        self._drive_lost   = 0.0

        # ── Resources ─────────────────────────────────────────────────────────
        # Earned from positive patterns. Convert passively to health each tick.
        # Costs resources to transfer health to another mind.
        self.resources = 0.0

        # ── Layer 1: feelings + health integral ───────────────────────────────
        # Per-ctx sliding-window success rates (parallel to drive but split by ctx)
        self._feel = {
            "n": {"gained": 0.0, "lost": 0.0, "buf": deque(maxlen=DRIVE_WINDOW)},
            "f": {"gained": 0.0, "lost": 0.0, "buf": deque(maxlen=DRIVE_WINDOW)},
        }
        self.health_integral = 0.0  # cumulative health per tick; resets on real death

        # ── Layer 2: transfer learning ────────────────────────────────────────
        # (target_idx, amount) → {"total": float, "count": int}
        # value = net health change to offeror over 20 ticks following the transfer
        self.transfer_learned = {}

        # ── Layer 3: signal channel ───────────────────────────────────────────
        # signal_learned: what I observe when others emit signals
        #   (source_idx, their_signal_tuple) → {"total": float, "count": int}
        #   value = my net health change over 10 ticks after seeing that signal
        self.signal_learned = {}

        # emit_learned: what happens to me when I emit a signal
        #   (target_idx, my_signal_tuple) → {"total": float, "count": int}
        #   value = my net health change over 10 ticks after emitting
        self.emit_learned = {}

    # ── properties ────────────────────────────────────────────────────────────

    @property
    def multiplier(self):
        m = 1.0 + (self._last_delta / 100.0) * SENSITIVITY
        return max(0.25, min(2.0, m))

    @property
    def feelings(self):
        """Per-domain success rates plus wealth (reserve level)."""
        out = {}
        for ctx, label in [("n", "survival"), ("f", "combat")]:
            fb    = self._feel[ctx]
            total = fb["gained"] + fb["lost"]
            out[label] = round(fb["gained"] / total, 3) if total > 0 else 0.5
        return out

    # ── public: health tracking ───────────────────────────────────────────────

    def record_health(self, h):
        """Called by server each tick to accumulate health integral."""
        self.health_integral += h

    def tick_resources(self):
        """Decay resources 3%, then convert up to RESOURCE_REGEN into health."""
        self.resources *= RESOURCE_DECAY
        convert         = min(self.resources, RESOURCE_REGEN, max(0.0, 100.0 - self.health))
        self.health    += convert
        self.resources  -= convert

    # ── public: normal play ───────────────────────────────────────────────────

    def choose(self, raw_signal):
        perms = _unique_perms(tuple(raw_signal))
        if self.health < PANIC_THRESHOLD:
            unknown = [p for p in perms if not self._known(p, "n")]
            if unknown:
                return list(max(unknown, key=lambda p: self._meta.estimate(p) or 0.0))
            return list(min(perms, key=lambda p: self.learned.get((p, "n"), {"count": 0})["count"]))
        return list(max(perms, key=lambda p: self._combined_score(p, "n")))

    # ── public: fight ─────────────────────────────────────────────────────────

    def choose_fight(self):
        return list(random.choice(_FIGHT_PATTERNS))

    def fight_known_count(self):
        return sum(1 for (p, ctx), v in self.learned.items()
                   if ctx == "f" and v["count"] > 0)

    def top_fight_patterns(self, n=3):
        entries = [(p, v["count"]) for (p, ctx), v in self.learned.items()
                   if ctx == "f" and v["count"] > 0]
        entries.sort(key=lambda x: -x[1])
        return [p for p, _ in entries[:n]]

    def clear_fight_memory(self, keep_patterns=()):
        keep = set(keep_patterns)
        for key in [k for k in list(self.learned.keys()) if k[1] == "f" and k[0] not in keep]:
            del self.learned[key]
        new_buf = deque(maxlen=BUFFER_SIZE)
        for entry in self._buffer:
            if entry["ctx"] != "f" or tuple(entry["chosen"]) in keep:
                new_buf.append(entry)
        self._buffer = new_buf
        self._rebuild_metas()

    # ── public: transfer (Layer 2) ────────────────────────────────────────────

    def choose_transfer(self, candidate_indices, aggressions=None):
        """
        Return (target_idx, amount) or None. Both target and amount are learned.
        Scoring = learned_score + aggression_prior. Only fires if score > 0.
        """
        if not candidate_indices:
            return None
        if aggressions is None:
            aggressions = {}

        valid = [(idx, amt) for idx in candidate_indices
                 for amt in TRANSFER_OPTIONS if amt <= self.resources]
        if not valid:
            return None

        best_score = 0.0
        best = None
        for idx, amt in valid:
            agg     = aggressions.get(idx, 0.0)
            learned = self._transfer_score(idx, amt)
            score   = learned + agg * 2.0
            if score > best_score:
                best_score = score
                best       = (idx, amt)

        # exploration: try smallest amount to most-threatening unknown target
        min_amt = TRANSFER_OPTIONS[0]
        unknown_threat = [idx for idx in candidate_indices
                          if self.transfer_learned.get((idx, min_amt), {}).get("count", 0) == 0
                          and aggressions.get(idx, 0.0) > 0.1
                          and min_amt <= self.resources]
        if unknown_threat and random.random() < self.drive * 0.06:
            tgt = max(unknown_threat, key=lambda idx: aggressions.get(idx, 0.0))
            return (tgt, min_amt)

        return best

    def observe_transfer(self, target_idx, amount, net_delta):
        """Record deferred outcome of a transfer (called 20 ticks after the transfer)."""
        key = (target_idx, amount)
        v   = self.transfer_learned.setdefault(key, {"total": 0.0, "count": 0})
        v["total"] += net_delta
        v["count"] += 1

    # ── public: signal channel (Layer 3) ──────────────────────────────────────

    def choose_signal(self, active_target_indices):
        """
        Broadcast one signal per tick. Score each of 16 signals by average
        emit_learned score across all current targets. Random if no data.
        """
        scores = {}
        for sig in SIGNAL_PATTERNS:
            total, count = 0.0, 0
            for idx in active_target_indices:
                key = (idx, sig)
                if key in self.emit_learned and self.emit_learned[key]["count"] > 0:
                    total += self.emit_learned[key]["total"]
                    count += self.emit_learned[key]["count"]
            scores[sig] = total / count if count > 0 else None

        known = [(sig, s) for sig, s in scores.items() if s is not None]
        if not known:
            return random.choice(SIGNAL_PATTERNS)
        return max(known, key=lambda x: x[1])[0]

    def observe_signal_received(self, source_idx, their_signal, net_delta):
        """Record: after source emitted this signal, my health changed by net_delta."""
        key = (source_idx, tuple(their_signal))
        v   = self.signal_learned.setdefault(key, {"total": 0.0, "count": 0})
        v["total"] += net_delta
        v["count"] += 1

    def observe_signal_emitted(self, target_idx, my_signal, net_delta):
        """Record: after I emitted this signal, my health changed by net_delta."""
        key = (target_idx, tuple(my_signal))
        v   = self.emit_learned.setdefault(key, {"total": 0.0, "count": 0})
        v["total"] += net_delta
        v["count"] += 1

    def comm_drift(self):
        """Evict one random entry from signal_learned or emit_learned."""
        pool = list(self.signal_learned.keys()) + list(self.emit_learned.keys())
        if not pool:
            return
        key = random.choice(pool)
        self.signal_learned.pop(key, None)
        self.emit_learned.pop(key, None)

    # ── public: observe (shared entry point for all health changes) ───────────

    def observe(self, chosen, actual_delta, ctx="n"):
        chosen = tuple(chosen)
        if len(self._buffer) == self._buffer.maxlen:
            evicted = self._buffer[0]
            self._subtract(evicted["chosen"], evicted["delta"], evicted["ctx"])
        self._buffer.append({"chosen": chosen, "delta": actual_delta, "ctx": ctx})
        self._add(chosen, actual_delta, ctx)
        self._last_delta = actual_delta
        self._update_drive(actual_delta)
        self._update_feeling(ctx, actual_delta)
        self._rebuild_metas()

    # ── public: summaries ─────────────────────────────────────────────────────

    def learned_summary(self):
        out = []
        for (p, ctx), v in self.learned.items():
            if v["count"] > 0:
                out.append({
                    "pattern": list(p),
                    "ctx":     ctx,
                    "avg":     round(v["total"] / v["count"], 2),
                    "count":   v["count"],
                })
        return sorted(out, key=lambda x: -x["avg"])

    def meta_summary(self):
        return self._meta.top_features(10)

    def transfer_summary(self):
        out = []
        for (idx, amt), v in self.transfer_learned.items():
            if v["count"] > 0:
                out.append({
                    "target": idx,
                    "amount": amt,
                    "avg":    round(v["total"] / v["count"], 2),
                    "count":  v["count"],
                })
        return sorted(out, key=lambda x: -x["avg"])

    def signal_summary(self):
        """Top signal correlations observed from each source."""
        out = []
        for (src, sig), v in self.signal_learned.items():
            if v["count"] > 0:
                out.append({
                    "source":  src,
                    "signal":  list(sig),
                    "avg":     round(v["total"] / v["count"], 2),
                    "count":   v["count"],
                })
        return sorted(out, key=lambda x: -abs(x["avg"]))[:20]

    # ── internal ──────────────────────────────────────────────────────────────

    def _meta_for(self, ctx):
        return self._meta_fight if ctx == "f" else self._meta

    def _known(self, p, ctx="n"):
        key = (p, ctx)
        return key in self.learned and self.learned[key]["count"] > 0

    def _effective_meta_weight(self):
        return max(1.0, META_WEIGHT * (0.2 + self.drive * 1.6))

    def _combined_score(self, p, ctx="n"):
        meta   = self._meta_for(ctx)
        meta_s = meta.estimate(p)
        mw     = self._effective_meta_weight()
        key    = (p, ctx)
        if self._known(p, ctx):
            count = self.learned[key]["count"]
            ls    = self.learned[key]["total"] / count
            if meta_s is not None:
                return (ls * count + meta_s * mw) / (count + mw)
            return ls
        return meta_s if meta_s is not None else 0.0

    def _transfer_score(self, target_idx, amount):
        v = self.transfer_learned.get((target_idx, amount))
        if v is None or v["count"] == 0:
            return 0.0
        return v["total"] / v["count"]

    def _update_drive(self, delta):
        if len(self._drive_buf) == self._drive_buf.maxlen:
            old = self._drive_buf[0]
            if old > 0:
                self._drive_gained -= old
            else:
                self._drive_lost -= abs(old)
        self._drive_buf.append(delta)
        if delta > 0:
            self._drive_gained += delta
        else:
            self._drive_lost += abs(delta)
        total = self._drive_gained + self._drive_lost
        if total > 0:
            self.drive = 1.0 - (self._drive_gained / total)
        else:
            self.drive = 0.5

    def _update_feeling(self, ctx, delta):
        if ctx not in self._feel:
            return
        fb = self._feel[ctx]
        if len(fb["buf"]) == fb["buf"].maxlen:
            old = fb["buf"][0]
            if old > 0:
                fb["gained"] -= old
            else:
                fb["lost"] -= abs(old)
        fb["buf"].append(delta)
        if delta > 0:
            fb["gained"] += delta
        else:
            fb["lost"] += abs(delta)

    def _add(self, pattern, delta, ctx="n"):
        key = (pattern, ctx)
        if key not in self.learned:
            self.learned[key] = {"total": 0.0, "count": 0}
        self.learned[key]["total"] += delta
        self.learned[key]["count"] += 1

    def _subtract(self, pattern, delta, ctx="n"):
        key = (pattern, ctx)
        if key in self.learned:
            self.learned[key]["total"] -= delta
            self.learned[key]["count"] -= 1

    def _rebuild_metas(self):
        normal_learned = {p: v for (p, ctx), v in self.learned.items() if ctx == "n"}
        fight_learned  = {p: v for (p, ctx), v in self.learned.items() if ctx == "f"}
        self._meta.rebuild(normal_learned)
        self._meta_fight.rebuild(fight_learned)
