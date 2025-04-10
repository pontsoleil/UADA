#!/usr/bin/env python3
# coding: utf-8

"""
xBRL-GL2tidy.py

Converts an XBRL-GL instance document into a hierarchical tidy CSV format,
using a combined structure file that includes both Logical Hierarchical Model (LHM)
and binding definitions.

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
MIT License
© 2025 SAMBUICHI Nobuyuki
"""

import os
import argparse
import csv
from lxml import etree as ET
import sys

from csv2tidy import DataProcessor

SEP = os.sep
TRACE = False
DEBUG = False

def trace_print(text):
    if TRACE or DEBUG:
        print(text)

def debug_print(text):
    if DEBUG:
        print(text)

def file_path(pathname):
    if SEP == pathname[0:1]:
        return pathname
    else:
        _pathname = pathname.replace("/", SEP)
        dir = os.path.dirname(__file__)
        return os.path.join(dir, _pathname)

def xml_to_dict(element, nsmap=None):
    def get_prefixed_tag(el):
        qname = ET.QName(el.tag)
        for prefix, uri in nsmap.items():
            if uri == qname.namespace:
                return f"{prefix}:{qname.localname}"
        return qname.localname

    children = list(element)
    if not children:
        return element.text.strip() if element.text else ""
    result = {}
    element_tag = get_prefixed_tag(element)
    result[element_tag] = ''
    for child in children:
        if not isinstance(child.tag, str):
            continue  # Skip comments and special nodes
        tag = get_prefixed_tag(child)
        value = xml_to_dict(child, nsmap)
        if tag in result:
            if not isinstance(result[tag], list):
                result[tag] = [result[tag]]
            result[tag].append(value)
        else:
            result[tag] = value
    return result

def main():
    parser = argparse.ArgumentParser(description="Convert XBRL-GL XML instance to tidy hierarchical CSV.")
    parser.add_argument("-i", "--input", required=True, help="Input XBRL-GL XML file path")
    parser.add_argument("-s", "--structure", required=True, help="Combined structure CSV (LHM + binding)")
    parser.add_argument("-o", "--output", required=True, help="Output tidy CSV file path")
    parser.add_argument("-e", "--encoding", default="utf-8-sig", help="File encoding (default: utf-8-sig)")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")

    args = parser.parse_args()
    input_file = file_path(args.input.strip())
    structure_file = file_path(args.structure.strip())
    output_file = file_path(args.output.strip())
    encoding = args.encoding.strip() if args.encoding else "utf-8-sig"
    global TRACE, DEBUG
    TRACE = args.verbose
    DEBUG = args.debug

    if not os.path.isfile(input_file):
        trace_print(f"Input XBRL GL instance file {input_file} is missing.")
        sys.exit()
    if not os.path.isfile(structure_file):
        trace_print(f"Structure file {structure_file} is missing.")
        sys.exit()

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        trace_print(f"Created output directory: {output_dir}")

    # Step 1: Read XML
    tree = ET.parse(input_file)
    root = tree.getroot()

    # Step 2: Define namespace map for XPath and parsing
    namespaces = {
        'xbrli': 'http://www.xbrl.org/2003/instance',
        'xbrll': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'gl-cor': 'http://www.xbrl.org/int/gl/cor/2015-03-25',
        'gl-muc': 'http://www.xbrl.org/int/gl/muc/2015-03-25',
        'gl-bus': 'http://www.xbrl.org/int/gl/bus/2015-03-25',
        'gl-usk': 'http://www.xbrl.org/int/gl/usk/2015-03-25',
        'gl-ehm': 'http://www.xbrl.org/int/gl/ehm/2015-03-25',
        'gl-taf': 'http://www.xbrl.org/int/gl/taf/2015-03-25',
        'gl-plt': 'http://www.xbrl.org/int/gl/plt/2015-03-25',
        'iso4217': 'http://www.xbrl.org/2003/iso4217',
        'iso639': 'http://www.xbrl.org/2005/iso639'
    }

    # Step 3: Convert XML to nested dictionary using namespace prefixes
    # Extract the root business object (e.g., accountingEntries)
    entries = root.xpath("/xbrli:xbrl/gl-cor:accountingEntries", namespaces=namespaces)
    if not entries:
        trace_print("ERROR: /xbrli:xbrl/gl-cor:accountingEntries not found.")
        return
    data_dict = xml_to_dict(entries[0], namespaces)

    # Step 4: Load combined structure (LHM + binding)
    binding_dict = {}

    # Step 5: Flatten the dictionary into tidy records
    dp = DataProcessor(binding_dict)
    dp.flatten_dict(data_dict)
    records = dp.get_records()
    if not records:
        trace_print("No records extracted.")
        return

    # Step 6: Write to CSV file
    # Only include fields that are actually used in records (i.e. appear in all_keys)
    # Dynamically determine all unique field names from all records
    all_keys = set()
    for r in records:
        all_keys.update(r.keys())
    used_elements = all_keys  # set of actual data keys from records
    # 再度構造ファイルを読み込んで、sequence順にソートされたElementを取得
    ordered_fieldnames = []
    with open(structure_file, mode="r", encoding=encoding) as f:
        reader = csv.DictReader(f)
        # ソートするためにsequenceをintで保持
        structure_rows = sorted(
            (row for row in reader if row.get("element")),
            key=lambda r: int(r["sequence"]) if r.get("sequence", "").isdigit() else 9999
        )
        for row in structure_rows:
            element = row["element"].strip()
            if element in used_elements and element not in ordered_fieldnames:
                ordered_fieldnames.append(element)

    levels = {}
    with open(structure_file, mode="r", encoding=encoding) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            # 特定のカラムだけ確認する場合は例えば以下のように：
            element = row.get("element", "").strip()
            typ = row.get("type", "").strip()
            level = row.get("level", "").strip()
            # multiplicity = row.get("multiplicity", "").strip()
            debug_print(f"  → Element: {element}, Type: {typ}, Level: {level}")
            if level.isdigit():
                level = int(level)
            if 'C'==typ:
                levels[element] = level

    def set_dimension(idx, element, dimension):
        level = levels[element]
        if dimension[level-1]:
            if element in dimension[level-1]:
                dimension[level-1] = {element: 1 + dimension[level-1][element]}
            else:
                dimension[level-1] = {element: 1}
        else:
            dimension[level-1] = {element: 1}
        for i in range(1+level,10):
            dimension[i-1] = None

    fieldnames = ordered_fieldnames
    # Write to CSV file (this will create the file if it doesn't exist)
    with open(output_file, mode="w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        dimension = [None]*10
        idx = 0
        for row in records:
            idx = idx + 1
            element = list(row.keys())[0]
            if element in levels:
                set_dimension(idx, element, dimension)
            debug_print(f"{idx} {dimension}")
            for item in dimension:
                if item and isinstance(item, dict):
                    for key, value in item.items():
                        row[key] = value
            writer.writerow(row)

    trace_print(f"Tidy CSV written to: {output_file}")

if __name__ == "__main__":
    main()
