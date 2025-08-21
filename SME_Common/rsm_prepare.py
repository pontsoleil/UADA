"""
analyseRSM.py
Generates Business Semantic Model (BSM) and Logical Hierarchical Model (LHM) CSV

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-07-29
Last Modified: 2025-0/-29

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

DATE = "07-30"
version = "January 2017"

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

def main():
    global TRACE, DEBUG
    """
    Read from the RSM BIEs CSV file

    Acronym, DEN, Definition, OccMin, OccMax
    """
    bsm_records = []
    lhm_records = []
    mbie_dict = {}
    bsm_dict = {}
    base_dir = "SME_Common"

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

    # def split_camel_case(text):
    #     if not text:
    #         return ""
    #     # 連続大文字（略語）とその直後の大文字小文字の区切りで分割
    #     pattern = r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])'
    #     splitted = re.split(pattern, text)
    #     return " ".join(splitted)

    # def remove_duplicates(word_list):
    #     seen = set()
    #     result = []
    #     for word in word_list:
    #         if word not in seen:
    #             seen.add(word)
    #             result.append(word)
    #     return result

    # def add_missing_prefix_words(prefix_word, name_word):
    #     prefix_list = [normalize_text(text) for text in prefix_word.split()]
    #     name_list = [normalize_text(text) for text in name_word.split()]
    #     # name_words に含まれていない prefix_words の単語を抽出
    #     missing = [word for word in remove_duplicates(prefix_list) if word not in remove_duplicates(name_list)]
    #     # それらを name_words の先頭に追加
    #     combined = missing + name_list
    #     return ' '.join(combined)

    # def get_name(data, path_list, level):
    #     sequence = data["sequence"]
    #     acronym = data["acronym"]
    #     den = data["DEN"]
    #     _1st_prefix = split_camel_case(path_list[0])
    #     _2nd_prefix = split_camel_case(path_list[1])
    #     _3rd_prefix = split_camel_case(path_list[2])
    #     _4th_prefix = split_camel_case(path_list[3])
    #     _5th_prefix = split_camel_case(path_list[4])
    #     _6th_prefix = split_camel_case(path_list[5])
    #     _1st_text = normalize_text(
    #         add_missing_prefix_words(_1st_prefix, den) if 1 == level else _1st_prefix
    #     )
    #     _2nd_text = normalize_text(
    #         add_missing_prefix_words(_2nd_prefix, den) if 2 == level else _2nd_prefix
    #     )
    #     _3rd_text = normalize_text(
    #         add_missing_prefix_words(
    #             add_missing_prefix_words(_2nd_prefix, _3rd_prefix), den
    #         )
    #         if 3 == level
    #         else _3rd_prefix
    #     )
    #     _4th_text = normalize_text(
    #         add_missing_prefix_words(
    #             add_missing_prefix_words(_3rd_prefix, _4th_prefix), den
    #         )
    #         if 4 == level
    #         else _4th_prefix
    #     )
    #     _5th_text = normalize_text(
    #         add_missing_prefix_words(
    #             add_missing_prefix_words(
    #                 add_missing_prefix_words(_3rd_prefix, _4th_prefix), _5th_prefix
    #             ),
    #             den,
    #         )
    #         if 5==level
    #         else ""
    #     )
    #     _6th_text = normalize_text(
    #         add_missing_prefix_words(
    #             add_missing_prefix_words(
    #                 add_missing_prefix_words(
    #                     add_missing_prefix_words(_3rd_prefix, _4th_prefix), _5th_prefix
    #                 ),
    #                 _6th_prefix,
    #             ),
    #             den,
    #         )
    #         if level > 5
    #         else ""
    #     )

    #     if 1==level:
    #         name = _1st_text
    #     else:
    #         if acronym in ["ASMA"]:
    #             if 2==level:
    #                 name = _3rd_text
    #             elif 3==level:
    #                 name = _4th_text
    #             elif 4==level:
    #                 name = _5th_text
    #             else:
    #                 name = _6th_text
    #         else:
    #             if 2==level:
    #                 name = _2nd_text
    #             elif 3==level:
    #                 name = _3rd_text
    #             elif 4==level:
    #                 name = _4th_text
    #             elif 5==level:
    #                 name = _5th_text
    #             else:
    #                 name = _6th_text
    #     if name.startswith("Agreement"):
    #         _name = name[9:]
    #     elif name.startswith("TransactionTradeLineItemTrade"):
    #         _name = name.replace("TransactionTradeLineItemTrade","Document")
    #     elif name.startswith("TradeTransactionTrade"):
    #         _name = name[21:]
    #     elif name.startswith("TransactionTradeSettlement"):
    #         _name = name[16:]
    #     elif name.startswith("TradeSettlement"):
    #         _name = name[15:]
    #     elif name.startswith("LineItemSettlementTrade"):
    #         _name = name.replace("LineItemSettlementTrade","Document")
    #     elif name.startswith("LineItemSettlement"):
    #         _name = name.replace("LineItemSettlement","Document")
    #     elif name.startswith("LineItemTrade"):
    #         _name = name.replace("LineItemTrade","Document")
    #     elif name.startswith("ItemTradeSettlement"):
    #         _name = name.replace("ItemTradeSettlement","Document")
    #     elif name.startswith("SubordinateLineItem"):
    #         _name = name.replace("SubordinateLineItem","Line")
    #     elif name.startswith("SubordinateLine"):
    #         _name = name.replace("SubordinateLine","Line")
    #     elif name.startswith("SubordinateTradeLineItem"):
    #         _name = name.replace("SubordinateTradeLineItem","Line")
    #     elif name.startswith("SubordinateDocumentTrade"):
    #         _name = name.replace("SubordinateDocumentTrade","Line")
    #     elif name.startswith("SubordinateDocumentFinancialAdjustmentTrade"):
    #         _name = name.replace("SubordinateDocumentFinancialAdjustmentTrade","LineFinancialAdjustment")
    #     elif name.startswith("SubordinateDocumentFinancialAdjustment"):
    #         _name = name.replace("SubordinateDocumentFinancialAdjustment","LineFinancialAdjustment")
    #     elif name.startswith("SubordinateDocument"):
    #         _name = name.replace("SubordinateDocument","Line")
    #     elif name.startswith("SubordinateItemTrade"):
    #         _name = name.replace("SubordinateItemTrade","Line")
    #     elif name.startswith("TransactionTradeLineItem"):
    #         _name = name.replace("TransactionTradeLineItem","Line")
    #     else:
    #         _name = name
    #     return _name

    """
    change, unid, acronym, DEN, Definition, Working_comments_and_instructions, Publication_comments, Object_Class_Term_Qualifier(s), Object_Class_Term, Property_Term_Qualifier(s), Property_Term, Datatype_Qualifier(s), Representation_Term, Qualified_Data_Type_UID, Associated_Object_Class_Term_Qualifier(s), Associated_Object_Class, Business_Term(s), Usage_Rule(s), Sequence_Number, Occurrence_Min, Occurrence_Max, Business_Process_Value, Business_Process_Meaning, Business_Process_Class.Schema, Product_Value, Product_Meaning, Product_Class.Schema, Industory_Value, Industory_Meaning, Industory_Class.Schema, Region_(Geo)_Value, Region_(Geo)_Meaning, Region_(Geo)_Class.Schema, Official_Constraints_Value, Official_Constraints_Meaning, Official_Constraints_Class.Schema, Role_Value, Role_Meaning, Role_Class.Schema, Supporting_Role_Value, Supporting_Role_Meaning, Supporting_Role_Class.Schema, System_Constraints_Value, System_Constraints_Meaning, System_Constraints_Class.Schema, "Facets To_restrict_the_set_of_values_of_Content_Component_or_Supplementary_Components", au, av, aw, ax, ay, az, ba, bb, bc, bd, be, bf, bg, bh, Example(s), BIE/CC/DT_Version, Ref_Library_Version, Submitter_Name, Ref_Component_UN_ID, Ref_CR_ID, Unique_submitter_ID, CR_Status_Date, CR_Status, Library_Maintenance_Comment, TDED, Submitted_Definition, Submitter_Comment, Submitted_DEN, Submission_Row_Number, Unique_CC/BIE_ID, CR_Storage_Date, Publication_Refs_--_Source, Persistent_Flag, cb, cc, Short_Name, ce
    """
    mbie_file = os.path.join(base_dir,"CCL 24A_21SEP24_MBIE.csv")
    with open(mbie_file, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)  # Uses first row as keys
        seq = 0
        for row in reader:
            acronym = row["acronym"]
            if "END"==acronym:
                break
            unid = row["unid"]
            den = row["DEN"]
            class_term = den[:den.index(".")]
            property_term = f'{row["Property_Term_Qualifier(s)"]} {row["Property_Term"]}'.strip()
            associated_class = f"{row['Associated_Object_Class_Term_Qualifier(s)']} {row['Associated_Object_Class']}".strip()
            acronym = row["acronym"]
            if "BBIE"==acronym:
                property_type = "Attribute"
                element = element_from_property(f'{property_term}. {row["Representation_Term"]}')
            elif "ASBIE"==acronym:
                property_type = "Composition"
                element = element_from_property(f'{property_term}. {associated_class}')
            else:
                property_type = "Class"
                element = element_from_class(class_term)
            if len(row["TDED"]) > 0:
                code_list = f'UNCL{row["TDED"]}'
            else:
                code_list = ""

            if acronym in ["BBIE", "ASBIE"]:
                occurrence_min = row["Occurrence_Min"]
                occurrence_max = row["Occurrence_Max"]
                if "unbounded"==occurrence_max:
                    occurrence_max = "n"
                multiplicity = f"{occurrence_min}..{occurrence_max}"
            else:
                multiplicity = ""
            mbie_dict[den] = {
                "seq": seq,
                "acronym": row["acronym"],
                "property_type": property_type,
                "class_term": class_term,
                "property_term": property_term,
                "representation_term": row["Representation_Term"],
                "code_list": code_list,
                "associated_class": associated_class,
                "element": element,
                "DEN": den,
                "multiplicity": multiplicity,
                "definition": row["Definition"],
                "TDED": row["TDED"],
                "short_name": row["Short_Name"],
                "UNID": unid,
            }
            seq += 1

    BIEs_file = os.path.join(base_dir,f"BIEs.csv")
    # fsm_file = os.path.join(base_dir,f"RSM_FSM.csv")
    # lhm_file = os.path.join(base_dir,f"RSM_LHM.csv")
    bsm_file = os.path.join(base_dir,f"RSM_BSM.csv")

    rsm_dict = {}
    """
    Acronym, DEN, Definition, OccMin, OccMax
    """
    rows = []
    class_terms = set()
    with open(BIEs_file, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)  # Uses first row as keys
        for row in reader:
            acronym = row["acronym"]
            if not acronym:
                continue
            elif "END"==acronym:
                break
            rows.append(row)
            den = row["DEN"]
            part = den.split(".")
            class_term = part[0]
            class_terms.add(class_term)

    seq = 0
    for row in rows:
        seq += 1
        property_term = representation_term = associated_class = ""
        acronym = row["acronym"]
        den = row["DEN"]
        part = [x.strip() for x in den.split(".")]
        class_term = part[0]
        if acronym in ["MA", "ABIE"]:
            rsm_dict[class_term] = {}
            rsm_dict[class_term]["properties"] = []
        elif acronym in ["ASMA", "ASBIE"]:
            if 3==len(part):
                property_term = part[1]
                associated_class = part[2]
            elif 2==len(part):
                associated_class = part[1]
            else:
                continue
        elif "BBIE"==acronym:
            property_term = part[1]
            representation_term = part[2]
        else:
            continue

        occurrence_min = row["Occurrence_Min"]
        occurrence_max = row["Occurrence_Max"]
        if "unbounded"==occurrence_max:
            occurrence_max = "n"
        if acronym in ["ASMA", "ASBIE", "BBIE"]:
            multiplicity = f"{occurrence_min}..{occurrence_max}"
        else:
            multiplicity = ""

        if "ASBIE"==acronym:
            if list(class_terms).index(associated_class) < 0:
                check = [x for x in class_terms if associated_class.endswith(x)]
                if len(check) > 0:
                    composite_class = check[0]

        definition = row["definition"]

        rsm_data = {
            "acronym": acronym,
            "class_term": class_term,
            "property_term": property_term,
            "representation_term": representation_term,
            "associated_class": associated_class,
            "multiplicity": multiplicity,
            "definition": definition,
            "DEN": den,
            "UNID": f'UNID{str(seq).zfill(4)}'
        }

        if acronym in ["MA", "ABIE"]:
            rsm_dict[class_term]["_data"] = rsm_data
        elif acronym in ["ASMA", "ASBIE", "BBIE"]:
            rsm_dict[class_term]["properties"].append(rsm_data)

    header = [
        "sequence",
        "level",
        "property_type",
        "identifier",
        "class_term",
        "property_term",
        "representation_term",
        "associated_class",
        "multiplicity",
        "definition",
        "acronym",
        "DEN",
        "version"
    ]

    bsm_records = []
    seq = 0
    for data in rsm_dict.values():
        seq += 1
        _data = data["_data"]
        bsm_record = {}
        for key in header:
            if key in _data:
                bsm_record[key] = _data[key]
        bsm_record["version"] = version
        bsm_record["sequence"] = str(seq)
        bsm_record["level"] = 1
        bsm_record["property_type"] = "Class"

        bsm_records.append(bsm_record)

        properties = data["properties"]
        for property in properties:
            seq += 1
            bsm_record = {}
            for key in header:
                if key in property:
                    bsm_record[key] = property[key]
            bsm_record["version"] = version
            bsm_record["sequence"] = str(seq)
            bsm_record["level"] = 2
            acronym = property["acronym"]
            if "BBIE"==acronym:
                bsm_record["property_type"] = "Attribute"
            elif acronym in ["ASMA", "ASBIE"]:
                bsm_record["property_type"] = "Composition"

            bsm_records.append(bsm_record)            

    with open(bsm_file, mode="w", newline="", encoding="utf-8-sig") as fsmfile:
        writer = csv.DictWriter(fsmfile, fieldnames=header)
        writer.writeheader()
        writer.writerows(bsm_records)
    trace_print(f'Wrote {bsm_file}')

    trace_print("END")

if __name__=="__main__":
    main()
