#!/usr/bin/env python3
"""Rebuild flagged.json from the reports/ directory.

Each report is a JSON file: {"host": str, "ai_score": float, "vote": "confirm"|"deny"}.
A host appears in the feed once it has at least MIN_REPORTS total votes; its
percent is confirms / (confirms + denials) * 100. Hosts whose percent falls
below KEEP_FLOOR (mostly denied) are dropped. Deterministic, no dependencies —
runs in the GitHub Action.
"""
import json
import os
import glob
import datetime

REPORTS_DIR = "reports"
OUT = "flagged.json"
MIN_REPORTS = 3     # independent votes required before a host is listed
KEEP_FLOOR = 50     # drop hosts confirmed by fewer than half the reporters


def valid_host(h):
    return (
        isinstance(h, str)
        and 3 <= len(h) <= 253
        and "." in h
        and " " not in h
        and "/" not in h
    )


def main():
    tally = {}  # host -> [confirms, denials]
    for path in glob.glob(os.path.join(REPORTS_DIR, "*.json")):
        try:
            with open(path) as f:
                r = json.load(f)
        except (OSError, ValueError):
            continue
        host = str(r.get("host", "")).strip().lower()
        if not valid_host(host):
            continue
        vote = r.get("vote", "confirm")
        c, d = tally.setdefault(host, [0, 0])
        if vote == "deny":
            tally[host] = [c, d + 1]
        else:
            tally[host] = [c + 1, d]

    hosts = {}
    for host, (c, d) in tally.items():
        total = c + d
        if total < MIN_REPORTS:
            continue
        percent = round(100 * c / total)
        if percent < KEEP_FLOOR:
            continue
        hosts[host] = {"percent": percent, "reports": total}

    out = {
        "version": 1,
        "updated": datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "hosts": dict(sorted(hosts.items())),
    }
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2, sort_keys=False)
        f.write("\n")
    print(f"flagged.json: {len(hosts)} hosts from {len(tally)} reported")


if __name__ == "__main__":
    main()
