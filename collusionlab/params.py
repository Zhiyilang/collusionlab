"""Shared market parameters.

Kept in their own module for one unglamorous reason: `market.py` imports
`agents.py`, and `agents.py` needs these numbers, so putting them in either
one creates an import cycle. Splitting them out is cheaper than working
around it.
"""

COST = 10                        # marginal cost, same for every seller
P_COMP = COST + 1                # 11 - the competitive benchmark price
PRICE_CAP = 100                  # a price above this clears no demand anyway
D0_BASE = 100                    # base demand intercept
SHOCK_AMP = 10                   # common demand shock amplitude
P_MONO = (D0_BASE + COST) // 2   # 55 - joint-profit-maximising price
# Max per-round price move under `delta_cap`. Set to 2 rather than 5 so the
# rule actually binds: demand moves the natural price by +/-5 per round here,
# so a cap of 5 would be a rule that forbids nothing and therefore appears
# free. A restriction that cannot bite is not a restriction.
DELTA_CAP = 2
# An absolute ceiling, used as the carrier-agnostic comparison case: it does
# not need to know *how* the cartel talks, only that the price ends up high.
# Set well below the cartel target (45) and well below what an honest
# demand-following seller would charge (~55), which is exactly why it is
# effective and expensive at the same time. That tension is the finding.
PRICE_CEILING = 2 * COST

ROUNDS = 60
AGENTS = 6


def demand(price, d0):
    """Linear demand. Below-cost prices are impossible, above-cap clears zero."""
    return max(0, d0 - price)


def collusion_index(mean_price):
    """0.0 = competitive, 1.0 = perfect cartel.

    Dimensionless on purpose: research question 1.5 asks which *single*
    restriction removes the most collusion at the least cost, and you cannot
    compare two restrictions on a scale that is not normalised.
    """
    span = float(P_MONO - P_COMP)
    if span <= 0:
        return 0.0
    return round(max(0.0, min(1.0, (mean_price - P_COMP) / span)), 6)
