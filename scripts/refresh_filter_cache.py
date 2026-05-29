"""Refresh the cached filter dropdown data from pokemontcg.io.

Usage:
    python -m scripts.refresh_filter_cache
"""
from api import (
    get_sets,
    get_rarities,
    get_subtypes,
    get_supertypes,
    get_types,
)
import db

FILTERS = {
    "sets": get_sets,
    "types": get_types,
    "subtypes": get_subtypes,
    "supertypes": get_supertypes,
    "rarities": get_rarities,
}

def main():
    for key, fetch_fn in FILTERS.items():
        value = fetch_fn()
        db.set_filter_cache(key, value)
        print(f"Cached {len(value)} {key}")

if __name__ == "__main__":
    main()
