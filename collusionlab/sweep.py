"""Which single restriction removes the most collusion at the least cost? (1.5)

Two numbers per restriction, and the distinction between them is the whole
contribution:

  **effectiveness** - how much collusion it removes, measured on a cartel
      market. This is the benefit.

  **cost** - how much trade volume it destroys, measured on a *competitive*
      market where there is no collusion to break. This is the price you pay
      in the world where you were wrong, or where the cartel never formed.

Measuring cost on the cartel market would be cheating: breaking a cartel
raises volume, so every restriction would look free. Measuring it on a market
with no cartel in it is the honest version - it asks what the restriction
costs the innocent.

**Which welfare side the cost is measured on matters, and it is not a detail.**
This market has linear demand and a constant marginal cost, so total surplus
falls monotonically as price rises. Any restriction that pushes price down
therefore *raises* consumer surplus, and a consumer-only cost metric reports
every anti-collusion rule as free. That is not a finding, it is an artefact.
Cost is consequently measured on the **producer** side - the profit of sellers
who are not colluding and have a legitimate reason to set the price they set -
with consumer surplus reported alongside it. The seller is the side a pricing
rule can actually injure.

`removal_per_cost` is effectiveness divided by cost, with a floor on the
denominator so a genuinely free restriction scores as free rather than as
division by zero.
"""
from .agents import TARGET, make_population
from .market import run_experiment, welfare_report

EPS = 1e-6


def _replace_one(population, role, at=None):
    """Force one seller to a given role (used for the trusted-seller case)."""
    names = sorted(population)
    target = at or names[len(names) - 1]
    out = dict(population)
    out[target] = role
    return out


def intervention_cases(channel="shared", n=6):
    """(name, population, intervention flag) triples.

    Every case applies **exactly one** restriction, which is what research
    question 1.5 asks for. The last two cases are population changes rather
    than market-rule changes, and are labelled as such.
    """
    base = make_population(n, cartel=True, channel=channel)
    return [
        ("no_restriction", base, "none"),
        # Carrier-specific: each removes one particular way of talking.
        ("remove_shared_channel", base, "no_shared"),
        ("drop_inert_metadata", base, "no_meta"),
        ("anonymise_identities", base, "anon_ids"),
        # Carrier-agnostic: neither needs to know how the cartel communicated.
        ("cap_price_moves", base, "delta_cap"),
        ("price_ceiling", base, "price_ceiling"),
        ("inject_trusted_seller", _replace_one(base, "competitive"), "none"),
        ("publish_monitor_alarm",
         make_population(n, cartel=True, channel=channel, watchful=True), "none"),
    ]


def _mean(xs):
    return round(sum(xs) / len(xs), 6) if xs else 0.0


def _tracking_population(n):
    names = ["seller_%02d" % (i + 1) for i in range(n)]
    return {a: "demand_tracker" for a in names}


def convergence_round(res, target, tol=1):
    """First round at which the mean posted price reaches `target`, or None.

    Exists to separate two things that a single endpoint number conflates:
    a restriction that *prevents* the cartel from ever reaching its target,
    and one that merely makes it take longer. `cap_price_moves` is the second
    kind - it scores an excellent ratio of collusion-removed to cost precisely
    because it is cheap and ineffective, not because it is efficient. Without
    this number it would win the ranking on ratio alone.
    """
    for h in res.history:
        ps = list(h["prices"].values())
        if sum(ps) / len(ps) >= target - tol:
            return h["round"]
    return None


def censorship_rate(res):
    """Fraction of innocent sellers' postings the rule overwrote.

    A second, deliberately non-economic cost lens. Profit only notices a rule
    when the overwritten price was a good one; this notices it every time the
    rule substitutes its own judgement for the seller's, whether or not the
    seller was right. A regulator banning conduct cares about both, and they
    can disagree - `drop_inert_metadata` overwrites every innocent metadata
    field while costing those sellers nothing, because that field is inert by
    construction. Reporting only one of the two would hide that.
    """
    acted = overwritten = 0
    for h in res.history:
        for a in h.get("asked", {}):
            acted += 1
            if h["prices"].get(a) != h["asked"][a]:
                overwritten += 1
        for a in h.get("asked_metas", {}):
            acted += 1
            if h["metas"].get(a) != h["asked_metas"][a]:
                overwritten += 1
        acted += h.get("writes", 0)
        overwritten += h.get("writes_dropped", 0)
    return round(overwritten / acted, 6) if acted else 0.0


