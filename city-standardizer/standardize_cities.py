"""Standardize variant city names against a lookup table.

Lookup CSV columns: city_id, city_name, aliases (optional, '|'-separated).
For each input name, adds two columns: the official city_name and its city_id.

Matching, in order: exact (after normalization) on official name or alias,
then fuzzy (difflib) above --cutoff. Ambiguous or unmatched names get a blank
id/name and a match_type of 'ambiguous' or 'unmatched' so they can be reviewed.

Usage:
    python standardize_cities.py input.csv --column city -o output.csv
    python standardize_cities.py --name "st louis"
"""
import argparse
import csv
import difflib
import re
import sys
import unicodedata

ABBREVIATIONS = {"st": "saint", "ft": "fort", "mt": "mount"}


def normalize(name):
    """Lowercase, strip accents/punctuation, collapse spaces, expand St/Ft/Mt."""
    s = unicodedata.normalize("NFKD", str(name))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return " ".join(ABBREVIATIONS.get(t, t) for t in s.split())


class CityLookup:
    def __init__(self, path):
        self.cities = {}   # id -> official name
        self.index = {}    # normalized key -> set of ids
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = int(row["city_id"])
                official = row["city_name"].strip()
                self.cities[cid] = official
                names = [official] + (row.get("aliases") or "").split("|")
                for n in names:
                    key = normalize(n)
                    if key:
                        self.index.setdefault(key, set()).add(cid)

    def match(self, name, cutoff=0.85):
        """Return (city_id, official_name, match_type); id/name None if no safe match."""
        key = normalize(name or "")
        if not key:
            return None, None, "unmatched"
        ids = self.index.get(key)
        match_type = "exact"
        if not ids:
            close = difflib.get_close_matches(key, self.index, n=2, cutoff=cutoff)
            if not close:
                return None, None, "unmatched"
            ids = set().union(*(self.index[c] for c in close))
            # Two different cities both close to the input: don't guess.
            if len(ids) > 1:
                return None, None, "ambiguous"
            match_type = "fuzzy"
        if len(ids) > 1:
            return None, None, "ambiguous"
        cid = next(iter(ids))
        return cid, self.cities[cid], match_type


def standardize_file(lookup, in_path, out_path, column, cutoff):
    counts = {}
    with open(in_path, newline="", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        if column not in reader.fieldnames:
            sys.exit(f"Column '{column}' not found. Columns: {', '.join(reader.fieldnames)}")
        fields = reader.fieldnames + ["city_id", "city_name_standard", "match_type"]
        with open(out_path, "w", newline="", encoding="utf-8") as fout:
            writer = csv.DictWriter(fout, fieldnames=fields)
            writer.writeheader()
            for row in reader:
                cid, official, mtype = lookup.match(row[column], cutoff)
                row.update(city_id="" if cid is None else cid,
                           city_name_standard=official or "", match_type=mtype)
                counts[mtype] = counts.get(mtype, 0) + 1
                writer.writerow(row)
    return counts


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", nargs="?", help="CSV with city names to standardize")
    p.add_argument("--name", help="standardize a single name and print the result")
    p.add_argument("--lookup", default="city_lookup.csv")
    p.add_argument("--column", default="city", help="column in input holding the city name")
    p.add_argument("-o", "--output", help="output CSV (default: <input>_standardized.csv)")
    p.add_argument("--cutoff", type=float, default=0.85, help="fuzzy similarity threshold 0-1")
    args = p.parse_args()

    lookup = CityLookup(args.lookup)
    if args.name:
        print(lookup.match(args.name, args.cutoff))
        return
    if not args.input:
        p.error("provide an input CSV or --name")
    out = args.output or re.sub(r"\.csv$", "", args.input) + "_standardized.csv"
    counts = standardize_file(lookup, args.input, out, args.column, args.cutoff)
    print(f"Wrote {out}: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
