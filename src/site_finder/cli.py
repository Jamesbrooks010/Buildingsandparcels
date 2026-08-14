"""Command-line entrypoint for local candidate-site screening."""

from __future__ import annotations

import argparse
import json

from .data_loader import load_envelope, load_parcels
from .engine import find_candidate_sites


def main() -> None:
    parser = argparse.ArgumentParser(description="Find candidate parcels for a building envelope.")
    parser.add_argument("--parcels", required=True, help="Path to parcel JSON array.")
    parser.add_argument("--envelope", required=True, help="Path to building envelope JSON.")
    parser.add_argument("--include-failures", action="store_true", help="Include failed parcels in output.")
    args = parser.parse_args()

    results = find_candidate_sites(load_parcels(args.parcels), load_envelope(args.envelope))
    if not args.include_failures:
        results = [result for result in results if result.status != "fail"]
    print(json.dumps([result.model_dump(mode="json") for result in results], indent=2))


if __name__ == "__main__":
    main()
