"""Small CLI. No command grants live agent authority."""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from .core_bridge import CoreBridge
from .doctor import inspect_versions
from .jsonutil import atomic_write, canonical
from .sources import OfficialGitHubClient, SourceUnavailable
from .watch import BaselineRequired, WatchStore


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="h360")
    commands = parser.add_subparsers(dest="command", required=True)
    watch = commands.add_parser("crewai-watch", help="Official releases/advisories; silent when unchanged")
    watch.add_argument("--state", type=Path, default=Path(".h360/crewai-watch.sqlite3"))
    watch.add_argument("--baseline", action="store_true", help="Record the currently reviewed sources without alerts (one time)")
    watch.add_argument("--output", type=Path, help="Write alerts atomically before acknowledging them")
    commands.add_parser("doctor", help="Inventory installed versions against one advisory's patch floors")
    demo = commands.add_parser("core-demo", help="Call actual Harmony360 mathematics and its native codec locally")
    demo.add_argument("--values", type=float, nargs="+", default=[1.0, 2.0, 3.0])
    demo.add_argument("--output", type=Path, default=Path("runtime-output/core-demo.har360"))
    args = parser.parse_args(argv)
    store = None
    try:
        if args.command == "doctor":
            print(canonical(inspect_versions()))
        elif args.command == "core-demo":
            core = CoreBridge()
            payload = {"schema": "harmony360.core-demo.v0.1", "state": "UNDER_REVIEW",
                       "canonical_authority_granted": False, "diagnostics": core.analyze(args.values)}
            checksum = core.seal(payload, args.output)
            if core.reconstruct(args.output, expected_sha256=checksum) != payload:
                raise ValueError("Fresh carrier reconstruction mismatch")
            print(canonical({"path": str(args.output), "sha256": checksum, "reconstruction": "PASS",
                             "core_calls": payload["diagnostics"]["core_calls"]}))
        else:
            if args.output:
                # Remove a previous run's alert artifact before a new attempt; pending rows remain in SQLite.
                if args.output.resolve() == args.state.resolve():
                    raise ValueError("Output must differ from the state database")
                args.output.unlink(missing_ok=True)
            snapshot = OfficialGitHubClient().fetch()
            store = WatchStore(args.state)
            pending = store.stage(snapshot, baseline=args.baseline)
            if args.baseline:
                print(canonical({"baseline_recorded_at": snapshot.checked_at,
                                 "releases": len(snapshot.releases), "advisories": len(snapshot.advisories),
                                 "alerts": 0}))
            elif pending:
                raw = (canonical({"alerts": pending}) + "\n").encode("utf-8")
                if args.output:
                    atomic_write(args.output, raw)
                else:
                    sys.stdout.write(raw.decode("utf-8"))
                    sys.stdout.flush()
                store.acknowledge([row["alert_id"] for row in pending])
            # A normal unchanged check deliberately produces no stdout or alert file.
        return 0
    except (SourceUnavailable, BaselineRequired, RuntimeError, ValueError, OSError, sqlite3.Error) as exc:
        print(f"h360: {exc}", file=sys.stderr)
        return 2
    finally:
        if store:
            store.close()


if __name__ == "__main__":
    raise SystemExit(main())

