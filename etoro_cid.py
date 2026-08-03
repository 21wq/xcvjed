#!/usr/bin/env python3
"""Resolve an eToro customer id (cid) to the account's public username.

eToro's public profile URLs are keyed by username, not by cid, so a cid on its
own cannot be searched for. The public JSON endpoints below are keyed by cid,
which makes them the practical way to go from a numeric id back to a name.

Standard library only -- no dependencies.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field

# Keyed by cid. Primary source: the public portfolio payload.
PORTFOLIO_URL = (
    "https://www.etoro.com/sapi/trade-data-real/live/public/portfolios"
    "?format=json&cid={cid}"
)
# Fallback: the rankings payload, which carries the username more reliably
# because it is what powers the "popular investor" listings.
RANKINGS_URL = "https://www.etoro.com/sapi/rankings/cid/{cid}/rankings/?Period=OneYearAgo"

SOURCES = (("portfolios", PORTFOLIO_URL), ("rankings", RANKINGS_URL))

# eToro's edge rejects the default urllib user agent outright.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class Result:
    cid: int
    username: str | None = None
    source: str | None = None
    payload: object | None = None
    notes: list[str] = field(default_factory=list)


def find_usernames(payload: object) -> list[str]:
    """Collect every non-empty string stored under a *username*-ish key.

    The shape of these payloads is undocumented and changes over time, so match
    on the key name anywhere in the tree rather than a fixed path.
    """
    found: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, str) and value and "username" in key.lower():
                    found.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return list(dict.fromkeys(found))


def fetch_json(url: str, timeout: float) -> object:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def lookup(cid: int, timeout: float = 15.0) -> Result:
    """Try each public endpoint in turn until one yields a username."""
    result = Result(cid=cid)

    for label, template in SOURCES:
        try:
            payload = fetch_json(template.format(cid=cid), timeout)
        except urllib.error.HTTPError as exc:
            hint = " (rate limited or bot-blocked)" if exc.code in (403, 429) else ""
            result.notes.append(f"{label}: HTTP {exc.code}{hint}")
            continue
        except urllib.error.URLError as exc:
            result.notes.append(f"{label}: network error: {exc.reason}")
            continue
        except json.JSONDecodeError:
            result.notes.append(f"{label}: response was not JSON")
            continue

        if result.payload is None:
            result.payload = payload
            result.source = label

        names = find_usernames(payload)
        if names:
            result.username = names[0]
            result.source = label
            result.payload = payload
            if len(names) > 1:
                result.notes.append(f"{label}: other names present: {', '.join(names[1:])}")
            return result

        result.notes.append(f"{label}: no username field in response")

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve an eToro cid (customer id) to its public username."
    )
    parser.add_argument("cid", type=int, nargs="+", help="one or more numeric cids")
    parser.add_argument(
        "--raw", action="store_true", help="print the full JSON payload instead of a summary"
    )
    parser.add_argument("--timeout", type=float, default=15.0, help="per-request timeout, seconds")
    args = parser.parse_args(argv)

    exit_code = 0
    for cid in args.cid:
        result = lookup(cid, args.timeout)

        if args.raw:
            json.dump(result.payload, sys.stdout, indent=2, ensure_ascii=False)
            print()
        elif result.username:
            print(f"{cid}: {result.username}  (via {result.source})")
            print(f"  https://www.etoro.com/people/{result.username.lower()}")
        else:
            print(f"{cid}: username not found", file=sys.stderr)
            exit_code = 1

        for note in result.notes:
            print(f"  note: {note}", file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
