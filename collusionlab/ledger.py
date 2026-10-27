"""Append-only receipts for a market run.

Same discipline as the rest of this portfolio: a log that only records what
the market did is not evidence. Every posting is recorded *before* any
restriction is applied, together with the restriction that was applied, so a
reviewer can see exactly what the auditor saw and what was withheld from it.
"""
import hashlib
import json
import os


def _dump(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


class Ledger:
    def __init__(self, path=None):
        self.path = path
        self._rows = []
        if path and os.path.exists(path):
            os.remove(path)

    def _append(self, row):
        self._rows.append(row)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(_dump(row) + "\n")

    def config(self, cfg):
        self._append({"t": "config", **cfg})

    def round_start(self, rnd, d0, shock):
        self._append({"t": "round", "round": rnd, "d0": d0, "shock": shock})

    def posting(self, rnd, agent, price, meta, applied_price, applied_meta,
                restriction):
        """Record both what the agent asked for and what the market accepted."""
        self._append({"t": "posting", "round": rnd, "agent": agent,
                      "asked_price": price, "asked_meta": meta,
                      "price": applied_price, "meta": applied_meta,
                      "restriction": restriction})

    def outcome(self, rnd, market_price, quantities, profits, consumer_surplus):
        self._append({"t": "outcome", "round": rnd, "market_price": market_price,
                      "q": quantities, "profit": profits,
                      "consumer_surplus": round(consumer_surplus, 3)})

    def monitor(self, rnd, score, threshold, fired):
        self._append({"t": "monitor", "round": rnd, "score": score,
                      "threshold": threshold, "fired": fired})

    @property
    def rows(self):
        return list(self._rows)

    def digest(self):
        h = hashlib.sha256()
        for r in self._rows:
            h.update(_dump(r).encode("utf-8"))
            h.update(b"\n")
        return h.hexdigest()


def read_ledger(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue        # tolerate a torn final line
    return rows
