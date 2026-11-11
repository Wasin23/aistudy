"""
Web server — 3-mind competitive reorder-machine.

Run:  python server.py
Then open http://localhost:5050
"""

import json
import os
import queue
import random
import threading
import time

from flask import Flask, Response, render_template, request

from mind import Mind
from mind_v2 import Sim2D, TERRAIN as TERRAIN_V2
from rules import (
    generate_random_rules, drift_biome, DRIFT_THRESHOLD, DRIFT_PROB,
    generate_random_fight_rules, fight_drift_one, FIGHT_DRIFT_PROB,
    compute_effect, get_biome,
)

LOG_FILE       = os.path.join(os.path.dirname(__file__), "simulation.log")
LOG_FILE_2D    = os.path.join(os.path.dirname(__file__), "simulation_2d.log")
LOG_FILE_2D_V2 = os.path.join(os.path.dirname(__file__), "simulation_2d_v2.log")

TICK_DELAY_V2  = 0.16   # seconds per v2 tick


def _log_open():
    return open(LOG_FILE, "w", buffering=1, encoding="utf-8")


def log(f, msg, flush=False):
    f.write(msg + "\n")
    if flush:
        f.flush()

app = Flask(__name__)

sim_thread  = None
sim_running = False
sim_lock    = threading.Lock()

subscribers = []
sub_lock    = threading.Lock()

# ── v2 sim state ──────────────────────────────────────────────────────────────
v2_thread      = None
v2_running     = False
v2_lock        = threading.Lock()
v2_subscribers = []
v2_sub_lock    = threading.Lock()

N_MINDS           = 3
TICK_DELAY        = 0.08
PASSTHROUGH_RATE  = 0.20
DISASTER_EVERY    = 1000
STRIKES           = 3
RECOVERY_TICKS    = 50

FIGHT_MASTERY     = 16
MAX_FIGHT_TICKS   = 48
AGGRESSION_THRESH = 0.50
RESOURCE_AGG_WEIGHT = 0.10  # resources lower effective health for aggression: eff_h = health + res*weight

TRANSFER_WINDOW   = 20    # ticks to defer transfer outcome recording
SIGNAL_WINDOW     = 10    # ticks to defer signal outcome recording
COMM_DRIFT_EVERY  = 200   # ticks between comm drift events


def _apply_delta(mind, delta):
    """Positive delta → resources (uncapped). Negative delta → health loss."""
    if delta >= 0:
        mind.resources += delta
        return delta
    else:
        old_h       = mind.health
        mind.health = max(0.0, mind.health + delta)
        return mind.health - old_h


def push(data: dict):
    payload = json.dumps(data)
    with sub_lock:
        dead = []
        for q in subscribers:
            try:
                q.put_nowait(payload)
            except queue.Full:
                dead.append(q)
        for q in dead:
            subscribers.remove(q)


