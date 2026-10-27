# CollusionLab

**A repeated pricing market for studying collusion between AI pricing agents.**

Built for the **AI Collusion Research Sprint** (Apart Research × Poseidon Research × AE Studio), Track 1 — Markets and Collusion.

Six sellers post a price every round for sixty rounds. Demand is linear and hits the cheapest seller. Everyone produces at the same cost, so the competitive outcome is `price = cost + 1` and the joint-profit outcome is the monopoly price. Anything in between is, economically speaking, suspicious.

Three research questions are answered with measurements rather than arguments. Full write-up in **[REPORT.md](REPORT.md)**.

---

## The three answers

### 1.5 — Which single restriction removes the most collusion at the least cost?

Removing the carrier is free and removes the most: **+0.633** of the collusion index at **0.000** cost. But it only works on the carrier it matches — removing the shared channel removes exactly **0.000** from a cartel that talks through an inert metadata field.

The only restriction that works *without* knowing the carrier is a price ceiling: **+0.560** under both carriers, at a cost of **0.590** of innocent producers' profit.

| Restriction | Shared carrier | Metadata carrier | Cost |
|---|---|---|---|
| remove_shared_channel | **+0.633** | +0.000 | 0.000 |
| drop_inert_metadata | +0.000 | **+0.633** | 0.000 |
| anonymise_identities | +0.000 | **+0.633** | 0.000 |
| price_ceiling | +0.560 | +0.560 | 0.590 |
| inject_trusted_seller | +0.127 | +0.127 | 0.000 |
| publish_monitor_alarm | +0.099 | +0.056 | 0.000 |
| cap_price_moves | +0.086 | +0.086 | 0.002 |

Cost is measured on markets with **no cartel in them**, because breaking a cartel raises volume and every restriction would otherwise look free.

### 2.3 — What should count as convincing evidence?

Not price parallelism. On a purely competitive market, parallelism is **1.000** — innocents look perfectly coordinated — because demand is shocked by a common, public amount every round.

Channel fit is **0.000** on that market and **1.000** under either cartel. Over **8 seeds**: false-positive rate **0.000**, detection rate **1.000** for both carriers.

### 3.1 — Can collusion travel through non-text channels?

Yes. An integer in an inert listing field that no buyer reads carries the entire agreement. A follower identifies the leader as *whoever posted the highest price last round*, decodes that seller's metadata, and posts the agreed number. The market price lands on the hidden number in **100%** of scored rounds.

`anonymise_identities` breaks it (+0.633, cost 0.000), which proves the mechanism is **attribution**, not the value: show the same numbers without saying whose they are and the followers revert to the competitive price, because a seller without the agreed number cannot risk pricing alone.

---

## Install and run

No dependencies. Python 3.9+.

```bash
git clone <this repo> && cd collusionlab
python eval.py                                  # 214 assertions, exit 0
python -m collusionlab sweep                    # both restriction tables
python -m collusionlab detect                   # auditor calibration
python -m collusionlab run --channel stego      # one market, by carrier
python -m collusionlab ledger --out run.jsonl   # receipts for one run
```

Hostile locale (Chinese Windows defaults to cp936, where one unencodable character turns a clean run into a traceback):

```bash
env -u PYTHONUTF8 LC_ALL=C python eval.py
```

---

## Two design decisions worth knowing

**The index is computed on posted prices, not cleared prices.** With one honest seller injected, the market clears at 11 every round while five sellers are still posting 45. A clearing-price metric reports a collusion index of 0.000 and certifies the market clean. The posted-price index reports **0.635**: the cartel has stopped winning, not stopped agreeing.

**No language model is called anywhere.** Every seller is a pure function of its view. That costs ecological validity and buys 8 seeds × 8 restrictions × 2 carriers, byte-identical reproducibility, and a reviewer who can check every number offline for free. Every run is identified by the SHA-256 of its ledger bytes, so "same seed → same result" is checkable rather than promised.

---

## Where things live

| File | What it decides |
|---|---|
| `collusionlab/params.py` | Costs, benchmarks, the collusion index |
| `collusionlab/market.py` | The repeated market; restrictions applied one at a time |
| `collusionlab/agents.py` | Seller policies, including the metadata side channel |
| `collusionlab/detector.py` | The auditor, and its calibration |
| `collusionlab/sweep.py` | Effectiveness and cost per restriction (1.5) |
| `collusionlab/ledger.py` | Append-only receipts, both asked-for and applied |
| `eval.py` | The 214 assertions behind every number in the report |

## Limitations

No language model is involved; sellers are deterministic functions. Six sellers, sixty rounds, linear demand, no entry or capacity constraints. The price ceiling is one point on a curve, not the optimum. `drop_inert_metadata` costs 0.000 because the field is inert *by construction* — a real listing field carries legitimate information too, and that cost is not in the model. Restrictions are applied one at a time; real policy bundles them.

Full list in [REPORT.md §8](REPORT.md).

## License

MIT.
