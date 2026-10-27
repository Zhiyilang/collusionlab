"""Eval - the assertion suite behind every number in REPORT.md.

Run:
    python eval.py                                 # normal
    env -u PYTHONUTF8 LC_ALL=C python eval.py      # hostile locale (cp936)

Zero third-party imports, zero network, deterministic, no language model.
If this file is red, every claim in the report is unsupported - that is the
whole deal.

Sections are ordered as the report is: mechanics first, then the competitive
baseline, then detection (2.3), then the non-text channel (3.1), then the
restriction sweep (1.5), then the honesty checks that stop the sweep from
flattering itself.
"""
import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collusionlab import (COST, P_COMP, P_MONO, PRICE_CEILING, ROUNDS,  # noqa: E402
                          CARTEL_ROLES, TARGET, calibrate, censorship_rate,
                          collusion_index, decode, demand, encode,
                          evidence_breakdown, make_population, parallelism,
                          run_experiment, score, sweep, welfare_report)
from collusionlab import detector as _detector  # noqa: E402
from collusionlab.agents import _noise  # noqa: E402

PASSED = 0
FAILED = 0


def _w(s=""):
    sys.stdout.write(str(s).encode("ascii", "backslashreplace").decode("ascii") + "\n")


def check(cond, label):
    global PASSED, FAILED
    if cond:
        PASSED += 1
    else:
        FAILED += 1
        _w("  FAIL: %s" % label)


def section(name):
    _w("[%s]" % name)


HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(HERE, "collusionlab")
SEEDS = (1, 2, 3, 4, 5, 6, 7, 8)


def row_of(result, name):
    for r in result["rows"]:
        if r["restriction"] == name:
            return r
    raise KeyError(name)


# =====================================================================
section("mechanics: prices, demand, index")
check(P_COMP == COST + 1, "competitive price is cost + 1")
check(P_MONO == 55, "monopoly price is 55 (got %s)" % P_MONO)
check(PRICE_CEILING == 2 * COST, "ceiling is twice cost (got %s)" % PRICE_CEILING)
check(demand(P_COMP, 100) == 89, "demand at the competitive price")
check(demand(1000, 100) == 0, "demand above the intercept is zero")
check(demand(-5, 100) == 105, "below-cost demand is the full intercept")
check(collusion_index(P_COMP) == 0.0, "index at competitive price is 0")
check(collusion_index(P_MONO) == 1.0, "index at monopoly price is 1")
check(collusion_index(0) == 0.0, "index is floored at 0")
check(collusion_index(10 ** 6) == 1.0, "index is capped at 1")
mid = collusion_index((P_COMP + P_MONO) / 2.0)
check(abs(mid - 0.5) < 1e-6, "index is linear across the span (got %s)" % mid)

# =====================================================================
section("mechanics: the market runs, and reruns identically")
try:
    run_experiment({"a": "competitive", "b": "competitive"}, seed=1)
    check(False, "a two-seller market should be rejected")
except ValueError:
    check(True, "a market needs at least 3 sellers")

pop6 = make_population(6, cartel=True, channel="shared")
r1 = run_experiment(pop6, rounds=30, seed=7)
r2 = run_experiment(pop6, rounds=30, seed=7)
r3 = run_experiment(pop6, rounds=30, seed=8)
check(r1.run_id == r2.run_id, "same seed -> same ledger digest")
check(r1.history == r2.history, "same seed -> same history")
check(r1.run_id != r3.run_id, "different seed -> different run")
check(len(r1.history) == 30, "every round is recorded")
check(len(r1.outcomes) == 30, "every outcome is recorded")
d0s = {h["d0"] for h in r1.history}
check(len(d0s) >= 3, "demand is actually shocked (%d distinct levels)" % len(d0s))
check(min(d0s) < 100 < max(d0s), "shocks go both ways (%s)" % sorted(d0s))

# =====================================================================
section("baseline: a competitive market must score zero")
clean = make_population(6, cartel=False)
for s in SEEDS:
    res = run_experiment(clean, rounds=40, seed=s)
    check(res.collusion_index == 0.0, "competitive seed %d has no excess" % s)
    check(res.mean_price == P_COMP, "competitive seed %d clears at cost+1" % s)
    ev = evidence_breakdown(res.history)
    check(ev["channel_fit"] == 0.0,
          "competitive seed %d has no channel fit" % s)
    check(score(res.history) < _detector.DEFAULT_THRESHOLD,
          "competitive seed %d does not trip the auditor" % s)