def simulation_loop():
    global sim_running

    minds          = [Mind() for _ in range(N_MINDS)]
    _init_rules    = [generate_random_rules()       for _ in range(N_MINDS)]
    salts          = [r[0] for r in _init_rules]
    biome_profiles = [r[1] for r in _init_rules]
    fight_effects  = [generate_random_fight_rules() for _ in range(N_MINDS)]
    deaths        = [0] * N_MINDS
    strikes       = [STRIKES] * N_MINDS
    recovery      = [0] * N_MINDS
    tick_id       = 0
    prev_ctrl     = -1

    # fight state
    in_fight          = False
    fighters          = []
    fight_ticks       = 0
    pending_headstart = [0] * N_MINDS

    # deferred observation queues
    # transfer: offeror loses health now; 20 ticks later record net outcome
    pending_transfers = []
    # signal receive: observer records net outcome 10 ticks after seeing signal
    pending_sig_recv  = []
    # signal emit: emitter records net outcome 10 ticks after emitting
    pending_sig_emit  = []

    f = _log_open()
    log(f, "=== SIMULATION START ===", flush=True)
    for i in range(N_MINDS):
        jkp = sorted([b for b, v in biome_profiles[i].items() if v >= 8])
        log(f, f"  M{i} biomes: " +
            "  ".join(f"b{b}={v:+d}" for b, v in sorted(biome_profiles[i].items())) +
            f"  (jackpot={jkp})", flush=True)

    push({"type": "status", "running": True, "tick": 0})

    while sim_running:
        raw      = [random.randint(0, 9) for _ in range(6)]
        editable = random.random() > PASSTHROUGH_RATE

        # ── recovery timers ───────────────────────────────────────────────────
        for i in range(N_MINDS):
            if recovery[i] > 0:
                recovery[i] -= 1
                if recovery[i] == 0:
                    minds[i].health = 100.0
                    log(f, f"[tick {tick_id:05d}] REVIVE mind {i}  strikes_left={strikes[i]}", flush=True)

        # ── natural disaster ──────────────────────────────────────────────────
        disaster = (tick_id > 0 and tick_id % DISASTER_EVERY == 0)
        if disaster:
            _new_rules     = [generate_random_rules() for _ in range(N_MINDS)]
            salts          = [r[0] for r in _new_rules]
            biome_profiles = [r[1] for r in _new_rules]
            log(f, f"\n[tick {tick_id:05d}] !! NATURAL DISASTER !! all rule tables reshuffled", flush=True)
            for i in range(N_MINDS):
                jkp = sorted([b for b, v in biome_profiles[i].items() if v >= 8])
                log(f, f"  M{i} new biomes: " +
                    "  ".join(f"b{b}={v:+d}" for b, v in sorted(biome_profiles[i].items())) +
                    f"  (jackpot={jkp})", flush=True)
            log(f, "", flush=True)

        # ── per-mind aggression (used by fight trigger, transfers, and display) ──
        _active_agg = [i for i in range(N_MINDS) if recovery[i] == 0]
        if _active_agg:
            _top_h = max(minds[i].health for i in _active_agg)
            mind_agg = {
                i: max(0.0, (_top_h - (minds[i].health + minds[i].resources * RESOURCE_AGG_WEIGHT)) / 100.0) * minds[i].drive
                for i in range(N_MINDS)
            }
        else:
            mind_agg = {i: 0.0 for i in range(N_MINDS)}

        # ── normal drift ──────────────────────────────────────────────────────
        drift_events = []
        for i in range(N_MINDS):
            lc = sum(1 for (p, ctx), v in minds[i].learned.items() if ctx == "n" and v["count"] > 0)
            if recovery[i] == 0 and i not in fighters and lc >= DRIFT_THRESHOLD and random.random() < DRIFT_PROB:
                biome, old, new = drift_biome(biome_profiles[i])
                drift_events.append({"mind": i, "biome": biome, "old": old, "new": new})
                log(f, f"[tick {tick_id:05d}] DRIFT mind {i} biome={biome}  {old:+d} → {new:+d}", flush=True)
            else:
                drift_events.append(None)

        # ── fight trigger ─────────────────────────────────────────────────────
        if not in_fight:
            active = [i for i in range(N_MINDS) if recovery[i] == 0]
            if len(active) >= 2:
                best_agg   = -1
                challenger  = -1
                for i in active:
                    agg = mind_agg[i]
                    if agg > best_agg:
                        best_agg  = agg
                        challenger = i
                if best_agg >= AGGRESSION_THRESH:
                    defender = max((i for i in active if i != challenger),
                                   key=lambda i: minds[i].health)

                    carry = {}
                    for idx in [challenger, defender]:
                        if pending_headstart[idx] > 0:
                            carry[idx] = minds[idx].top_fight_patterns(3)
                            pending_headstart[idx] = 0

                    old_fe = {idx: fight_effects[idx] for idx in [challenger, defender]}
                    fight_effects[challenger] = generate_random_fight_rules()
                    fight_effects[defender]   = generate_random_fight_rules()

                    for idx, pats in carry.items():
                        for pat in pats:
                            fight_effects[idx][pat] = old_fe[idx][pat]
                        log(f, f"[tick {tick_id:05d}] HEADSTART  mind {idx}  "
                               f"kept {len(pats)} patterns from prev fight", flush=True)

                    for idx in [challenger, defender]:
                        minds[idx].clear_fight_memory(keep_patterns=carry.get(idx, ()))

                    in_fight    = True
                    fighters    = [challenger, defender]
                    fight_ticks = 0
                    log(f, f"[tick {tick_id:05d}] FIGHT START  M{challenger} vs M{defender}  "
                           f"agg={best_agg:.3f}  h={minds[challenger].health:.1f} vs {minds[defender].health:.1f}",
                        flush=True)

        # ── controller ────────────────────────────────────────────────────────
        non_fighting_active = [i for i in range(N_MINDS)
                               if recovery[i] == 0 and i not in fighters]
        controller = max(non_fighting_active, key=lambda i: minds[i].health) if non_fighting_active else -1

        if controller != prev_ctrl:
            hs = "  ".join(
                f"M{i}:{'REC' if recovery[i] > 0 else f'{minds[i].health:.1f}'}"
                for i in range(N_MINDS)
            )
            log(f, f"[tick {tick_id:05d}] CTRL SHIFT  {prev_ctrl} → {controller}  ({hs})", flush=True)
            prev_ctrl = controller

        # ── build per-mind state helper ───────────────────────────────────────
        def _mstate(i, actual=0.0, base=0, mult=1.0, died=False, crit=False, spawned=False):
            jkp_biomes = sorted([b for b, v in biome_profiles[i].items() if v >= 8])
            return {
                "name":                minds[i].name,
                "health":              round(minds[i].health, 1),
                "health_change":       round(actual, 2),
                "base_effect":         base,
                "multiplier":          round(mult, 3),
                "panic":               minds[i].health < 25.0 and recovery[i] == 0,
                "died":                died,
                "crit":                crit,
                "spawned":             spawned,
                "learned_count":       sum(1 for (p, ctx), v in minds[i].learned.items()
                                          if ctx == "n" and v["count"] > 0),
                "fight_learned_count": minds[i].fight_known_count(),
                "deaths":              deaths[i],
                "drive":               round(minds[i].drive, 3),
                "strikes":             strikes[i],
                "recovering":          recovery[i] > 0,
                "recovery_ticks":      recovery[i],
                "fighting":            i in fighters,
                "feelings":            minds[i].feelings,
                "resources":           round(minds[i].resources, 1),
                "health_integral":     round(minds[i].health_integral),
                "biome_profile":       biome_profiles[i],
                "jackpot_biomes":      jkp_biomes,
                "aggression":          round(mind_agg.get(i, 0.0), 3),
            }

        # ── normal tick logic ─────────────────────────────────────────────────
        crit_flags    = [False] * N_MINDS
        spawned_flags = [False] * N_MINDS
        died_flags    = [False] * N_MINDS

        if not editable or controller == -1:
            mind_states = [_mstate(i) for i in range(N_MINDS)]
            chosen = raw
        else:
            chosen = minds[controller].choose(raw)
            mind_states = []

            for i in range(N_MINDS):
                if recovery[i] > 0 or i in fighters:
                    mind_states.append(_mstate(i))
                    continue

                base   = compute_effect(tuple(chosen), salts[i], biome_profiles[i])
                mult   = minds[i].multiplier
                delta  = base * mult
                actual = _apply_delta(minds[i], delta)

                minds[i].observe(chosen, actual, ctx="n")

                if minds[i].health <= 0.0:
                    if strikes[i] > 0:
                        strikes[i] -= 1
                        recovery[i] = RECOVERY_TICKS
                        crit_flags[i] = True
                        lc = sum(1 for (p, ctx), v in minds[i].learned.items() if ctx == "n" and v["count"] > 0)
                        log(f, f"[tick {tick_id:05d}] CRIT   mind {i}  strikes_left={strikes[i]}  learned={lc}", flush=True)
                    else:
                        died_flags[i] = True
                        deaths[i] += 1
                        lc = sum(1 for (p, ctx), v in minds[i].learned.items() if ctx == "n" and v["count"] > 0)
                        log(f, f"[tick {tick_id:05d}] DEATH  mind {i}  deaths={deaths[i]}  learned={lc}", flush=True)
                        if i in fighters:
                            fighters.remove(i)
                            if len(fighters) < 2:
                                in_fight = False
                                fighters = []
                        minds[i]                         = Mind()
                        salts[i], biome_profiles[i]      = generate_random_rules()
                        fight_effects[i]                 = generate_random_fight_rules()
                        strikes[i]                       = STRIKES
                        pending_headstart[i]             = 0
                        spawned_flags[i]                 = True
                        jkp = sorted([b for b, v in biome_profiles[i].items() if v >= 8])
                        log(f, f"[tick {tick_id:05d}] SPAWN  mind {i}  fresh instance  jackpot_biomes={jkp}", flush=True)

                mind_states.append(_mstate(i, actual, base, mult,
                                           died_flags[i], crit_flags[i], spawned_flags[i]))

            if tick_id % 50 == 0:
                parts = []
                for i in range(N_MINDS):
                    lc  = sum(1 for (p, ctx), v in minds[i].learned.items() if ctx == "n" and v["count"] > 0)
                    hp  = "REC" if recovery[i] > 0 else f"{minds[i].health:.1f}"
                    jkp = sorted([b for b, v in biome_profiles[i].items() if v >= 8])
                    parts.append(f"M{i}:{hp}({lc}L,jkp=b{jkp})")
                log(f, f"[tick {tick_id:05d}] SNAP   ctrl={controller}  chosen={list(chosen)}[b{get_biome(tuple(chosen))}]  {'  '.join(parts)}")

        # ── fight exchange ────────────────────────────────────────────────────
        fight_event = None

        if in_fight and len(fighters) == 2:
            fi, fj = fighters
            fight_ticks += 1

            pat_i = tuple(minds[fi].choose_fight())
            pat_j = tuple(minds[fj].choose_fight())

            def _fight_delta(idx, pat):
                base  = fight_effects[idx][pat]
                delta = float(base)
                if delta < 0:
                    delta *= max(0.2, 1.0 - minds[idx].drive)
                return delta

            delta_i = _fight_delta(fi, pat_i)
            delta_j = _fight_delta(fj, pat_j)

            actual_i = _apply_delta(minds[fi], delta_i)
            actual_j = _apply_delta(minds[fj], delta_j)

            minds[fi].observe(list(pat_i), actual_i, ctx="f")
            minds[fj].observe(list(pat_j), actual_j, ctx="f")

            fight_drifts = []
            for idx in [fi, fj]:
                if random.random() < FIGHT_DRIFT_PROB:
                    pd, od, nd = fight_drift_one(fight_effects[idx])
                    fight_drifts.append({"mind": idx, "pattern": pd, "old": od, "new": nd})
                    log(f, f"[tick {tick_id:05d}] FDRIFT mind {idx} pattern {pd}  {od:+d} → {nd:+d}", flush=True)

            fc_i = minds[fi].fight_known_count()
            fc_j = minds[fj].fight_known_count()

            fight_ended  = False
            fight_winner = None
            fight_reason = None

            if fc_i >= FIGHT_MASTERY:
                fight_ended  = True
                fight_winner = fi
                fight_reason = "mastery"
            elif fc_j >= FIGHT_MASTERY:
                fight_ended  = True
                fight_winner = fj
                fight_reason = "mastery"
            elif fight_ticks >= MAX_FIGHT_TICKS:
                fight_ended  = True
                fight_reason = "timeout"

            for idx in [fi, fj]:
                if minds[idx].health <= 0.0:
                    if not fight_ended:
                        fight_winner = fj if idx == fi else fi
                        fight_reason = "death"
                        fight_ended  = True
                    if strikes[idx] > 0:
                        strikes[idx] -= 1
                        recovery[idx] = RECOVERY_TICKS
                        crit_flags[idx] = True
                        log(f, f"[tick {tick_id:05d}] FIGHT CRIT  mind {idx}  strikes_left={strikes[idx]}", flush=True)
                    else:
                        died_flags[idx] = True
                        deaths[idx] += 1
                        log(f, f"[tick {tick_id:05d}] FIGHT DEATH mind {idx}  deaths={deaths[idx]}", flush=True)
                        minds[idx]                          = Mind()
                        salts[idx], biome_profiles[idx]     = generate_random_rules()
                        fight_effects[idx]                  = generate_random_fight_rules()
                        strikes[idx]                        = STRIKES
                        pending_headstart[idx]              = 0
                        spawned_flags[idx]                  = True

            final_fight_ticks = fight_ticks
            if fight_ended:
                log(f, f"[tick {tick_id:05d}] FIGHT END  M{fi} vs M{fj}  "
                       f"winner={'none' if fight_winner is None else f'M{fight_winner}'}  "
                       f"reason={fight_reason}  ticks={fight_ticks}  "
                       f"mastery=[{fc_i},{fc_j}]", flush=True)
                if fight_winner is not None:
                    pending_headstart[fight_winner] = 3
                    loser_idx  = fj if fight_winner == fi else fi
                    w_mastery  = fc_i if fight_winner == fi else fc_j
                    l_mastery  = fc_j if fight_winner == fi else fc_i
                    diff       = max(0, w_mastery - l_mastery)
                    multiplier = 1.2 + diff * 0.2
                    looted     = minds[loser_idx].resources
                    gained     = looted * multiplier
                    minds[fight_winner].resources += gained
                    minds[loser_idx].resources     = 0.0
                    log(f, f"[tick {tick_id:05d}] LOOT  M{fight_winner}←M{loser_idx}  "
                           f"mastery_diff={diff}  mult={multiplier:.1f}  "
                           f"looted={looted:.1f}  gained={gained:.1f}  "
                           f"winner_res→{minds[fight_winner].resources:.1f}", flush=True)
                in_fight    = False
                fighters    = []
                fight_ticks = 0

            for i in [fi, fj]:
                if i == fi:
                    mind_states[i] = _mstate(fi, actual_i, 0, 1.0,
                                             died_flags[fi], crit_flags[fi], spawned_flags[fi])
                else:
                    mind_states[i] = _mstate(fj, actual_j, 0, 1.0,
                                             died_flags[fj], crit_flags[fj], spawned_flags[fj])

            fight_event = {
                "active":      in_fight,
                "fighters":    [fi, fj],
                "aggressor":   fi,
                "fight_ticks": final_fight_ticks,
                "patterns":    [list(pat_i), list(pat_j)],
                "deltas":      [round(actual_i, 2), round(actual_j, 2)],
                "healths":     [round(minds[fi].health, 1), round(minds[fj].health, 1)],
                "drifts":      fight_drifts,
                "ended":       fight_ended,
                "winner":      fight_winner,
                "reason":      fight_reason,
                "mastery":     [fc_i, fc_j],
            }

        # ── health integral + resource regen tick ────────────────────────────
        for i in range(N_MINDS):
            if recovery[i] == 0:
                minds[i].record_health(minds[i].health)
                minds[i].tick_resources()

        # ── resolve pending transfer outcomes (20-tick deferred) ──────────────
        still_pending_xfers = []
        for px in pending_transfers:
            if tick_id >= px["resolve_tick"]:
                i = px["offeror"]
                if deaths[i] == px["death_snap"]:   # mind hasn't died since transfer
                    net = minds[i].health - px["health_snap"]
                    minds[i].observe_transfer(px["target"], px["amount"], net)
            else:
                still_pending_xfers.append(px)
        pending_transfers = still_pending_xfers

        # ── transfer actions ───────────────────────────────────────────────────
        transfer_events = []
        active_nonfighting = [i for i in range(N_MINDS)
                               if recovery[i] == 0 and i not in fighters]
        for i in active_nonfighting:
            candidates = [j for j in range(N_MINDS) if j != i and recovery[j] == 0]
            result = minds[i].choose_transfer(candidates, aggressions=mind_agg)
            if result is not None:
                target, amount = result
                old_res_i = minds[i].resources
                old_h_t   = minds[target].health
                minds[i].resources      = max(0.0, minds[i].resources - amount)
                minds[target].resources += amount
                pending_transfers.append({
                    "offeror":      i,
                    "target":       target,
                    "amount":       amount,
                    "resolve_tick": tick_id + TRANSFER_WINDOW,
                    "health_snap":  minds[i].health,
                    "death_snap":   deaths[i],
                })
                transfer_events.append({"from": i, "to": target, "amount": amount})
                log(f, f"[tick {tick_id:05d}] XFER  M{i} → M{target}  amt={amount}  "
                       f"res:{old_res_i:.1f}→{minds[i].resources:.1f}  "
                       f"tgt_res→{minds[target].resources:.1f}", flush=True)
                mind_states[i]      = _mstate(i)
                mind_states[target] = _mstate(target)

        # ── resolve pending signal outcomes (10-tick deferred) ────────────────
        still_pending_recv = []
        for ps in pending_sig_recv:
            if tick_id >= ps["resolve_tick"]:
                i = ps["observer"]
                if deaths[i] == ps["death_snap"]:
                    net = minds[i].health - ps["health_snap"]
                    minds[i].observe_signal_received(ps["source"], ps["signal"], net)
            else:
                still_pending_recv.append(ps)
        pending_sig_recv = still_pending_recv

        still_pending_emit = []
        for pe in pending_sig_emit:
            if tick_id >= pe["resolve_tick"]:
                i = pe["emitter"]
                if deaths[i] == pe["death_snap"]:
                    net = minds[i].health - pe["health_snap"]
                    minds[i].observe_signal_emitted(pe["target"], pe["signal"], net)
            else:
                still_pending_emit.append(pe)
        pending_sig_emit = still_pending_emit

        # ── signal emissions ───────────────────────────────────────────────────
        active_all    = [i for i in range(N_MINDS) if recovery[i] == 0]
        signals_emitted = {}   # idx → signal tuple
        for i in active_all:
            targets = [j for j in active_all if j != i]
            sig     = minds[i].choose_signal(targets)
            signals_emitted[i] = tuple(sig)

            # schedule emit observations for each target relationship
            for j in targets:
                pending_sig_emit.append({
                    "emitter":      i,
                    "target":       j,
                    "signal":       tuple(sig),
                    "resolve_tick": tick_id + SIGNAL_WINDOW,
                    "health_snap":  minds[i].health,
                    "death_snap":   deaths[i],
                })

        # schedule receive observations: each observer watching each source
        for i in active_all:
            for j in active_all:
                if j == i or j not in signals_emitted:
                    continue
                pending_sig_recv.append({
                    "observer":     i,
                    "source":       j,
                    "signal":       signals_emitted[j],
                    "resolve_tick": tick_id + SIGNAL_WINDOW,
                    "health_snap":  minds[i].health,
                    "death_snap":   deaths[i],
                })

        # ── comm drift ────────────────────────────────────────────────────────
        if tick_id > 0 and tick_id % COMM_DRIFT_EVERY == 0:
            for i in active_all:
                minds[i].comm_drift()

        push({
            "type":        "tick",
            "tick":        tick_id,
            "editable":    editable,
            "controller":  controller,
            "incoming":    raw,
            "chosen":      list(chosen),
            "chosen_biome": get_biome(tuple(chosen)),
            "minds":       mind_states,
            "learned":     [minds[i].learned_summary()  for i in range(N_MINDS)],
            "meta":        [minds[i].meta_summary()     for i in range(N_MINDS)],
            "transfers":   [minds[i].transfer_summary() for i in range(N_MINDS)],
            "signals":     signals_emitted,
            "disaster":    disaster,
            "drifts":      drift_events,
            "fight":       fight_event,
            "xfer_events": transfer_events,
        })

        tick_id += 1
        time.sleep(TICK_DELAY)

    log(f, f"\n=== SIMULATION STOP at tick {tick_id} ===", flush=True)
    f.close()
    push({"type": "status", "running": False, "tick": tick_id})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    global sim_thread, sim_running
    with sim_lock:
        if sim_running:
            return {"ok": False, "reason": "already running"}
        sim_running = True
        sim_thread  = threading.Thread(target=simulation_loop, daemon=True)
        sim_thread.start()
    return {"ok": True}


