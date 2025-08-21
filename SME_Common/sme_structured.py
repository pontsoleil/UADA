#!/usr/bin/env python3
# coding: utf-8
"""
sme_structured.py
Flatten definition hierarchy for SME Common EDI from Logical Hiererchy Model (LHM) CSV

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-06-28
Last Modified: 2025-07-13

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

class FlattenLHM:
    def __init__ (
            self,
            lhm_file,
            remove_chars,
            flatten_terms,
            encoding,
            trace,
            debug
        ):

        self.lhm_file = lhm_file.replace('/', os.sep)
        self.lhm_file = file_path(self.lhm_file)
        if not self.lhm_file or not os.path.isfile(self.lhm_file):
            print(f'[INFO] No input Semantic file {self.lhm_file}.')
            sys.exit()

        self.out_file = f"{self.lhm_file[:-4]}_flat.csv"

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

    def flatten(self):
        # read CSV file
        in_header =  [
            "version","sequence","level","type","identifier","UNID","acronym","label_local","multiplicity","seq","class_term","property_term","representation_term","associated_class","definition_local","code_list","attribute","DEN","definition","short_name","name","element","xpath"
        ]
        out_header =  [
            "version","sequence","UNID","acronym","level","label_local","type","depth","name","multiplicity","definition_local","DEN","definition","code_list","xpath"
        ]
        with open(self.lhm_file, encoding = self.encoding, newline='') as f:
            reader = csv.DictReader(f, fieldnames = in_header)
            next(reader) # skip header row
            hierarchy = [""]
            records = []
            for row in reader:
                record = {}
                for field in out_header:
                    if field in row:
                        record[field] = row[field]
                    else:
                        record[field] = ""
                type = record["type"]
                record["type"] = ""
                record["depth"] = ""
                if record["level"].isdigit():
                    level = int(record["level"])
                else:
                    continue
                if "multiplicity" in record and record["multiplicity"]:
                    max_occur = record["multiplicity"][-1]
                else:
                    max_occur = ""

                while len(hierarchy) < 1 + level:
                    hierarchy.append("")

                if "C"==type:
                    if "n"==max_occur:
                        depth = 1 + hierarchy[level-1]
                        record["name"] = f'd{record["name"]}'
                        record["type"] = "dimension"
                        record["depth"] = hierarchy[level - 1]
                    else:
                        depth = hierarchy[level - 1] if level > 0 else 1
                        if level > 0:
                            record["name"] = ""
                            record["xpath"] = ""
                    hierarchy[level] = depth
                else:
                    record["type"] = "field"
                    depth = hierarchy[level - 1]
                    hierarchy[level] = depth
                    record["depth"] = depth

                hierarchy = hierarchy[:1+level]
                self.debug_print(f'{level} {max_occur} {hierarchy} {record["type"]} | {record["DEN"]}')
                records.append(record)

        # CSV出力
        with open(self.out_file, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=out_header)
            writer.writeheader()
            writer.writerows(records)

        self.trace_print(f"Output file {self.out_file}")

# Main function to execute the script
def main():
    # Create the parser
    parser = argparse.ArgumentParser(
        prog='sme_structured.py',
        usage='%(prog)s LHM_file -e encoding [options] ',
        description='Flatten basic model to produce structured CSV definition.'
    )
    parser.add_argument('LHM_file', metavar='LHM_file', type = str, help='Loogical Hierarchical Model file path')
    parser.add_argument('-e', '--encoding', required = False, default='utf-8-sig', help='File encoding, default is utf-8-sig')
    parser.add_argument('-t', '--trace', required = False, action='store_true')
    parser.add_argument('-d', '--debug', required = False, action='store_true')

    args = parser.parse_args()

    REMOVE_CHARS = " -._'"
    FLATTEN_TERMS = ["Trade Agreement","Trade Settlement","Trade Delivery","Trade Transaction","Trade Line Item"]

    processor = FlattenLHM(
        lhm_file = args.LHM_file.strip(),
        remove_chars = REMOVE_CHARS,
        flatten_terms = FLATTEN_TERMS,
        encoding = args.encoding.strip() if args.encoding else None,
        trace = args.trace,
        debug = args.debug
    )

    processor.flatten()

if __name__ == '__main__':
    main()
