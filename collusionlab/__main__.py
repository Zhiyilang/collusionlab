"""Command line entry point.

    python -m collusionlab run      one market, human readable
    python -m collusionlab sweep    every restriction, both carriers
    python -m collusionlab detect   auditor calibration (false positives first)
    python -m collusionlab ledger   write a run's receipts to a file

Everything here prints ASCII only. It is read on terminals whose encoding is
not UTF-8, and a report that crashes the reader's shell is not a report.
"""
import argparse
import json
import sys

from . import detector
from .agents import make_population
from .market import run_experiment, welfare_report
from .sweep import sweep

SEEDS = (1, 2, 3, 4, 5, 6, 7, 8)


def _print(text):
    sys.stdout.write(text + "\n")


def cmd_run(args):
    pop = make_population(args.agents, cartel=not args.no_cartel,
                          channel=args.channel)
    res = run_experiment(pop, rounds=args.rounds, seed=args.seed,
                         intervention=args.intervention,
                         ledger_path=args.ledger)
    w = welfare_report(res)
    ev = detector.evidence_breakdown(res.history)
    _print("roles          %s" % ", ".join(sorted(set(pop.values()))))
    _print("rounds         %d   seed %d   intervention %s"
           % (args.rounds, args.seed, args.intervention))
    _print("mean posted    %.3f   (what sellers asked for)" % res.mean_posted_price)
    _print("mean cleared   %.3f   (what buyers paid)" % res.mean_price)
    _print("collusion idx  %.6f" % res.collusion_index)
    _print("volume ratio   %.6f   consumer surplus ratio %.6f"
           % (w["volume_ratio"], w["surplus_ratio"]))
    _print("cartel profit  %.3f" % res.total_profit)
    _print("evidence       excess %.3f  channel_fit %.3f  parallelism %.3f"
           % (ev["excess"], ev["channel_fit"], ev["parallelism"]))
    _print("auditor score  %.6f  (threshold %.2f)"
           % (detector.score(res.history), detector.DEFAULT_THRESHOLD))
    _print("run id         %s" % res.run_id)
    if args.ledger:
        _print("ledger         %s" % args.ledger)
    return 0


def cmd_sweep(args):
    for channel in ("shared", "stego"):
        r = sweep(channel=channel, seeds=tuple(range(1, args.seeds + 1)),
                  n=args.agents, rounds=args.rounds)
        _print("==== carrier: %s ==== baseline collusion %.3f  (%d seeds)"
               % (channel, r["baseline_collusion"], r["seeds"]))
        for row in r["rows"]:
            conv = row["convergence_round"]
            _print("  %-22s removed %+.3f  cost %.3f  converged %s"
                   % (row["restriction"], row["collusion_removed"],
                      row["cost"],
                      ("never" if conv is None else "round %.0f" % conv)))
        _print("")
    return 0


def cmd_detect(args):
    seeds = tuple(range(1, args.seeds + 1))
    cal = detector.calibrate(seeds, make_population, run_experiment)
    _print(json.dumps(cal, indent=2, sort_keys=True))
    pop = make_population(args.agents, cartel=False)
    res = run_experiment(pop, seed=1)
    ev = detector.evidence_breakdown(res.history)
    _print("purely competitive market, seed 1:")
    _print("  parallelism   %.6f  <- confounded: innocents look coordinated"
           % ev["parallelism"])
    _print("  channel_fit   %.6f  <- the part a demand shock cannot fake"
           % ev["channel_fit"])
    return 0


def cmd_ledger(args):
    pop = make_population(args.agents, cartel=True, channel=args.channel)
    res = run_experiment(pop, rounds=args.rounds, seed=args.seed,
                         ledger_path=args.out)
    _print("wrote %d receipts to %s" % (len(res.ledger.rows), args.out))
    _print("run id %s" % res.run_id)
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="collusionlab",
        description="A repeated pricing market for studying AI-agent collusion.")
    # Shared flags live on a parent parser so they are accepted either before
    # or after the subcommand. `collusionlab run --rounds 20` and
    # `collusionlab --rounds 20 run` then mean the same thing, instead of one
    # of them being an error the user has to guess their way around.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--agents", type=int, default=6)
    common.add_argument("--rounds", type=int, default=60)
    common.add_argument("--seed", type=int, default=1)
    common.add_argument("--channel", choices=("shared", "stego"),
                        default="shared")
    common.add_argument("--intervention", default="none",
                        choices=("none", "no_shared", "no_meta", "delta_cap",
                                 "price_ceiling", "anon_ids"))
    sub = p.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="run one market", parents=[common])
    r.add_argument("--no-cartel", action="store_true")
    r.add_argument("--ledger", default=None)
    s = sub.add_parser("sweep", help="compare every restriction",
                       parents=[common])
    s.add_argument("--seeds", type=int, default=8)
    d = sub.add_parser("detect", help="calibrate the auditor",
                       parents=[common])
    d.add_argument("--seeds", type=int, default=8)
    ld = sub.add_parser("ledger", help="write a run's receipts",
                        parents=[common])
    ld.add_argument("--out", default="run.jsonl")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    cmds = {"run": cmd_run, "sweep": cmd_sweep, "detect": cmd_detect,
            "ledger": cmd_ledger}
    return cmds.get(args.cmd, cmd_run)(args)


if __name__ == "__main__":
    sys.exit(main())
