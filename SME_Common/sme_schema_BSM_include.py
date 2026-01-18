#!/usr/bin/env python3
# coding: utf-8
"""
sme_schema.py
Generates Schema file for SME Common EDI from Business Semantic Model (BSM) CSV

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-05-18
Last Modified: 2025-10-10

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
import unicodedata

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
            DATE,
            root_term,
            remove_chars,
            encoding,
            annotation,
            trace,
            debug
        ):

        self.WS = "  "
        WS = self.WS
        self.version_date = "20250901"
        self.version_num = "4p3"

        self.bsm_file = bsm_file.replace('/', os.sep)
        self.bsm_file = file_path(self.bsm_file)
        if not self.bsm_file or not os.path.isfile(self.bsm_file):
            print(f'[INFO] No input Semantic file {self.bsm_file}.')
            sys.exit()

        self.REMOVE_CHARS = remove_chars
        self.encoding = encoding.strip() if encoding else 'utf-8-sig'
        # Set debug and trace flags, and file path separator
        self.root_element = self.normalize_text(root_term)
        # dir = os.path.dirname(__file__)
        self.schema_file = f'{self.root_element}_BSM_{DATE}.xsd'
        self.schema_file = file_path(self.schema_file)
        self.ram_schema_file = f'ReusableAggregateBusinessInformationEntity-sme_{self.version_num}_include.xsd'
        self.ram_schema_file = file_path(self.ram_schema_file)

        self.DATE = DATE
        self.ANNOTATION = annotation
        self.TRACE = trace
        self.DEBUG = debug

        self.class_id_map = {}
        self.object_class_dict = {}

        self.html = [
            '<!-- ====================================================================== -->',
            f'<!-- ===== {self.root_element} Schema Module {" " * (59 - len(f"{self.root_element} Schema Module "))}===== -->',
            '<!-- ====================================================================== -->',
            '<!--',
            'Schema agency:  ITCA',
            'Schema version: ver 4.3',
            'Schema date:    2025-09-01',
            '-->',
            '<xsd:schema',
            2*WS + f'targetNamespace="urn:un:unece:uncefact:data:standard:{self.root_element}:{self.version_num}" ',
            2*WS + 'xmlns:xsd="http://www.w3.org/2001/XMLSchema"',
            2*WS + 'xmlns:ccts="urn:un:unece:uncefact:documentation:standard:CoreComponentsTechnicalSpecification:2" ',
            2*WS + 'xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:34"',
            2*WS + 'xmlns:qdt="urn:un:unece:uncefact:data:standard:QualifiedDataType:34"',
            2*WS + f'xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:34"',
            2*WS + f'xmlns:rsm="urn:un:unece:uncefact:data:standard:{self.root_element}:{self.version_num}" ',
            2*WS + 'elementFormDefault="qualified" attributeFormDefault="unqualified" ',
            2*WS + f'version="{self.version_date}">',
            '<!-- ======================================================================= -->',
            '<!-- ===== Imports                                                     ===== -->',
            '<!-- ======================================================================= -->',
            '<!-- ======================================================================= -->',
            '<!-- ===== Import of Unqualified Data Type Schema Module               ===== -->',
            '<!-- ======================================================================= -->',
            WS + '<xsd:import namespace="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:34"',
            2*WS + 'schemaLocation="XMLSchemas-D23B/13DEC23/uncefact/data/standard/UnqualifiedDataType_34p0.xsd"/>',
            '<!-- ======================================================================= -->',
            '<!-- ===== Import of Qualified Data Type Schema Module                 ===== -->',
            '<!-- ======================================================================= -->',
            WS + '<xsd:import namespace="urn:un:unece:uncefact:data:standard:QualifiedDataType:34"',
            2*WS + 'schemaLocation="XMLSchemas-D23B/13DEC23/uncefact/data/standard/QualifiedDataType_34p0.xsd"/>',
            '<!-- ======================================================================= -->',
            '<!-- ===== Import of Reusable Aggregate Business Information Entity Schema Module ===== -->',
            '<!-- ======================================================================= -->',
            WS + f'<xsd:import namespace="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:34"',
            2*WS + f'schemaLocation="ReusableAggregateBusinessInformationEntity-sme_{self.version_num}_include.xsd"/>',
            '<!-- ======================================================================= -->',
            '<!-- ===== Element Declarations                                        ===== -->',
            '<!-- ======================================================================= -->'
        ]

        self.ram_html = [
            '<!-- ====================================================================== -->',
            f'<!-- ===== {self.root_element} Schema Module {" " * (59 - len(f"{self.root_element} Schema Module "))}===== -->',
            '<!-- ====================================================================== -->',
            '<!--',
            'Schema agency:  ITCA',
            'Schema version: ver 4.3',
            'Schema date:    2025-09-01',
            '-->',
            '<xsd:schema',
            2*WS + f'targetNamespace="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:34" ',
            2*WS + 'xmlns:xsd="http://www.w3.org/2001/XMLSchema"',
            2*WS + 'xmlns:ccts="urn:un:unece:uncefact:documentation:standard:CoreComponentsTechnicalSpecification:2" ',
            2*WS + 'xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:34"',
            2*WS + 'xmlns:qdt="urn:un:unece:uncefact:data:standard:QualifiedDataType:34"',
            2*WS + f'xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:34"',
            2*WS + 'elementFormDefault="qualified" attributeFormDefault="unqualified" ',
            2*WS + f'version="{self.version_date}">',
            '<!-- ======================================================================= -->',
            '<!-- ===== Imports                                                     ===== -->',
            '<!-- ======================================================================= -->',
            '<!-- ======================================================================= -->',
            '<!-- ===== Import of Unqualified Data Type Schema Module               ===== -->',
            '<!-- ======================================================================= -->',
            WS + '<xsd:import namespace="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:34"',
            2*WS + 'schemaLocation="XMLSchemas-D23B/13DEC23/uncefact/data/standard/UnqualifiedDataType_34p0.xsd"/>',
            '<!-- ======================================================================= -->',
            '<!-- ===== Import of Qualified Data Type Schema Module                 ===== -->',
            '<!-- ======================================================================= -->',
            WS + '<xsd:import namespace="urn:un:unece:uncefact:data:standard:QualifiedDataType:34"',
            2*WS + 'schemaLocation="XMLSchemas-D23B/13DEC23/uncefact/data/standard/QualifiedDataType_34p0.xsd"/>',
            '<!-- ======================================================================= -->',
            '<!-- ===== Include of Reusable Aggregate Business Information Entity Module ===== -->',
            '<!-- ======================================================================= -->',
            WS + '<xsd:include schemaLocation="XMLSchemas-D23B/13DEC23/uncefact/data/standard/ReusableAggregateBusinessInformationEntity_34p0.xsd"/>',
            '<!-- ======================================================================= -->',
            '<!-- ===== Type Declarations                                        ===== -->',
            '<!-- ======================================================================= -->'
        ]

    def print(self, message):
        if self.DEBUG:
            print(message)

    def debug_print(self, message):
        if self.DEBUG:
            print(f"[DEBUG] {message}")

    def error_print(self, message):
        if self.TRACE or self.DEBUG:
            print(f"[ERROR] {message}")

    def trace_print(self, message):
        if self.TRACE or self.DEBUG:
            print(f"[TRACE] {message}")

    def normalize_text(self, s):
        # 全角→半角・互換文字を標準化（＜Lin＞→<Lin> など）
        t = unicodedata.normalize('NFKC', s)
        t = re.sub(r"\s*\[[^\]]*\]", "", t)
        # ＜Lin＞（<Lin>）が含まれるか
        has_lin = "<Lin>" in t
        if has_lin:
            t = t.replace("<Lin>", "")  # まず除去
        # 空白と " ._/()-" を全部削除
        # \s は改行や全角空白も含む
        cleaned = re.sub(r"[.\s_/()\-]+", "", t)
        result = ("Line" + cleaned) if has_lin else cleaned
        return result

    # Utility function to update class term
    def update_class_term(self, row):
        unid = row["UNID"]
        property_type = row["property_type"]
        _type = row['property_type']
        class_term = self.normalize_text(row['class_term'])
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
        property_term = self.normalize_text(row['property_term'])
        if property_term:
            property_term = self.normalize_text(property_term)
            row["property_term"] = property_term
        associated_class = self.normalize_text(row['associated_class'])
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

    def annotation(self, unid, acronym, den, short_name, definition, label_sme, definition_sme, multiplicity, multiplicity_sme, base=0):
        if not self.ANNOTATION:
            return ""
        WS = "  "
        html = [
            WS*(base + 2) + '<xsd:annotation>',
            WS*(base + 3) + '<xsd:documentation xml:lang="en">'
        ]
        if unid:
            html.append(WS*(base + 4) + f'<ccts:UniqueID>{unid}</ccts:UniqueID>')
        if acronym:
            html.append(WS*(base + 4) + f'<ccts:Acronym>{acronym}</ccts:Acronym>')
        if den:
            html.append(WS*(base + 4) + f'<ccts:DictionaryEntryName>{den}</ccts:DictionaryEntryName>')
        html.append(WS*(base + 4) + f'<ccts:Version>{self.version_num.replace("p",".")}</ccts:Version>')
        if definition:
            # 改行文字を削除
            text = re.sub(r'[\r\n]+', '', definition)
            # 半角・全角スペースの連続を単一の半角スペースに変換
            text = re.sub(r'[ \u3000]+', ' ', text)
            text = text.strip()
            text = WS*(base + 4) + f'<ccts:Definition>{text}</ccts:Definition>'           
            html.append(text)
        if multiplicity:
            if re.match(r".*([01]\.\.[1n]).*", multiplicity):
                pass
            else:
                msg = f'"{den}"の多重度[{multiplicity}]不正'
                self.error_print(msg)
            html.append(WS*(base + 4) + f'<ccts:Cardinality>{multiplicity}</ccts:Cardinality>')
        if short_name:
            html.append(WS*(base + 4) + f'<ccts:Name>{short_name}</ccts:Name>')

        html += [
            WS*(base + 3) + '</xsd:documentation>',
            WS*(base + 3) + '<xsd:documentation xml:lang="ja">'
        ]

        if label_sme:
            html.append(WS*(base + 4) + f'<ccts:Name>{label_sme}</ccts:Name>')
        if definition_sme:
            # 改行文字を削除
            text = re.sub(r'[\r\n]+', '', definition_sme)
            # 半角・全角スペースの連続を単一の半角スペースに変換
            text = re.sub(r'[ \u3000]+', ' ', text)
            text = text.strip()
            text = WS*(base + 4) + f'<ccts:Definition>{text}</ccts:Definition>'
            html.append(text)
        if multiplicity_sme:
            if re.match(r".*([01]\.\.[1n]).*", multiplicity_sme):
                pass
            else:
                msg = f'"{den}"の多重度[{multiplicity_sme}]不正'
                self.error_print(msg)
            html.append(WS*(base + 4) + f'<ccts:Cardinality>{multiplicity_sme}</ccts:Cardinality>')

        html += [
            WS*(base + 3) + '</xsd:documentation>',
            WS*(base + 2) + '</xsd:annotation>'
        ]

        return html

    def schema(self):
        WS = "  "
        header = [
            "version",
            "sme_nr",
            "mbie_nr",
            "level",
            "property_type",
            "class_term",
            "sequence",
            "multiplicity",
            "multiplicity_sme",
            "identifier",
            "property_term",
            "representation_term",
            "code_list",
            "XML_datatype",
            "associated_class",
            "selector",
            "fixed_value",
            "label_sme",
            "label_csv",
            "definition_sme",
            "label_ja",
            "definition_ja",
            "UNID",
            "acronym",
            "DEN",
            "short_name",
            "definition",
            "element",
            "XML_element_name",
        ]
        """
        Read CSV file
        """
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

        """
        SMEInvoice
        """
        root_class = None
        properties = None
        asma_num = 0
        for key, data in self.object_class_dict.items():
            acronym = data["acronym"]
            unid = data["UNID"]
            den = data["DEN"]
            label_sme = data["label_sme"]
            short_name = data["short_name"]
            multiplicity = data["multiplicity"]
            multiplicity_sme = data["multiplicity_sme"]
            definition = data["definition"]
            definition_sme = data["definition_sme"]
            definition_sme =  re.sub(r'\s+', ' ', definition_sme).strip()
            """
            Schema header
            """
            self.print("\n".join(self.html))
            if "MA"==acronym:
                root_class = data["class_term"]
                element = data['element']
                properties = data["properties"]
                html = [
                    '<!-- ======================================================================= -->',
                    '<!-- ===== Root Element Declarations                                   ===== -->',
                    '<!-- ======================================================================= -->',
                    '<!-- ======================================================================= -->',
                    f'<!-- ===== {element} {" " * (66 - len(f"===== {element} "))}===== -->',
                    '<!-- ======================================================================= -->',
                    WS + f'<xsd:element name="{element}"  type="rsm:{element}Type">',
                ]
                self.print("\n".join(html))
                self.html += html
                # annotation
                if self.ANNOTATION:
                    html = self.annotation("CII", "RSM", den, short_name, definition, label_sme, definition_sme, multiplicity, multiplicity_sme, 0)
                    self.print("\n".join(html))
                    self.html += html
                html = [
                    WS + '</xsd:element>',
                    '<!-- ======================================================================= -->',
                    f'<!-- ===== {element}Type {" " * (66 - len(f"===== {element}Type "))}===== -->',
                    '<!-- ======================================================================= -->',
                    WS + f'<xsd:complexType name="{element}Type">',
                ]
                self.print("\n".join(html))
                self.html += html
                html = []
                if self.ANNOTATION:
                    html = self.annotation("CII-2", "MA", den, short_name, definition, label_sme, definition_sme, multiplicity, multiplicity_sme, 0)
                html += [2*WS + '<xsd:sequence>']
                self.print("\n".join(html))
                self.html += html
            else:
                element = data['class_term']
                if element!=root_class:
                    continue

        for _, v in properties.items():
            unid = v["UNID"]
            acronym = v["acronym"]
            den = v["DEN"]
            property_type = v["property_type"]
            element = v["element"]
            multiplicity = v["multiplicity"]
            VALID_multiplicity = True
            if re.match(r".*([01]\.\.[1n]).*", multiplicity):
                min = multiplicity[0]
                max = multiplicity[-1]
                if "n"==max:
                    max="unbounded"
            else:
                msg = f'"{den}"の多重度[{multiplicity}]不正'                
                self.error_print(msg)
                VALID_multiplicity = False
            m = ""
            if "1"!=min:
                m = f' minOccurs="{min}"'
            if "1"!=max:
                m += f' maxOccurs="{max}"'
            multiplicity_sme = v["multiplicity_sme"]
            property_term = v["property_term"]
            label_sme = v["label_sme"]
            short_name = v["short_name"]
            definition = v["definition"]
            definition_sme = v["definition_sme"]
            definition_sme =  re.sub(r'\s+', ' ', definition_sme).strip()
            if "Attribute"==property_type:
                name = v["XML_element_name"]
                data_type = v["XML_datatype"]
                associated_class = v["associated_class"]
                if name and data_type:
                    html = 3*WS + f'<xsd:element name="{name}" type="{data_type}"{m}>'
                    self.print(html)
                    self.html.append(html)
                else:
                    continue
            elif "Composition"==property_type:
                name = v["XML_element_name"]
                data_type = v["XML_datatype"]
                associated_class = v["associated_class"]
                if name and associated_class:                    
                    multiplicity = v["multiplicity"]
                    if VALID_multiplicity:
                        html = 3*WS + f'<xsd:element name="{name}" type="ram:{associated_class}_smeType"{m}>'
                    else:
                        html = 3*WS + f'<!-- {multiplicity} <xsd:element name="{name}" type="ram:{associated_class}_smeType"{m}> -->'
                    if self.ANNOTATION:
                        self.print(html)
                    self.html.append(html)
                else:
                    continue
            else:
                continue
            if self.ANNOTATION:
                asma_num += 1
                html = self.annotation(f'CII{str(asma_num).zfill(2)}', "ASMA", den, short_name, definition, label_sme, definition_sme, multiplicity, multiplicity_sme, 2)
                self.print("\n".join(html))
                self.html += html
                html = 3*WS + f'</xsd:element>'
                self.print(html)
                self.html.append(html)
            else:
                html = self.html[-1][:-1] + "/>"
                self.print(html)
                self.html[-1] = html


        html = [
            2*WS + '</xsd:sequence>',
            WS + '</xsd:complexType>',	
        ]
        self.print("\n".join(html))
        self.html += html

        # self.html.append('</xsd:schema>')
        html = '</xsd:schema>'
        self.print(html)
        self.html.append(html)

        with open(self.schema_file, 'w', encoding=self.encoding) as f:
            for item in self.html:
                f.write(item + '\n')

        self.trace_print(f"Output file {self.schema_file}")

        """
        Reusable Aggregate Business Entity
        """
        self.print("\n".join(self.ram_html))

        for key, data in self.object_class_dict.items():
            acronym = data["acronym"]
            unid = data["UNID"]
            den = data["DEN"]
            label_sme = data["label_sme"]
            short_name = data["short_name"]
            multiplicity = data["multiplicity"]
            multiplicity_sme = data["multiplicity_sme"]
            definition = data["definition"]
            definition_sme = data["definition_sme"]
            definition_sme =  re.sub(r'\s+', ' ', definition_sme).strip()           
            """
            Schema header
            """
            if "MA"!=acronym:
                element = data['class_term']
                if element==root_class:
                    continue
                base_type = data["XML_datatype"]
                html = [
                    '<!-- ======================================================================= -->',
                    f'<!-- ===== {element}_smeType {" " * (66 - len(f"===== {element}_smeType "))}===== -->',
                    '<!-- ======================================================================= -->',
                    WS + f'<xsd:complexType name="{element}_smeType">',
                    2*WS + f'<xsd:complexContent>',
                    3*WS + f'<xsd:restriction base="{base_type}">',
                ]
                self.print("\n".join(html))
                self.ram_html += html
                html = []
                if self.ANNOTATION:
                    html = self.annotation(unid, acronym, den, short_name, definition, label_sme, definition_sme, multiplicity, multiplicity_sme, 2)
                html += [4*WS + '<xsd:sequence>']
                self.print("\n".join(html))
                self.ram_html += html
            VALID_multiplicity = True
            for k, v in data["properties"].items():
                class_term = v["class_term"]
                if root_class==class_term:
                    continue
                unid = v["UNID"]
                acronym = v["acronym"]
                den = v["DEN"]
                property_type = v["property_type"]
                element = v["element"]
                multiplicity = v["multiplicity"]
                if re.match(r".*([01]\.\.[1n]).*", multiplicity):
                    min = multiplicity[0]
                    max = multiplicity[-1]
                    if "n"==max:
                        max="unbounded"
                else:
                    msg = f'"{den}"の多重度[{multiplicity}]不正'
                    self.error_print(msg)
                    VALID_multiplicity = False
                m = ""
                if "1"!=min:
                    m = f' minOccurs="{min}"'
                if "1"!=max:
                    m += f' maxOccurs="{max}"'
                m_sme = v["multiplicity_sme"]
                property_term = v["property_term"]
                label_sme = v["label_sme"]
                short_name = v["short_name"]
                definition = v["definition"]
                definition_sme = v["definition_sme"]
                definition_sme =  re.sub(r'\s+', ' ', definition_sme).strip()
                if "Attribute"==property_type:
                    name = v["XML_element_name"]
                    data_type = v["XML_datatype"]
                    associated_class = v["associated_class"]
                    if name and data_type:
                        html = 5*WS + f'<xsd:element name="{name}" type="{data_type}"{m}>'
                        if self.ANNOTATION:
                            self.print(html)
                        self.ram_html.append(html)
                    else:
                        continue
                elif "Composition"==property_type:
                    name = v["XML_element_name"]
                    data_type = v["XML_datatype"]
                    associated_class = v["associated_class"]
                    if name and associated_class:
                        if VALID_multiplicity:
                            html = 5*WS + f'<xsd:element name="{name}" type="ram:{associated_class}_smeType"{m}>'
                        else:
                            html = 5*WS + f'<!-- {multiplicity} <xsd:element name="{name}" type="ram:{associated_class}_smeType"{m}> -->'
                        if self.ANNOTATION:
                            self.print(html)
                        self.ram_html.append(html)
                    else:
                        continue
                else:
                    continue

                if not VALID_multiplicity:
                    continue

                if self.ANNOTATION:
                    html = self.annotation(unid, acronym, den, short_name, definition, label_sme, definition_sme, multiplicity, multiplicity_sme, 4)
                    self.print("\n".join(html))
                    self.ram_html += html
                    html = 5*WS + f'</xsd:element>'
                    self.print(html)
                    self.ram_html.append(html)
                else:
                    html = self.ram_html[-1][:-1] + "/>"
                    self.print(html)
                    self.ram_html[-1] = html

            if root_class==class_term:
                continue

            html = [
                4*WS + '</xsd:sequence>',
                3*WS + '</xsd:restriction>',
                2*WS + '</xsd:complexContent>',
                WS + '</xsd:complexType>',	
            ]
            self.print("\n".join(html))
            self.ram_html += html
        html = '</xsd:schema>'
        self.print(html)
        self.ram_html.append(html)

        with open(self.ram_schema_file, 'w', encoding=self.encoding) as f:
            for item in self.ram_html:
                f.write(item + '\n')

        self.trace_print(f"Output file {self.ram_schema_file}")

# Main function to execute the script
def main():
    # # Create the parser
    # parser = argparse.ArgumentParser(
    #     prog='sme_schema.py',
    #     usage='%(prog)s BSM_file -r Root class term -e encoding [options] ',
    #     description='Converts logical model to HMD with graph walk.'
    # )
    # parser.add_argument('BSM_file', metavar='BSM_file', type = str, help='Business semantic model file path')
    # # Allow multiple values with action='append' or nargs='+'
    # parser.add_argument("-r", "--root", help="Root class term for schema module to process.")
    # parser.add_argument('-e', '--encoding', required = False, default='utf-8-sig', help='File encoding, default is utf-8-sig')
    # parser.add_argument('-t', '--trace', required = False, action='store_true')
    # parser.add_argument('-d', '--debug', required = False, action='store_true')

    # args = parser.parse_args()

    BSM_File = "SME_common10-08_BSM.csv"
    root = "SMEConsolidatedSelfInvoice"
    encoding = 'utf-8-sig'
    DATE = "10-10"
    REMOVE_CHARS = " -._'"

    processor = SchemaModule(
        bsm_file = BSM_File,
        DATE = DATE,
        root_term = root,
        remove_chars = REMOVE_CHARS,
        encoding = encoding,
        annotation = True,
        trace = True,
        debug = True
    )

    processor.schema()

if __name__ == '__main__':
    main()