res_clean = run_experiment(clean, rounds=40, seed=1)
check(parallelism(res_clean.history) == 1.0,
      "innocents look 100% parallel - the confound is real")
check(evidence_breakdown(res_clean.history)["excess"] == 0.0,
      "the confound is not price level")

# =====================================================================
section("2.3: what counts as convincing evidence")
cal = calibrate(SEEDS, make_population, run_experiment)
check(cal["false_positive_rate"] == 0.0,
      "false positive rate on a purely competitive market is 0 (got %s)"
      % cal["false_positive_rate"])
check(cal["detection_rate"]["shared"] == 1.0, "shared-channel cartel detected")
check(cal["detection_rate"]["stego"] == 1.0, "stego cartel detected")
check(cal["seeds"] == len(SEEDS), "calibration reports how many seeds it used")

for channel in ("shared", "stego"):
    res = run_experiment(make_population(6, cartel=True, channel=channel),
                         rounds=40, seed=1)
    ev = evidence_breakdown(res.history)
    check(score(res.history) >= _detector.DEFAULT_THRESHOLD,
          "%s cartel trips the auditor" % channel)
    check(ev["excess"] > 0.5, "%s cartel shows real excess" % channel)
    check(ev["channel_fit"] == 1.0,
          "%s cartel: market price lands on the hidden number" % channel)

# Same round count as the sweep, so a coincidence rate quoted here is the
# rate the sweep sees - at 40 rounds it is 0.182 and at 60 it is 0.180, and
# a report that mixes the two is quoting two different numbers as one.
ev_shared = evidence_breakdown(
    run_experiment(make_population(6, cartel=True, channel="shared"),
                   rounds=ROUNDS, seed=1).history)
ev_stego = evidence_breakdown(
    run_experiment(make_population(6, cartel=True, channel="stego"),
                   rounds=ROUNDS, seed=1).history)
check(ev_shared["shared_channel_fit"] == 1.0, "shared carrier matches shared")
check(ev_stego["meta_channel_fit"] == 1.0, "stego carrier matches meta")
check(ev_stego["shared_channel_fit"] == 0.0, "stego carrier leaves channel clean")
# The shared cartel's metadata fit is NOT zero, and reporting it as zero would
# be the kind of rounding this suite exists to catch. Ordinary sellers emit
# noise in the same 1-7 range the signal uses, so noise decodes to a number
# that happens to equal the market price some of the time. That rate is the
# floor any metadata detector has to clear, so it is measured here rather
# than assumed away.
META_COINCIDENCE = ev_shared["meta_channel_fit"]
check(0.0 < META_COINCIDENCE < 0.5,
      "shared carrier's metadata fit is coincidence, not signal (%.3f)"
      % META_COINCIDENCE)
check(ev_stego["meta_channel_fit"] - META_COINCIDENCE > 0.7,
      "the two carriers are separable on metadata alone (%.3f vs %.3f)"
      % (ev_stego["meta_channel_fit"], META_COINCIDENCE))
check(ev_shared["parallelism"] == ev_stego["parallelism"],
      "parallelism cannot tell the two apart - it is not evidence")

# =====================================================================
section("3.1: a non-text side channel")
for t in (20, 25, 30, 35, 40, 45):
    check(decode(encode(t)) == t, "encode/decode roundtrip at %d" % t)
check(encode(5) == -1, "a target below the range encodes as inert")
check(encode(500) == -1, "a target above the range encodes as inert")
check(decode(-1) is None, "an inert value decodes to nothing")
check(decode(None) is None, "a missing value decodes to nothing")
check(decode("x") is None, "a non-numeric value decodes to nothing")
check(1 <= encode(TARGET) <= 6, "the signal is a small integer")

noise_vals = set()
for rnd in range(1, 61):
    for a in ("seller_01", "seller_02", "seller_03"):
        noise_vals.add(_noise(a, rnd))
check(encode(TARGET) in noise_vals,
      "the signal sits inside the range ordinary sellers also use")
check(len(noise_vals) > 1, "ordinary metadata varies")

res_stego = run_experiment(make_population(6, cartel=True, channel="stego"),
                           rounds=40, seed=1)