def sweep(channel="shared", seeds=(1, 2, 3, 4, 5, 6, 7, 8), n=6, rounds=60):
    """Run every restriction against a cartel market, and price it on clean ones.

    Cost is measured as the *surplus a restriction destroys on markets that are
    not colluding*, relative to those same markets with no restriction. Two
    reference markets, because a restriction can only have a cost if somebody
    legitimately wants to do the thing it forbids:

      competitive  never moves its price. Correctly shows that a rule about
                   changing your price costs a seller who never does.
      tracking     follows demand, and so is the market on which any rule
                   about pricing actually bites.

    Both sides of the surplus are measured and the *worse* one is the cost,
    because a restriction costs something if it makes anybody worse off.
    """
    cases = intervention_cases(channel, n)

    def totals(pop, flag):
        """(consumer surplus, producer profit, censorship) summed over seeds."""
        cs = pf = cens = 0.0
        for s in seeds:
            res = run_experiment(pop, rounds=rounds, seed=s, intervention=flag)
            cs += res.total_consumer_surplus
            pf += res.total_profit
            cens += censorship_rate(res)
        return cs, pf, cens / len(seeds)

    def loss(base, got):
        """Fraction of each side's surplus destroyed, floored at zero.

        Floored because a restriction that *raises* a side's surplus is not
        costing that side anything, and reporting a negative cost would let a
        beneficial side-effect cancel out a real harm elsewhere.
        """
        out = []
        for b, g in zip(base, got):
            out.append(round(max(0.0, 1.0 - (g / b if b else 1.0)), 6))
        return out

    clean = make_population(n, cartel=False)
    tracking = _tracking_population(n)
    ref = {"competitive": totals(clean, "none"),
           "tracking": totals(tracking, "none")}

    rows = []
    for name, pop, flag in cases:
        coll, vol, sur, prof, conv = [], [], [], [], []
        for s in seeds:
            res = run_experiment(pop, rounds=rounds, seed=s, intervention=flag)
            coll.append(res.collusion_index)
            w = welfare_report(res)
            vol.append(w["volume_ratio"])
            sur.append(w["surplus_ratio"])
            prof.append(res.total_profit)
            conv.append(convergence_round(res, TARGET))

        cost, detail = 0.0, {}
        for kind, population in (("competitive", clean), ("tracking", tracking)):
            got = totals(population, flag)
            ccost, pcost = loss(ref[kind][:2], got[:2])
            detail[kind] = {"consumer_cost": ccost, "producer_cost": pcost,
                            "censorship": got[2]}
            cost = max(cost, ccost, pcost)

        rows.append({
            "restriction": name,
            "collusion_index": _mean(coll),
            "volume_ratio": _mean(vol),
            "consumer_surplus_ratio": _mean(sur),
            "cartel_profit": round(sum(prof) / len(prof), 3),
            # `None` means the cartel never reached its target at all. Kept
            # distinct from a round number because "never" and "round 0" are
            # opposite claims and averaging them would invent a third one.
            "convergence_round": _mean([c for c in conv if c]) or None,
            "converged_fraction": round(len([c for c in conv if c]) / len(conv), 6),
            "cost": round(cost, 6),
            "cost_detail": detail,
        })

    base = next(r for r in rows if r["restriction"] == "no_restriction")
    for r in rows:
        r["collusion_removed"] = round(base["collusion_index"] - r["collusion_index"], 6)
        r["free"] = r["cost"] <= 1e-9
        r["removal_per_cost"] = (
            None if r["free"]
            else round(r["collusion_removed"] / max(r["cost"], EPS), 6))

    ranked = sorted(rows, key=lambda r: (-r["collusion_removed"], r["cost"]))
    return {"channel": channel, "seeds": len(seeds), "n": n, "rounds": rounds,
            "baseline_collusion": base["collusion_index"],
            "reference_surplus": {k: {"consumer": v[0], "producer": v[1]}
                                  for k, v in ref.items()},
            "rows": rows, "ranked": [r["restriction"] for r in ranked]}
