#!/usr/bin/env python3
# coding: utf-8
"""
xbrl_gl_palette_parser.py
Parses XBRL Global Ledger (XBRL GL) taxonomy and extracts labeled hierarchical element structures into CSV format.

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-04-02

MIT License

(c) 2025 SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Usage:
    python xbrl_gl_label_parser.py --base-dir <taxonomy-root-directory> [--palette <palette-subdir>] [--lang <language-code>] [--debug] [--trace]

Arguments:
    --base-dir     Required. Path to the root of the XBRL GL taxonomy (e.g., XBRL-GL-PWD-2016-12-01).
    --palette      Optional. Subdirectory name of the palette folder (default: case-c-b-m-u-e-t-s).
    --lang         Optional. Language code for multilingual labels. Default is 'ja'.
    --debug        Optional. Enables detailed debug output.
    --trace        Optional. Enables trace messages.
    --output       Optional. Filename for the output CSV (default: XBRL_GL_Parsed_LHM_Structure.csv).

Example:
    python xbrl_gl_label_parser.py --base-dir XBRL-GL-PWD-2016-12-01 --palette case-c-b --lang ja --debug --output gl_hierarchy_and_labels.csv
"""

import lxml.etree as ET
import os
import re
import csv
import argparse
from collections import defaultdict

TRACE = True
DEBUG = True

def trace_print(text):
    if TRACE or DEBUG:
        print(text)

def debug_print(text):
    if DEBUG:
        print(text)

# Helper to clean label IDs
def clean_label_id(label_id):
    label_id = re.sub(r"^label_", "", label_id)
    label_id = re.sub(r"(_lbl|_\d+(_\d+)?)$", "", label_id)
    return label_id

# Argument parser for base directory
parser = argparse.ArgumentParser(description="Parse XBRL-GL schemas and extract labeled hierarchy.")
parser.add_argument("--palette", type=str, default="case-c-b-m-u-e-t-s", help="Palette subdirectory under gl/plt/ (e.g. case-c-b or case-c-b-m-u-e-t-s)")
parser.add_argument("--base-dir", type=str, required=True, help="Base directory path to XBRL GLtaxonomy, e.g. XBRL-GL-PWD-2016-12-01")
parser.add_argument("--debug", action="store_true", help="Enable debug output")
parser.add_argument("--trace", action="store_true", help="Enable trace output")
parser.add_argument("--lang", type=str, default="ja", help="Language code for local labels (e.g. 'ja', 'en')")

args = parser.parse_args()
base_dir = args.base_dir
palette = args.palette
DEBUG = args.debug
TRACE = args.trace
LANG = args.lang

xsd_path = os.path.join(base_dir, f"gl/plt/{palette}/gl-cor-content-2016-12-01.xsd")
namespaces = {
    'xs': "http://www.w3.org/2001/XMLSchema",
    'xbrli': "http://www.xbrl.org/2003/instance"
}
modules = ['gen', 'cor', 'bus', 'muc', 'usk', 'ehm', 'taf', 'srcd']

# Load base schemas and build type maps
element_type_map = {}
type_base_map = {}
type_base_lookup = {}
complex_type_lookup = {}
for mod in modules:
    path = os.path.join(base_dir, f"gl/{mod}/gl-{mod}-2016-12-01.xsd")
    if os.path.exists(path):
        tree = ET.parse(path)
        root = tree.getroot()
        for el in root.xpath("//xs:element", namespaces=namespaces):
            name, type_ = el.get("name"), el.get("type")
            if name and type_:
                # debug_print(f"gl-{mod}:{name}")
                element_type_map[f"gl-{mod}:{name}"] = type_
        for tdef in root.xpath("//xs:simpleType | //xs:complexType", namespaces=namespaces):
            name = tdef.get("name")
            if name:
                # debug_print(name)
                complex_type_lookup[name] = tdef
                restriction = tdef.find(".//xs:restriction", namespaces)
                if restriction is not None:
                    base = restriction.get("base")
                    if base:
                        type_base_map[name] = base
                        type_base_lookup[name] = base
                extension = tdef.find(".//xs:extension", namespaces)
                if extension is not None:
                    base = extension.get("base")
                    if base:
                        type_base_map[name] = base
                        type_base_lookup[name] = base

