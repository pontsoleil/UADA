#!/usr/bin/env python3
# coding: utf-8
"""
Universal Audit Data Converter: xml2structured_csv.py

This script converts an XBRL-GL XML instance document into a standard structured CSV (based on xBRL-CSV).
It extracts data according to an LHM (Logical Hierarchical Model) definition and a specified XPath mapping.
The output includes a UTF-8 BOM-encoded CSV file and a corresponding JSON metadata file for structured CSV.

Designed by Nobuyuki Sambuichi (Sambuichi Professional Engineers Office)
Written by Nobuyuki Sambuichi (Sambuichi Professional Engineers Office)

MIT License

(c) 2025 Nobuyuki Sambuichi (Sambuichi Professional Engineers Office)

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
"""

import os
import sys
import re
import csv
import json
import argparse
from lxml import etree
from csv2tidy import DataProcessor

TRACE = False
DEBUG = False

def debug_print(message):
    if DEBUG:
        print(f"[DEBUG] {message}")

def trace_print(message):
    if TRACE:
        print(f"[TRACE] {message}")

class NamespaceContext:
    def __init__(self, ns_map):
        self.ns_map = ns_map

    def get(self):
        return self.ns_map

class XPathResolver:
    def __init__(self, xml_file, namespaces):
        self.tree = etree.parse(xml_file)
        self.namespaces = namespaces

    def find(self, xpath, tree):
        try:
            debug_print(f"Evaluating source XPath: {xpath}")
            elements = tree.xpath(xpath, namespaces=self.namespaces)
            return elements
        except Exception as e:
            debug_print(f"XPath error: {e}")
            return []

