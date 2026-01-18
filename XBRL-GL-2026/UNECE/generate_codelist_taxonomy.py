#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_codelist_taxonomy.py

Generate an XBRL code list taxonomy (aligned pool) from a CSV list:
- XSD (concepts + roleType + linkbaseRef)
- definition linkbase (domain-member: domain head -> all members)
- label linkbase (label + documentation, any language)
- review CSV (code, QName, name, description)

Optionally generate one or more selection profiles (subsets) that reuse the SAME domain head (A pattern):
- sel/<selectionCode>/<...>.xsd
- sel/<selectionCode>/<...>-def.xml
"""

from __future__ import annotations

import argparse
import csv
import os
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple


# ----------------------------
# Utilities
# ----------------------------

NCNAME_RE = re.compile(r"[^A-Za-z0-9_.-]")

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&apos;"))

def sanitise_code_for_ncname(code: str) -> str:
    """
    Convert a code value to something safe for an XML NCName *suffix*.
    We still prefix with "_" so it is always a valid element name.
    Example: "AA" -> "AA", "9" -> "_9", "A/B" -> "A_B"
    """
    c = code.strip()
    c = NCNAME_RE.sub("_", c)
    if c[0].isdigit():
        c = "_" + c
    # Avoid empty
    return c if c else "UNKNOWN"

def member_local_name(code: str) -> str:
    """
    Member element local name convention: _<code> (underscore + code),
    keeping it close to raw codes while ensuring NCName rules.
    """
    return sanitise_code_for_ncname(code)

# def default_domain_head(num: str) -> str:
#     # Neutral default; you can override with --domain-head
#     return "codeDomain"

# def role_slug_default(title: str) -> str:
#     slug = title.strip().lower()
#     slug = re.sub(r"[^a-z0-9]+", "-", slug)
#     slug = slug.strip("-")
#     return slug or "code-list"

def LC3(term):
    """
    Lower camel case converter (e.g., 'Entity Phone Number' → 'entityPhoneNumber')
    """
    parts = re.split(r'\s+', term.strip())
    return parts[0].lower() + ''.join(p.title() for p in parts[1:])


# ----------------------------
# Readers
# ----------------------------

@dataclass
class CodeItem:
    code: str
    name: str
    description: str
    local: str  # element local name, e.g. _380

def read_codes(csv_path: str,
               code_col: str,
               name_col: str,
               desc_col: str) -> List[CodeItem]:
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in (code_col, name_col, desc_col) if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}. Found: {reader.fieldnames}")

        items: List[CodeItem] = []
        for row in reader:
            code = (row.get(code_col) or "").strip()
            if not code:
                continue
            name = (row.get(name_col) or "").strip()
            desc = (row.get(desc_col) or "").strip()
            items.append(CodeItem(code=code, name=name, description=desc, local=member_local_name(code)))
        return items


def read_selection_codes(path: str) -> List[str]:
    """
    Reads selection codes from:
    - a text file: one code per line
    - or a CSV with a 'code' column (auto-detected)
    """
    # If CSV-like, try DictReader
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        if "," in sample or "\t" in sample:
            try:
                reader = csv.DictReader(f)
                if reader.fieldnames and "code" in [h.strip().lower() for h in reader.fieldnames]:
                    # find actual header name matching "code"
                    header_map = {h.strip().lower(): h for h in reader.fieldnames}
                    code_h = header_map["code"]
                    codes = []
                    for row in reader:
                        c = (row.get(code_h) or "").strip()
                        if c:
                            codes.append(c)
                    return codes
            except Exception:
                pass

        # Fallback: plain lines
        f.seek(0)
        codes = []
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            codes.append(ln)
        return codes


# ----------------------------
# Writers
# ----------------------------

def write_aligned_pool(
    out_dir: str,
    num: str,
    release: str,
    ns: str,
    prefix: str,
    title: str,
    domain_head: str,
    role_slug: str,
    xsd_name: str,
    def_name: str,
    lab_name: str,
    lang: str,
    items: List[CodeItem],
) -> None:
    
    ensure_dir(out_dir)

    # XSD
    role_uri = f"{ns}/role/{role_slug}"
    role_id = f'role_{role_slug.replace("-","_")}'
    xsd_lines: List[str] = []
    xsd_lines.append( '<?xml version="1.0" encoding="UTF-8"?>')
    xsd_lines.append( '<xs:schema')
    xsd_lines.append( '  xmlns:xs="http://www.w3.org/2001/XMLSchema" ')
    xsd_lines.append( '  xmlns:xbrli="http://www.xbrl.org/2003/instance"')
    xsd_lines.append( '  xmlns:link="http://www.xbrl.org/2003/linkbase"')
    xsd_lines.append( '  xmlns:xlink="http://www.w3.org/1999/xlink" ')
    xsd_lines.append(f'  xmlns:{prefix}="{ns}"')
    xsd_lines.append(f'  targetNamespace="{ns}"')
    xsd_lines.append(f'  elementFormDefault="qualified" attributeFormDefault="unqualified">')
    xsd_lines.append("")
    xsd_lines.append( '  <xs:import namespace="http://www.xbrl.org/2003/instance" schemaLocation="http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd"/>')
    xsd_lines.append( '  <xs:import namespace="http://www.xbrl.org/2003/linkbase" schemaLocation="http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"/>')
    xsd_lines.append( '  <xs:annotation>')
    xsd_lines.append( '    <xs:appinfo>')
    xsd_lines.append(f'      <!-- UNTDID {num}: {xml_escape(title)} (release {release}) aligned pool -->')
    xsd_lines.append(f'      <!-- Member naming convention: _<code> (QName {prefix}:_<code> etc.) -->')
    xsd_lines.append( '      <!-- linkbase -->')
    xsd_lines.append(f'      <link:linkbaseRef xlink:type="simple" xlink:href="{def_name}" ')
    xsd_lines.append( '                        xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase"/>')
    xsd_lines.append(f'      <link:linkbaseRef xlink:type="simple" xlink:href="{lab_name}" ')
    xsd_lines.append( '                        xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase"/>')
    xsd_lines.append( '      <!-- ELR -->')
    xsd_lines.append(f'      <link:roleType roleURI="{role_uri}" id="{role_id}">')
    xsd_lines.append(f'        <link:definition>{xml_escape(title)} (UNTDID {num}, {release})</link:definition>')
    xsd_lines.append( '        <link:usedOn>link:definitionLink</link:usedOn>')
    xsd_lines.append( '        <link:usedOn>link:labelLink</link:usedOn>')
    xsd_lines.append( '      </link:roleType>')
    xsd_lines.append( '    </xs:appinfo>')
    xsd_lines.append( '  </xs:annotation>')
    xsd_lines.append("")
    xsd_lines.append( '  <!-- Domain head (abstract) -->')
    xsd_lines.append(f'  <xs:element name="{domain_head}" id="{domain_head}" abstract="true"')
    xsd_lines.append( '    substitutionGroup="xbrli:item" type="xbrli:stringItemType" xbrli:periodType="instant"/>')
    xsd_lines.append( "")
    xsd_lines.append( "  <!-- Members (all codes) -->")
    for it in items:
        xsd_lines.append(f'  <xs:element name="{it.local}" id="{it.local}" substitutionGroup="xbrli:item"')
        xsd_lines.append( '              type="xbrli:stringItemType" xbrli:periodType="instant"/>')
    xsd_lines.append("")
    xsd_lines.append("</xs:schema>")

    file = os.path.join(out_dir, xsd_name).replace(os.sep,'/')
    with open(file, "w", encoding="utf-8") as f:
        f.write("\n".join(xsd_lines))
    print(f"Aligned pool xsd written to: {file}")

    # Definition linkbase (domain-member)
    def_lines: List[str] = []
    def_lines.append( '<?xml version="1.0" encoding="UTF-8"?>')
    def_lines.append( '<link:linkbase')
    def_lines.append( '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
    def_lines.append( '  xmlns:link="http://www.xbrl.org/2003/linkbase"')
    def_lines.append( '  xmlns:xlink="http://www.w3.org/1999/xlink"')
    def_lines.append( '  xsi:schemaLocation="http://www.xbrl.org/2003/linkbase')
    def_lines.append( '                      http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd">')
    def_lines.append( '  <!-- ELR -->')
    def_lines.append(f'  <link:roleRef roleURI="{role_uri}" xlink:type="simple"')
    def_lines.append(f'                xlink:href="{xsd_name}#{role_id}"/>')
    def_lines.append( '  <!-- EE1 -->')
    def_lines.append( '  <link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/domain-member" xlink:type="simple"')
    def_lines.append( '                   xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#domain-member"/>')
    def_lines.append("")
    def_lines.append(f'  <link:definitionLink xlink:type="extended" xlink:role="{role_uri}">')
    def_lines.append(f'    <link:loc xlink:type="locator" xlink:href="{xsd_name}#{domain_head}" xlink:label="dom"/>')
    # locators
    for idx, it in enumerate(items, start=1):
        c = sanitise_code_for_ncname(it.code)
        def_lines.append(f'    <link:loc xlink:type="locator" xlink:href="{xsd_name}#{it.local}" xlink:label="{c}"/>')
    def_lines.append("")
    # arcs
    for idx, it in enumerate(items, start=1):
        c = sanitise_code_for_ncname(it.code)
        def_lines.append( '    <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member"')
        def_lines.append(f'                        xlink:from="dom" xlink:to="{c}" order="{idx}"/>')
    def_lines.append("  </link:definitionLink>")
    def_lines.append("")
    def_lines.append("</link:linkbase>")

    file = os.path.join(out_dir, def_name).replace(os.sep,'/')
    with open(file, "w", encoding="utf-8") as f:
        f.write("\n".join(def_lines))
    print(f"Aligned pool def written to: {file}")

    # Label linkbase
    lab_lines: List[str] = []
    lab_lines.append( '<?xml version="1.0" encoding="UTF-8"?>')
    lab_lines.append( '<link:linkbase')
    lab_lines.append( '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
    lab_lines.append( '  xmlns:link="http://www.xbrl.org/2003/linkbase"')
    lab_lines.append( '  xmlns:xlink="http://www.w3.org/1999/xlink"')
    lab_lines.append( '  xsi:schemaLocation="http://www.xbrl.org/2003/linkbase')
    lab_lines.append( '                      http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd">')
    lab_lines.append( '  <!-- ELR -->')
    lab_lines.append(f'  <link:roleRef roleURI="{role_uri}" xlink:type="simple"')
    lab_lines.append(f'                xlink:href="{xsd_name}#{role_id}"/>')
    lab_lines.append( '')
    lab_lines.append( '  <link:labelLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">')
    lab_lines.append(f'    <link:loc xlink:type="locator" xlink:href="{xsd_name}#{domain_head}" xlink:label="dom"/>')
    lab_lines.append(f'    <link:label xlink:type="resource" xlink:label="lab_dom"')
    lab_lines.append(f'                xlink:role="http://www.xbrl.org/2003/role/label" xml:lang="{lang}">{xml_escape(title)}</link:label>')
    lab_lines.append( '    <link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="dom" xlink:to="lab_dom"/>')
    lab_lines.append( "")

    for idx, it in enumerate(items, start=1):
        loc = f"_{idx}"
        lab = f"lab{it.local}"
        doc = f"doc{it.local}"
        label_text = f"{it.code} {it.name}".strip()
        lab_lines.append(f'    <link:loc xlink:type="locator" xlink:href="{xsd_name}#{it.local}" xlink:label="{loc}"/>')
        lab_lines.append(f'    <link:label xlink:type="resource" xlink:label="{lab}" xlink:role="http://www.xbrl.org/2003/role/label" xml:lang="{lang}">{xml_escape(label_text)}</link:label>')
        lab_lines.append(f'    <link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="{loc}" xlink:to="{lab}"/>')
        if it.description:
            lab_lines.append(f'    <link:label xlink:type="resource" xlink:label="{doc}" xlink:role="http://www.xbrl.org/2003/role/documentation" xml:lang="{lang}">{xml_escape(it.description)}</link:label>')
            lab_lines.append(f'    <link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="{loc}" xlink:to="{doc}"/>')
        lab_lines.append("")
    lab_lines.append("  </link:labelLink>")
    lab_lines.append("")
    lab_lines.append("</link:linkbase>")

    file = os.path.join(out_dir, lab_name).replace(os.sep,'/')
    with open(file, "w", encoding="utf-8") as f:
        f.write("\n".join(lab_lines))
    print(f"Aligned pool lab written to: {file}")

    # Review CSV
    review_path = os.path.join(out_dir, f"untdid{num}-{release}.csv")
    with open(review_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code", "qname", "name", "description"])
        for it in items:
            w.writerow([it.code, f"{prefix}:{it.local}", it.name, it.description])


def write_shared(
    shared_dir: str,
    num: str,
    release: str,
    base_ns: str,
    base_xsd: str,
    prefix_base: str,
    shared_ns:str,
    shared_xsd: str,
    prefix_shared: str,
    domain_head: str,
    selection_code: str,
    role_slug: str,
    allowed_codes: List[str],
) -> Tuple[str, str]:
    """
    Selection profile uses SAME domain head concept from base taxonomy (A pattern).
    Generates:
    - untdid<num>-<selection_code>.xsd (defines roleType and linkbaseRef; imports base)
    - untdid<num>-<selection_code>-def.xml (domain-member arcs from base domain head -> selected members)
    Returns (selection_role_uri, selection_def_filename).
    """
    ensure_dir(shared_dir)

    # shared_ns = f"{shared_ns}/{selection_code}"
    shared_role_uri = f"{shared_ns}/role/{role_slug}"
    shared_role_id = f'role_shared_{selection_code.replace("-","_")}'
    xsd_name = f"{selection_code}-{release}-shr.xsd"
    def_name = f"{selection_code}-{release}-shr-def.xml"
    # XSD
    xsd: List[str] = []
    xsd.append( '<?xml version="1.0" encoding="UTF-8"?>')
    xsd.append( '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"')
    xsd.append( '  xmlns:link="http://www.xbrl.org/2003/linkbase"')
    xsd.append( '  xmlns:xlink="http://www.w3.org/1999/xlink"')
    xsd.append(f'  xmlns:{prefix_base}="{base_ns}"')
    xsd.append(f'  xmlns:{prefix_shared}="{shared_ns}"')
    xsd.append(f'  targetNamespace="{shared_ns}"')
    xsd.append( '  elementFormDefault="qualified" attributeFormDefault="unqualified">')
    # xsd.append(f'  <xs:include schemaLocation="{base_xsd}"/>')
    xsd.append(f'  <xs:import namespace="{base_ns}"')
    xsd.append(f'             schemaLocation="{base_xsd}"/>')
    xsd.append( '  <xs:annotation>')
    xsd.append( '    <xs:appinfo>')
    xsd.append(f'      <!-- Selection profile for UNTDID {num} ({release}): {selection_code} -->')
    xsd.append(f'      <!-- Reuses base domain head: {prefix_base}:{domain_head} -->')
    xsd.append( "      <!-- Linkbase -->")
    xsd.append(f'      <link:linkbaseRef xlink:href="{def_name}" xlink:type="simple"')
    xsd.append( '                        xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase"/>')
    xsd.append( "      <!-- ELR -->")
    xsd.append(f'      <link:roleType roleURI="{shared_role_uri}"')
    xsd.append(f'                     id="{shared_role_id}">')
    xsd.append(f'        <link:definition>UNTDID {num} selection: {selection_code}</link:definition>')
    xsd.append( '         <link:usedOn>link:definitionLink</link:usedOn>')
    xsd.append( '      </link:roleType>')
    xsd.append( '    </xs:appinfo>')
    xsd.append( '  </xs:annotation>')
    xsd.append( "</xs:schema>")

    file = os.path.join(shared_dir, xsd_name).replace(os.sep,'/')
    with open(file, "w", encoding="utf-8") as f:
        f.write("\n".join(xsd))
    print(f"Shared xsd written to: {file}")

    # Definition linkbase (same domain head, selection ELR)
    # Note: member IDs are in base schema: #_<code_sanitised>
    codes = [c.strip() for c in allowed_codes if c.strip()]
    defl: List[str] = []
    defl.append( '<?xml version="1.0" encoding="UTF-8"?>')
    defl.append( '<link:linkbase')
    defl.append( '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
    defl.append( '  xmlns:link="http://www.xbrl.org/2003/linkbase"')
    defl.append( '  xmlns:xlink="http://www.w3.org/1999/xlink"')
    defl.append( '  xsi:schemaLocation="http://www.xbrl.org/2003/linkbase')
    defl.append( '                      http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd">')
    defl.append( '  <!-- ELR -->')
    defl.append(f'  <link:roleRef roleURI="{shared_role_uri}" xlink:type="simple"')
    defl.append(f'                xlink:href="{shared_xsd}#{shared_role_id}"/>')
    defl.append( '  <!-- EE1 -->')
    defl.append( '  <link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/domain-member" xlink:type="simple"')
    defl.append( '                   xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#domain-member"/>')
    defl.append( "")
    defl.append(f'  <link:definitionLink xlink:type="extended" xlink:role="{shared_role_uri}">')
    defl.append(f'    <link:loc xlink:type="locator" xlink:href="{base_xsd}#{domain_head}" xlink:label="dom"/>')

    # locators
    for i, c in enumerate(codes, start=1):
        local = member_local_name(c)
        defl.append(f'    <link:loc xlink:type="locator" xlink:href="{base_xsd}#{local}" xlink:label="{c}"/>')
    defl.append("")
    # arcs
    for i, c in enumerate(codes, start=1):
        defl.append( '    <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member"')
        defl.append(f'                        xlink:from="dom" xlink:to="{c}" order="{i}"/>')

    defl.append("  </link:definitionLink>")
    defl.append("")
    defl.append("</link:linkbase>")

    file = os.path.join(shared_dir, def_name).replace(os.sep,'/')
    with open(file, "w", encoding="utf-8") as f:
        f.write("\n".join(defl))
    print(f"Shared def written to: {file}")

    return shared_role_uri, def_name


# ----------------------------
# Main
# ----------------------------

def main() -> None:
    PARSE = False
    if PARSE:
        ap = argparse.ArgumentParser(description="Generate XBRL code list taxonomy from CSV")
        ap.add_argument("--csv", required=True, help="Input CSV with columns for code,name,description")
        ap.add_argument("--out", required=True, help="Output directory root (e.g., XBRL-GL-2026/TEST/gl/gen/pool)")
        ap.add_argument("--num", required=True, help="UNTDID element number (e.g., 1001, 1225)")
        ap.add_argument("--release", default="d24a", help="Release tag used in filenames (default: d24a)")
        ap.add_argument("--ns", default=None, help="Namespace URI (default: http://www.xbrl.org/int/gl/2026-12-31/gen/pool/uncl_<num>)")
        ap.add_argument("--title", required=True, help="Human title for the list, e.g. 'Document name code'")
        ap.add_argument("--lang", default="en", help="Label language (default: en)")

        ap.add_argument("--code-col", default="code", help="CSV column name for code (default: code)")
        ap.add_argument("--name-col", default="name", help="CSV column name for name (default: name)")
        ap.add_argument("--desc-col", default="description", help="CSV column name for description (default: description)")

        ap.add_argument("--shared_root", default="XBRL-GL-2026/TEST/gl/gen/shared", help="Root directory for selection definition")
        # selections: repeatable
        ap.add_argument("--selection",
                        help="Selection definition: selectionCode=path_to_codes_file (txt or CSV with code column). "
                             "Example: --selection invoice-basic=invoice-basic-codes.txt")

        args = ap.parse_args()

        csv = args.csv.strip()
        out = args.out.strip()
        num = args.num.strip()
        release = args.release.strip().lower()
        title = args.title.strip()

        code_col = args.code_col.strip()
        name_col = args.name_col.strip()
        desc_col = args.desc_col.strip()

        lang = args.lang.strip()

        shared_root = args.shared_root.strip()
        if args.selection:
            selection = args.selection.strip()
        else:
            selection = None
    else:
        lang = "en"
        num = "5305" # "1001"
        release = "d23a"
        csv = f"XBRL-GL-2026/TEST/gl/gen/pool/untdid{num}-{release}.csv"
        out = "XBRL-GL-2026/TEST/gl/gen/pool"
        title = "Duty or tax or fee category code" # "Document name code"
        code_col = "code"
        name_col = "name"
        desc_col = "description"
        shared_root = "XBRL-GL-2026/TEST/gl/gen/shared"
        prefix = f"uncl_{num}"
        selection = f"{prefix}={shared_root}/{prefix}-{release}.txt"

    # Aligned pool location
    out_dir = os.path.join(out, prefix).replace(os.sep,'/')
    ensure_dir(out_dir)

    xsd_name = f"{prefix}-{release}.xsd"
    def_name = f"{prefix}-{release}-def.xml"
    lab_name = f"{prefix}-{release}-lab.xml"

    prefix = f"uncl_{num}"
    ns = f"http://www.xbrl.org/int/gl/2026-12-31/gen/{prefix}"
    shared_ns = f"http://www.xbrl.org/int/gl/2026-12-31/gen/shared/{prefix}"
    terms = title.split(" ")
    role_slug = "-".join([x[0].lower() + x[1:] for x in terms]) # "document-name-code"
    domain_head = f'{LC3(title)}Domain' # "documentNameCodeDomain"

    items = read_codes(csv, code_col, name_col, desc_col)

    write_aligned_pool(
        out_dir=out_dir,
        num=num,
        release=release,
        ns=ns,
        prefix=prefix,
        title=title,
        domain_head=domain_head,
        role_slug=role_slug,
        xsd_name=xsd_name,
        def_name=def_name,
        lab_name=lab_name,
        lang=lang,
        items=items,
    )

    # Selections (A pattern: same domain head; different ELR)
    if selection:
        ensure_dir(shared_root)

        if "=" not in selection:
            raise ValueError(f"Invalid --selection value: {selection}. Use selectionCode=path")
        sel_code, sel_path = selection.split("=", 1)
        sel_code = sel_code.strip()
        sel_path = sel_path.strip()
        allowed_codes = read_selection_codes(sel_path)

        shared_dir = os.path.join(shared_root, sel_code).replace(os.sep,'/')
        # Pool XSD relative path from shared dir
        base_xsd = os.path.relpath(os.path.join(out_dir, xsd_name), shared_dir).replace(os.sep, "/")

        write_shared(
            shared_dir=shared_dir,
            num=num,
            release=release,
            base_ns=ns,
            base_xsd=base_xsd,
            prefix_base=prefix,
            shared_ns=shared_ns,
            shared_xsd=xsd_name,
            prefix_shared=f"{prefix}_s",
            domain_head=domain_head,
            selection_code=sel_code,
            role_slug=role_slug,
            allowed_codes=allowed_codes,
        )

    print("Done.")

    print(f"Aligned pool written to: {out_dir.replace(os.sep,'/')}")
    role_uri = f"{ns}/role/{role_slug}"
    print(f"Base ELR: {role_uri}")

    if selection:
        print(f"Selections written under: {shared_dir.replace(os.sep,'/')}")

if __name__ == "__main__":
    main()
