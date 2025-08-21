#!/usr/bin/env python3
# coding: utf-8
"""
sme_flatten_BSM.py
Flatten definition hierarchy for SME Common EDI from Basic Semantic Model (BSM) CSV

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-06-28
Last Modified: 2025-06-28

MIT License

(c) 2023-2025 SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

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
import argparse
import csv
import re

def file_path(pathname):
    _pathname = pathname.replace("/", os.sep)
    if os.sep == _pathname[0:1]:
        return _pathname
    else:
        dir = os.path.dirname(__file__)
        return os.path.join(f"{dir}", _pathname)

class FlattenBSM:
    def __init__ (
            self,
            bsm_file,
            remove_chars,
            flatten_terms,
            encoding,
            trace,
            debug
        ):

        self.bsm_file = bsm_file.replace('/', os.sep)
        self.bsm_file = file_path(self.bsm_file)
        if not self.bsm_file or not os.path.isfile(self.bsm_file):
            print(f'[INFO] No input Semantic file {self.bsm_file}.')
            sys.exit()

        self.out_file = f"{self.bsm_file[:-4]}_flat.csv"

        self.REMOVE_CHARS = remove_chars
        self.FLATTEN_TERMS = flatten_terms
        self.encoding = encoding.strip() if encoding else 'utf-8-sig'

        self.TRACE = trace
        self.DEBUG = debug

        self.object_class_dict = {}
        self.class_id_map = {}

    def debug_print(self, text):
        if self.DEBUG:
            print(text)

    def trace_print(self, text):
        if self.TRACE or self.DEBUG:
            print(text)

    def normalize_text(self, text):
        if not text:
            return ""
        # Replace "-", ".", and "_" with a space
        replaced = text.translate(str.maketrans('', '', self.REMOVE_CHARS))
        # Replace multiple spaces with a single space and trim leading/trailing spaces
        normalized = re.sub(r'\s+', " ", replaced).strip()
        return normalized

    # Utility function to update class term
    def update_class_term(self, row):
        property_type = row["property_type"]
        _type = row['property_type']
        class_term = row['class_term']
        unid = row['UNID']
        if not unid and "Class"==_type:
            self.object_class_dict[class_term] = row
            self.object_class_dict[class_term]['properties'] = []
            return class_term, "", ""
        property_term = row['property_term']
        associated_class = row['associated_class']
        if _type in ['Class','Specialized Class']:
            if not class_term in self.object_class_dict:
                self.object_class_dict[class_term] = row
                self.object_class_dict[class_term]['properties'] = []
        else:
            if class_term!=row['class_term']:
                row['class_term'] = class_term
            self.object_class_dict[class_term]['properties'].append(row)
        return class_term, property_term, associated_class

    def flatten(self):
        def flatten_properties(properties, FLATTEN_TERMS):
            """properties リストを再帰的にflattenする"""
            flattened = []
            properties = sorted(properties, key=lambda p: int(p["sequence"]) if p.get("sequence", "").isdigit() else 0)
            for prop in properties:
                class_term = prop.get("class_term")
                acronym = prop.get("acronym")
                _type = prop.get("property_type")
                associated_class = prop.get("associated_class", "")
                multiplicity = prop.get("multiplicity")
                if acronym == "ASMA" or (
                    _type == "Composition"
                    and "1" == multiplicity[-1]
                    and associated_class.endswith(tuple(FLATTEN_TERMS))
                ):
                    # 再帰的にその中もflatten
                    associated = self.object_class_dict[associated_class]
                    if "properties" in associated:
                        inner = associated["properties"]
                        flattend_props = flatten_properties(inner, FLATTEN_TERMS)
                        flattened.extend(flattend_props)
                else:
                    flattened.append(prop)
            return flattened

        # read CSV file
        header =  ["version","sequence","seq","level","property_type","identifier","class_term","property_term","representation_term","associated_class","multiplicity","definition","acronym","code_list","element","label_local","definition_local","DEN","UNID"]

        with open(self.bsm_file, encoding = self.encoding, newline='') as f:
            reader = csv.DictReader(f, fieldnames = header)
            next(reader)
            for row in reader:
                record = {}
                for key in header:
                    if key in row:
                        record[key] = row[key]
                    else:
                        record[key] = ''
                class_term, property_term, associated_class = self.update_class_term(record)
                record["class_term"] = class_term
                record["property_term"] = property_term
                record["associated_class"] = associated_class
                unid = record["UNID"]
                self.debug_print(f"{unid} {record['property_type']} | {class_term} | {record['associated_class'] or record['property_term']}")

        self.flattened = {}
        for key, data in self.object_class_dict.items():
            class_term = data["class_term"]
            if class_term not in self.flattened:
                self.flattened[class_term] = []
            if "properties" in data:
                properties = data["properties"]
                flattened_props = flatten_properties(properties, self.FLATTEN_TERMS)
                self.flattened[class_term].extend(flattened_props)




        # class_term 出現順を保持（キーの順番通り）
        self.class_term_order = {term: idx for idx, term in enumerate(self.flattened)}

        # すべてのフラット化されたプロパティを収集
        all_rows = []
        for class_term, data in self.object_class_dict.items():
            # Class本体を1行出力（properties欄は空にする）
            class_row = [data.get(col, "") for col in header]
            all_rows.append(class_row)

            properties = self.flattened[class_term]

            # 複雑な条件に従ってソート
            def sort_key(p):
                # 1. Attribute 優先
                property_type_priority = 0 if p.get("property_type") == "Attribute" else 1
                # 2. multiplicity の最後が n かどうか
                multiplicity = p.get("multiplicity", "")
                multiplicity_priority = 1 if multiplicity.strip().endswith("n") else 0
                # 3. class_term の接頭辞による優先順位付け
                class_term = p.get("class_term", "").strip()
                class_priority_map = {
                    "CI": 0,
                    "CIIH": 1,
                    "CIIL": 2,
                    "CIILB": 3,
                }
                class_prefix_priority = 9  # デフォルトは最低優先度
                for prefix, priority in class_priority_map.items():
                    if class_term.startswith(prefix + "_") or class_term.startswith(prefix + " "):
                        class_prefix_priority = priority
                        break
                # 4. seq 昇順
                seq_str = p.get("seq", "")
                try:
                    seq = int(seq_str) if seq_str.strip().isdigit() else 9999
                except:
                    seq = 9999
                return (property_type_priority, multiplicity_priority, class_prefix_priority, seq)

            properties_sorted = sorted(properties, key=sort_key)

            for prop in properties_sorted:
                prop_row = [prop.get(col, "") for col in header]
                all_rows.append(prop_row)


        # CSV出力
        with open(self.out_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(all_rows)

        self.trace_print(f"Output file {self.out_file}")

# Main function to execute the script
def main():
    # Create the parser
    parser = argparse.ArgumentParser(
        prog='sme_flatten_BSM.py',
        usage='%(prog)s BSM_file -e encoding [options] ',
        description='Flatten basic model.'
    )
    parser.add_argument('BSM_file', metavar='BSM_file', type = str, help='Loogical Hierarchical Model file path')
    parser.add_argument('-e', '--encoding', required = False, default='utf-8-sig', help='File encoding, default is utf-8-sig')
    parser.add_argument('-t', '--trace', required = False, action='store_true')
    parser.add_argument('-d', '--debug', required = False, action='store_true')

    args = parser.parse_args()

    REMOVE_CHARS = " -._'"
    FLATTEN_TERMS = ["Trade Agreement","Trade Settlement","Trade Delivery","Trade Transaction","Trade Line Item"]

    processor = FlattenBSM(
        bsm_file = args.BSM_file.strip(),
        remove_chars = REMOVE_CHARS,
        flatten_terms = FLATTEN_TERMS,
        encoding = args.encoding.strip() if args.encoding else None,
        trace = args.trace,
        debug = args.debug
    )

    processor.flatten()

if __name__ == '__main__':
    main()
