"""
sme_prepare.py
Generates Business Semantic Model (BSM) and Logical Hierarchical Model (LHM) CSV

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-05-18
Last Modified: 2025-08-16

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
import re
import math
import csv

DEBUG = True
TRACE = True

character_list = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

unid_map = {}

def debug_print(message):
    if DEBUG:
        print(f"[DEBUG] {message}")

def trace_print(message):
    if TRACE:
        print(f"[TRACE] {message}")

def file_path(pathname):
    _pathname = pathname.replace("/", os.sep)
    if os.sep == _pathname[0]:
        return _pathname
    dir = os.path.dirname(__file__)
    return os.path.join(dir, _pathname)

# def normalize_text(text):
#     REMOVE_CHARS = " -._"
#     # Replace "-", ".", and "_" with a space
#     replaced = text.translate(str.maketrans('', '', REMOVE_CHARS))
#     # Replace multiple spaces with a single space and trim leading/trailing spaces
#     normalized = re.sub(r'\s+', " ", replaced).strip()
#     return normalized
# def encode_base62(number):
#     # Characters used in base62 encoding (0–9, a–z, A–Z)
#     # Special case for 0
#     if number == 0:
#         return character_list[0]
#     result = ""
#     # Convert the number to base62 by repeated division
#     while number > 0:
#         number, remainder = divmod(number, 62)
#         result = character_list[remainder] + result  # Prepend corresponding character
#     return result

# def decode_base62(encoded):
#     # Characters used in base62 encoding
#     base = 62
#     result = 0
#     # Convert base62 string back to a decimal number
#     for char in encoded:
#         result = result * base + character_list.index(char)
#     return result

# def revise_unid(acronym, unid):
#     if acronym in ["MA", "ABIE"]:
#         if unid[2:].isdigit():
#             num = int(unid[3:])
#             encoded = encode_base62(num)
#             class_unid = unid[:2] + encoded
#         else:
#             class_unid = unid
#         _unid = class_unid
#         suffix_num = 0
#     else:
#         suffix_num += 1
#         _unid = f"{class_unid}_{str(suffix_num).zfill(2)}"
#     return _unid, suffix_num

def main():
    global TRACE, DEBUG

    bsm_records = []
    lhm_records = []
    mbie_dict = {}
    bsm_dict = {}
    base_dir = "SME_Common"

    def get_den(row):
        den = None
        l = None
        if row["name1"].strip():
            l = 1
            den = row["name1"].strip()
        elif row["name2"].strip():
            l = 2
            den = row["name2"].strip()
        elif row["name3"].strip():
            l = 3
            den = row["name3"].strip()
        elif row["name4"].strip():
            l = 4
            den = row["name4"].strip()
        elif row["name5"].strip():
            l = 5
            den = row["name5"].strip()
        elif row["name6"].strip():
            l = 6
            den = row["name6"].strip()
        elif row["name7"].strip():
            l = 7
            den = row["name7"].strip()
        elif row["name8"].strip():
            l = 8
            den = row["name8"].strip()
        elif row["name9"].strip():
            l = 9
            den = row["name9"].strip()
        elif row["name10"].strip():
            l = 10
            den = row["name10"].strip()
        elif row["name11"].strip():
            l = 11
            den = row["name11"].strip()
        elif row["name12"].strip():
            l = 12
            den = row["name12"].strip()
        elif row["name13"].strip():
            l = 13
            den = row["name13"].strip()
        elif row["name14"].strip():
            l = 14
            den = row["name14"].strip()
        return l, den

    def normalize_text(text):
        # remove_words = "(CIILB_|CIIL_|CIIH_|CI_|Applicable|Defined|Specified|Supply Chain|Additional|Including|Included|Processing|Details)"
        remove_chars = " ._"
        # _text = re.sub(remove_words, "", text).translate(
        #     str.maketrans("", "", remove_chars)
        # )
        _text = text.translate(
            str.maketrans("", "", remove_chars)
        )
        if _text.endswith("IdentificationIdentifier"):
            _text = _text.replace("IdentificationIdentifier", "ID")
        elif _text.endswith("IdentificationID"):
            _text = _text.replace("IdentificationID", "ID")        
        elif _text.endswith("Identifier"):
            _text = _text.replace("Identifier", "ID")
        elif _text.endswith("NameText"):
            _text = _text.replace("NameText", "Name")
        return _text

    def element_from_class(class_term):
        return normalize_text(class_term)

    def element_from_property(property):
        return normalize_text(property)

    def split_camel_case(text):
        if not text:
            return ""
        # 連続大文字（略語）とその直後の大文字小文字の区切りで分割
        pattern = r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])'
        splitted = re.split(pattern, text)
        return " ".join(splitted)

    def remove_duplicates(word_list):
        seen = set()
        result = []
        for word in word_list:
            if word not in seen:
                seen.add(word)
                result.append(word)
        return result

    def add_missing_prefix_words(prefix_word, name_word):
        prefix_list = [normalize_text(text) for text in prefix_word.split()]
        name_list = [normalize_text(text) for text in name_word.split()]
        # name_words に含まれていない prefix_words の単語を抽出
        missing = [word for word in remove_duplicates(prefix_list) if word not in remove_duplicates(name_list)]
        # それらを name_words の先頭に追加
        combined = missing + name_list
        return ' '.join(combined)

    def get_name(data, path_list, level):
        # sequence = data["sequence"]
        acronym = data["acronym"]
        den = data["DEN"]

        _1st_prefix = split_camel_case(path_list[0])
        _2nd_prefix = split_camel_case(path_list[1])
        _3rd_prefix = split_camel_case(path_list[2])
        _4th_prefix = split_camel_case(path_list[3])
        _5th_prefix = split_camel_case(path_list[4])
        _6th_prefix = split_camel_case(path_list[5])

        _1st_text = normalize_text(
            add_missing_prefix_words(_1st_prefix, den) if 1 == level else _1st_prefix
        )
        _2nd_text = normalize_text(
            add_missing_prefix_words(_2nd_prefix, den) if 2 == level else _2nd_prefix
        )
        _3rd_text = normalize_text(
            add_missing_prefix_words(
                add_missing_prefix_words(_2nd_prefix, _3rd_prefix), den
            )
            if 3 == level
            else _3rd_prefix
        )
        _4th_text = normalize_text(
            add_missing_prefix_words(
                add_missing_prefix_words(_3rd_prefix, _4th_prefix), den
            )
            if 4 == level
            else _4th_prefix
        )
        _5th_text = normalize_text(
            add_missing_prefix_words(
                add_missing_prefix_words(
                    add_missing_prefix_words(_3rd_prefix, _4th_prefix), _5th_prefix
                ),
                den,
            )
            if 5==level
            else ""
        )
        _6th_text = normalize_text(
            add_missing_prefix_words(
                add_missing_prefix_words(
                    add_missing_prefix_words(
                        add_missing_prefix_words(_3rd_prefix, _4th_prefix), _5th_prefix
                    ),
                    _6th_prefix,
                ),
                den,
            )
            if level > 5
            else ""
        )

        if 1==level:
            name = _1st_text
        else:
            if acronym in ["ASMA"]:
                if 2==level:
                    name = _3rd_text
                elif 3==level:
                    name = _4th_text
                elif 4==level:
                    name = _5th_text
                else:
                    name = _6th_text
            else:
                if 2==level:
                    name = _2nd_text
                elif 3==level:
                    name = _3rd_text
                elif 4==level:
                    name = _4th_text
                elif 5==level:
                    name = _5th_text
                else:
                    name = _6th_text

        if name.startswith("Agreement"):
            _name = name[9:]
        elif name.startswith("TransactionTradeLineItemTrade"):
            _name = name.replace("TransactionTradeLineItemTrade","Document")
        elif name.startswith("TradeTransactionTrade"):
            _name = name[21:]
        elif name.startswith("TransactionTradeSettlement"):
            _name = name[16:]
        elif name.startswith("TradeSettlement"):
            _name = name[15:]
        elif name.startswith("LineItemSettlementTrade"):
            _name = name.replace("LineItemSettlementTrade","Document")
        elif name.startswith("LineItemSettlement"):
            _name = name.replace("LineItemSettlement","Document")
        elif name.startswith("LineItemTrade"):
            _name = name.replace("LineItemTrade","Document")
        elif name.startswith("ItemTradeSettlement"):
            _name = name.replace("ItemTradeSettlement","Document")
        elif name.startswith("SubordinateLineItem"):
            _name = name.replace("SubordinateLineItem","Line")
        elif name.startswith("SubordinateLine"):
            _name = name.replace("SubordinateLine","Line")
        elif name.startswith("SubordinateTradeLineItem"):
            _name = name.replace("SubordinateTradeLineItem","Line")
        elif name.startswith("SubordinateDocumentTrade"):
            _name = name.replace("SubordinateDocumentTrade","Line")
        elif name.startswith("SubordinateDocumentFinancialAdjustmentTrade"):
            _name = name.replace("SubordinateDocumentFinancialAdjustmentTrade","LineFinancialAdjustment")
        elif name.startswith("SubordinateDocumentFinancialAdjustment"):
            _name = name.replace("SubordinateDocumentFinancialAdjustment","LineFinancialAdjustment")
        elif name.startswith("SubordinateDocument"):
            _name = name.replace("SubordinateDocument","Line")
        elif name.startswith("SubordinateItemTrade"):
            _name = name.replace("SubordinateItemTrade","Line")
        elif name.startswith("TransactionTradeLineItem"):
            _name = name.replace("TransactionTradeLineItem","Line")
        else:
            _name = name
        return _name

    # mbie_file = os.path.join(base_dir,"CCL 24A_21SEP24_MBIE.csv")
    mbie_file = os.path.join(base_dir,"MBIEs24A.csv")
    remove_chars = r"[()\[\] ]"  # regex class of characters to remove
    # ["Nr", "UNID", "Acronym", "DEN", "Definition", "Publication comments", "Object Class Term Qualifier(s)", "Object Class Term", "Property Term Qualifier(s)", "Property Term", "Datatype Qualifier(s)", "Representation Term", "Qualified Data Type UID", "Associated Object Class Term Qualifier(s)", "Associated Object Class", "Business Term(s)", "Usage Rule(s)", "Sequence Number", "Occurrence Min", "Occurrence Max", "Context Categories", "Example(s)", "Version", "Ref Library Version", "Submitter Name", "Ref Component UN ID", "Unique submitter ID", "CR Status Date", "CR Status", "Library Maintenance Comment", "TDED", "Submitted Definition", "Submitter Comment", "Submitted DEN", "Publication Refs -- Source", "Short Name"]
    with open(mbie_file, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)  # Uses first row as keys
        for row in reader:
            acronym = row["Acronym"]
            if "END"==acronym:
                break

            nr = row["Nr"]
            nr = int(nr) if nr.isdigit() else 0
            sequence = row["Sequence Number"]
            sequence = int(sequence) if sequence.isdigit() else 0

            den = row["DEN"]
            class_term_qualifier = row["Object Class Term Qualifier(s)"].strip()
            class_term = row["Object Class Term"].strip()
            if class_term_qualifier:
                class_term = f'{class_term_qualifier}_ {class_term}'
            property_term_qualifier = row["Property Term Qualifier(s)"].strip()
            property_term = row["Property Term"].strip()
            if property_term_qualifier:
                property_term = f'{property_term_qualifier}_ {property_term}'
            datatype_qualifier = row["Datatype Qualifier(s)"].strip()
            representation_term = row["Representation Term"].strip()
            if datatype_qualifier:
                representation_term = f'{datatype_qualifier}_ {representation_term}'
            associated_class_qualifier = row['Associated Object Class Term Qualifier(s)'].strip()
            associated_class_term = row['Associated Object Class'].strip()
            if associated_class_qualifier:
                associated_class_term = f"{associated_class_qualifier}_ {associated_class_term}"

            multiplicity = ""
            occurence_min = row["Occurrence Min"]
            occurence_max = row["Occurrence Max"]            
            if "unbounded"==occurence_max:
                occurence_max = "n"
            if occurence_min and occurence_max:
                multiplicity = f"{occurence_min}..{occurence_max}"

            if "BBIE"==acronym:
                property_type = "Attribute"
                element = element_from_property(f'{property_term} {row["Representation Term"].strip()}')
            elif "ASBIE"==acronym:
                property_type = "Composition"
                element = element_from_property(f'{property_term} {row["Associated Object Class"].strip()}')
            else:
                property_type = "Class"
                element = element_from_class(class_term)

            code_list = ""
            if len(row["TDED"]) > 0:
                tded = re.sub(remove_chars, "", row["TDED"])
                code_list = f'UNCL{tded}'

            data = {
                "mbie_nr": nr,
                "acronym": acronym,
                "property_type": property_type,
                "class_term": class_term,
                "property_term": property_term,
                "representation_term": representation_term,
                "code_list": code_list,
                "associated_class": associated_class_term,
                "element": element,
                "DEN": den,
                "sequence": sequence,
                "multiplicity": multiplicity,
                "definition": row["Definition"],
                "short_name": row["Short Name"],
                "UNID": row["UNID"]
            }
            mbie_dict[den] = data

    DATE = "08-10"
    in_file = os.path.join(base_dir,f"sme_common{DATE}.csv")

    DATE = "08-18"
    fsm_file = os.path.join(base_dir,f"SME_common{DATE}_FSM.csv")
    bsm_file = os.path.join(base_dir,f"SME_common{DATE}_BSM.csv")
    lhm_file = os.path.join(base_dir,f"SME_common{DATE}_LHM.csv")

    # 08-05 nr,category,UNID,acronym,name1,name2,name3,name4,name5,name6,name7,name8,name9,name10,name11,name12,name13,name14,label_local,definition_local,multiplicity,fixed_value,version,code_list,issueing_agency,input_method,input_value,selfbilling,selfbilling_details,withholding_tax,selfbilling_statement,journal_entry,v1,AH,JP-PINT_ID,business_term,JP-PINT_card,,
    # 08-10 nr,category,UNID,acronym,name1,name2,name3,name4,name5,name6,name7,name8,name9,name10,name11,name12,name13,name14,label_local,definition_local,multiplicity,fixed_value,version,code_list,issueing_agency,input_method,input_value,example,Consolidated_Invoice,Revised_ Consolidated_Invoice,JP-PINT_Mapping,AF,JP-PINT_ID,business_term,JP-PINT_card
    with open(in_file, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)  # Uses first row as keys
        PATH_LENGTH = 15
        path_list = [None]*PATH_LENGTH

        for row in reader:
            acronym = row["acronym"]
            if not acronym or "SC"==acronym:
                continue
            elif "END"==acronym:
                break

            lhm_data = {
                "version": "",
                "sme_nr": "",
                "mbie_nr": "",
                "level": "",
                "type": "",
                "identifier": "",
                "UNID": "",
                "acronym": "",
                "label_local": "",
                "multiplicity": "",
                "class_term": "",
                "property_term": "",
                "representation_term": "",
                "associated_class": "",
                "definition_local": "",
                "code_list": "",
                "attribute": "",
                "DEN": "",
                "definition": "",
                "short_name": "",
                "element": "",
                "xpath": ""
            }

            for key in lhm_data.keys():
                if key in row:
                    lhm_data[key] = row[key].strip()
            nr = row["nr"]
            lhm_data["sme_nr"] = int(nr) if nr.isdigit() else 0

            lvl, den = get_den(row)

            level = math.floor((2 + lvl)/2)
            lhm_data["level"] = level

            lhm_data["DEN"] = den
            lhm_data["multiplicity_SME"] = row["multiplicity"].strip()
            lhm_data["multiplicity"] = ""

            property_term = ""
            representation_term = ""
            associated_class = ""

            if "." in den:
                parts = den.split(".")
                class_term = parts[0].strip()
                if len(parts) > 1:
                    if "BBIE"==acronym:
                        property_term = parts[1].strip()
                        representation_term = parts[2].strip()
                    elif "ASBIE"==acronym:
                        property_term = parts[1].strip()
                        associated_class = parts[2].strip()
            else:
                class_term = den

            lhm_data["class_term"] = class_term
            lhm_data["property_term"] = property_term
            lhm_data["representation_term"] = representation_term
            lhm_data["associated_class"] = associated_class
            lhm_data["mbie_nr"] = 0
            lhm_data["sequence"] = 0

            if den and den in mbie_dict:
                mbie_data = mbie_dict[den]
                if mbie_data:
                    lhm_data["mbie_nr"] = mbie_data["mbie_nr"]
                    lhm_data["sequence"] = mbie_data["sequence"]
                    lhm_data["multiplicity"] = mbie_data["multiplicity"]
                    lhm_data["definition"] = mbie_data["definition"]
                    lhm_data["short_name"] = mbie_data["short_name"]

            if "MA"==acronym:
                lhm_data["type"] = "C"
                lhm_data["level"] = 0
                element = element_from_class(class_term)
                lhm_data["element"] = element
                xpath = f'/{element}'
                lhm_data["xpath"] = xpath
                path_list[0] = element
            elif "ASMA"==acronym:
                lhm_data["type"] = "C"
                lhm_data["level"] = 1
                element = element_from_class(class_term)
                lhm_data["element"] = element
                path_list[1] = element
                xpath = f'/{path_list[0]}/{path_list[1]}'
                lhm_data["xpath"] = xpath
            elif "BBIE"==acronym:
                lhm_data["type"] = "A"
                lhm_data["property_term"] = property_term
                lhm_data["representation_term"] = representation_term
                if "Identifier"==lhm_data["representation_term"] and "1..1"==lhm_data["multiplicity_SME"]:
                    lhm_data["identifier"] = "PK"
                element = element_from_property(f'{property_term}. {representation_term}')
                if element.endswith("IdentificationIdentifier"):
                    element = element.replace("IdentificationIdentifier", "ID")
                elif element.endswith("Identifier"):
                    element = element.replace("Identifier", "ID")
                elif element.endswith("Text"):
                    element = element.replace("Text", "")
                lhm_data["element"] = element
                path_list[level] = element
                xpath = f'/{path_list[0]}'
                for i in range(1,1+level):
                    xpath += f'/{path_list[i]}'
                lhm_data["xpath"] = xpath
            elif "ASBIE"==acronym:
                lhm_data["type"] = "C"
                lhm_data["property_term"] = property_term
                lhm_data["associated_class"] = associated_class
                element = element_from_property(f'{property_term}. {associated_class}')
                lhm_data["element"] = element
                path_list[level] = element
                xpath = f"/{path_list[0]}"
                for i in range(1,1+level):
                    xpath += f'/{path_list[i]}'
                lhm_data["xpath"] = xpath
            elif "ABIE"==acronym:
                element = element_from_class(class_term)
                lhm_data["element"] = element

            name = get_name(lhm_data, path_list, level)
            remove_words = "(CIILB|CIIL|CIIH|CII|CI|Included|Specified|Trade|SupplyChain|Applicable|Agreement|Settlement|Party|Defined|Additional|Including|Processing)"
            remove_chars = " ._"
            text = name.translate(
                str.maketrans("", "", remove_chars)
            )
            _text = re.sub(remove_words, "", text).translate(
                str.maketrans("", "", remove_chars)
            )
            _text = _text.replace("UniversalCommunication","")
            _text = _text.replace("LineItem","Document")
            _text = _text.replace("SubordinateLine","Line")
            _text = _text.replace("ReferenceReferenced","Reference")
            lhm_data["name"] = _text

            if "ABIE"!=acronym:
                lhm_records.append(lhm_data)

            bsm_data = lhm_data.copy()
            if "MA"==acronym and 1==level:
                root = class_term
                bsm_data["property_type"] = "Class"
                bsm_data["level"] = 1
                bsm_data["multiplicity_SME"] = ""
                bsm_dict[root] = bsm_data
                if "properties" not in bsm_dict[root]:
                    bsm_dict[root]["properties"] = {}
            elif "ASMA"==acronym and 1==level:
                bsm_data["property_type"] = "Composition"
                bsm_data["level"] = 2
                bsm_data["associated_class"] = class_term
                bsm_data["class_term"] = root
                bsm_dict[root]["properties"][class_term] = bsm_data
                _bsm_data = lhm_data.copy()
                _bsm_data["property_type"] = "Class"
                _bsm_data["level"] = 1
                _bsm_data["multiplicity_SME"] = ""
                bsm_dict[class_term] = _bsm_data
                if "properties" not in bsm_dict[class_term]:
                    bsm_dict[class_term]["properties"] = {}
            elif "ABIE"==acronym:
                bsm_data["property_type"] = "Class"
                bsm_data["level"] = 1
                bsm_data["multiplicity_SME"] = ""
                if class_term not in bsm_dict:
                    bsm_dict[class_term] = bsm_data
                if "properties" not in bsm_dict[class_term]:
                    bsm_dict[class_term]["properties"] = {}
                for k,v in bsm_dict[class_term]["properties"].items():
                    if k in bsm_data:
                        if k not in bsm_dict[class_term]["properties"]:
                            bsm_dict[class_term]["properties"][k] = bsm_data[k]
                        elif v != bsm_data[k]:
                            debug_print(f'** {class_term}["{k}"] hass different value old:{bsm_dict[class_term][k]} new:{bsm_data[k]}')
            elif "BBIE"==acronym:
                bsm_data["property_type"] = "Attribute"
                bsm_data["level"] = 2
                bsm_data["property_term"] = property_term
                bsm_data["representation_term"] = representation_term
                attribute = f'{property_term}. {representation_term}'
                bsm_data["element"] = normalize_text(attribute)
                if attribute not in bsm_dict[class_term]["properties"]:
                    bsm_dict[class_term]["properties"][attribute] = bsm_data
                else:
                    for k,v in bsm_dict[class_term]["properties"][attribute].items():
                        if k!="sme_nr" and k in bsm_data and v!=bsm_data[k]:
                            debug_print(f'** {class_term}["properties"]["{attribute}"]["{k}]:{v} differs from {bsm_data[k]}')
            elif "ASBIE"==acronym:
                bsm_data["property_type"] = "Composition"
                bsm_data["level"] = 2
                bsm_data["property_term"] = property_term
                bsm_data["associated_class"] = associated_class
                association = f'{property_term}. {associated_class}'
                bsm_data["element"] = normalize_text(association)
                bsm_dict[class_term]["properties"][association] = bsm_data

            debug_print(f'{bsm_data["sme_nr"]} level:{bsm_data["level"]} {bsm_data["property_type"]} "{bsm_data["DEN"]}" [{bsm_data["multiplicity"]}] [{bsm_data["multiplicity_SME"]}]\t"{bsm_data["label_local"]}"')

    fsm_records = []
    for bsm_den, data in bsm_dict.items():
        bsm_properties = data["properties"]
        fsm_records.append(bsm_dict[bsm_den])
        debug_print(f'fsm_records append {bsm_den}')

        used_dens = []
        for bsm_data in bsm_properties.values():
            acronym = bsm_data["acronym"]
            unid = bsm_data["UNID"]
            den_property = bsm_data["DEN"]
            used_dens.append(den_property)
            multiplicity = bsm_data["multiplicity"]
            multiplicity_mbie = ""
            if den_property in mbie_dict:
                mbie_data = mbie_dict[den_property]
                multiplicity_mbie = mbie_data["multiplicity"]
                if multiplicity_mbie!=multiplicity:
                    print(f"[INFO] {unid} {den_property} has modified multiplicity {multiplicity} CCL defined {multiplicity_mbie}.")    
            else: # MBIEs24A 定義表に未定義
                multiplicity = "Not defined in D24A"
                bsm_data["multiplicity"] = multiplicity
            fsm_records.append(bsm_data)
            debug_print(f'fsm_records append {den_property} SME:{multiplicity} MBIE:{multiplicity_mbie}')
        
        mbie_properties = [
            (den, data)
            for den, data in mbie_dict.items()
            if den.startswith(bsm_den) and data["acronym"] in ["BBIE", "ASBIE"]
        ]
        for mbie_den, mbie_data in mbie_properties:
            if mbie_den not in used_dens:
                acronym = mbie_data["acronym"]
                multiplicity_mbie = mbie_data["multiplicity"]
                if acronym not in ["MA","ASMA","ABIE"] and mbie_den not in bsm_properties:
                    mbie_data["multiplicity"] = multiplicity_mbie
                    if multiplicity_mbie and "1"==multiplicity_mbie[0]: # 必須要素は削除不可
                        mbie_data["multiplicity_SME"] = f"Cannot remove {multiplicity_mbie}"
                    else:
                        mbie_data["multiplicity_SME"] = "0..0"
                    fsm_records.append(mbie_data)
                    debug_print(f'fsm_records append {mbie_den} SME:{ mbie_data["multiplicity_SME"]} MBIE:{multiplicity_mbie}')

    bsm_records = []
    for bsm_den,data in bsm_dict.items():
        bsm_properties = data["properties"]
        bsm_records.append(data)
        debug_print(f'bsm_records append {bsm_den}')

        sorted_items = sorted(
            ((name, property_data) for name, property_data in bsm_properties.items()),
            key=lambda x: x[1]["mbie_nr"],
        )

        used_dens = []
        for _, bsm_data in sorted_items:
            acronym = bsm_data["acronym"]
            unid = bsm_data["UNID"]
            den_property = bsm_data["DEN"]
            used_dens.append(den_property)
            multiplicity = bsm_data["multiplicity"]
            multiplicity_mbie = ""
            if den_property in mbie_dict:
                mbie_data = mbie_dict[den_property]
                multiplicity_mbie = mbie_data["multiplicity"]
                if multiplicity_mbie!=multiplicity:
                    print(f"[INFO] {unid} {den_property} has modified multiplicity {multiplicity} CCL defined {multiplicity_mbie}.")    
            else: # MBIEs24A 定義表に未定義
                multiplicity = "Not defined in D24A"
                bsm_data["multiplicity"] = multiplicity
            bsm_records.append(bsm_data)
            debug_print(f'bsm_records append {den_property} SME:{multiplicity} MBIE:{multiplicity_mbie}')

        mbie_properties = [
            (den, data)
            for den, data in mbie_dict.items()
            if den.startswith(bsm_den) and data["acronym"] in ["BBIE", "ASBIE"]
        ]
        for mbie_den, mbie_data in mbie_properties:
            if mbie_den not in used_dens:
                acronym = mbie_data["acronym"]
                multiplicity_mbie = mbie_data["multiplicity"]
                if acronym not in ["MA","ASMA","ABIE"] and mbie_den not in bsm_properties:
                    mbie_data["multiplicity"] = multiplicity_mbie
                    if multiplicity_mbie and "1"==multiplicity_mbie[0]: # 必須要素は削除不可
                        mbie_data["multiplicity_SME"] = f"Cannot remove {multiplicity_mbie}"
                    else:
                        mbie_data["multiplicity_SME"] = "0..0"
                    bsm_records.append(mbie_data)
                    debug_print(f'bsm_records append {mbie_den} SME:{ mbie_data["multiplicity_SME"]} MBIE:{multiplicity_mbie}')

    # Write to a CSV file
    fsm_field_names = [
        "version",
        "sme_nr",
        "mbie_nr",
        "level",
        "property_type",
        "class_term",
        "sequence",
        "identifier",
        "property_term",
        "multiplicity",
        "multiplicity_SME",
        "representation_term",
        "code_list",
        "attribute",
        "associated_class",
        "label_local",
        "definition_local",
        "UNID",
        "acronym",
        "DEN",
        "definition",
        "short_name",
        "name",
        "element",
        "xpath",
    ]
    fsm_records_ = [
        {k: v for k, v in record.items() if k in fsm_field_names}
        for record in fsm_records
    ]
    _fsm_records = sorted(
        fsm_records_,
        key=lambda r: (r.get("class_term", ""), int(r.get("mbie_nr", 0) or 0))
    )
    with open(fsm_file, mode="w", newline="", encoding="utf-8-sig") as fsmfile:
        writer = csv.DictWriter(fsmfile, fieldnames=fsm_field_names)
        writer.writeheader()
        writer.writerows(_fsm_records)

    trace_print(f'Wrote {fsm_file}')

    bsm_field_names = [
        "version",
        "sme_nr",
        "mbie_nr",
        "level",
        "property_type",
        "class_term",
        "sequence",
        "identifier",
        "property_term",
        "multiplicity",
        "multiplicity_SME",        
        "representation_term",
        "code_list",
        "attribute",        
        "associated_class",
        "label_local",
        "definition_local",
        "UNID",
        "acronym",
        "DEN",
        "definition",
        "short_name",
        "name",
        "element",
        "xpath",
    ]
    bsm_records = [
        {k: v for k, v in record.items() if k in bsm_field_names}
        for record in bsm_records
    ]
    with open(bsm_file, mode="w", newline="", encoding="utf-8-sig") as bsmfile:
        writer = csv.DictWriter(bsmfile, fieldnames=bsm_field_names)
        writer.writeheader()
        writer.writerows(bsm_records)

    trace_print(f'Wrote {bsm_file}')

    lhm_field_names = [
        "version",
        "sme_nr",
        "mbie_nr",
        "level",
        "type",
        "label_local",
        "multiplicity",
        "multiplicity_SME",
        "class_term",
        "sequence",
        "identifier",
        "property_term",
        "representation_term",
        "code_list",
        "attribute",
        "associated_class",
        "definition_local",
        "UNID",
        "acronym",
        "DEN",
        "definition",
        "short_name",
        "name",
        "element",
        "xpath",
    ]
    lhm_records = [
        {k: v for k, v in record.items() if k in lhm_field_names}
        for record in lhm_records
    ]
    with open(lhm_file, mode="w", newline="", encoding="utf-8-sig") as lhmfile:
        writer = csv.DictWriter(lhmfile, fieldnames=lhm_field_names)
        writer.writeheader()
        writer.writerows(lhm_records)

    trace_print(f'Wrote {lhm_file}')

    trace_print("END")

if __name__=="__main__":
    main()
