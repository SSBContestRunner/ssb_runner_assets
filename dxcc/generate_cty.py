"""Inject <ituz> into the bundled cty.xml.gz from the AD1C cty.dat.

Source of ITU zones: https://www.country-files.com/cty/cty.dat
cty.dat encodes, per entity, `Name: CQ: ITU: Cont: Lat: Lon: TZ: Prefix:` and a
comma separated prefix list where a token may carry overrides:
  prefix            -> entity CQ/ITU defaults
  prefix(CQ)        -> CQ override
  prefix[ITU]       -> ITU override
  prefix(CQ)[ITU]   -> both
  =CALL(CQ)[ITU]    -> exact callsign override
Only <ituz> is added; <cqz>/<cont>/<adif> are left untouched.
"""

import gzip
import re
import shutil
import sys
import xml.etree.ElementTree as ET

CTY = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cty.dat"
SRC = sys.argv[2] if len(sys.argv) > 2 else "/tmp/cty.src.xml.gz"
DST = sys.argv[3] if len(sys.argv) > 3 else "/tmp/cty.xml.gz"

TOKEN_RE = re.compile(r"^([=*]?)(.+?)(?:\((\d+)\))?(?:\[(\d+)\])?$")


def parse_cty(path):
    table = {}  # lower prefix -> itu
    exact = {}  # lower exact call -> itu
    cur_itu = None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            if not line[0].isspace():
                parts = line.split(":")
                if len(parts) < 8:
                    continue
                cur_itu = int(parts[2].strip())
                prim = parts[-2].strip()
                if prim:
                    table.setdefault(prim.lower(), cur_itu)
                continue
            for tok in line.strip().rstrip(";").split(","):
                tok = tok.strip()
                if not tok:
                    continue
                m = TOKEN_RE.match(tok)
                if not m:
                    continue
                marker, name, _cq, itu = m.groups()
                value = int(itu) if itu else cur_itu
                if marker == "=":
                    exact[name.lower()] = value
                else:
                    table[name.lower()] = value
    return table, exact


def resolve(table, exact, call):
    c = call.lower()
    if c in exact:
        return exact[c], "exact"
    p = c
    while p:
        if p in table:
            return table[p], "prefix" if p == c else "fallback"
        p = p[:-1]
    return None, "none"


def main():
    table, exact = parse_cty(CTY)
    print(f"cty.dat: prefixes={len(table)} exact_calls={len(exact)}")

    with gzip.open(SRC, "rb") as fh:
        tree = ET.parse(fh)
    root = tree.getroot()
    prefixes = root.find("prefixes")
    if prefixes is None:
        raise SystemExit("no <prefixes> in source XML")

    stats = {"exact": 0, "prefix": 0, "fallback": 0, "none": 0}
    samples = []
    records = list(prefixes)
    for rec in records:
        call_el = rec.find("call")
        call = (call_el.text or "").strip() if call_el is not None else ""
        if not call:
            continue
        # keep the element order stable: insert <ituz> right after <cqz>
        existing = rec.find("ituz")
        if existing is not None:
            rec.remove(existing)
        itu, how = resolve(table, exact, call)
        stats[how] += 1
        if itu is None:
            continue
        el = ET.Element("ituz")
        el.text = str(itu)
        idx = 1
        for i, child in enumerate(list(rec)):
            if child.tag == "cqz":
                idx = i + 1
                break
        rec.insert(idx, el)
        if len(samples) < 8 or call.upper().startswith(("BI", "W9", "VE3", "JA1")):
            samples.append((call, itu, how))

    with open(DST, "wb") as raw:
        with gzip.GzipFile(
            fileobj=raw, mode="wb", compresslevel=9, mtime=0
        ) as fh:
            tree.write(fh, encoding="utf-8")

    print(f"records={len(records)} stats={stats}")
    for s in samples[:20]:
        print("  ", s)


main()