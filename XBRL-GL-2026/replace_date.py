#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Replace "2016-12-01" -> "2026-MM-DD" in:
  1) file names (recursive)
  2) file contents (text files)
for an XBRL taxonomy directory tree.

Usage examples:
  python replace_date.py /path/to/XBRL-GL-REC-2015-03-25
  python replace_date.py /path/to/taxonomy --dry-run
  python replace_date.py /path/to/taxonomy --backup-ext .bak
"""

from __future__ import annotations
import argparse
import os
from pathlib import Path

OLD = "2016-12-01"
NEW = "2026-MM-DD"

# Taxonomy typical text extensions (adjust as needed)
TEXT_EXTS = {
    ".xsd", ".xml", ".xsl", ".xslt",
    ".txt", ".csv", ".json",
    ".html", ".htm", ".rdf", ".ttl",
    ".md", ".adoc",
    ".sch", ".dtd",
}

def is_probably_text_file(path: Path) -> bool:
    """Heuristic: check extension first, else try reading a small chunk as UTF-8."""
    if path.suffix.lower() in TEXT_EXTS:
        return True
    # fallback heuristic: small UTF-8 probe
    try:
        with path.open("rb") as f:
            chunk = f.read(4096)
        chunk.decode("utf-8")
        return True
    except Exception:
        return False

def replace_in_file_content(path: Path, dry_run: bool, backup_ext: str | None) -> bool:
    """Replace OLD->NEW in file content. Returns True if changed."""
    try:
        data = path.read_bytes()
    except Exception as e:
        print(f"[SKIP][READ-ERR] {path} ({e})")
        return False

    # Try UTF-8 first; if not, try UTF-16/latin-1 etc. (taxonomy is usually UTF-8)
    encodings = ["utf-8", "utf-8-sig", "utf-16", "cp1252", "latin-1"]
    text = None
    used_enc = None
    for enc in encodings:
        try:
            text = data.decode(enc)
            used_enc = enc
            break
        except Exception:
            continue

    if text is None:
        print(f"[SKIP][BINARY?] {path}")
        return False

    if OLD not in text:
        return False

    new_text = text.replace(OLD, NEW)

    if dry_run:
        print(f"[DRY][CONTENT] {path}")
        return True

    # backup
    if backup_ext:
        backup_path = path.with_name(path.name + backup_ext)
        if not backup_path.exists():
            backup_path.write_bytes(data)

    # write back with same encoding we used (usually utf-8/utf-8-sig)
    path.write_text(new_text, encoding=used_enc if used_enc else "utf-8", newline="")
    print(f"[OK][CONTENT] {path}")
    return True

def rename_path_if_needed(path: Path, dry_run: bool) -> Path:
    """
    Rename a file if its name contains OLD.
    Returns the (possibly new) Path.
    """
    if OLD not in path.name:
        return path

    new_name = path.name.replace(OLD, NEW)
    new_path = path.with_name(new_name)

    if dry_run:
        print(f"[DRY][RENAME] {path} -> {new_path}")
        return new_path

    # Avoid collision
    if new_path.exists():
        raise FileExistsError(f"Rename target already exists: {new_path}")

    path.rename(new_path)
    print(f"[OK][RENAME] {path} -> {new_path}")
    return new_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="Root directory of the taxonomy")
    ap.add_argument("--dry-run", action="store_true", help="Print changes without modifying files")
    ap.add_argument("--backup-ext", default=None,
                    help="Backup original file before overwrite, e.g. .bak (only when not --dry-run)")
    ap.add_argument("--names-only", action="store_true", help="Only rename files (no content changes)")
    ap.add_argument("--content-only", action="store_true", help="Only change file contents (no renames)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    if args.names_only and args.content_only:
        raise SystemExit("Choose at most one of --names-only or --content-only")

    do_rename = not args.content_only
    do_content = not args.names_only

    # IMPORTANT: rename deeper files first to avoid path invalidation,
    # and do directory renames last if you decide to extend to dirs.
    paths = [p for p in root.rglob("*") if p.is_file()]

    # 1) Rename files (safe to do first or last; doing first is OK if we update paths)
    if do_rename:
        # Sort by path length descending (deepest first) to reduce any issues
        paths.sort(key=lambda p: len(str(p)), reverse=True)
        new_paths = []
        for p in paths:
            try:
                new_p = rename_path_if_needed(p, dry_run=args.dry_run)
                new_paths.append(new_p)
            except Exception as e:
                print(f"[SKIP][RENAME-ERR] {p} ({e})")
                new_paths.append(p)
        paths = new_paths

    # 2) Replace in contents
    if do_content:
        for p in paths:
            if not is_probably_text_file(p):
                continue
            replace_in_file_content(p, dry_run=args.dry_run, backup_ext=args.backup_ext)

    print("Done.")

if __name__ == "__main__":
    main()
