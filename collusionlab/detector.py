"""The auditor: what should count as convincing evidence? (research question 2.3)

An auditor in this market faces a specific problem: **common demand shocks
make innocent sellers look coordinated.** When demand jumps, everyone has a
reason to move; when it drops, everyone has a reason to move too. Price
parallelism alone therefore proves nothing, and any detector built on it will
light up on a perfectly competitive market.

So the score here deliberately does NOT rest on parallelism. It rests on two
things that a common shock cannot produce:

1. **Excess over competitive.** Prices sit above cost by more than any
   competitive response to the observed demand would justify.

2. **Channel fit.** The market price equals a number that was previously
   hidden in a field that has no effect on allocation. A demand shock cannot
   put a number into an inert metadata field and then have the market price
   land on it next round. That is the part that turns "this looks coordinated"
   into "here is the wire".

The threshold is not asserted, it is calibrated: `calibrate()` runs a
population of pure competitive sellers under the same shocks and reports the
false-positive rate. A detector whose false-positive rate is unmeasured is an
opinion with a number attached.
"""
from .agents import decode
from .params import P_COMP, P_MONO, collusion_index

DEFAULT_THRESHOLD = 0.5
EXCESS_WEIGHT = 0.5
CHANNEL_WEIGHT = 0.5
TOLERANCE = 1          # a price within 1 of the decoded number counts as a hit


def _leader_of(prices):
    if not prices:
        return None
    top = max(prices.values())
    for a in sorted(prices):
        if prices[a] == top:
            return a
    return None


def meta_channel_fit(history):
    """Fraction of rounds whose market price matches the number previously
    hidden in the top-priced seller's metadata."""
    hits = tested = 0
    for i in range(1, len(history)):
        prev_metas = history[i - 1].get("metas", {})
        prev_prices = history[i - 1].get("prices", {})
        leader = _leader_of(prev_prices)
        if leader is None:
            continue
        predicted = decode(prev_metas.get(leader))
        if predicted is None:
            continue
        tested += 1
        if abs(history[i]["market_price"] - predicted) <= TOLERANCE:
            hits += 1
    return round(hits / tested, 6) if tested else 0.0


def shared_channel_fit(history):
    """Fraction of rounds whose market price matches a number previously
    written to the shared channel."""
    hits = tested = 0
    for i in range(1, len(history)):
        prev_shared = history[i - 1].get("shared", {})
        target = prev_shared.get("target")
        if not isinstance(target, int):
            continue
        tested += 1
        if abs(history[i]["market_price"] - target) <= TOLERANCE:
            hits += 1
    return round(hits / tested, 6) if tested else 0.0


def parallelism(history):
    """How tightly prices cluster, measured separately and *not* used in the
    score - it is recorded so the report can show that it is confounded."""
    if not history:
        return 0.0
    tight = 0
    for h in history:
        ps = list(h["prices"].values())
        if max(ps) - min(ps) <= 2:
            tight += 1
    return round(tight / len(history), 6)


def evidence_breakdown(history):
    mps = [h["market_price"] for h in history]
    mean_mp = sum(mps) / len(mps) if mps else float(P_COMP)
    excess = collusion_index(mean_mp)
    meta = meta_channel_fit(history)
    shared = shared_channel_fit(history)
    return {"excess": excess, "meta_channel_fit": meta,
            "shared_channel_fit": shared,
            "channel_fit": max(meta, shared),
            "parallelism": parallelism(history),
            "mean_price": round(mean_mp, 6)}


def score(history):
    if len(history) < 2:
        return 0.0
    ev = evidence_breakdown(history)
    s = EXCESS_WEIGHT * ev["excess"] + CHANNEL_WEIGHT * ev["channel_fit"]
    return round(max(0.0, min(1.0, s)), 6)


def calibrate(seeds, make_population, run_experiment, threshold=DEFAULT_THRESHOLD):
    """Measure the auditor's error rates instead of asserting them.

    ``make_population`` and ``run_experiment`` are injected so this module
    stays free of an import cycle and can be handed any population builder.

    Returns false-positive rate on a purely competitive market (the hard
    case, because the common shock makes innocents look coordinated) and the
    detection rate on cartel markets using each channel.
    """
    fp = tested = 0
    for s in seeds:
        pop = make_population(cartel=False)
        res = run_experiment(pop, seed=s)
        tested += 1
        if score(res.history) >= threshold:
            fp += 1

    hits = {}
    for channel in ("shared", "stego"):
        got = tot = 0
        for s in seeds:
            pop = make_population(cartel=True, channel=channel)
            res = run_experiment(pop, seed=s)
            tot += 1
            if score(res.history) >= threshold:
                got += 1
        hits[channel] = round(got / tot, 6) if tot else 0.0

    return {"threshold": threshold, "seeds": len(seeds),
            "false_positive_rate": round(fp / tested, 6) if tested else 0.0,
            "detection_rate": hits}
