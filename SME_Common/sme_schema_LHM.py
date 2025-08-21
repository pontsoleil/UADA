#!/usr/bin/env python3
# coding: utf-8
"""
sme_schema.py
Generates Schema file for SME Common EDI from Logical Hierarchical Model (LHM) CSV

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
            lhm_file,
            DATE,
            root_term,
            remove_chars,
            encoding,
            annotation,
            trace,
            debug
        ):

        self.lhm_file = lhm_file.replace('/', os.sep)
        dir = os.path.dirname(__file__)
        self.lhm_file = file_path(f'{dir}/{self.lhm_file}')
        if not self.lhm_file or not os.path.isfile(self.lhm_file):
            print(f'[INFO] No input Semantic file {self.lhm_file}.')
            sys.exit()

        self.REMOVE_CHARS = remove_chars
        self.encoding = encoding.strip() if encoding else 'utf-8-sig'
        # Set debug and trace flags, and file path separator
        self.root_element = self.normalize_text(root_term)
        self.schema_file = f'{self.root_element}_{DATE}.xsd'
        self.schema_file = file_path(f'{dir}/{self.schema_file}')

        self.ANNOTATION = annotation
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

    def annotation(self, unid, acronym, den, definition, label_local, definition_local, multiplicity, leading_space=""):
        html = [
            f'{leading_space}    <xsd:annotation>',
            f'{leading_space}      <xsd:documentation xml:lang="en">'
        ]
        if unid:
            html.append(f'{leading_space}        <ccts:UniqueID>{unid}</ccts:UniqueID>')
        if acronym:
            html.append(f'{leading_space}        <ccts:Acronym>{acronym}</ccts:Acronym>')
        if den:
            html.append(f'{leading_space}        <ccts:DictionaryEntryName>{den}</ccts:DictionaryEntryName>')
        if definition:

            html.append(f'{leading_space}        <ccts:Definition>{definition}</ccts:Definition>')
        html += [
            f'{leading_space}      </xsd:documentation>',
            f'{leading_space}      <xsd:documentation xml:lang="ja">'
        ]
        if label_local:
            html.append(f'{leading_space}        <ccts:Name>{label_local}</ccts:Name>')
        if definition_local:
            # 改行文字を削除
            text = definition_local.replace("\n", "")
            # 半角・全角スペースの連続を単一の半角スペースに変換
            text = re.sub(r"[ 　]+", " ", text)
            text = f'{leading_space}        <ccts:Definition>{text}'
            if 4==len(multiplicity):
                min = multiplicity[0]
                max = multiplicity[-1]
                if "n"==max:
                    max="unbounded"
                text += f' Occurence Min={min} Max={max}'
            text += '</ccts:Definition>'
            html.append(text)
        html += [
            f'{leading_space}      </xsd:documentation>',
            f'{leading_space}    </xsd:annotation>'
        ]
        return html

    def schema(self):
        def get_type(representation):
            if "Identifier"==representation:
                datatype = "ID"
            else:
                datatype = representation
            _type = f'udt:{datatype.replace(" ","")}Type'
            return _type
        
        # read CSV file
        self.debug_print("\n".join(self.html))
        # header = ["version","sequence","level","type","identifier","UNID","acronym","label_local","multiplicity","seq","class_term","property_term","representation_term","associated_class","definition_local","code_list","attribute","DEN","definition","short_name","name","element","xpath","accounting"]
        # 重複定義を削除したLHMシートを入力とする
        header = ["version","sequence","level","type","identifier","UNID","acronym","label_local","multiplicity","seq","class_term","property_term","representation_term","associated_class","definition_local","code_list","attribute","DEN","definition","short_name","element"]
        with open(self.lhm_file, encoding = self.encoding, newline='') as f:
            reader = csv.DictReader(f, fieldnames = header)
            next(reader)
            previous_level = 0
            complex_tyle_level = [""]*10
            for row in reader:
                record = {}
                for key in header:
                    _key = key #.lower()
                    if _key in row:
                        record[_key] = row[_key]
                    else:
                        record[_key] = ''
                if "END"==record["acronym"]:
                    break
                if not record["acronym"] or "SC"==record["acronym"]:
                    continue
                level = record["level"]
                if level.isdigit():
                    level = int(level)
                else:
                    level = 0
                if level < previous_level:
                    # self.debug_print(f'previous:{previous_level} leve;:{level}]')
                    lvl = previous_level
                    while lvl > level:
                        lvl -= 1
                        html = [
                            "      "*lvl + "      </xsd:sequence>",
                            "      "*lvl + "    </xsd:complexType>",
                            "      "*lvl + "  </xsd:element>"
                        ]
                        self.debug_print("\n".join(html))
                        self.html += html
                acronym = record["acronym"]
                element = record["element"]
                multiplicity = record["multiplicity"]
                unid = record["UNID"]
                den = record[ "DEN"]
                definition = record["definition"]
                label_local = record["label_local"]
                definition_local = record["definition_local"]
                if not multiplicity:
                    multiplicity = "1..1"
                # self.debug_print(f'{level} {acronym} {element} {multiplicity}')
                complex_tyle_level[level] = element
                leading_space = "      "*level
                if "BBIE"!=acronym:
                    html = leading_space + f'  <xsd:element name="{element}" '
                    if 4==len(multiplicity):
                        if "0"==multiplicity[0]:
                            html += 'minOccurs="0" '
                        if "n"==multiplicity[-1]:
                            html += 'maxOccurs="unbounded"'
                    html += ">"
                    self.debug_print(html)
                    self.html.append(html)
                    if self.ANNOTATION:
                        multiplicity = record["multiplicity"]
                        html = self.annotation(unid, acronym, den, definition, label_local, definition_local, multiplicity, leading_space)
                        self.debug_print("\n".join(html))
                        self.html += html
                    html = [
                        leading_space + "    <xsd:complexType>",
                        leading_space + "      <xsd:sequence>"
                    ]
                    self.debug_print("\n".join(html))
                    self.html += html
                else:
                    representation = record["representation_term"]
                    _type = get_type(representation)
                    html = leading_space + f'  <xsd:element name="{element}" type="{_type}" '
                    if "0"==multiplicity[0]:
                        html += 'minOccurs="0" '
                    if "n"==multiplicity[-1]:
                        html += 'maxOccurs="unbounded"'
                    if self.ANNOTATION:
                        html += ">"
                        self.debug_print(html)
                        self.html.append(html)
                        html = self.annotation(unid, acronym, den, definition, label_local, definition_local, multiplicity, leading_space)
                        self.debug_print("\n".join(html))
                        self.html += html
                        html = leading_space + f'  </xsd:element>'
                        self.debug_print(html)
                        self.html.append(html)
                    else:
                        html += "/>"
                        self.debug_print(html)
                        self.html.append(html)
                previous_level = level

        lvl = previous_level
        while lvl > 1:
            lvl -= 1
            html = [
                "      "*lvl + "      </xsd:sequence>",
                "      "*lvl + "    </xsd:complexType>",
                "      "*lvl + "  </xsd:element>"
            ]
            self.debug_print("\n".join(html))
            self.html += html

        html = [
            "      </xsd:sequence>",
            "    </xsd:complexType>",
            "  </xsd:element>",
            "</xsd:schema>"
        ]
        
        self.debug_print("\n".join(html))
        self.html += html

        with open(self.schema_file, 'w', encoding=self.encoding) as f:
            for item in self.html:
                f.write(item + '\n')
                
        self.trace_print(f"Output file {self.schema_file}")

# Main function to execute the script
def main():
    # Create the parser
    parser = argparse.ArgumentParser(
        prog='sme_schema_LHM.py',
        usage='%(prog)s LHM_file -r Root class term -e encoding [options] ',
        description='Generate XML schema based on the LHM.'
    )
    parser.add_argument('LHM_file', metavar='LHM_file', type = str, help='Logical Hierarchical Model definition file path')
    parser.add_argument("-r", "--root", help="Root class term for schema module to process.")
    parser.add_argument('-e', '--encoding', required = False, default='utf-8-sig', help='File encoding, default is utf-8-sig')
    parser.add_argument('-a', '--annotation', required = False, action='store_true')
    parser.add_argument('-t', '--trace', required = False, action='store_true')
    parser.add_argument('-d', '--debug', required = False, action='store_true')

    try:
        args = parser.parse_args()
    except Exception as e:
        print(f"引数の解析でエラーが発生しました: {e}")
        sys.exit(1)  # または適切なエラー処理 

    DATE = "07-05"
    REMOVE_CHARS = " -._'"

    processor = SchemaModule(
        lhm_file = args.LHM_file.strip(),
        DATE = DATE,
        root_term = args.root.strip() if args.root else None,
        remove_chars = REMOVE_CHARS,
        encoding = args.encoding.strip() if args.encoding else None,
        annotation = args.annotation,
        trace = args.trace,
        debug = args.debug
    )

    processor.schema()

if __name__ == '__main__':
    main()