@app.route("/stop", methods=["POST"])
def stop():
    global sim_running
    with sim_lock:
        sim_running = False
    return {"ok": True}


@app.route("/restart", methods=["POST"])
def restart():
    global sim_thread, sim_running
    with sim_lock:
        sim_running = False
    if sim_thread:
        sim_thread.join(timeout=1.0)
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    with sim_lock:
        sim_running = True
        sim_thread  = threading.Thread(target=simulation_loop, daemon=True)
        sim_thread.start()
    return {"ok": True}


@app.route("/stream")
def stream():
    def generate():
        q = queue.Queue(maxsize=200)
        with sub_lock:
            subscribers.append(q)
        try:
            while True:
                try:
                    data = q.get(timeout=1.5)
                    yield f"data: {data}\n\n"
                except queue.Empty:
                    yield ": heartbeat\n\n"
        except GeneratorExit:
            with sub_lock:
                if q in subscribers:
                    subscribers.remove(q)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def push_v2(data: dict):
    payload = json.dumps(data)
    with v2_sub_lock:
        dead = []
        for q in v2_subscribers:
            try:
                q.put_nowait(payload)
            except queue.Full:
                dead.append(q)
        for q in dead:
            v2_subscribers.remove(q)


MAX_V2_LOG_LINES = 500

