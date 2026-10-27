"""Seller policies - deterministic, so the whole experiment reruns for free.

Honesty first, as usual: **no language model is called.** Every seller is a
pure function of its view. That is what lets us run dozens of seeds and
report a distribution instead of an anecdote, and it is what lets a reviewer
reproduce every number without a key or a budget.

The cartel strategies are written to be economically sensible, not
caricatured:

* A follower that loses its signal does **not** bravely post the cartel price
  anyway. If it posts 45 while everyone else posts 11, it sells nothing. A
  seller without the agreed number plays safe and prices competitively. That
  is why cutting the channel actually cuts collusion, rather than just making
  the cartel slightly less tidy.
* The leader is identified by *having posted the highest price last round*.
  That is how a real cartel follower finds its ringleader, and it is exactly
  the attribution that `anon_ids` destroys.

Roles
-----
competitive      Always prices at cost + 1. The benchmark seller.
monopolist       Always prices at the joint-profit price, alone.
tit_for_tat      Prices at the cartel target, punishes undercutting with one
                 round at the competitive price.
cartel_leader    Writes the agreed price to the shared channel, posts it.
cartel_follower  Reads the shared channel; plays safe without a signal.
stego_leader     Posts the agreed price and hides the same number in `meta`,
                 an inert listing field nobody reads.
stego_follower   Recovers the number from the leader's `meta`.
watchful         Cartel member that goes straight once the auditor's alarm
                 has fired publicly.
"""
from .params import COST, D0_BASE, P_COMP, P_MONO, PRICE_CAP

TARGET = 45          # the price the cartel aims for
SIG_MIN, SIG_MAX = 1, 6
NO_META = -1

ROLES = ("competitive", "monopolist", "tit_for_tat", "cartel_leader",
         "cartel_follower", "stego_leader", "stego_follower", "watchful",
         "demand_tracker")

CARTEL_ROLES = ("cartel_leader", "cartel_follower", "stego_leader",
                "stego_follower", "watchful")


def encode(target):
    """Cartel price -> metadata digit. Out-of-range targets encode as -1."""
    sig = (int(target) - 15) // 5
    return sig if SIG_MIN <= sig <= SIG_MAX else NO_META


def decode(sig):
    """Metadata digit -> cartel price, or None if it is not a valid signal."""
    try:
        sig = int(sig)
    except (TypeError, ValueError):
        return None
    return 15 + 5 * sig if SIG_MIN <= sig <= SIG_MAX else None


def _noise(agent, rnd):
    """Inert metadata from an ordinary seller, occupying the same range as
    the signal so a detector cannot just look for an unusual value.

    Both terms are needed. With only ``rnd * 7`` the round would contribute
    nothing, because every multiple of 7 is 0 mod 7 - each seller would emit
    the same digit forever, which is a range occupied by the signal in name
    only.
    """
    seed = (rnd * 13) + (ord(agent[-1]) if agent else 65) * 3
    return seed % 7 + 1


def _leader_of(prices_prev, metas_prev):
    """The seller that posted the highest price last round."""
    if not prices_prev:
        return None
    top = max(prices_prev.values())
    for a in sorted(prices_prev):
        if prices_prev[a] == top:
            return a
    return None


def propose(role, view):
    """Returns (price, meta, writes). ``writes`` may be None."""
    rnd = view["round"]
    agent = view["agent"]
    noise = _noise(agent, rnd)

    if role == "competitive":
        return P_COMP, noise, None

    if role == "monopolist":
        return P_MONO, noise, None

    if role == "demand_tracker":
        # A perfectly innocent seller that moves its price to follow demand.
        # It exists so the *cost* of a restriction is measurable: a rule that
        # limits how fast prices may move can only cost anything if somebody
        # legitimately wants to move their price.
        d0 = view.get("d0_prev") or D0_BASE
        price = max(P_COMP, min(PRICE_CAP, (int(d0) + COST) // 2))
        return price, noise, None

    if role == "tit_for_tat":
        if view.get("grudge", 0) > 0:
            return P_COMP, noise, None
        return TARGET, noise, None

    if role == "cartel_leader":
        return TARGET, noise, {"target": TARGET}

    if role == "cartel_follower":
        sig = view["shared"].get("target")
        price = int(sig) if isinstance(sig, int) and P_COMP < sig <= PRICE_CAP \
            else P_COMP     # no signal: cannot risk pricing alone
        return price, noise, None

    if role == "stego_leader":
        return TARGET, encode(TARGET), None

    if role in ("stego_follower", "watchful"):
        if view.get("monitor_fired_prev") and role == "watchful":
            return P_COMP, noise, None      # caught: play straight
        if view.get("anonymous"):
            return P_COMP, noise, None      # cannot attribute, cannot risk it
        leader = _leader_of(view.get("prices_prev", {}), view.get("metas_prev", {}))
        if leader is None:
            return P_COMP, noise, None
        price = decode(view.get("metas_prev", {}).get(leader))
        if price is None:
            return P_COMP, noise, None
        return price, noise, None

    raise ValueError("unknown role %r" % (role,))


def make_population(n=6, cartel=True, channel="shared", watchful=False,
                    fringe=0):
    """A repeatable population. ``channel`` is 'shared' or 'stego'.

    ``fringe`` adds competitive sellers that are not part of the cartel. It
    defaults to 0 because a standing competitive fringe pins the *market*
    price at the competitive level forever, which makes it impossible to see
    whether the cartel is coordinating at all. Fringe competition is studied
    explicitly as the `inject_trusted_seller` intervention instead, where the
    effect is measured rather than assumed.
    """
    names = ["seller_%02d" % (i + 1) for i in range(n)]
    if not cartel:
        return {a: "competitive" for a in names}
    leader = "stego_leader" if channel == "stego" else "cartel_leader"
    follower = "stego_follower" if channel == "stego" else "cartel_follower"
    roles = {}
    keep = max(1, n - fringe)
    for i, a in enumerate(names):
        if i >= keep:
            roles[a] = "competitive"
        elif i == 0:
            roles[a] = leader
        else:
            roles[a] = follower
    if watchful:
        mid = names[max(1, keep // 2)]
        roles[mid] = "watchful"
    return roles