class StructuredCSVBuilder:
    def __init__(self, binding_csv, out_csv, currency, encoding):
        self.binding_csv = binding_csv
        self.out_csv = out_csv
        self.currency = currency
        self.encoding = encoding

        self.records = []
        self.headers = set()
        self.dimensions = set()
        
        self.binding_map = {}
        with open(binding_csv, newline='', encoding=encoding) as f:
            reader = csv.DictReader(f)
            source_levels = target_levels = [""] * 10
            for row in reader:
                _type = row["type"]
                level = row.get("level")
                if not level:
                    continue
                _l = int(level)
                # source XML
                source_element = row.get("2016PWD")
                source_levels[_l] = source_element
                for i in range(_l+1, 10):
                    source_levels[i] = ""
                _levels = [x for x in source_levels if x]
                source_xpath = "/xbrli:xbrl/" + "/".join(_levels)
                row["source_xpath"] = source_xpath
                # target XML
                target_element = row.get("element")
                target_xpath = row.get("xpath")
                target_multiplicity = row.get("multiplicity")
                target_level = len(target_xpath.split("/")) - 1
                target_levels[target_level] = target_element
                for i in range(target_level+1, 10):
                    target_levels[i] = ""
                # Class
                if "C"==_type:
                    row["children"] = []
                    if target_multiplicity[-1]=="*":
                        self.dimensions.add(target_element)
                self.binding_map[target_element] = row
                # set children's target element name
                parent_element = target_levels[target_level - 1]
                if parent_element and parent_element in self.binding_map:
                    self.binding_map[parent_element]["children"].append(target_element)

        self.namespaces = {
            "gl-cor": "http://www.xbrl.org/int/gl/cor/2025-12-01",
            "gl-bus": "http://www.xbrl.org/int/gl/bus/2025-12-01",
            "gl-muc": "http://www.xbrl.org/int/gl/muc/2025-12-01",
            "gl-usk": "http://www.xbrl.org/int/gl/usk/2025-12-01",
            "gl-ehm": "http://www.xbrl.org/int/gl/ehm/2025-12-01",
            "gl-taf": "http://www.xbrl.org/int/gl/taf/2025-12-01",
            "gl-srcd": "http://www.xbrl.org/int/gl/srcd/2025-12-01",
            "xbrli": "http://www.xbrl.org/2003/instance",
            "link": "http://www.xbrl.org/2003/linkbase",
            "iso4217": "http://www.xbrl.org/2003/iso4217",
        }


    def xml_to_dict(self, element, nsmap=None):
        def get_prefixed_tag(el):
            qname = etree.QName(el.tag)
            ns = [x for x,v in self.namespaces.items() if v==qname.namespace]
            if ns:
                return f"{ns[0]}:{qname.localname}"
            return  qname.localname

        children = list(element)
        if not children:
            return element.text.strip() if element.text else ""
        result = {}
        element_tag = get_prefixed_tag(element)
        result[element_tag] = ''
        if ':' not in element_tag:
            self.debug_print(element_tag)
        # self.dimensions.add(element_tag)
        for child in children:
            if not isinstance(child.tag, str):
                continue  # Skip comments and special nodes
            tag = get_prefixed_tag(child)
            value = self.xml_to_dict(child, nsmap)
            if tag in result:
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(value)
            else:
                result[tag] = value
        return result

    def json_meta_file(self, taxonomy_base, json_file):
        namespaces = {
            'xbrli': 'http://www.xbrl.org/2003/instance',
            'xbrll': 'http://www.xbrl.org/2003/linkbase',
            'xlink': 'http://www.w3.org/1999/xlink',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'gl-cor': 'http://www.xbrl.org/int/gl/cor/2025-12-01',
            'gl-muc': 'http://www.xbrl.org/int/gl/muc/2025-12-01',
            'gl-bus': 'http://www.xbrl.org/int/gl/bus/2025-12-01',
            'gl-usk': 'http://www.xbrl.org/int/gl/usk/2025-12-01',
            'gl-ehm': 'http://www.xbrl.org/int/gl/ehm/2025-12-01',
            'gl-taf': 'http://www.xbrl.org/int/gl/taf/2025-12-01',
            'gl-srcd': 'http://www.xbrl.org/int/gl/srcd/2025-12-01',
            'gl-plt': 'http://www.xbrl.org/int/gl/plt/2025-12-01',
            'iso4217': 'http://www.xbrl.org/2003/iso4217',
            'iso639': 'http://www.xbrl.org/2005/iso639',
            'ns0': "http://example.com"
        }
        palettes = [
            "case-c",
            "case-c-b",
            "case-c-b-m",
            "case-c-b-m-u",
            "case-c-b-m-u-e",
            "case-c-b-m-u-e-t",
            "case-c-b-m-u-e-t-s",
            "case-c-b-m-u-t",
            "case-c-b-m-u-t-s",
            "case-c-b-t",
            "case-c-t"
        ]
        for prefix in  self.unique_prefixes:
            namespaces[prefix] = f"http://www.{prefix}"
        json_meta = {
            "documentInfo": {
                "documentType": "https://xbrl.org/2021/xbrl-csv",
                "namespaces": namespaces
            },
            "tableTemplates": {
                "xbrl-gl_template": {
                    "dimensions": {
                        "period": "2025-05-17T00:00:00",
                        "entity": "ns0:Example Co.",
                    },
                    "columns": {},
                }
            },
            "tables": {"xbrl-gl_table": {"template": "xbrl-gl_template"}},
        }

        dimensions = [f.replace(":", "_") for f in self.dimension_fields]
        properties = [f.replace(":", "_") for f in self.non_dimension_fields]

        modules = set()
        for x in properties:
            modules.add(x[3:x.index("_")][0] )
        matching = [
            p for p in palettes
            if set(p.removeprefix("case-").split("-")) == modules
        ]
        debug_print(matching)
        if 1==len(matching):
            taxonomy = f"../gl-{matching[0]}/plt/gl-plt-oim-2025-12-01.xsd"
            json_meta["documentInfo"]["taxonomy"] = [taxonomy]
        else:
            taxonomy = f"{taxonomy_base}/gl-case-c-b-m-u-e-t-s/plt/gl-plt-oim-2025-12-01.xsd"

        for dimension in dimensions:
            dimension_name = dimension[3:]
            dimension_column = dimension.split("_", 1)[-1]
            json_meta["tableTemplates"]["xbrl-gl_template"]["dimensions"][
                f"gl-plt:d_{dimension_name}"
            ] = f"${dimension_column}"
            json_meta["tableTemplates"]["xbrl-gl_template"]["columns"][
                dimension_column
            ] = {}

        for property in properties:
            property_name = property[1 + property.index("_"):]
            property_module = property[: property.index("_")]
            if self.datatype_map[property.replace("_",":")].endswith("monetaryItemType"):
                json_meta["tableTemplates"]["xbrl-gl_template"]["columns"][
                    property_name
                ] = {
                    "dimensions": {
                        "concept": f"{property_module}:{property_name}",
                        "unit": f"iso4217:{self.currency.upper()}",
                    }
                }
            else:
                json_meta["tableTemplates"]["xbrl-gl_template"]["columns"][
                    property_name
                ] = {"dimensions": {"concept": f"{property_module}:{property_name}"}}

        csv_file = json_file[1+json_file.rindex(os.sep):].replace("json", "csv")
        json_meta["tables"]["xbrl-gl_table"]["url"] = csv_file

        try:
            with open(json_file, "w", encoding=self.encoding) as file:
                json.dump(json_meta, file, ensure_ascii=False, indent=4)
            trace_print(f"JSON meta file '{json_file}' has been created successfully.")
        except Exception as e:
            print(f"An error occurred while creating the JSON file: {e}")

        print("** END **")

    # Function to merge lines and delete unnecessary lines
    def merge_rows(self, records, dimensions):
        i = 0
        changed = True
        while changed:
            changed = False
            while i < len(records):
                row = records[i]
                debug_print(f"{i} row:{row}")
                dims = []
                for dim in dimensions:
                    targets = [k for k in row.keys() if k in self.parent and self.parent[k] in dimensions]
                    if row.get(dim) or dim in targets:
                        dims.append(dim)
                if len(dims) < 2:
                    i += 1
                    continue
                children = []
                for r in records: # look for another child having the same dimension
                    target_dims = dims[:-1]
                    d = dims[-1]
                    for dim in target_dims:
                        if dim not in row or dim not in r or row[dim]!= r[dim]:
                            continue
                    if d in r and row[d] != r[d]:
                        children.append(r)
                        break
                if 0==len(children):
                    # copy data to parent
                    condition = {key: row[key] for key in target_dims}
                    for r in records[:i]:
                        # If all parent dimensions match and no values exist in other dimensions, then set values
                        if all(r.get(k, "") == condition[k] for k in target_dims):
                            if all(not r.get(k, "") for k in dimensions if k not in target_dims):
                                if r:
                                    parent = r
                                    for k, v in row.items():
                                        if parent and k not in dimensions and k not in parent:
                                            parent[k] = v
                    debug_print(f"{i} parent: {parent}")
                    # Delete row
                    del records[i]
                    changed = True
                    break
                i += 1
        return records

    def extract_recursive(self, elem, binding_key):
        binding = self.binding_map[binding_key]
        source_xpath = binding.get('source_xpath')
        multiplicity = binding.get('multiplicity', '1')
        is_multiple = multiplicity.strip()[-1] == '*'
        children = binding.get("children", [])

        elements = elem.xpath(source_xpath.split('/')[-1], namespaces=self.namespaces)
        results = []

        for el in elements:
            if not isinstance(el, etree._Element):
                continue

            if not children:
                text = el.text.strip() if el.text else ''
                if text:
                    results.append(text)
                continue

            child_result = {}
            # tag = etree.QName(el).localname
            # ns = [k for k, v in self.namespaces.items() if v == etree.QName(el).namespace]
            # if ns:
            #     prefixed_tag = f"{ns[0]}:{tag}"
            child_result[binding_key] = ""

            for child_key in children:
                child_binding = self.binding_map[child_key]
                child_xpath = child_binding.get('source_xpath')
                child_elements = el.xpath(child_xpath.split('/')[-1], namespaces=self.namespaces)

                if not child_elements:
                    continue

                is_child_multiple = child_binding.get('multiplicity', '1')[-1] == '*'

                if is_child_multiple:
                    grouped_children = []
                    for ce in child_elements:
                        if ce.text and ce.text.strip() and not child_binding.get("children"):
                            grouped_children.append(ce.text.strip())
                        else:
                            group = {}
                            tag = etree.QName(ce).localname
                            ns = [k for k, v in self.namespaces.items() if v == etree.QName(ce).namespace]
                            if ns:
                                prefixed_tag = f"{ns[0]}:{tag}"
                                target_element = [x["element"] for x in self.binding_map.values() if prefixed_tag==x["2016PWD"]]
                                if target_element and len(target_element) > 0:
                                    _element = target_element[0]
                                    group[_element] = ""
                            for grandchild_key in child_binding.get("children", []):
                                nested = self.extract_recursive(ce, grandchild_key)
                                if nested:
                                    group[grandchild_key] = nested
                            if group:
                                grouped_children.append(group)
                    if grouped_children:
                        child_result[child_key] = grouped_children
                else:
                    ce = child_elements[0]
                    if ce.text and ce.text.strip() and not child_binding.get("children"):
                        child_result[child_key] = ce.text.strip()
                    else:
                        if child_key not in child_result:
                            child_result[child_key] = {}
                        for grandchild_key in child_binding.get("children", []):
                            nested = self.extract_recursive(ce, grandchild_key)
                            if nested:
                                child_result[child_key][grandchild_key] = nested

            if child_result:
                results.append(child_result)

        if is_multiple:
            return results
        return results[0] if results else None

    def process(self, xml_file):
        debug_print("=== Starting XPath evaluation ===")
        self.resolver = XPathResolver(xml_file, self.namespaces)
        tree = etree.parse(xml_file)
        root = tree.getroot()

        # Step 1 check XML instance
        entries = self.resolver.find("/xbrli:xbrl/gl-cor:accountingEntries", root)
        if not entries:
            print("ERROR: /xbrli:xbrl/gl-cor:accountingEntries not found.")
            return None

        # Step 2: Convert XML to nested dictionary using namespace prefixes
        # Extract the root business object (e.g., accountingEntries)
        entries = root.xpath("/xbrli:xbrl/gl-cor:accountingEntries", namespaces=self.namespaces)
        if not entries:
            trace_print("ERROR: /xbrli:xbrl/gl-cor:accountingEntries not found.")
            return
        _data_dict = self.xml_to_dict(entries[0], self.namespaces)

        # Step 3 Parse XML instance document
        data_dict = {}
        for key in self.binding_map:
            if self.binding_map[key]['level'] == '1':  # top-level elements under accountingEntries
                result = self.extract_recursive(root, key)
                if result:
                    data_dict[key] = result

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
        # Only include fields that are actually used in records (i.e. appear in used_keys)
        # Dynamically determine all unique field names from all records
        qname_pattern = r'^[A-Za-z_][\w.-]*:[A-Za-z_][\w.-]*$' # QName regex pattern
        used_qname = set()
        used_keys = set()
        for r in records:
            used_keys.update(r.keys())
            for v in r.values():
                if isinstance(v, str) and re.fullmatch(qname_pattern, v):
                    used_qname.add(v)

        # Read and sort structure file rows by 'sequence' as integer (if available)
        with open(self.binding_csv, mode="r", encoding=self.encoding) as f:
            sorted_rows = sorted(
                (row for row in csv.DictReader(f) if row.get("element")),
                key=lambda r: (
                    int(r["sequence"]) if r.get("sequence", "").isdigit() else 9999
                ),
            )

        # Extract and collect unique prefixes
        unique_prefixes = {qname.split(":")[0] for qname in used_qname if ":" in qname}
        self.unique_prefixes = [x for x in unique_prefixes if x not in self.namespaces.keys()]
        # Extract 'element' values from sorted rows if they appear in used_keys
        self.ordered_fieldnames = []
        self.ordered_fieldnames = [
            row["element"].strip()
            for row in sorted_rows
            if row.get("element", "").strip() in used_keys
            and row["element"].strip() not in self.ordered_fieldnames
        ]

        self.datatype_map = {}
        for row in sorted_rows:
            element = row["element"].strip()
            datatype = row["datatype"]
            self.datatype_map[element] = datatype

        levels = {}
        parents = [None]*10
        self.parent = {}
        for row in sorted_rows:
            element = row.get("element", "").strip()
            typ = row.get("type", "").strip()
            level = row.get("level", "").strip()
            debug_print(f"  → Element: {element}, Type: {typ}, Level: {level}")
            if level.isdigit():
                level = int(level)
            if 'C'==typ:
                levels[element] = level
                parents[level] = element
                for l in range(1+level, 10):
                    if (parents[l]):
                        parents[l] = None
            elif level > 1:
                self.parent[element] = parents[level - 1]

        dimension = [None]*10
        idx = 0
        revised_records = []
        for row in records:
            idx = idx + 1
            first_element = list(row.keys())[0]
            if first_element in levels:
                dim = first_element
            else:
                continue
                dim = self.binding_map[first_element]['xpath'].split('/')[-2]
            if dim in levels: # dim is Class
                level = levels[dim]
                if dimension[level-1]:
                    if dim in dimension[level-1]:
                        dimension[level-1] = {dim: 1 + dimension[level-1][dim]}
                    else:
                        dimension[level-1] = {dim: 1}
                else:
                    dimension[level-1] = {dim: 1}
                for i in range(1+level, 10):
                    if dimension[i-1]:
                        dimension[i-1] = None
                debug_print(f"{idx} {dimension}")
            for item in dimension:
                if item and isinstance(item, dict):
                    for key, value in item.items():
                        row[key] = value
            revised_records.append(row)

        fieldnames = list(self.ordered_fieldnames)
        dimensions = [f for f in fieldnames if f in self.dimensions]
        # merged_records = self.merge_rows(revised_records, dimensions)
        merged_records = revised_records
        used_fields = set()
        for record in merged_records:
            for key in record:
                if record[key] not in [None, '', []]:
                    used_fields.add(key)

        # Convert to field name without namespace
        self.dimension_fields = [f.replace(":", "_") for f in fieldnames if f in dimensions and f in used_fields]
        self.non_dimension_fields = [f.replace(":", "_") for f in fieldnames if f not in dimensions and f in used_fields]
        # These fields are used in json_meta_file()
        fieldnames = self.dimension_fields + self.non_dimension_fields
        local_fieldnames = [f.split("_", 1)[-1] for f in fieldnames]
        # Write to CSV file (this will create the file if it doesn't exist)
        with open(self.out_csv, mode="w", newline="", encoding=self.encoding) as f:
            writer = csv.DictWriter(f, fieldnames=local_fieldnames)
            writer.writeheader()
            for row in merged_records:
                # Check if any of the fieldnames are included in the row
                if not any(f in [k.replace(":", "_") for k in row.keys()] for f in self.non_dimension_fields):
                    continue  # Skip if none
                # Convert key to local name also in output row
                local_row = {k.split(":", 1)[-1]: v for k, v in row.items()}
                writer.writerow(local_row)

        trace_print(f"Tidy CSV written to: {self.out_csv}")

        json_file = f"{self.out_csv[:-4]}.json"
        self.json_meta_file("../OIM-CSV/XBRL-GL-2025", json_file)


def main():
    global DEBUG, TRACE

    parser = argparse.ArgumentParser(description="Convert XML to structured CSV using xBRL-CSV rules.")
    parser.add_argument('xml_file', help='Input XML file')
    parser.add_argument('-o', '--out_csv', required=True, help='Output CSV file')
    parser.add_argument('-m', '--taxonomy_xsd', required=True, help='Taxonomy XSD file path for reference')
    parser.add_argument('-b', '--binding_csv', required=True, help='CSV file specifying XPath bindings')
    parser.add_argument('-c', '--currency', default='USD', help='Currency code (default USD)')
    parser.add_argument('-e', '--encoding', default='utf-8-sig', help='Encoding for CSV output (default utf-8-sig)')
    parser.add_argument('-t', '--trace', action='store_true', help='Enable trace output')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')

    args = parser.parse_args()

    DEBUG = args.debug
    TRACE = args.trace

    builder = StructuredCSVBuilder(args.binding_csv, args.out_csv, args.currency, args.encoding)
    builder.process(args.xml_file)

if __name__ == "__main__":
    main()
