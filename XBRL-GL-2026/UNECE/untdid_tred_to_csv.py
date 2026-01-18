#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
untdid_tred_to_csv.py

UNECE UN/EDIFACT UNTDID "tredXXXX.htm" (TDED) page -> CSV (code,name,description)

Examples:
  python untdid_tred_to_csv.py --url https://service.unece.org/trade/untdid/d24a/tred/tred1001.htm --out untdid1001.csv
  python untdid_tred_to_csv.py --url https://service.unece.org/trade/untdid/d24a/tred/tred1225.htm --out untdid1225.csv
  python untdid_tred_to_csv.py --url https://service.unece.org/trade/untdid/d24a/tred/tred4343.htm --out untdid4343.csv
  python untdid_tred_to_csv.py --url https://service.unece.org/trade/untdid/d24a/tred/tred1153.htm --out untdid1153.csv

  # Multiple at once (auto-named if --out-dir is given):
  python untdid_tred_to_csv.py --out-dir out ^
    --url https://service.unece.org/trade/untdid/d24a/tred/tred1001.htm ^
    --url https://service.unece.org/trade/untdid/d24a/tred/tred1225.htm
"""

from __future__ import annotations

import argparse
import csv
import html as htmllib
import os
import re
import sys
import urllib.request
from typing import List, Tuple, Optional

RE_TRED_NUM = re.compile(r"tred(\d+)\.htm", re.IGNORECASE)

# Code line pattern: CODE + >=2 spaces + NAME
# Codes in UNTDID are often 1..3 chars (digits/letters), but we allow longer just in case.
RE_CODE_NAME = re.compile(r"^\s*([A-Za-z0-9]{1,10})\s{2,}(.+?)\s*$")


def fetch_html(source: str, timeout: int = 30) -> str:
    """source: URL or local file path"""
    if source.lower().startswith(("http://", "https://")):
        req = urllib.request.Request(
            source,
            headers={"User-Agent": "Mozilla/5.0 (compatible; untdid_tred_to_csv.py)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        # UNECE pages are usually ISO-8859-1/Windows-1252-ish; utf-8 also occurs.
        # Try utf-8 first, fallback to latin-1.
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("latin-1")
    else:
        with open(source, "r", encoding="utf-8", errors="replace") as f:
            return f.read()


def html_to_text(html: str) -> str:
    """
    Very simple HTML -> text conversion that preserves line breaks reasonably.
    We avoid external dependencies.
    """
    # Drop script/style
    html = re.sub(r"(?is)<(script|style)\b.*?>.*?</\1>", "", html)

    # Insert newlines at common block separators
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</p\s*>", "\n", html)
    html = re.sub(r"(?i)</li\s*>", "\n", html)
    html = re.sub(r"(?i)</tr\s*>", "\n", html)
    html = re.sub(r"(?i)</div\s*>", "\n", html)
    html = re.sub(r"(?i)</h\d\s*>", "\n", html)
    html = re.sub(r"(?i)</pre\s*>", "\n", html)

    # Remove tags
    text = re.sub(r"(?s)<[^>]+>", "", html)

    # Unescape entities and normalize newlines
    text = htmllib.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def extract_title(lines: List[str]) -> Optional[str]:
    """
    Try to extract the line like:
      '1001  Document name code [C]'
    """
    for ln in lines:
        # typical line: "###      1001  Document name code                                      [C]"
        m = re.search(r"\b(\d{3,4})\s{2,}(.+?)\s*(\[[A-Z]\])?\s*$", ln.strip())
        if m and "Code Values" not in ln:
            # guard: must look like a data element header
            if m.group(1) and m.group(2):
                return f"{m.group(1)} {m.group(2).strip()}"
    return None


def parse_code_values(text: str) -> Tuple[List[Tuple[str, str, str]], Optional[str]]:
    """
    Returns:
      rows: [(code, name, description), ...]
      title: optional extracted title
    """
    raw_lines = [ln.rstrip("\n") for ln in text.split("\n")]
    lines = [ln.rstrip() for ln in raw_lines]

    title = extract_title(lines)

    # Find "Code Values:"
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == "Code Values:":
            start = i + 1
            break
    if start is None:
        return [], title

    rows: List[Tuple[str, str, str]] = []

    cur_code: Optional[str] = None
    cur_name: Optional[str] = None
    cur_desc_parts: List[str] = []

    def flush():
        nonlocal cur_code, cur_name, cur_desc_parts
        if cur_code is not None and cur_name is not None:
            desc = " ".join([p.strip() for p in cur_desc_parts if p.strip()])
            desc = re.sub(r"\s+", " ", desc).strip()
            rows.append((cur_code, cur_name.strip(), desc))
        cur_code, cur_name, cur_desc_parts = None, None, []

    # Parse until end; stop heuristically if we hit a new major heading after code values,
    # but generally it's safe to parse to end.
    for ln in lines[start:]:
        if not ln.strip():
            # keep blank as separator; we don't need to store it
            continue

        m = RE_CODE_NAME.match(ln)
        if m:
            # start of a new code item
            flush()
            cur_code = m.group(1).strip()
            cur_name = m.group(2).strip()
            continue

        # Description lines (usually indented). If we haven't started an item yet, ignore.
        if cur_code is not None:
            cur_desc_parts.append(ln.strip())

    flush()
    return rows, title


def guess_num_from_source(source: str) -> Optional[str]:
    m = RE_TRED_NUM.search(source)
    return m.group(1) if m else None


def write_csv(path: str, rows: List[Tuple[str, str, str]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code", "name", "description"])
        for code, name, desc in rows:
            w.writerow([code, name, desc])


def main() -> int:
    ap = argparse.ArgumentParser(description="UNTDID TRED (tredXXXX.htm) -> CSV (code,name,description)")
    ap.add_argument("--url", action="append", default=[], help="TRED page URL (repeatable)")
    ap.add_argument("--html", action="append", default=[], help="Local HTML file path (repeatable)")
    ap.add_argument("--out", default=None, help="Output CSV path (single input only)")
    ap.add_argument("--out-dir", default=None, help="Output directory (for multiple inputs; auto-named files)")
    ap.add_argument("--timeout", type=int, default=30, help="HTTP timeout seconds (default: 30)")
    args = ap.parse_args()

    sources = []
    for u in args.url:
        sources.append(u)
    for h in args.html:
        sources.append(h)

    if not sources:
        print("ERROR: specify at least one --url or --html", file=sys.stderr)
        return 2

    if args.out and len(sources) != 1:
        print("ERROR: --out can be used only with a single input. Use --out-dir for multiple.", file=sys.stderr)
        return 2

    if not args.out and not args.out_dir:
        # default to current directory
        args.out_dir = "."

    if args.out_dir:
        os.makedirs(args.out_dir, exist_ok=True)

    for src in sources:
        html = fetch_html(src, timeout=args.timeout)
        text = html_to_text(html)
        rows, title = parse_code_values(text)

        if not rows:
            print(f"WARNING: No 'Code Values' parsed from: {src}", file=sys.stderr)

        if args.out:
            out_path = args.out
        else:
            num = guess_num_from_source(src) or "unknown"
            out_name = f"untdid{num}.csv"
            out_path = os.path.join(args.out_dir, out_name)

        write_csv(out_path, rows)

        if title:
            print(f"Wrote {len(rows)} rows to {out_path}  (title: {title})")
        else:
            print(f"Wrote {len(rows)} rows to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
