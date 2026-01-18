"""
sme_prepare.py
Generates Business Semantic Model (BSM) and Logical Hierarchical Model (LHM) CSV

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-05-18
Last Modified: 2025-10-20

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
"""
https://vocabulary.uncefact.org/code-lists
https://service.unece.org/trade/untdid/d23a/tred/tredxxxx.htm
"""
import os
import re, unicodedata
import csv
import copy
from typing import Any, Mapping

DEBUG = True
TRACE = True
SME_COMMON = True
DNM = False

character_list = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

base_dir = "SME_Common"
unid_map = {}

sme_records = []
sme_dict = {}
bsm_records = []
lhm_records = []
lhm_class_dict = {}
lhm_balance_conf_records = []

mbie_dict_den = {}
mbie_dict = {}
mbie_translate_ja = {}
abie_mapping = {}
abie_mapping_den = {}
bsm_dict = {}
class_id_map = {}
qdt_dict = {}
tded_dict = {}
object_class_dict = {}

current_multiplicity = None
LIFO_list = None
LHM_model = None

path_list = [""]

def debug_print(message):
    if DEBUG:
        print(f"[DEBUG] {message}")

def error_print(message):
    if DEBUG:
        print(f"[ERROR] {message}")

def trace_print(message):
    if TRACE:
        print(f"[TRACE] {message}")

def file_path(pathname):
    _pathname = pathname.replace("/", os.sep)
    if os.sep == _pathname[0]:
        return _pathname
    dir = os.path.dirname(__file__)
    return os.path.join(dir, _pathname)

def as_int(x, default=0):
    try:
        return int(x)
    except (TypeError, ValueError):
        return default

def as_float(x, default=0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default

def get_den(row):
    den = None
    l = None
    if row.get("name1","").strip():
        l = 1
        den = row.get("name1","").strip()
    elif row.get("name2","").strip():
        l = 2
        den = row.get("name2","").strip()
    elif row.get("name3","").strip():
        l = 3
        den = row.get("name3","").strip()
    elif row.get("name4","").strip():
        l = 4
        den = row.get("name4","").strip()
    elif row.get("name5","").strip():
        l = 5
        den = row.get("name5","").strip()
    elif row.get("name6","").strip():
        l = 6
        den = row.get("name6","").strip()
    elif row.get("name7","").strip():
        l = 7
        den = row.get("name7","").strip()
    elif row.get("name8","").strip():
        l = 8
        den = row.get("name8","").strip()
    elif row.get("name9","").strip():
        l = 9
        den = row.get("name9","").strip()
    elif row.get("name10","").strip():
        l = 10
        den = row.get("name10","").strip()
    elif row.get("name11","").strip():
        l = 11
        den = row.get("name11","").strip()
    elif row.get("name12","").strip():
        l = 12
        den = row.get("name12","").strip()
    elif row.get("name13","").strip():
        l = 13
        den = row.get("name13","").strip()
    elif row.get("name14","").strip():
        l = 14
        den = row.get("name14","").strip()
    return l, den

def normalize_text(text):
    # remove_words = "(CIILB_|CIIL_|CIIH_|CI_|Applicable|Defined|Specified|Supply Chain|Additional|Including|Included|Processing|Details)"
    remove_words = r"<Hdr>|<Lin>"
    REMOVE_CHARS = " ._/()-"
    _text = re.sub(remove_words, "", text).translate(
        str.maketrans("", "", REMOVE_CHARS)
    )
    if _text.endswith("IdentificationIdentifier"):
        _text = _text.replace("IdentificationIdentifier", "ID")
    elif _text.endswith("IdentificationID"):
        _text = _text.replace("IdentificationID", "ID")
    elif _text.endswith("Identifier"):
        _text = _text.replace("Identifier", "ID")
    elif _text.endswith("Text"):
        _text = _text.replace("Text", "")
    return _text

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

def check_muliplicity(den, multiplicity, multiplicity_sme, multiplicity_sme2=None):
    min = max = min_SME = max_SME = None
    match = re.match(r".*([01]\.\.[1n]).*", multiplicity)
    if match:
        multiplicity = match.group(1)
        min = multiplicity[0]
        max = multiplicity[-1]
    else:
        msg = f'"{den}"のD24Aでの多重度[{multiplicity}]不正'
        error_print(msg)
    match_SME = re.match(r".*([01]\.\.[1n]).*", multiplicity_sme)
    if match_SME:
        multiplicity_sme = match_SME.group(1)
        min_SME = multiplicity_sme[0]
        max_SME = multiplicity_sme[-1]
    else:
        msg = f'*Error* 多重度[{multiplicity_sme}]形式不正'
        error_print(msg)
        return msg
    message = ""
    if min and min_SME < min:
        message = f'D24Aでは必須項目です.'
    if max and "1"==max and "n"==max_SME:
        message += f'D24Aの最大繰り返し回数は 1.'
    if multiplicity_sme2:
        match_sme = re.match(r".*([01]\.\.[1n]).*",multiplicity_sme2)
        if match_sme:
            multiplicity_sme2 = match_sme.group(1)
            if multiplicity_sme!=multiplicity_sme2:
                min_sme = multiplicity_sme2[0]
                max_sme = multiplicity_sme2[-1]
                if min_sme < min:
                    message += f'D24Aでは必須項目です.'
                if "1"==max and "n"==max_sme:
                    message += f'D24Aの最大繰り返し回数は 1.'
    if message:
        if multiplicity_sme2 and multiplicity_sme!=multiplicity_sme2:
            message = f'*Error* {multiplicity_sme} [{multiplicity_sme2}] {message}'
        else:
            message = f'*Error* {multiplicity_sme} {message}'
        error_print(f'{den} [{multiplicity}] {message}')
    if not message:
        message = multiplicity_sme
    return message

# Function to parse class terms and handle specializations
def parse_class(class_term, REFERENCE_OF = False):
    global current_multiplicity, LIFO_list, LHM_model, object_class_dict
    """
    Step 1: Copy a class to the Hierarchical Message Definition and place it on the top of
    the LIFO list.
    """
    _class_term = class_term
    if "|" in _class_term: # romove originating class name for this associated class
        _class_term = class_term[class_term.index("|"): + 1]
        class_qualifier = class_term[:class_term.index("|")]
    else:
        class_qualifier = ""
    if _class_term not in object_class_dict:
        error_print(f"'{_class_term}' not in object_class_dict")
        return
    if "properties" not in object_class_dict[_class_term]:
        error_print(f"'{_class_term}'has no properties")
        return

    object_class = copy.deepcopy(object_class_dict[_class_term])

    if REFERENCE_OF:
        object_class['property_type'] = 'Reference Association'

    _type = object_class['property_type']
    trace_print(f"{_type in ['Subclass','Specialized Class'] and '-' or ' '} {_type}: parse_class('{class_term}') check  '{_class_term}'{'['+current_multiplicity+']' if current_multiplicity else ''}\t{LIFO_list}")
    """
    A. Copy the class to the hierarchical logical data model.
    Copy all properties and associations to the hierarchical logical data model.
    Conventionally, properties not related to the associated object class should be placed
    before them, but this is not a requirement.

    B. Place the selected class on the top of the LIFO list if not Reference Association.
    """
    if REFERENCE_OF:
        level = len(LIFO_list) + 1
    else:
        LIFO_list.append(class_term)
        level = len(LIFO_list)
    debug_print(f'  Update LIFO_list {LIFO_list}')
    object_class['level'] = level
    if level > 1:
        LIFO_term = "-".join(LIFO_list)
    if REFERENCE_OF:
        """
        iii)    Reference Associations
        •    Copy associated class with adding it to the LIFO (Last In, First Out) list.
        For copying reference association's associated class, the new entry in the LHM should include:
            - Level: n
            - Type: 'R' (Relation)
            - Identifier: Empty
            - Name:
            - If an association role for the reference association is defined, format as "{association role}_{associated class}".
            - If no association role is defined, use "{associated class}".
            - Datatype: Leave empty as datatype is not applicable for reference association's associated class.
        """
        LIFO_term += f"-{class_term}"
        debug_print(f"class_term:{class_term} _class_term:{_class_term} object_class['class_term']:{LIFO_term}")
        definition = object_class['definition']
        definition = definition.replace('A class', f"The reference association to the {class_term.replace('_', ' ')} class, which is a class")
        object_class['definition'] = definition
        object_class['type'] = 'R'
        properties_list = []
        for key in object_class_dict:
            if key.startswith(_class_term):
                properties = object_class_dict[_class_term].get('properties', [])
                for prop in properties:
                    properties_list.append(prop)
        for prop in properties_list:
            object_class['properties'][key] = prop
        hasPK = any(property['identifier'] == 'PK' for property in properties_list)
        if "-" not in object_class['class_term'] and not hasPK:
            error_print(f"Referenced class {object_class['class_term']} has no PK(primary Key).")
        else:
            pass
    else:
        object_class['type'] = 'C'
    if level > 1 and current_multiplicity:
        object_class['multiplicity'] = current_multiplicity

    LHM_model.append(object_class)

    debug_print(f"  {level} Class:'{object_class['class_term']}'")
    properties = copy.deepcopy(object_class['properties'])

    if SME_COMMON:
        sorted_properties = sorted(
            properties.values(),
            key=lambda p: (
                0 if p["property_type"] == "Attribute" else 1,
                as_float(p.get("sequence", 0)),
                # as_float(p.get("sme_nr", 9999)),
            )
        )
    else:
        sorted_properties = sorted(
            properties.values(),
            key=lambda p: (
                0 if p["property_term"] == "Identification" and p["representation_term"] == "Identifier"
                else 1 if p["property_type"] == "Attribute"
                else 2
            )
        )

    level += 1
    for property_ in sorted_properties:
        property = property_.copy()
        if _class_term!=property["class_term"]:
            property["class_term"] = _class_term
        property["class_term"] = _class_term
        if property['property_type'] in ['Attribute(PK)','Attribute']:
            """
            a) Step 1: Copy a class from the BSM to the LHM.
            Procedure:
            In this step, all attributes and associations relevant to the class are incorporated, with
            the 'level' of attribute entries incremented by 1. Let the resulting value of 'level' be n
            after the increment.
            Attributes and reference associations are prioritized over composition/aggregation associations
            to maintain clarity and order. The copying logic is detailed as follows:
            """
            # if 'Active' in  property['property_term']:
            #     # Skip 'xxActive' attribute, which indicates that the master record is active and not usable for LHM.
            #     continue
            property['level'] = level
            property['type'] = 'A'
            LIFO_term = "-".join(LIFO_list)
            if REFERENCE_OF:
                LIFO_term += f"-{class_term}"
                """
                iii) Reference Associations
                •    Copy the unique identifier of the associated class.
                Additionally, check for reference associations to identify the unique identifier of the associated class. If found, copy this identifier to the LHM as:
                    - Level: n + 1
                    - Type: 'A' (Attribute)
                    - Identifier: 'REF' (Reference Identifier)
                    - Name: The property term of the found unique identifier.
                    - Datatype: The representation term of the found unique identifier.
                Note: This entry in the LHM is a reference identifier, serving as a foreign key to the reference association class.
                """
                if 'PK'==property['identifier']:
                    property['identifier'] = 'REF'
                    definition = property['definition']
                    definition = definition.replace('unique identifier', 'reference identifier')
                    property['definition'] = definition
                    if class_qualifier:
                        if class_qualifier not in _class_term:
                            class_term_ = property["class_term"] =f'{class_qualifier}_ {_class_term}'
                        else:
                            class_term_ = _class_term
                        den = property["DEN"]
                        property["DEN"] = f'{class_term_}. {den[2+den.index("."):]}'
                    if den.endswith("Identification. Identifier"):
                        property["label"] = f'{den[2+den.index("."):-26]}ID'

                    LHM_model.append(property)

                    debug_print(f"  {level} {property['property_type']} {property['identifier']} [{property['multiplicity']}] {property['property_term']}{property['associated_class']}")
            elif property['property_type'] in ['Attribute(PK)','Attribute']:
                den = property["DEN"]
                parts = [x.strip() for x in den.split(".")]
                property["label"] = parts[1]
                if den.endswith("Identification. Identifier"):
                    property["label"] = f'{den[2+den.index("."):-26]}ID'

                LHM_model.append(property)

                debug_print(f"  {level} {property['property_type']} [{property['multiplicity']}] {property['property_term']}{property['associated_class']}")

    if REFERENCE_OF:
        # When dealing with Reference Association, no additional checks are required for Properties, including Associations.
        return
    """
    Step 2: Find the next class.
    The following rules provide guidance on choosing the association,
    which is a property that has the associated object class defined,
    to use for stepping from the current class to the next in a "walk".
    Once an association has been used to step from the current class to a new class,
    do not re-use it unless the current class itself has been reached again by a different
    association.
    All selections of associations must be consistent with the intended semantics of the
    data.
    The following rules should be applied in the order they are listed.
    As soon one of them is reached that is applicable, select the class it specifies and
    return to step 1, above.
    """
    def traverse_associated_class(associated_class):
        property_type = associated_class['property_type']
        associated_class_term = associated_class['associated_class']
        current_multiplicity = None
        if associated_class_term and associated_class_term not in LIFO_list:

            LHM_model.append(associated_class)

            current_multiplicity = associated_class['multiplicity_sme']
            current_multiplicity = current_multiplicity if current_multiplicity and '-'!=current_multiplicity else None
            debug_print(f"traverse_associated_class")
            debug_print(f"  {level} {property_type}[{current_multiplicity}] {associated_class_term}")

            parse_class(associated_class_term, 'Reference Association'==property_type and associated_class_term or None)

    if not SME_COMMON:
        """
        B. Mandatory, Singular.
        Pick any 1..1 association that is navigable to needed information.
        """
        mandate_classes = [
            cls
            for cls in properties
            if cls["property_type"]
            in ["Reference Association", "Aggregation", "Composition"]
            and cls["multiplicity"] in ["1", "1..1"]
        ]
        """
        C. Singular.
        Pick any navigable association that is (0,1) and leads to needed information.
        """
        singular_classes = [
            cls
            for cls in properties
            if cls["property_type"]
            in ["Reference Association", "Aggregation", "Composition"]
            and "0..1" == cls["multiplicity"]
        ]
        """
        E. Other Plural.
        Pick any navigable association that leads to needed information.
        """
        other_classes = [
            cls
            for cls in properties
            if cls["property_type"]
            in ["Reference Association", "Aggregation", "Composition"]
            and cls["multiplicity"] in ["0..*", "1..*", "0..n", "1..n"]
        ]
        """
        B. Mandatory, Singular.
        Pick any 1..1 association that is navigable to needed information.
        """
        for associated_class in mandate_classes:
            traverse_associated_class(associated_class)
        """
        C. Singular.
        Pick any navigable association that is (0,1) and leads to needed information.
        """
        for associated_class in singular_classes:
            traverse_associated_class(associated_class)
        """
        E. Other Plural.
        Pick any navigable association that leads to needed information.
        """
        for associated_class in other_classes:
            traverse_associated_class(associated_class)
        """
        F. None.
        If none of the above rules apply, cross the current class off the LIFO list.
        Take the prior class on the LIFO as the “current” class and immediately repeat steps
        A-E.
        If you have crossed the last class of the LIFO list, you have finished the process of
        selecting the classes and associations for the hierarchical logical data model.
        The sequence of Rules (B) – (E) leads to message types that seem more coherent to people.
        If there is doubt or disagreement about which association to pick based on this rule,
        the committee may ignore rules (B) – (E) completely and pick any association.
        The message will have the same information content.
        """
    else:
        level = len(LIFO_list) + 1
        classes = [
            cls
            for cls in sorted_properties
            if cls["property_type"]
            in ["Reference Association", "Aggregation", "Composition"]
        ]
        if "MA" == object_class["acronym"]:
            classes = sorted(
                classes,
                key=lambda r: as_float(r.get("sme_nr", 0)),
            )
        for associated_class in classes:
            associated_class["level"] = level
            traverse_associated_class(associated_class)

    debug_print(f"-- Done: {LIFO_list[-1]}\n")
    LIFO_list.pop(-1)
    debug_print(f"POP LIFO_list: {class_term} type is '{_type}'\t{LIFO_list}")

def update_record(record):
    # global path_list
    UPDATE_FIELDS = [
        "label_ja",
        "definition_ja",
        "UNID",
        "short_name",
        "definition",
        "property_type",
        "class_term",
        "sequence",
        "identifier",
        "property_term",
        "representation_term",
        "code_list",
        "XML_datatype",
    ]
    den = record["DEN"]
    if den.startswith("CIIH") or den.startswith("CIIL"):
        if den in mbie_dict_den:
            data = mbie_dict_den[den]
            for key in record.keys():
                if key in UPDATE_FIELDS and key in data:
                    record[key] = data[key]
        level = record["level"]
        if isinstance(level, str) and level.isdigit():
            level = int(level)
        # XPath 用の path_list
        ensure_level(path_list, level)
        acronym = record["acronym"]
        if "ABIE"!=acronym:
            if "SC"==acronym:
                attribute = record["xml_element_name"]
                path_list[level] = attribute
            else:
                element = record["element"]
                path_list[level] = element
            record["xpath"] = "/" + "/".join(path_list)
        level_csv = record["level_csv"]
        if level_csv:
            if isinstance(level_csv,str):
                level_csv = int(level_csv)
                record["level_csv"] = str(level_csv - 1)
    return record

def ensure_level(path_list, level):
    if not level:
        return
    """path_list の長さを level+1 に合わせる（短ければ埋め、長ければ詰める）"""
    while len(path_list) <= level:
        path_list.append("")
    while len(path_list) > level + 1:
        del path_list[-1]

def main():
    global TRACE, DEBUG
    global unid_map, bsm_records, lhm_records, lhm_class_dict, lhm_balance_conf_records, mbie_dict_den, bsm_dict
    global LIFO_list, LHM_model, object_class_dict

    mbie_file =         os.path.join(base_dir,"MBIEs24A.csv")
    abie_mapping_file = os.path.join(base_dir,"D23B_abie_mapping.csv")
    qdt_file =          os.path.join(base_dir,"D23B_qDT.csv")
    tded_file =         os.path.join(base_dir,"TDED.csv")

    lhm_balance_conf_file = os.path.join(base_dir,f"lhm_balance_confirmation.csv")

    DATE = "09-01"
    in_file = os.path.join(base_dir,f"sme_common{DATE}.csv")

    DATE = "10-20"
    fsm_file = os.path.join(base_dir,f"SME_common{DATE}_FSM.csv")
    bsm_file = os.path.join(base_dir,f"SME_common{DATE}_BSM.csv")
    lhm_file = os.path.join(base_dir,f"SME_common{DATE}_LHM.csv")

    lhm_out_file = os.path.join(base_dir,f"SME_common{DATE}_out_LHM.csv")
    out_file = os.path.join(base_dir,f"sme_common{DATE}_out.csv")


    REMOVE_CHARS = r"[_\u3000\n\r\(\)\[\]\-\s\.]*" # regex class of characters to remove

    # Nr,UNID,Acronym,DEN,Definition,Publication comments,Object Class Term Qualifier(s),Object Class Term,Property Term Qualifier(s),Property Term,Datatype Qualifier(s),Representation Term,Qualified Data Type UID,Associated Object Class Term Qualifier(s),Associated Object Class,Business Term(s),Usage Rule(s),Sequence Number,Occurrence Min,Occurrence Max,Context Categories,Example(s),Version,Ref Library Version,Submitter Name,Ref Component UN ID,Unique submitter ID,CR Status Date,CR Status,Library Maintenance Comment,TDED,Submitted Definition,Submitter Comment,Submitted DEN,Publication Refs -- Source,Short Name
    trace_print(f'\n-- Parse {mbie_file} --')
    with open(mbie_file, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)  # Uses first row as keys
        for row in reader:
            acronym = row["Acronym"]
            if "END"==acronym:
                break

            nr = row["Nr"]
            nr = int(nr) if nr.isdigit() else 0
            sequence = row.get("Sequence Number","")
            sequence = int(sequence) if sequence.isdigit() else 0

            unid = row["UNID"]
            den = row["DEN"]

            class_term_qualifier = row.get("Object Class Term Qualifier(s)","").strip()
            class_term = row.get("Object Class Term","").strip()
            if class_term_qualifier:
                class_term = f'{class_term_qualifier}_ {class_term}'
            property_term_qualifier = row.get("Property Term Qualifier(s)","").strip()
            property_term = row.get("Property Term","").strip()
            if property_term_qualifier:
                property_term = f'{property_term_qualifier}_ {property_term}'
            datatype_qualifier = row.get("Datatype Qualifier(s)","").strip()
            representation_term = row.get("Representation Term","").strip()
            if datatype_qualifier:
                representation_term = f'{datatype_qualifier}_ {representation_term}'
            associated_class_qualifier = row['Associated Object Class Term Qualifier(s)'].strip()
            associated_class_term = row['Associated Object Class'].strip()
            if associated_class_qualifier:
                associated_class_term = f"{associated_class_qualifier}_ {associated_class_term}"

            multiplicity = ""
            occurence_min = row.get("Occurrence Min","")
            occurence_max = row.get("Occurrence Max","")
            if "unbounded"==occurence_max:
                occurence_max = "n"
            if occurence_min and occurence_max:
                multiplicity = f"{occurence_min}..{occurence_max}"

            if acronym in ["BBIE","SC"]:
                property_type = "Attribute"
                element = normalize_text(f'{property_term} {row.get("Representation Term","").strip()}')
            elif "ASBIE"==acronym:
                property_type = "Composition"
                element = normalize_text(f'{property_term} {row.get("Associated Object Class","").strip()}')
            else:
                property_type = "Class"
                element = normalize_text(class_term)

            code_list = ""
            if len(row["TDED"]) > 0:
                tded = re.sub(REMOVE_CHARS, "", row["TDED"])
                code_list = 'TDED{}'.format(tded)

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
                "sequence": sequence if "Class"!=property_type else "",
                "multiplicity": multiplicity,
                "definition": row.get("Definition",""),
                "short_name": row.get("Short Name",""),
                "UNID": unid,
                "TDED": row.get("TDED",""),#if representation_term.endswith("Code") else "",
                "submitted_definition": row.get("Submitted Definition",""),
            }
            mbie_dict[unid] = data
            mbie_dict_den[den] = data

    mbie_ja_file = os.path.join(base_dir,"MBIEs24A_ja.csv")
    #  UNID,short_name,short_name_ja,definition,definition_ja
    trace_print(f'\n-- Parse {mbie_ja_file} --')
    with open(mbie_ja_file, mode="r", newline="", encoding="utf-8-sig") as file_ja:
        reader = csv.DictReader(file_ja)  # Uses first row as keys
        for row in reader:
            unid = row.get("UNID","")
            mbie_translate_ja[unid] = row

    # "Version","UNID","Acronym","Dictionary Entry Name","ObjectClassQualifierTerm","ObjectClassTerm","Cardinality","PropertyTerm","PrimaryRepresentationTerm","XML datatype","AssociatedObjectClassQualifierTerm","AssociatedObjectClassTerm","XML element name","Definition"
    trace_print(f'\n-- Parse {abie_mapping_file} --')
    with open(abie_mapping_file, mode="r", newline="", encoding="utf-8-sig") as file_abie:
        reader = csv.DictReader(file_abie)  # Uses first row as keys
        for row in reader:
            unid = row.get("UNID","")
            abie_mapping[unid] = row
            den = row.get("Dictionary Entry Name","")
            abie_mapping_den[den] = row

    # "XML datatype", "D23B", "UNTDID"
    trace_print(f'\n-- Parse {qdt_file} --')
    with open(qdt_file, mode="r", newline="", encoding="utf-8-sig") as file_qdt:
        reader = csv.DictReader(file_qdt)  # Uses first row as keys
        for row in reader:
            xml_datatype = row.get("XML datatype","")
            qdt_dict[xml_datatype] = row

    # "Code", "URL", "Code name", "Desc", "Repr", "Note"
    trace_print(f'\n-- Parse {tded_file} --')
    with open(tded_file, mode="r", newline="", encoding="utf-8-sig") as file_tded:
        reader = csv.DictReader(file_tded)  # Uses first row as keys
        for row in reader:
            code = row.get("Code","")
            tded_dict[code] = row

    IN_FIELDS = [
        "nr",
        "category",
        "UNID",
        "acronym",
        "name1",
        "name2",
        "name3",
        "name4",
        "name5",
        "name6",
        "name7",
        "name8",
        "name9",
        "name10",
        "name11",
        "name12",
        "name13",
        "name14",
        "label_sme",
        "label_csv",
        "definition_sme",
        "multiplicity_sme",
        "selector",
        "fixed_value",
        "version",
        "code_list",
        "issueing_agency",
        "input_method",
        "input_value",
        "xml_imput_sing",
        "selfbilling",
        "amendment_selfbilling",
        "single_selfbilling",
        "core_selfbilling",
        "accounting",
        "JP PINT v1.0",
        "Id",
        "Business Term",
        "Card.",
    ]

    BALANCE_CONF_FIELDS = (
        "sme_nr",
        "acronym",
        "level",
        "multiplicity_sme",
        "label_sme",
        "UNID",
        "DEN",
    )

    LHM_FIELDS = [
        "version",
        "sme_nr",
        "mbie_nr",
        "acronym",
        "level",
        "multiplicity",
        "multiplicity_sme",
        "label_sme",
        "definition_sme",
        "level_csv",
        "multiplicity_csv",
        "label_csv",
        "label_ja",
        "definition_ja",
        "UNID",
        "DEN",
        "short_name",
        "definition",
        "property_type",
        "class_term",
        "sequence",
        "identifier",
        "property_term",
        "representation_term",
        "code_list",
        "XML_datatype",
        "associated_class",
        "selector",
        "fixed_value",
        "element",
        "XML_element_name",
        "xpath",
    ]

    trace_print(f'\n-- Parse {in_file} --')
    with open(in_file, mode="r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, fieldnames=IN_FIELDS)
        next(reader) # skip header row
        for row in reader:
            acronym = row.get("acronym", "")
            if not acronym:
                continue
            if acronym == "END":
                break

            record = {}
            for field in IN_FIELDS:
                if field in row:
                    record[field] = row[field]
                else:
                    record[field] = ""
            nr = record["nr"]
            if nr:
                nr = float(nr)
                sme_dict[nr] = record

    with open(lhm_file, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, fieldnames=LHM_FIELDS)
        next(reader) # skip header row
        for row in reader:
            record = {}
            for field in LHM_FIELDS:
                if field in row:
                    record[field] = row[field]
                else:
                    record[field] = ""

            record = update_record(record)

            sme_nr = record["sme_nr"]
            if sme_nr:
                sme_nr = float(sme_nr)
            record["sme_nr"] = sme_nr
            den = record["DEN"]
            class_term = record["class_term"]
            property_type = record["property_type"]
            if "Class"==property_type and not class_term in lhm_class_dict:
                class_nr = sme_nr
                lhm_class_dict[class_nr] = {"data":record, "property":[]}
            elif "Composition"==property_type:
                class_nr = sme_nr
                lhm_class_dict[class_nr] = {"data":record, "property":[]}
            if property_type in ["Attribute", "Composition"]:
                lhm_class_dict[class_nr]["property"].append(record)
            lhm_records.append(record)

    trace_print(f'\n-- Parse {lhm_balance_conf_file} --')
    with open(lhm_balance_conf_file, mode="r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, fieldnames=BALANCE_CONF_FIELDS)
        next(reader) # skip header row
        for row in reader:
            acronym = row.get("acronym", "")
            if not acronym:
                continue
            if acronym == "END":
                break
            record = {}
            for field in BALANCE_CONF_FIELDS:
                if field in row:
                    record[field] = row[field]
                else:
                    record[field] = ""
            acronym = record["acronym"]
            class_level = record["level"]
            class_nr = record["sme_nr"]
            class_den = record["DEN"]
            if class_nr and isinstance(class_nr, str):
                class_nr = float(class_nr)

            if class_nr in lhm_class_dict:
                data = lhm_class_dict[class_nr]["data"]
            else:
                data = {}

            for field in LHM_FIELDS:
                if field in row:
                    data[field] = row[field]
            
            if acronym in ["MA", "ABIE"]:
                lhm_balance_conf_records.append(data)
                if class_nr in lhm_class_dict:
                    property_records = lhm_class_dict[class_nr]["property"]
                    for property in property_records:
                        level = int(class_level)
                        property_acronym = property["acronym"]
                        if "BBIE"==property_acronym:
                            property["level"] = str(level + 1)
                        elif "SC"==property_acronym:
                            property["level"] = str(level + 2)
                    lhm_balance_conf_records += property_records
            elif "AS"==acronym[:2]:
                if "ASMA"==acronym:
                    sme_nr = data["sme_nr"]
                    if sme_nr and isinstance(sme_nr, str):
                        sme_nr = float(sme_nr)
                    data = [x for x in lhm_records if x["sme_nr"]==sme_nr and "ASMA"==x["acronym"]]
                    if data:
                        data = data[0]
                elif class_nr in lhm_class_dict:
                    data = lhm_class_dict[class_nr]["data"]

                if not data:
                    data = {}
                    for field in LHM_FIELDS:
                        if field in row:
                            data[field] = row[field]
                        else:
                            data[field] = ""
                    sme_nr = data["sme_nr"]
                    if isinstance(sme_nr, str):
                        data["sme_nr"] = float(sme_nr)

                if class_den in mbie_dict_den:
                    mbie = mbie_dict_den[class_den]
                    class_unid = mbie["UNID"]
                    data["UNID"] = class_unid
                else:
                    data["UNID"] = "JPSxxxxxxxx"
                    
                lhm_balance_conf_records.append(data)

    # CSV出力
    with open(lhm_out_file, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=LHM_FIELDS)
        writer.writeheader()
        writer.writerows(lhm_balance_conf_records)

    trace_print(f"Output LHM file {lhm_out_file}")

    for data in lhm_balance_conf_records:
        den = data["DEN"]
        sme_nr = data["sme_nr"]
        sme_data = {}
        if sme_nr in sme_dict:
            sme_data = sme_dict[sme_nr]
        level = data["level"]
        if level and isinstance(level, str):
            level = int(level)
        record = {}
        if level==1:
            record["name1"] = den
        elif level==2:
            record["name2"] = den
        elif level==3:
            record["name3"] = den
        elif level==4:
            record["name4"] = den
        elif level==5:
            record["name5"] = den
        elif level==6:
            record["name6"] = den
        elif level==7:
            record["name7"] = den
        elif level==8:
            record["name8"] = den
        elif level==9:
            record["name9"] = den
        elif level==10:
            record["name10"] = den
        elif level==11:
            record["name11"] = den
        elif level==12:
            record["name12"] = den
        elif level==13:
            record["name13"] = den
        elif level==14:
            record["name14"] = den

        for key in IN_FIELDS:
            if not key.startswith("name"):
                if key in data:
                    record[key] = data[key]
                elif key in sme_data:
                    record[key] = sme_data[key]
                else:
                    pass
        
        sme_records.append(record)

    # CSV出力
    with open(out_file, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=IN_FIELDS)
        writer.writeheader()
        writer.writerows(sme_records)

    trace_print(f"Output SME file {out_file}")

if __name__=="__main__":
    main()