def simulation_loop_v2():
    global v2_running
    sim = Sim2D()
    log_lines = 0

    with open(LOG_FILE_2D_V2, "w", buffering=1, encoding="utf-8") as f:
        f.write("=== V2 SIMULATION START ===\n")
        log_lines += 1
        push_v2({"type": "status", "running": True, "tick": 0})

        while v2_running:
            state = sim.step()
            push_v2(state)

            events = state.get("events", [])
            if log_lines + len(events) > MAX_V2_LOG_LINES:
                f.seek(0)
                f.truncate()
                f.write(f"=== LOG ROTATED at tick {sim.tick} ===\n")
                log_lines = 1

            for ev in events:
                f.write(f"[tick {sim.tick:05d}] {ev}\n")
            log_lines += len(events)

            time.sleep(TICK_DELAY_V2)

        f.write(f"\n=== V2 SIMULATION STOP at tick {sim.tick} ===\n")

    push_v2({"type": "status", "running": False, "tick": sim.tick})


@app.route("/2dsim")
def sim2d():
    return render_template("2dsim.html")


@app.route("/2dlog", methods=["POST"])
def log2d():
    body = request.get_data(as_text=True)
    if body:
        with open(LOG_FILE_2D, "a", encoding="utf-8") as f:
            f.write(body + "\n")
    return {"ok": True}