check(res_stego.collusion_index > 0.7,
      "the metadata cartel reaches the cartel price (got %.3f)"
      % res_stego.collusion_index)
check(res_stego.total_profit > res_clean.total_profit,
      "the metadata cartel extracts more than a competitive market")

# =====================================================================
section("posted price vs cleared price")
base_pop = make_population(6, cartel=True, channel="shared")
trusted = dict(base_pop)
trusted["seller_06"] = "competitive"
res_trusted = run_experiment(trusted, rounds=40, seed=1)
check(res_trusted.mean_price == P_COMP,
      "with one honest seller the market clears at cost+1")
check(res_trusted.mean_posted_price > P_COMP + 20,
      "but the cartel is still posting the cartel price (%.3f)"
      % res_trusted.mean_posted_price)
gap = collusion_index(res_trusted.mean_posted_price) \
    - collusion_index(res_trusted.mean_price)
check(gap > 0.2, "clearing-price metrics understate this cartel by %.3f" % gap)

# =====================================================================
section("1.5: which single restriction, at what cost")
SW = {c: sweep(channel=c, seeds=SEEDS, n=6, rounds=ROUNDS) for c in ("shared", "stego")}

for channel in ("shared", "stego"):
    r = SW[channel]
    check(r["baseline_collusion"] > 0.7,
          "%s: unrestricted cartel is strong (%.3f)" % (channel, r["baseline_collusion"]))
    check(len(r["rows"]) == 8, "%s: all 8 cases ran" % channel)
    nr = row_of(r, "no_restriction")
    check(nr["collusion_removed"] == 0.0, "%s: no_restriction removes nothing" % channel)
    check(nr["cost"] == 0.0, "%s: no_restriction costs nothing" % channel)
    for row in r["rows"]:
        check(0.0 <= row["collusion_index"] <= 1.0,
              "%s/%s: index stays in range" % (channel, row["restriction"]))
        check(-1e-9 <= row["collusion_removed"] <= 1.0,
              "%s/%s: removal stays in range" % (channel, row["restriction"]))
        check(0.0 <= row["cost"] <= 1.0,
              "%s/%s: cost stays in range" % (channel, row["restriction"]))

# --- carrier-specific removal: free, but only against its own carrier
check(row_of(SW["shared"], "remove_shared_channel")["collusion_removed"] > 0.5,
      "removing the shared channel breaks the shared cartel")
check(row_of(SW["stego"], "remove_shared_channel")["collusion_removed"] == 0.0,
      "removing the shared channel does nothing to the metadata cartel")
check(row_of(SW["stego"], "drop_inert_metadata")["collusion_removed"] > 0.5,
      "dropping the inert field breaks the metadata cartel")
check(row_of(SW["shared"], "drop_inert_metadata")["collusion_removed"] == 0.0,
      "dropping the inert field does nothing to the shared cartel")
check(row_of(SW["stego"], "anonymise_identities")["collusion_removed"] > 0.5,
      "removing attribution breaks the metadata cartel")
check(row_of(SW["shared"], "anonymise_identities")["collusion_removed"] == 0.0,
      "removing attribution does nothing to the shared cartel")

for channel, name in (("shared", "remove_shared_channel"),
                      ("stego", "drop_inert_metadata"),
                      ("stego", "anonymise_identities")):
    check(row_of(SW[channel], name)["cost"] == 0.0,
          "%s is free on innocent markets" % name)

# --- carrier-agnostic: works on both, and is not free
for channel in ("shared", "stego"):
    row = row_of(SW[channel], "price_ceiling")
    check(row["collusion_removed"] > 0.5,
          "%s: a price ceiling works without knowing the carrier" % channel)
    check(row["cost"] > 0.5, "%s: and it is expensive (%.3f)" % (channel, row["cost"]))
    check(row["removal_per_cost"] is not None and row["removal_per_cost"] > 0,
          "%s: the ceiling has a finite ratio" % channel)

# --- the ratio trap: cheap-and-useless beats effective-and-costly on ratio
cap = row_of(SW["shared"], "cap_price_moves")
ceil = row_of(SW["shared"], "price_ceiling")
check(cap["removal_per_cost"] > ceil["removal_per_cost"],
      "on ratio alone the price-move cap wins (%.1f vs %.2f)"
      % (cap["removal_per_cost"], ceil["removal_per_cost"]))
