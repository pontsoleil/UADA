#!/usr/bin/env python3
# coding: utf-8
"""
sme_schema.py
Generates Schema file for SME Common EDI from Business Semantic Model (BSM) CSV

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-05-18
Last Modified: 2025-05-19

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
# import copy
import re
# from collections import OrderedDict, Counter

def file_path(pathname):
    _pathname = pathname.replace("/", os.sep)
    if os.sep == _pathname[0:1]:
        return _pathname
    else:
        dir = os.path.dirname(__file__)
        return os.path.join(f"{dir}", _pathname)

class SchemaModule:
    def __init__ (
            self,
            bsm_file,
            root_term,
            remove_chars,
            encoding,
            trace,
            debug
        ):

        self.bsm_file = bsm_file.replace('/', os.sep)
        self.bsm_file = file_path(self.bsm_file)
        if not self.bsm_file or not os.path.isfile(self.bsm_file):
            print(f'[INFO] No input Semantic file {self.bsm_file}.')
            sys.exit()

        self.REMOVE_CHARS = remove_chars
        self.encoding = encoding.strip() if encoding else 'utf-8-sig'
        # Set debug and trace flags, and file path separator
        self.root_element = self.normalize_text(root_term)
        self.schema_file = f'{self.root_element}.xsd'

        self.TRACE = trace
        self.DEBUG = debug

        self.class_id_map = {}
        self.object_class_dict = {}
        self.version_date = "20230720135040"
        self.version_num = "4p1"
        self.html = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!-- ====================================================================== -->',
            f'<!-- ===== {self.root_element} Schema Module {" " * (59 - len(f"{self.root_element} Schema Module "))}===== -->',
            '<!-- ====================================================================== -->',
            '<!--',
            'Schema agency:  ',
            'Schema version: ',
            'Schema date:    ',
            '-->',
            '<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" ',
            'xmlns:ccts="urn:un:unece:uncefact:documentation:standard:CoreComponentsTechnicalSpecification:2" ',
            f'xmlns:rsm="urn:un:unece:uncefact:3055:413:data:standard:{self.root_element}:{self.version_num}" ',
            'xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:33" ',
            f'targetNamespace="urn:un:unece:uncefact:3055:413:data:standard:{self.root_element}:{self.version_num}" ',
            'elementFormDefault="qualified" ',
            'attributeFormDefault="unqualified" ',
            f'version="{self.version_date}">',
            '<!-- ======================================================================= -->',
            '<!-- ===== Imports                                                     ===== -->',
            '<!-- ======================================================================= -->',
            '<!-- ===== Import of Unqualified Data Type Schema Module               ===== -->',
            '<!-- ======================================================================= -->',
            '  <xsd:import namespace="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:33" schemaLocation="UnqualifiedDataType_33p0.xsd"/>',
            '<!-- ======================================================================= -->',
            '<!-- ===== Element Declarations                                        ===== -->',
            '<!-- ======================================================================= -->',
            '<!-- ===== Root Element Declarations                                   ===== -->',
            '<!-- ======================================================================= -->',
            '<!-- Global型宣言 -->',
            f'  <xsd:element name="{self.root_element}" type="rsm:{self.root_element}Type"/>',
            '<!-- ======================================================================= -->',
            '<!-- ===== Type Definitions                                            ===== -->'
        ]

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
        unid = row['unid']
        property_type = row["property_type"]
        if not unid:
            return None
        _type = row['property_type']
        class_term = row['class_term']
        if "." in class_term:
            class_term = class_term[:class_term.index(".")]
        class_term = self.normalize_text(class_term)
        if "Class"==property_type:
            if class_term not in self.class_id_map:
                class_num = str(len(list(self.class_id_map))).zfill(2)
                class_id = unid[:2] + class_num
                self.class_id_map[class_term] = {"class_id": class_id, "seq": 0}
            else:
                class_id_data = self.class_id_map[class_term]
                class_id = class_id_data["class_id"]
            _id = class_id
        else:
            class_id_data = self.class_id_map[class_term]
            class_id = class_id_data["class_id"]
            seq = class_id_data["seq"]
            seq += 1
            class_id_data["seq"] = seq
            _id = f"{class_id}_{str(seq)}"
        row["id"] = _id
        row["class_term"] = class_term
        property_term = row['property_term']
        if property_term:
            property_term = self.normalize_text(property_term)
            row["property_term"] = property_term
        associated_class = row['associated_class']
        if associated_class:
            associated_class = self.normalize_text(associated_class)
            row["associated_class"] = associated_class
        if _type in ['Class','Specialized Class']:
            if not class_term in self.object_class_dict:
                self.object_class_dict[class_term] = row
                self.object_class_dict[class_term]['properties'] = {}
        else:
            self.object_class_dict[class_term]['properties'][unid] = row
            self.object_class_dict[class_term]['properties'][unid]['class_term'] = class_term
        return class_term, property_term, associated_class

    def annotation(self, html, unid, acronym, den, definition, label_local, definition_local, leading_space=""):
        html += [
            f'{leading_space}    <xsd:annotation>',
            f'{leading_space}      <xsd:documentation xml:lang="en">',
            f'{leading_space}        <ccts:UniqueID>{unid}</ccts:UniqueID>',
            f'{leading_space}        <ccts:Acronym>{acronym}</ccts:Acronym>',
            f'{leading_space}        <ccts:DictionaryEntryName>{den}</ccts:DictionaryEntryName>',
            f'{leading_space}        <ccts:Definition>{definition}</ccts:Definition>',
            f'{leading_space}      </xsd:documentation>',
            f'{leading_space}      <xsd:documentation xml:lang="ja">',
            f'{leading_space}        <ccts:Name>{label_local}</ccts:Name>',
            f'{leading_space}        <ccts:Definition>{definition_local}</ccts:Definition>',
            f'{leading_space}      </xsd:documentation>',
            f'{leading_space}    </xsd:annotation>'
        ]
        return html

    def schema(self):
        # read CSV file
        header =  ['sequence', 'level', 'property_type', 'identifier', 'class_term', 'property_term', 'representation_term', 'associated_class', 'multiplicity', 'definition', 'acronym', 'id', 'domain_name', 'element', 'label_local', 'definition_local', 'den', 'unid']

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
                id = record["id"]
                self.debug_print(f"{id} {record['property_type']} | {class_term} | {record['associated_class'] or record['property_term']}")

        for key, data in self.object_class_dict.items():
            acronym = data["acronym"]
            unid = data["unid"]
            den = data["den"]
            element = data["element"]
            definition = data["definition"]
            label_local = data["label_local"]
            definition_local = data["definition_local"]
            definition_local =  re.sub(r'\s+', ' ', definition_local).strip()
            self.html += [
                '<!-- ======================================================================= -->',
                f'<!-- ===== {element}Type {" " * (66 - len(f"===== {element}Type "))}===== -->',
                '<!-- ======================================================================= -->',
                f'  <xsd:complexType name="{element}Type">',
            ]
            self.annotation(self.html, unid, acronym, den, definition, label_local, definition_local)
            self.html.append('    <xsd:sequence>')
            for k, v in data["properties"].items():
                unid = v["unid"]
                acronym = v["acronym"]
                den = v["den"]
                property_type = v["property_type"]
                element = v["element"]
                multiplicity = v["multiplicity"]
                min = multiplicity[0]
                max = multiplicity[-1]
                multiplicity = ""
                if "1"!=min:
                    multiplicity = f' minOccurs="{min}"'
                if "1"!=max:
                    multiplicity += ' maxOccurs="unbounded"'
                property_term = v["property_term"]
                definition = v["definition"]
                label_local = v["label_local"]
                definition_local = v["definition_local"]
                definition_local =  re.sub(r'\s+', ' ', definition_local).strip()
                if "Attribute"==property_type:
                    representation_term = v["representation_term"]
                    # Define a mapping for the representation term to data type conversion
                    representation_map = {
                        "Identifier": "ID",
                        "Date Time": "DateTime"
                    }
                    # Default to using the representation_term as data_type
                    data_type = representation_map.get(representation_term, representation_term)
                    # Construct the name
                    name = f"{property_term}{data_type}"
                    # Replace suffixes for specific cases
                    if name.endswith("IdentificationID"):
                        name = name.replace("IdentificationID", "ID")
                    elif name.endswith("Text"):
                        name = name.replace("Text", "")
                    # data_type = representation_term
                    # if "Identifier"==representation_term:
                    #     data_type = "ID"
                    # elif "Date Time"==representation_term:
                    #     data_type = "DateTime"
                    # name = f"{property_term}{data_type}"
                    # if name.endswith("IdentificationID"):
                    #    name = name.replace("IdentificationID", "ID")
                    # elif name.endswith("Text"):
                    #    name = name.replace("Text", "")
                    self.html += [
                        f'      <xsd:element name="{name}" type="udt:{data_type}Type"{multiplicity}>',
                    ]
                else:
                    associated_class = v["associated_class"]
                    name = f"{property_term}{associated_class}" 
                    self.html += [
                        f'      <xsd:element name="{name}" type="rsm:{associated_class}Type"{multiplicity}>'
                    ]
                self.annotation(self.html, unid, acronym, den, definition, label_local, definition_local, "    ")
                self.html.append(f'      </xsd:element>')

            self.html += [
                '    </xsd:sequence>',
                f'  </xsd:complexType>'
            ]

        self.html.append('</xsd:schema>')

        with open(self.schema_file, 'w', encoding=self.encoding) as f:
            for item in self.html:
                f.write(item + '\n')
                
        self.trace_print(f"Output file {self.schema_file}")

# Main function to execute the script
def main():
    # Create the parser
    parser = argparse.ArgumentParser(
        prog='sme_schema.py',
        usage='%(prog)s BSM_file -r Root class term -e encoding [options] ',
        description='Converts logical model to HMD with graph walk.'
    )
    parser.add_argument('BSM_file', metavar='BSM_file', type = str, help='Business semantic model file path')
    # Allow multiple values with action='append' or nargs='+'
    parser.add_argument("-r", "--root", help="Root class term for schema module to process.")
    parser.add_argument('-e', '--encoding', required = False, default='utf-8-sig', help='File encoding, default is utf-8-sig')
    parser.add_argument('-t', '--trace', required = False, action='store_true')
    parser.add_argument('-d', '--debug', required = False, action='store_true')

    args = parser.parse_args()

    REMOVE_CHARS = " -._'"

    processor = SchemaModule(
        bsm_file = args.BSM_file.strip(),
        root_term = args.root.strip() if args.root else None,
        remove_chars = REMOVE_CHARS,
        encoding = args.encoding.strip() if args.encoding else None,
        trace = args.trace,
        debug = args.debug
    )

    processor.schema()

if __name__ == '__main__':
    main()