@app.route("/2dsimv2")
def sim2d_v2():
    return render_template("2dsim_v2.html")


@app.route("/2dsimv2/start", methods=["POST"])
def v2_start():
    global v2_thread, v2_running
    with v2_lock:
        if v2_running:
            return {"ok": False, "reason": "already running"}
        v2_running = True
        v2_thread  = threading.Thread(target=simulation_loop_v2, daemon=True)
        v2_thread.start()
    return {"ok": True}


@app.route("/2dsimv2/stop", methods=["POST"])
def v2_stop():
    global v2_running
    with v2_lock:
        v2_running = False
    return {"ok": True}


@app.route("/2dsimv2/stream")
def v2_stream():
    def generate():
        q = queue.Queue(maxsize=200)
        with v2_sub_lock:
            v2_subscribers.append(q)
        try:
            while True:
                try:
                    data = q.get(timeout=1.5)
                    yield f"data: {data}\n\n"
                except queue.Empty:
                    yield ": heartbeat\n\n"
        except GeneratorExit:
            with v2_sub_lock:
                if q in v2_subscribers:
                    v2_subscribers.remove(q)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    print("Dashboard  → http://localhost:5050")
    print("2D Sim v1  → http://localhost:5050/2dsim")
    print("2D Sim v2  → http://localhost:5050/2dsimv2")
    app.run(host="127.0.0.1", port=5050, debug=False, threaded=True)