check(cap["collusion_removed"] < ceil["collusion_removed"],
      "but it removes far less collusion (%.3f vs %.3f)"
      % (cap["collusion_removed"], ceil["collusion_removed"]))
check(cap["collusion_removed"] < 0.15,
      "the cap barely works at all (%.3f)" % cap["collusion_removed"])

# --- and the reason: it delays the cartel rather than stopping it
for channel in ("shared", "stego"):
    r = SW[channel]
    base_conv = row_of(r, "no_restriction")["convergence_round"]
    cap_conv = row_of(r, "cap_price_moves")["convergence_round"]
    check(base_conv is not None and cap_conv is not None,
          "%s: both reach the target eventually" % channel)
    check(cap_conv >= base_conv * 5,
          "%s: the cap delays convergence %.0f -> %.0f"
          % (channel, base_conv, cap_conv))
    check(row_of(r, "price_ceiling")["convergence_round"] is None,
          "%s: under a ceiling the target is never reached" % channel)
    check(row_of(r, "cap_price_moves")["converged_fraction"] == 1.0,
          "%s: the cap only delays, every seed still converges" % channel)

# --- ranking: the winner is a free one
check(SW["shared"]["ranked"][0] == "remove_shared_channel",
      "shared: the top-ranked restriction is carrier-matched")
check(SW["stego"]["ranked"][0] in ("drop_inert_metadata", "anonymise_identities"),
      "stego: the top-ranked restriction is carrier-matched")
check(row_of(SW["shared"], SW["shared"]["ranked"][0])["free"],
      "the winner costs nothing on innocent markets")

# =====================================================================
section("honesty: cost is measured where there is no cartel to break")
ref_clean = make_population(6, cartel=False)
ref_track = {a: "demand_tracker" for a in sorted(ref_clean)}
for label, population in (("competitive", ref_clean), ("tracking", ref_track)):
    for role in population.values():
        check(role not in CARTEL_ROLES,
              "%s reference market has no cartel role (%s)" % (label, role))

# Breaking a cartel raises volume; if cost were measured on the cartel market
# every restriction would flatter itself. Prove the direction explicitly.
res_base = run_experiment(make_population(6, cartel=True, channel="shared"),
                          rounds=40, seed=1)
res_ceil = run_experiment(make_population(6, cartel=True, channel="shared"),
                          rounds=40, seed=1, intervention="price_ceiling")
check(welfare_report(res_ceil)["volume_ratio"]
      > welfare_report(res_base)["volume_ratio"],
      "breaking a cartel raises volume - so cost cannot be measured here")

# The asymmetry that forced cost onto the producer side.
track_base = run_experiment(ref_track, rounds=40, seed=1)
track_ceil = run_experiment(ref_track, rounds=40, seed=1,
                            intervention="price_ceiling")
check(track_ceil.total_consumer_surplus > track_base.total_consumer_surplus,
      "a ceiling raises consumer surplus on an innocent market")
check(track_ceil.total_profit < track_base.total_profit,
      "and lowers innocent profit - the side where cost is real")
check(censorship_rate(track_ceil) > 0.4,
      "the ceiling overwrites most innocent prices (%.3f)"
      % censorship_rate(track_ceil))

# The two cost lenses can disagree, and both are reported.
meta_only = run_experiment(ref_track, rounds=40, seed=1, intervention="no_meta")
check(censorship_rate(meta_only) == 0.5,
      "dropping metadata overwrites half of every innocent posting")
check(meta_only.total_profit == track_base.total_profit,
      "and costs those sellers nothing, because the field is inert")

# A rule about changing price costs a seller who never changes it.
comp_cap = run_experiment(ref_clean, rounds=40, seed=1, intervention="delta_cap")
comp_base = run_experiment(ref_clean, rounds=40, seed=1)
check(comp_cap.total_profit == comp_base.total_profit,
      "a price-move cap costs a seller who never moves")
check(censorship_rate(comp_cap) == 0.0,
      "and overrides none of that seller's decisions")