# Load content schemas
content_roots = {}
for mod in modules:
    path = os.path.join(base_dir, f"gl/plt/{palette}/gl-{mod}-content-2016-12-01.xsd")
    if os.path.exists(path):
        content_roots[mod] = ET.parse(path).getroot()
        tree = ET.parse(path)
        root = tree.getroot()
        for el in root.xpath("//xs:element", namespaces=namespaces):
            name, type_ = el.get("name"), el.get("type")
            if name and type_:
                # debug_print(f"gl-{mod}:{name}")
                element_type_map[f"gl-{mod}:{name}"] = type_
        for tdef in root.xpath("//xs:simpleType | //xs:complexType", namespaces=namespaces):
            name = tdef.get("name")
            if name:
                # debug_print(name)
                complex_type_lookup[name] = tdef
                restriction = tdef.find(".//xs:restriction", namespaces)
                if restriction is not None:
                    base = restriction.get("base")
                    if base:
                        type_base_map[name] = base
                        type_base_lookup[name] = base
                extension = tdef.find(".//xs:extension", namespaces)
                if extension is not None:
                    base = extension.get("base")
                    if base:
                        type_base_map[name] = base
                        type_base_lookup[name] = base

# Load content schemas
content_roots = {}
for mod in modules:
    path = os.path.join(base_dir, f"gl/plt/{palette}/gl-{mod}-content-2016-12-01.xsd")
    if os.path.exists(path):
        content_roots[mod] = ET.parse(path).getroot()

# Load label linkbases (EN and JA)
def load_labels(mod, lang):
    label_map = defaultdict(dict)
    suffix = "label.xml" if lang == "en" else f"label-{lang}.xml"
    path = os.path.join(base_dir, f"gl/{mod}/lang/gl-{mod}-2016-12-01-{suffix}")
    if not os.path.exists(path):
        return label_map
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {'link': 'http://www.xbrl.org/2003/linkbase', 'xlink': 'http://www.w3.org/1999/xlink'}

    locator_map = {}
    label_resources = {}

    # Map locator label -> href target
    for loc in root.xpath(".//link:loc", namespaces=ns):
        label_id = loc.get("{http://www.w3.org/1999/xlink}label")
        href = loc.get("{http://www.w3.org/1999/xlink}href")
        _, anchor = href.split("#")
        if label_id and href and '#' in href:
            locator_map[label_id] = anchor

    # Collect label resources
    for label in root.xpath(".//link:label", namespaces=ns):
        label_id = label.get("{http://www.w3.org/1999/xlink}label")
        role = label.get("{http://www.w3.org/1999/xlink}role")
        label_text = label.text.strip() if label.text else ""
        if label_id not in label_resources:
            label_resources[label_id] = {}
        if role.endswith("label"):
            label_resources[label_id]["label"] = label_text
        elif role.endswith("documentation"):
            label_resources[label_id]["documentation"] = label_text


    # Resolve labelArcs and map labels to href anchors
    for arc in root.xpath(".//link:labelArc", namespaces=ns):
        from_label = arc.get("{http://www.w3.org/1999/xlink}from")
        to_label = arc.get("{http://www.w3.org/1999/xlink}to")
        href = locator_map.get(from_label)
        label = label_resources.get(to_label)
        if href and label is not None:
            role = label.get("{http://www.w3.org/1999/xlink}role")
            if lang == "en":
                if "label" in label:
                    label_map[href]["label"] = label["label"]
                if "documentation" in label:
                    label_map[href]["documentation"] = label["documentation"]
            elif lang != "en":
                if "label" in label:
                    label_map[href][f"label_{lang}"] = label["label"]
                if "documentation" in label:
                    label_map[href][f"documentation_{lang}"] = label["documentation"]

    return label_map

label_texts = defaultdict(dict)
for mod in modules:
    labels = [load_labels(mod, "en")]
    if LANG != "en":
        labels.append(load_labels(mod, LANG))
    for label_map in labels:
        for k, v in label_map.items():
            label_texts[k].update(v)

# Helpers
def is_tuple_type(complex_type_element):
    if complex_type_element is None:
        return False
    if complex_type_element.find("xs:simpleContent", namespaces) is not None:
        return False
    complex_content = complex_type_element.find("xs:complexContent", namespaces)
    if complex_content is not None:
        for tag in ["xs:restriction", "xs:extension"]:
            inner = complex_content.find(tag, namespaces)
            if inner is not None:
                base = inner.get("base")
                return base == "anyType"
    return False

def resolve_base_type(type_str):
    type_name = type_str.split(":")[-1]
    return type_base_lookup.get(type_name, "")

