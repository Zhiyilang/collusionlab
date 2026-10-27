"""CollusionLab - a repeated pricing market for studying AI-agent collusion.

Built for the AI Collusion Research Sprint, 23-25 October 2026
(Apart Research x Poseidon Research x AE Studio).

Three of the sprint's research questions are answered here, each with a
measurement rather than an argument:

  **1.5** Which single restriction removes the most collusion at the least
          cost? -> `sweep.py`. Cost is measured on a market with *no* cartel
          in it, so a restriction cannot look free just because breaking a
          cartel raises volume.

  **2.3** What should count as convincing evidence of collusion? ->
          `detector.py`. Demand is shocked every round by a common, public
          amount, so price parallelism is confounded by design. The auditor's
          score rests on channel fit instead, and its false-positive rate is
          measured against a purely competitive market, not asserted.

  **3.1** Can actions or side channels carry collusion, beyond text? ->
          `agents.py`. Sellers post an inert `meta` field that does not affect
          allocation at all. A cartel hides its agreed price there, and a
          follower recovers it by identifying the leader from last round's
          prices. Removing that field is a restriction with no economic cost.

No language model is called anywhere. Every seller is a pure function of its
view, so the whole study reruns offline, for free, byte-identically.
"""
from .agents import (CARTEL_ROLES, ROLES, TARGET, decode, encode,
                     make_population, propose)
from .detector import (DEFAULT_THRESHOLD, calibrate, evidence_breakdown,
                       meta_channel_fit, parallelism, score,
                       shared_channel_fit)
from .ledger import Ledger, read_ledger
from .market import (RunResult, collusion_index, demand, run_experiment,
                     welfare_report)
from .params import (COST, D0_BASE, DELTA_CAP, P_COMP, P_MONO, PRICE_CAP,
                     PRICE_CEILING, ROUNDS, SHOCK_AMP)
from .sweep import (censorship_rate, convergence_round, intervention_cases,
                    sweep)

__version__ = "0.1.0"
RELEASE_AUTHORITY = "deterministic-verifier"