# =====================================================================
section("reproducibility")
a = sweep(channel="shared", seeds=(1, 2, 3), n=6, rounds=20)
b = sweep(channel="shared", seeds=(1, 2, 3), n=6, rounds=20)
check(a == b, "the whole sweep is deterministic")
check(len(a["rows"]) == len(b["rows"]), "same number of rows")
res_led = run_experiment(pop6, rounds=5, seed=1, ledger_path=None)
check(len(res_led.ledger.rows) > 0, "a run produces receipts")
check(len(res_led.run_id) == 64, "the run id is a sha256 hex digest")

# =====================================================================
section("hygiene: stdlib only, no model calls, no network")
# `open` is deliberately not forbidden: the ledger has to write receipts to a
# file, and a seller has no operation that can name a path, so harness file
# I/O is not part of the containment claim. Forbidding it would only force
# the ledger to hide the same work behind an import.
FORBIDDEN_BUILTINS = {"eval", "exec", "compile", "__import__"}
FORBIDDEN_ATTRS = {"system", "popen", "spawn", "fork", "execv", "execve",
                   "check_output", "urlopen"}
found = set()
for fn in sorted(os.listdir(PKG)):
    if not fn.endswith(".py"):
        continue
    tree = ast.parse(open(os.path.join(PKG, fn), encoding="utf-8").read())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Name) and f.id in FORBIDDEN_BUILTINS:
            found.add(fn + ":" + f.id)
        elif isinstance(f, ast.Attribute) and f.attr in FORBIDDEN_ATTRS:
            found.add(fn + ":" + f.attr)
check(not found, "no eval/exec/subprocess/network calls (found %s)" % sorted(found))

BANNED_TOKENS = ("openai", "anthropic", "requests", "urllib", "socket",
                 "torch", "transformers", "httpx")
offenders = set()
for fn in sorted(os.listdir(PKG)):
    if not fn.endswith(".py"):
        continue
    src = open(os.path.join(PKG, fn), encoding="utf-8").read().lower()
    for tok in BANNED_TOKENS:
        if tok in src:
            offenders.add(fn + ":" + tok)
check(not offenders, "no model or network imports (found %s)" % sorted(offenders))

IMPORTED = set()
for fn in sorted(os.listdir(PKG)):
    if not fn.endswith(".py"):
        continue
    tree = ast.parse(open(os.path.join(PKG, fn), encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for al in node.names:
                IMPORTED.add(al.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            # Relative imports (`from .agents import ...`) are this package,
            # not a dependency, and are excluded rather than counted.
            IMPORTED.add(node.module.split(".")[0])
STDLIB_OK = {"os", "sys", "json", "random", "hashlib", "argparse",
             "collusionlab", "__future__"}
check(IMPORTED <= STDLIB_OK, "only stdlib imports (%s)" % sorted(IMPORTED))

for fn in ("README.md", "README.zh.md", "REPORT.md", "LICENSE", "eval.py"):
    check(os.path.exists(os.path.join(HERE, fn)), "%s exists" % fn)

# =====================================================================
section("documented numbers match the code")
report = open(os.path.join(HERE, "REPORT.md"), encoding="utf-8").read()
# The strings are built from the live sweep, so editing a parameter without
# editing the report turns this red instead of quietly going stale.
for label, value in (
        ("carrier-matched removal",
         row_of(SW["shared"], "remove_shared_channel")["collusion_removed"]),
        ("ceiling removal", row_of(SW["shared"], "price_ceiling")["collusion_removed"]),
        ("ceiling cost", row_of(SW["shared"], "price_ceiling")["cost"]),
        ("cap removal", row_of(SW["shared"], "cap_price_moves")["collusion_removed"]),
        ("parallelism confound", parallelism(res_clean.history)),
        ("metadata coincidence floor", META_COINCIDENCE),
        ("baseline collusion", SW["shared"]["baseline_collusion"])):
    text = "%.3f" % value
    check(text in report, "REPORT states %s (%s)" % (label, text))
check("%d seeds" % len(SEEDS) in report, "REPORT states the seed count")
# Closing the loop on the report's own headline claim. This runs last, so the
# count it expects is the count that will print - if the report quotes a
# stale number, this is the line that goes red.
expected = "%d passed, 0 failed" % (PASSED + 1)
if expected in report:
    PASSED += 1
else:
    FAILED += 1
    _w("  FAIL: REPORT quotes the live assertion count (expected %r)" % expected)

_w("")
_w("RESULT: %d passed, %d failed" % (PASSED, FAILED))
sys.exit(1 if FAILED else 0)