# Traversal
records = []
def process_sequence(seq, _type, module, path, base, namespaces):
    debug_print(f" - Processing xs:sequence in path: /{path}")
    for el in seq.findall("xs:element", namespaces=namespaces):
        ref = el.get("ref")
        name = el.get("name")
        el_name = ref or name
        el_type = element_type_map.get(el_name, "")
        type_name = el_type.split(":")[-1]
        complex_type = complex_type_lookup.get(type_name)
        is_tuple = False
        if complex_type is not None:
            is_tuple = is_tuple_type(complex_type)

        path_str = f"gl-{module}:{path}" if "gl-" not in path else path
        new_path = f"{path_str}/{el_name}"
        min_occurs = el.get("minOccurs", "1")
        max_occurs = el.get("maxOccurs", "1")
        base_type = resolve_base_type(el_type) if not is_tuple and el_type else ""
        level = 1 + new_path.count("/")

        raw_key = el_name.replace(":", "_")
        label_info = label_texts.get(raw_key, {})

        record = {
            "Level": level,
            "Element": el_name,
            "Type": el_type,
            "Path": f"/{new_path}",
            "isTuple": is_tuple,
            "minOccurs": min_occurs,
            "maxOccurs": max_occurs,
            "BaseType": base_type,
            "Label": label_info.get("label", ""),
            "Documentation": label_info.get("documentation", ""),
            "LocalLabel": label_info.get("label_ja", ""),
            "LocalDocumentation": label_info.get("documentation_ja", "")
        }
        records.append(record)
        if not el_type:
            continue
        type_name = el_type.split(":")[-1]
        if is_tuple:
            mod = el_type.split(":")[0][3:]
            for _path in [
                os.path.join(base_dir, f"gl/{mod}/gl-{mod}-2016-12-01.xsd"),
                os.path.join(base_dir, f"gl/plt/{palette}/gl-{mod}-content-2016-12-01.xsd")
            ]:
                if os.path.exists(_path):
                    tree = ET.parse(_path)
                    nested = tree.xpath(f".//xs:complexType[@name='{type_name}']", namespaces=namespaces)
                    if nested:
                        walk_complex_type(type_name, nested[0], "tuple", mod, new_path, namespaces)
                        break

def walk_complex_type(name, element, _type, module, path, namespaces):
    if ":" not in path:
        debug_print(f"Walking {_type} type '{name}' at path: /gl-{module}:{path}")
    else:
        debug_print(f"Walking {_type}: '{name}' at path: /{path}")
    sequence = element.find("xs:sequence", namespaces)
    if sequence is not None:
        process_sequence(sequence, _type, module, path, name, namespaces)
        return
    complex_content = element.find("xs:complexContent", namespaces)
    if complex_content is not None:
        for tag in ["xs:restriction", "xs:extension"]:
            inner = complex_content.find(tag, namespaces)
            if inner is not None:
                base = inner.get("base")
                seq = inner.find("xs:sequence", namespaces)
                if seq is not None:
                    process_sequence(seq, _type, module, path, base, namespaces)
                return

# Start with root complexType
root = content_roots["cor"]
complex_type_list = root.xpath(".//xs:complexType[@name='accountingEntriesComplexType']", namespaces=namespaces)
if complex_type_list:
    href = "gl-cor_accountingEntries"
    record = {
        "Level": 1,
        "Element": "accountingEntries",
        "Type": "gl-cor:accountingEntriesComplexType",
        "Path": "/gl-cor:accountingEntries",
        "isTuple": True,
        "minOccurs": "1",
        "maxOccurs": "unbounded",
        "BaseType": "",
        "Label": label_texts[href].get("label", ""),
        "Documentation": label_texts[href].get("documentation", ""),
        "LocalLabel": label_texts[href].get("label_ja", ""),
        "LocalDocumentation": label_texts[href].get("documentation_ja", "")
    }
    records.append(record)
    
    walk_complex_type("accountingEntriesComplexType", complex_type_list[0], "tuple", "cor", "accountingEntries", namespaces)
else:
    print("❌ Not found: accountingEntriesComplexType")

# Output to CSV
output_dir = "XBRL-GL-2025"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, f"XBRL_GL_{palette}_Parsed_LHM_Structure.csv")

with open(output_file, mode='w', newline='', encoding='utf-8-sig') as f:
    if records:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    else:
        print("⚠️ No records to write.")

print(f"\n✅ Saved parsed structure to: {output_file}")
