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
bsm_records = []
lhm_records = []
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

IN_FIELDS = [
    "category",
    "version",
    "sme_nr",
    "mbie_nr",
    "level",
    "type",
    "identifier",
    "UNID",
    "acronym",
    "label_sme",
    "label_csv",
    "multiplicity_sme",
    "class_term",
    "property_term",
    "representation_term",
    "associated_class",
    "selector",
    "fixed_value",
    "definition_sme",
    "TDED",
    "submitted_definition",
    "code_list",
    "DEN",
    "definition",
    "short_name",
    "element",
    "xpath",
    "pint_id",
    "business_term",
    "card",
    "selfbilling",
    "amendment_selfbilling",
    "single_selfbilling",
    "core_selfbilling",
    "pint_id",
    "business_term",
    "card",
]

FIELD_REMAP = {
    "mbie_nr":              ("mbie_dict","mbie_nr"),
    "xml_element":          ("mbie_dict","element"),
    "sequence":             ("mbie_dict","sequence"),
    "multiplicity":         ("mbie_dict","multiplicity"),
    "code_list":            ("mbie_dict","code_list"),
    "TDED":                 ("mbie_dict","TDED"),
    "submitted_definition": ("mbie_dict","submitted_definition"),
    "short_name":           ("mbie_dict","short_name"),
    "definition":           ("mbie_dict","definition"),
    "label_ja":             ("mbie_translate_ja", "short_name_ja"),
    "definition_ja":        ("mbie_translate_ja", "definition_ja"),
    "XML_datatype":         ("abie_mapping","XML datatype"),
    "XML_element_name":     ("abie_mapping","XML element name"),
}

FSM_FIELDS = [
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
    "definition",
    "short_name",
    "element",
    "XML_element_name",
    "selfbilling",
    "amendment_selfbilling",
    "single_selfbilling",
    "core_selfbilling",
    "pint_id",
    "business_term",
    "card",
]

BSM_FIELDS = [
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
    "definition",
    "short_name",
    "element",
    "XML_element_name",
    "selfbilling",
    "amendment_selfbilling",
    "single_selfbilling",
    "core_selfbilling",
    "pint_id",
    "business_term",
    "card",
]

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
    "selfbilling",
    "amendment_selfbilling",
    "single_selfbilling",
    "core_selfbilling",
    "pint_id",
    "business_term",
    "card",
]

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

def main():
    global TRACE, DEBUG
    global unid_map, bsm_records, lhm_records, mbie_dict_den, bsm_dict
    global LIFO_list, LHM_model, object_class_dict

    mbie_file =         os.path.join(base_dir,"MBIEs24A.csv")
    abie_mapping_file = os.path.join(base_dir,"D23B_abie_mapping.csv")
    qdt_file =          os.path.join(base_dir,"D23B_qDT.csv")
    tded_file =         os.path.join(base_dir,"TDED.csv")

    # DATE = "09-22"
    DATE = "09-01"
    in_file = os.path.join(base_dir,f"sme_common{DATE}.csv")

    DATE = "10-25"
    fsm_file = os.path.join(base_dir,f"SME_common{DATE}_FSM.csv")
    bsm_file = os.path.join(base_dir,f"SME_common{DATE}_BSM.csv")
    lhm_file = os.path.join(base_dir,f"SME_common{DATE}_LHM.csv")

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

    def row_to_fsm_data(row):
        """row(IN_FIELDS) から FSMM フィールドだけを抜き出し、空文字で初期化→strip して詰める"""
        d = dict((k, "") for k in IN_FIELDS)
        for k in d.keys():
            if k in row and row[k] is not None:
                d[k] = row[k].strip()
        acronym = d["acronym"]
        # レベル算出
        lvl, den = get_den(row)  # 既存の関数
        level = (2 + lvl) // 2
        if acronym == "MA":
            level = 0
        d["level"] = level
        d["DEN"] = den
        # nr→sme_nr（数値化）
        nr = row.get("nr", "")
        d["sme_nr"] = as_float(nr)

        d = apply_remap_to_record(d, FSM_FIELDS, FIELD_REMAP)

        if "qdt:" in d["XML_datatype"]:
            code_list = d["code_list"]
            xml_datatype = d["XML_datatype"]
            q = qdt_dict.get(xml_datatype,"")
            schema_url = q.get("D23B","")
            if schema_url:
                code_list += f' | XMLSchema {schema_url}'
            d["code_list"] = code_list

        return d

    def split_den_by_acronym(den, acronym):
        """DEN を acronym 別に分解（不足は空文字）"""
        class_term = property_term = representation_term = associated_class = ""
        if "." in den:
            parts = [p.strip() for p in den.split(".")]
            if acronym == "ASMA":
                # 例: <root>. Specified. <assoc>
                associated_class = parts[0] if parts else ""
            elif acronym == "ASBIE":
                # 例: <class>. <prop>. <assoc>
                class_term = parts[0] if len(parts) > 0 else ""
                property_term = parts[1] if len(parts) > 1 else ""
                associated_class = parts[2] if len(parts) > 2 else ""
            elif acronym == "ABIE":
                class_term = parts[0] if parts else ""
            elif acronym in ["BBIE","SC"]:
                # 例: <class>. <prop>. <repr>
                class_term = parts[0] if len(parts) > 0 else ""
                property_term = parts[1] if len(parts) > 1 else ""
                representation_term = parts[2] if len(parts) > 2 else ""
        else:
            # MA 等のルート
            class_term = den.strip()
        return class_term, property_term, representation_term, associated_class

    def decorate(term, selector, prop_path, category):
        """term に [selector]、(prop_path)、<category> を順に付与"""
        if selector:
            term = "{}[{}]".format(term, selector)
        if prop_path:
            path = re.sub(r"\[[^\]]*\]", "", prop_path).strip()
            term = "{} ({})".format(term, path)
        # if category:
        #     term = "{} <{}>".format(term, category)
        return term

    def ensure_level(path_list, level):
        """path_list の長さを level+1 に合わせる（短ければ埋め、長ければ詰める）"""
        while len(path_list) <= level:
            path_list.append("")
        while len(path_list) > level + 1:
            del path_list[-1]

    def property_path(class_conditions, upto):
        """class_conditions[0:upto] の (property, selector) を / 連結。
        selector があれば 'property[selector]' にする。
        """
        parts = []
        for x in class_conditions[:upto + 1]:
            if not x:
                continue
            prop = x[0] if len(x) > 0 else None
            sel  = x[1] if len(x) > 1 else None
            if not prop:
                continue
            if sel:
                parts.append("%s[%s]" % (prop, sel))
            else:
                parts.append(prop)
        return "/".join(parts)

    def last_part_without_brackets(part):
        if not part:
            return ""
        s = part.strip()
        # 先頭と末尾が括弧なら外す
        if s.startswith("(") and s.endswith(")"):
            s = s[1:-1].strip()
        # '/' で分割して最後を取る
        tail = s.split("/")[-1].strip()
        # 角括弧 [ ... ] を除去
        tail = re.sub(r"\[[^\]]*\]", "", tail).strip()
        # 念のため余分な閉じ括弧を除去
        tail = tail.rstrip(")")
        return tail

    def normalize_attribute(text):
        """
        re.X（verbose）で可読性を上げ、行内にコメントを記述
        全体像：
          ^\s*                     … 先頭の空白を許容
          (?P<class> … )           … 「クラス名＋[selector]」の塊（必須）
          \s*
          (?P<prop>  … )?          … 「(property path …)」の塊（任意）
          \s*
          (?P<cat>   … )?          … 「<category>」の塊（任意）
          \s*$                     … 末尾の空白を許容して終了
        """
        pat = re.compile(r"""
            ^\s*
            (?P<class>
                # class 部は、次に出てくる '('（property 開始）や '<'（category 開始）
                # までは取り込みたい。ただし、途中の '[ ... ]'（selector）は
                # かたまりとして残す必要がある。
                (?:                     # ← 非キャプチャで A|B の並びを 1 回以上
                    [^[(<]+             # A: '[', '(', '<' 以外の通常文字を 1 文字以上
                    |                   #    （空白含む。次の特別記号が来るまで貪欲に）
                    \[[^\]]*\]          # B: 角括弧ブロック全体 '[ ... ]' をまるごと
                                        #    （中に '(' や '<' があっても ']' まで飲み込む）
                )+
            )
            \s*
            (?P<prop>
                # prop 部は ( ... ) 全体を 1 かたまりで取得（任意）。
                # 丸括弧の内部に '[ ... ]' が来ても壊れないよう、
                #   ・ '[^\[\)]'  … '[' と ')' 以外なら 1 文字として消費
                #   ・ '\[[^\]]*\]' … 角括弧ブロックは ']' まで一気に消費
                \(
                    (?:[^\[\)]|\[[^\]]*\])*
                \)
            )?
            \s*
            (?P<cat>
                # cat 部は < ... > 全体（任意）
                <[^>]*>
            )?
            \s*$
        """, re.X)
        m = pat.match(text)
        if m:
            part1 = m.group("class").strip()
            part2 = (m.group("prop") or "").strip()
            part3 = (m.group("cat") or "").strip()
        base = part1 # re.sub(r"\[[^\]]*?\]\s*", "", part1)
        # ( ... ) から最後のパスを取り出し、末尾要素を prefix に
        prefix = last_part_without_brackets(part2)
        element = ("%s. %s" % (prefix, base)) if prefix else base
        element = re.sub(r"\[[^\]]*\]", "", element).strip()
        return element

    def normalize_selector(text):
        """全角→半角、空白・ドット等を除去して要素名化（例: 'Reason. Code' -> 'ReasonCode')."""
        s = unicodedata.normalize('NFKC', text)
        # 区切り類（ドット/空白/下線/ハイフン）を削除
        normalized_selector = re.sub(r"[.\s_-]+", "", s)
        return normalized_selector

    def get_field(d: Mapping[str, Any], unid: str, field: str, default: Any = "") -> Any:
        """Return d[unid][field] if present, else default."""
        if d and isinstance(d, dict):
            t = d.get(unid) or {}
            return t.get(field, default)
        return default

    def get_dict_from_globals(name: str) -> dict | None:
        obj = globals().get(name) # get global dict by its name
        return obj if isinstance(obj, dict) else None

    def apply_remap_to_record(record, FSM_FIELDS, FIELD_REMAP):
        d = record.copy()
        unid = d.get("UNID", "")
        acronym = d.get("acronym", "")
        if d["sme_nr"] in [32]:
            debug_print(f'UNTDED:{d["TDED"]} code_list:{d["code_list"]}')
        tded = code_list = sme_code_list = ""
        sme_code_list = re.sub(r"[\r\n]+", " ", record["code_list"]).strip()
        sme_code_number = None
        if "JECxxxx" in record["code_list"]:
            sme_code_number = ""
        else:
            s = re.findall(r'(?<!\d)\d{4}(?!\d)', record["code_list"])
            if len(s) > 0:
                sme_code_number = s[0]

        for k in FIELD_REMAP:
            if unid:
                if "ABIE"==acronym and "XML_element_name"==k:
                    continue
                source, field = FIELD_REMAP[k]
                source_dict = get_dict_from_globals(source)
                field_val = get_field(source_dict, unid, field, "")
                debug_print(f'REMAP {source}[{k}] "{field_val}"')
                d[k] = field_val
                if k=="code_list":
                    s = re.findall(r'(?<!\d)\d{4}(?!\d)', field_val)   # -> ['0678','1234','5678']
                    if len(s) > 0:
                        code_list = s[0]
                        if sme_code_number:
                            if sme_code_number==code_list:
                                sme_code_list = f'{sme_code_list} D24Aと一致.'
                            else:
                                sme_code_list = f'{sme_code_list} / D24A {field_val}'
                        elif sme_code_list:
                            sme_code_list = f'{sme_code_list} / D24A {field_val}'
                        else:
                            sme_code_list = f'D24A {field_val}'
                    elif sme_code_list:
                        sme_code_list = f'{sme_code_list} D24A定義なし'
                elif k=="TDED":
                    cl_tded = tded = None
                    cl_s = re.findall(r'(?<!\d)\d{4}(?!\d)', sme_code_list)
                    if len(cl_s) > 0:
                        cl_tded = cl_s[0]
                    s = re.findall(r'(?<!\d)\d{4}(?!\d)', field_val)
                    if len(s) > 0:
                        tded = s[0]
                    if not tded:
                        tded = cl_tded if cl_tded else ""
                    if tded:
                        if code_list!=tded:
                            sme_code_list = f'{sme_code_list} / UNTDED {tded}'
                        t = tded_dict.get(tded,None)
                        if t:
                            code_name = t.get("Code name","")
                            url       = t.get("URL","")
                            desc      = t.get("Desc","")
                            repr      = t.get("Repr","") 
                            note      = t.get("Note","") 
                            description = f" {code_name} <{desc}> ({repr}) {note} {url}"
                            if "TDED" in sme_code_list:
                                sme_code_list = re.sub(tded, description, sme_code_list)
                            else:
                                sme_code_list = f'{sme_code_list} / UNTDED{description}'
                elif k == "submitted_definition":
                    s = re.findall(r'(?<!\d)\d{4}(?!\d)', field_val)
                    if len(s) > 0:
                        submitted_definition = s[0]
                        sme_code_list = f'{sme_code_list} / D24A定義文:{submitted_definition}'
            if k not in d:
                d[k] = ""
            if not d[k] and k in ["multiplicity","multiplicity_sme"]:
                if not d[k]:
                    if acronym in ["ASMA","ASBIE"] and not d[k]:
                        d[k] = "0..n"
                    elif acronym not in ["MA", "ABIE"]:
                        d[k] = "0..1"
        if sme_code_list:
            debug_print(f'{d["label_sme"]} {d["code_list"]}')
            d["code_list"] = sme_code_list

        x = {}
        for k in FSM_FIELDS:
            if k in d:
                x[k] = d[k]
            else:
                x[k] = ""

        return x

    def remove_selector(record):
        def pick_condition_in_paren(s: str) -> str | None:
            m = re.search(r'[（(]([^()（）]*)[)）]', s)   # 最初の (…) / （…） を取得（ネスト不可）
            if not m:
                return None
            inside = m.group(1).strip().replace('／', '/')  # 全角スラッシュを半角に
            return inside

        def clean(s):
            if s:
                # s = re.sub(r"\s*\[[^\]]*\]", "", s).strip()
                # s = re.sub(r"<Hdr>\s*", "", s).strip()
                base = re.sub(r"\s*\([^\]]*\)", "", s).strip()
                condition = pick_condition_in_paren(s)
                if condition:
                    s = f'({condition}) {base}'
                else:
                    s = base
            return s

        data = record

        class_term = clean(record["class_term"])
        data["class_term"] = class_term

        associated_class = clean(record["associated_class"])
        data["associated_class"] = associated_class

        element = clean(record["element"])
        data["element"] = element

        # if "xpath" in data:
        #     xpath = clean(record["xpath"])
        #     data["xpath"] = xpath

        return data

    """
    ここからメイン
    """
    path_list = [""]
    class_conditions = [(None, None, None)]  # (property_term, selector, category)
    root_id = "JP00000000"
    fsm_records = []
    _class_term_cache = ""  # MA で得た class_term を ASMA で利用
    bbie_sequence = None
    sc_sequence = None
    # bsm_dict = {} if 'bsm_dict' not in globals() else bsm_dict  # 既存があれば再利用
    # "nr,category,UNID,acronym,name1,name2,name3,name4,name5,name6,name7,name8,name9,name10,name11,name12,name13,name14,label_sme,label_csv,definition_sme,multiplicity_sme,selector,fixed_value,version,code_list,issueing_agency,input_method,input_value,xml_imput_sing,selfbilling,amendment_selfbilling,single_selfbilling,core_selfbilling,accounting,JP PINT v1.0,Id,Business Term,Card.
    trace_print(f'\n-- Parse {in_file} --')
    with open(in_file, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            acronym = row.get("acronym", "")
            if not acronym:
                continue
            if acronym == "END":
                break

            # 行の基本データ
            fsm_data = row_to_fsm_data(row)

            level = fsm_data["level"]
            den = fsm_data["DEN"]
            # カテゴリ短縮
            cat_raw = fsm_data.get("category", "")
            category = "Hdr" if cat_raw == "ヘッダ部" else ("Lin" if cat_raw == "明細部" else "")

            # DEN の分解
            if "SC"!=acronym:
                class_term, property_term, representation_term, associated_class = split_den_by_acronym(den, acronym)
                attribute_term = None
            else:
                if attribute_term and "@" in attribute_term:
                    _property_term = attribute_term[:attribute_term.index("@")-1]
                else:
                    _property_term = "{}. {}".format(property_term, representation_term)
                _, property_term_, representation_term, associated_class = split_den_by_acronym(den, acronym)
                attribute_term = "{}/@{}".format(_property_term, property_term_)

            selector = None
            if "SC"!=acronym:
                # 条件（selector, property, category）の積み上げ
                selector = row.get("selector", "")
                while len(class_conditions) < 2 + level:
                    class_conditions.append((None, None, None))
                while len(class_conditions) > 2 + level:
                    del class_conditions[-1]
                if acronym in ("MA", "ASMA", "ASBIE") and (selector or property_term or category):
                    class_conditions[level + 1] = (property_term, selector, category)
                # 用いる条件の取り出し
                sel_here  = class_conditions[level][1]  if level < len(class_conditions) and class_conditions[level]  else ""
                cat_here  = class_conditions[level][2]  if level < len(class_conditions) and class_conditions[level]  else ""
                prop_upto = len(class_conditions) - 1   # 最後（自分）を除いた path

            # acronym ごとの表示 term 調整
            if acronym in ("ASMA", "ASBIE"):
                if "ASMA"==acronym:
                    class_term = _class_term_cache
                else:
                    prop_path_ = property_path(class_conditions, prop_upto - 1)
                    class_term = decorate(class_term, sel_here, prop_path_, cat_here)
                if associated_class:
                    _sel  = class_conditions[level + 1][1]
                    _cat  = class_conditions[level + 1][2]
                    _prop = property_path(class_conditions, len(class_conditions))
                    associated_class = decorate(associated_class, _sel, _prop, _cat)
                property_term = ""

            elif acronym == "MA":
                _sel  = class_conditions[level + 1][1]
                _cat  = class_conditions[level + 1][2]
                _prop = property_path(class_conditions, len(class_conditions))
                class_term = decorate(class_term, _sel, _prop, _cat)
                _class_term_cache = class_term

            elif acronym == "ABIE":
                _sel  = class_conditions[level + 1][1]
                _cat  = class_conditions[level + 1][2]
                _prop = property_path(class_conditions, len(class_conditions))
                class_term = decorate(class_term, _sel, _prop, _cat)

            elif acronym == "BBIE":
                _sel  = class_conditions[level][1]
                _cat  = class_conditions[level][2]
                _prop = property_path(class_conditions, len(class_conditions))
                class_term = decorate(class_term, _sel, _prop, _cat)
                if fsm_data["selector"]:
                    property_term += "[{}]".format(fsm_data["selector"])
                if fsm_data["sequence"]:
                    bbie_sequence = fsm_data["sequence"]
                else:
                    bbie_sequence += 1
                sc_sequence = 0

            elif acronym == "SC":
                sc_sequence += 0.1
                fsm_data["sequence"] = bbie_sequence + sc_sequence

            else:
                continue

            # LHM 書き出しに必要な基本項目
            fsm_data["class_term"] = class_term
            fsm_data["property_term"] = property_term
            fsm_data["representation_term"] = representation_term
            fsm_data["associated_class"] = associated_class

            # XPath 用の path_list
            ensure_level(path_list, level)

            # acronym 別の LHM/BSM 処理
            bsm_data = None
            attribute = ""
            if acronym == "MA":
                fsm_data["type"] = "C"
                fsm_data["property_type"] = "Class"
                fsm_data["level"] = 0
                element = normalize_text(class_term)
                fsm_data["element"] = element
                xml_name = element
                fsm_data["XML_element_name"] = xml_name
                
                if not row.get("UNID"):
                    fsm_data["UNID"] = root_id

                root_term = fsm_data["class_term"]

                # BSM（クラス作成）
                bsm_data = fsm_data.copy()
                bsm_data["level"] = 1
                bsm_data["multiplicity_sme"] = "1..1"
                bsm_dict[root_term] = bsm_data
                if "properties" not in bsm_dict[root_term]:
                    bsm_dict[root_term]["properties"] = {}

            elif acronym == "ASMA":
                fsm_data["type"] = "C"
                fsm_data["property_type"] = "Composition"
                fsm_data["level"] = 1
                attribute = normalize_attribute(associated_class)
                element = normalize_text(attribute)
                fsm_data["element"] = element
                element = normalize_text(associated_class)
                if selector:
                    element += f'[{normalize_selector(selector)}]'
                fsm_data["element"] = element
                _c = re.sub(r"\(.*?\)\s*|\[.*?\]\s*|<.*?>\s*", "", root_term).strip()
                _a = re.sub(r"\(.*?\)\s*|\[.*?\]\s*|<.*?>\s*", "", associated_class).strip()
                fsm_data["DEN"] = "{}. Specified. {}".format(_c, _a)

                # BSM（Composition ＆ 子クラス自動生成）
                bsm_data = fsm_data.copy()
                bsm_data["level"] = 2
                bsm_data["associated_class"] = associated_class
                bsm_data["class_term"] = root_term
                bsm_dict[root_term]["properties"][associated_class] = bsm_data

                _b = bsm_data.copy()
                _b["type"] = "C"
                _b["property_type"] = "Class"
                _b["acronym"] = "ABIE"
                _b["level"] = 1
                _b["multiplicity"] = ""
                _b["multiplicity_sme"] = ""
                _b["class_term"] = associated_class
                _b["associated_class"] = ""
                _b["DEN"] = "{}. Details".format(_a)
                bsm_dict[associated_class] = _b
                if "properties" not in bsm_dict[associated_class]:
                    bsm_dict[associated_class]["properties"] = {}

            elif acronym == "ASBIE":
                fsm_data["type"] = "C"
                fsm_data["property_type"] = "Composition"
                fsm_data["property_term"] = ""
                fsm_data["associated_class"] = associated_class
                attribute = normalize_attribute(associated_class)
                element = normalize_text(attribute)
                if selector:
                    element += f'[{normalize_selector(selector)}]'
                fsm_data["element"] = element
                xml_name = element[:element.index("[")] if "[" in element else element
                fsm_data["XML_element_name"] = xml_name

                # BSM (Composition)
                bsm_data = fsm_data.copy()
                bsm_data["level"] = 2
                if class_term not in bsm_dict:
                    bsm_dict[class_term] = {"properties": {}}
                else:
                    pass
                bsm_dict[class_term]["properties"][associated_class] = bsm_data

            elif acronym == "ABIE":
                fsm_data["type"] = "C"
                fsm_data["property_type"] = "Class"

                # BSM (Class)
                bsm_data = fsm_data.copy()
                bsm_data["level"] = 1
                _class_term = bsm_data["class_term"]
                if class_term not in bsm_dict:
                    bsm_dict[class_term] = bsm_data
                else:
                    pass
                if "properties" not in bsm_dict[class_term]:
                    bsm_dict[_class_term]["properties"] = {}

            elif acronym in ["BBIE","SC"]:
                fsm_data["type"] = "A"
                fsm_data["property_type"] = "Attribute"
                if "BBIE"==acronym:
                    fsm_data["property_term"] = property_term
                    attribute = "{}. {}".format(property_term, representation_term)
                else:
                    fsm_data["property_term"] = attribute_term
                    attribute = "{}. {}".format(attribute_term, representation_term)
                fsm_data["representation_term"] = representation_term
                if fsm_data["property_term"] == "Identification" and fsm_data["representation_term"] == "Identifier":
                    fsm_data["identifier"] = "PK"
                element = normalize_text(attribute)
                fsm_data["element"] = element
                if "SC"==acronym:
                    attribute = element[element.index("@"):]
                    fsm_data["XML_element_name"] = attribute
                else:
                    path_list[level] = element
                # fsm_data["xpath"] = "/" + "/".join(path_list)

                # BSM (Attribute)
                bsm_data = fsm_data.copy()
                bsm_data["level"] = 2
                if class_term not in bsm_dict:
                    pass

                if attribute not in bsm_dict[class_term]["properties"]:
                    bsm_dict[class_term]["properties"][attribute] = bsm_data
                    multiplicity = bsm_data["multiplicity"]
                    multiplicity_sme = bsm_data["multiplicity_sme"]
                    check = check_muliplicity(bsm_data["DEN"], bsm_data["multiplicity"], bsm_data["multiplicity_sme"])
                    if check:
                        bsm_dict[class_term]["properties"][attribute]["multiplicity_sme"] = check
                else:
                    _bsm_data = bsm_dict[class_term]["properties"][attribute]
                    multiplicity = _bsm_data["multiplicity"]
                    multiplicity_sme = _bsm_data["multiplicity_sme"]
                    multiplicity_sme2 = bsm_data["multiplicity_sme"]
                    check = check_muliplicity(bsm_data["DEN"], multiplicity, multiplicity_sme, multiplicity_sme2)
                    if check:
                        bsm_dict[class_term]["properties"][attribute]["multiplicity_sme"] = check

            if attribute:
                debug_print(f'{bsm_data["acronym"]} class:"{class_term}" [{bsm_data["multiplicity"]}] SME:[{bsm_data["multiplicity_sme"]}] attribute:"{attribute} " label_sme:"{bsm_data["label_sme"]}"')
            elif "ABIE"!=acronym:
                debug_print(f'{bsm_data["acronym"]} class:"{class_term}" [{bsm_data["multiplicity"]}] SME:[{bsm_data["multiplicity_sme"]}] label_sme:"{bsm_data["label_sme"]}"\n')
            else:
                debug_print(f'{bsm_data["acronym"]} class:"{class_term}" label_sme:"{bsm_data["label_sme"]}"')

            # レコード出力（ABIE も含めるならこのまま／除外したいなら条件を付ける）
            fsm_records.append(fsm_data)

    # 逆引きマップ: UNID -> fsm_records内のインデックス
    index_by_den = {}
    fsm_records_ = []

    for class_term, data in bsm_dict.items():
        # クラス見出しを追加
        debug_print(f"\n{class_term}")
        if "sme_nr" not in data:
            pass
        fsm_records_.append(data)
        class_den = f"{class_term}. Details"
        index_by_den[class_den] = len(fsm_records_) - 1

        _class_term = re.sub(r"\(.*?\)\s*|\[.*?\]\s*|<.*?>\s*", "", class_term).strip() # re.sub(r"(\(.*?\)\s*)?(\].*?\]\s*)?(<.*?>\s*)?", "", class_den)
        suffix = class_term.replace(_class_term,"").strip()

        used_dens = []
        bsm_properties = data["properties"]
        for attribute, bsm_data in bsm_properties.items():
            """
            attribute
                Attribute: f"{property_term}. {representation}"
                Composition: f"{associated_class} ({property path})"
            """
            property_acronym = bsm_data["acronym"]
            property_type = bsm_data["property_type"]
            representation_term = bsm_data["representation_term"]
            property_den = bsm_data["DEN"]
            _bsm_den = f"{class_term}. {attribute}"
            used_dens.append(_bsm_den)
            multiplicity_sme = bsm_data["multiplicity_sme"]
            multiplicity_mbie = bsm_data["multiplicity"]

            if property_den in mbie_dict_den:
                mbie_data = mbie_dict_den[property_den]
                mbie_representation_term = mbie_data["representation_term"]
                if representation_term!=mbie_representation_term:
                    bsm_data["representation_term"] = mbie_representation_term                
                multiplicity_mbie = mbie_data["multiplicity"]
                if multiplicity_mbie != multiplicity_sme:
                    trace_print(f'"{_bsm_den}"の多重度をD24Aの[{multiplicity_mbie}]から[{multiplicity_sme}]に変更.')
                    error = None
                    if multiplicity_mbie[-1]=="1" and multiplicity_sme[-1]=="n":
                        multiplicity_sme = f"{multiplicity_sme} D24Aの多重度の上限 1 を超えており不正."
                        error = True
                    if multiplicity_mbie[0]=="1" and multiplicity_sme[0]=="0":
                        multiplicity_sme = f"{multiplicity_sme} D24Aでは必須(minOccurs='1')とされており任意にはできない."
                        error = True
                    if error:
                        multiplicity_sme = f"*Error* {multiplicity_sme}"
                    bsm_data["multiplicity_sme"] = multiplicity_sme
            else: # MBIEs24A 定義表に未定義
                if property_acronym in ["ASMA", "SC"]:
                    multiplicity = "0..1"
                else:
                    multiplicity = "D24Aで未定義"
                bsm_data["multiplicity"] = multiplicity
            # debug_print(f'{property_acronym} {class_term} : {_bsm_den}')
            fsm_records_.append(bsm_data)
            index_by_den[_bsm_den] = len(fsm_records_) - 1

        mbie_properties = [
            (den, data)
            for den, data in mbie_dict_den.items()
            if den.startswith(_class_term) and data["acronym"] in ["ASBIE","BBIE","SC"]
        ]

        for mbie_den, mbie_data in mbie_properties:
            multiplicity_mbie = mbie_data["multiplicity"]
            _mbie_den = f'{mbie_den[:mbie_den.index(".")]} {suffix}. {mbie_den[2+mbie_den.index("."):]}'
            if _mbie_den not in used_dens:
                acronym = mbie_data["acronym"]
                if acronym not in ["MA", "ASMA", "ABIE"]:
                    mbie_data["multiplicity"] = multiplicity_mbie
                    if multiplicity_mbie and multiplicity_mbie[0] == "1": # 必須要素は削除不可
                        mbie_data["multiplicity_sme"] = f"*Error* D24Aで定義された必須項目[{multiplicity_mbie}]は、削除不可."
                    else:
                        mbie_data["multiplicity_sme"] = "0..0"
            else:
                property_text = _mbie_den[2 + _mbie_den.index("."):]
                if mbie_data['property_type'] == 'Composition':
                    property_text = re.sub(r"^([^\.]+)\.\s*(.+)$", r"(\1) \2", property_text)
                prop = [v for k, v in bsm_properties.items() if property_text == k]
                if prop:
                    multiplicity_sme = prop[0].get("multiplicity_sme", "0..0")
                else:
                    multiplicity_sme = "0..0"
                if multiplicity_mbie.endswith("1") and multiplicity_sme.endswith("n"):
                    mbie_data["multiplicity_sme"] = f"*Error* 最大繰り返し回数[{multiplicity_sme}]が、D24Aで定義された繰り返し回数[{multiplicity_mbie}]を超えることは不可."
                else:
                    mbie_data["multiplicity_sme"] = multiplicity_sme

            if "*Error*" in mbie_data.get("multiplicity_sme", ""):
                debug_print(f'fsm_records update {mbie_den} Multiplicity SME:{mbie_data["multiplicity_sme"]} MBIE:{multiplicity_mbie}')

            # ---- 同じ DEN が既に fsm_records_ にあるなら multiplicity_sme を上書き ----
            if _mbie_den not in index_by_den:
                # なければ追加し、索引も更新
                _mbie_data = mbie_data.copy()
                class_term = _mbie_data["class_term"]
                if not suffix:
                    _class_term = class_term
                elif "["==suffix[0]:
                    _class_term = f'{class_term}{suffix}'
                else:
                    _class_term = f'{class_term} {suffix}'
                _mbie_data["class_term"] = _class_term
                _mbie_data["sme_nr"] = ""

                if (_mbie_data["mbie_nr"], _mbie_data["class_term"]) not in [(x["mbie_nr"], x["class_term"]) for x in fsm_records_ if "mbie_nr" in x]:
                    property_type = _mbie_data["property_type"]
                    if "Composition"==property_type:
                        associated_class = _mbie_data["associated_class"]
                        property_term = _mbie_data["property_term"]
                        if property_term:
                            _mbie_data["associated_class"] = f"{associated_class} ({property_term})"
                            _mbie_data["property_term"] = ""
                    # _mbie_data["sme_nr"] = 9999
                    debug_print(f'{_mbie_data["acronym"]} {_class_term} : {_mbie_den} -ADD to fsm_records-')
                    fsm_records_.append(_mbie_data)
                    index_by_den[_mbie_den] = len(fsm_records_) - 1

    debug_print(f"\n** Write to a FSM file {fsm_file} **")
    fsm_out = []
    # FSM_FIELDS = [x for x in FSM_FIELDS if x != 'xpath']
    for record in fsm_records_:
        # 事前にすべての出力列を空で初期化（列欠落防止）
        data = {k: "" for k in FSM_FIELDS}
        for k in FSM_FIELDS:
            if k in record:
                data[k] = record[k]
        if record["acronym"] in ["ASMA","SC"]:
            data["multiplicity"] = "0..1"
        fsm_out.append(data)

    # class_term（文字列）,property_type（文字列）, sequence（数値）, sme_nr（数値）の順で安定ソート
    # 並べ順の優先度（未定義は 99 で最後）
    _PT_ORDER = {"CLASS": 0, "ATTRIBUTE": 1, "COMPOSITION": 2}
    def pt_rank(r):
        pt = r.get("property_type", "")
        pt = (pt or "").strip().upper()
        return _PT_ORDER.get(pt, 99)

    _FLOAT_RE = re.compile(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$')

    def sme_rank(r):
        """実数なら (0, float値)、非数値なら (1, 0.0) を返し、非数値を後方へ。"""
        x = r.get("sme_nr", "")
        # すでに数値型ならそのまま採用
        if isinstance(x, (int, float)):
            return (0, float(x))
        # 文字列等は実数表現か判定
        s = str(x).strip()
        if s and _FLOAT_RE.fullmatch(s):
            return (0, float(s))
        # 非数値
        return (1, 0.0)

    def sequence_rank(r):
        """数値なら (0, 数値)、非数値なら (1, 0) を返し、非数値を後方へ。"""
        s = str(r.get("sequence", "")).strip()
        if s and (s.isdigit() or (s[0] in "+-" and s[1:].isdigit())):
            return (0, int(s))
        return (1, 0)

    _fsm_records = sorted(
        fsm_out,
        key=lambda r: (
            (r.get("class_term", "") or ""),
            pt_rank(r),
            sequence_rank(r),
            sme_rank(r),
        ),
    )

    with open(fsm_file, mode="w", newline="", encoding="utf-8-sig") as fsmfile:
        writer = csv.DictWriter(fsmfile, fieldnames=FSM_FIELDS)
        writer.writeheader()
        writer.writerows(_fsm_records)

    trace_print(f'Wrote {fsm_file}')

    # Write to a BSM file
    debug_print(f"\n** Write to a BSM file {bsm_file} **")
    bsm_records = []
    for class_den, data in bsm_dict.items():
        bsm_records.append(data)

        bsm_properties = data["properties"]
        sorted_items = sorted(
            ((name, property_data) for name, property_data in bsm_properties.items()),
            key=lambda x: x[1]["sme_nr"] or 0,
        )

        used_dens = []
        for _, bsm_data in sorted_items:
            acronym = bsm_data["acronym"]
            unid = bsm_data["UNID"]
            den_property = bsm_data["DEN"]
            used_dens.append(den_property)
            multiplicity_sme = bsm_data["multiplicity_sme"]
            multiplicity_mbie = ""
            if den_property in mbie_dict_den:
                mbie_data = mbie_dict_den[den_property]
                multiplicity_mbie = mbie_data["multiplicity"]
                if multiplicity_mbie!=multiplicity_sme:
                    check = check_muliplicity(den_property, multiplicity_mbie, multiplicity_sme)
                    bsm_data["multiplicity_sme"] = check
                    trace_print(f'{unid} {den_property} modified multiplicity [{multiplicity_sme}] from [{multiplicity_mbie or "None"}] in D24A.')
            else: # MBIEs24A 定義表に未定義
                if acronym in ["ASMA","SC"]:
                    multiplicity = "0..1"
                else:
                    multiplicity = "D24Aで未定義"
                bsm_data["multiplicity"] = multiplicity
            if "SC"!=acronym:
                bsm_records.append(bsm_data)
            # debug_print(f'bsm_records append {den_property} SME:{multiplicity} MBIE:{multiplicity_mbie}')

        mbie_properties = [
            (den, data)
            for den, data in mbie_dict_den.items()
            if den.startswith(class_den) and data["acronym"] in ["ASBIE","BBIE"]
        ]

        for mbie_den, mbie_data in mbie_properties:
            if mbie_den not in used_dens and (mbie_data["mbie_nr"], mbie_data["class_term"]) not in [(x["mbie_nr"], x["class_term"]) for x in bsm_records]:
                _mbie_data = mbie_data.copy()
                mbie_acronym = _mbie_data["acronym"]
                multiplicity_mbie = _mbie_data["multiplicity"]
                if mbie_acronym not in ["MA","ASMA","ABIE"] and mbie_den not in bsm_properties:
                    _mbie_data["multiplicity"] = multiplicity_mbie
                    if multiplicity_mbie and "1"==multiplicity_mbie[0]: # 必須要素は削除不可
                        _mbie_data["multiplicity_sme"] = f"*Error* {multiplicity_mbie} 必須要素は削除不可."
                    else:
                        _mbie_data["multiplicity_sme"] = "0..0"
                        # continue
                    bsm_records.append(_mbie_data)
                if "*Error*" in  _mbie_data["multiplicity_sme"]:
                    debug_print(f'bsm_records append {mbie_den} Multiplicity SME:{_mbie_data["multiplicity_sme"]} MBIE:{multiplicity_mbie}')


    # BSM_FIELDS = [x for x in BSM_FIELDS if x != 'xpath']

    # --- TitleCase 分割 & 語順反転キー（CITrade / CIIH 等に対応） ---
    _TOKEN_RE = re.compile(r'[A-Z]{2,}[A-Za-z]+|[A-Z][a-z]+|[A-Z]{2,}|\d+')
    def title_rev_key(name: str) -> str:
        toks = _TOKEN_RE.findall(name or "")
        return " ".join(reversed(toks)).lower()

    # --- クラス名の装飾を落としてベース名を得る: (...) / [...] / <...> を除去 ---
    _DECOR_RE = re.compile(r'\s*(\([^)]*\)|\[[^\]]*\]|<[^>]*>)')
    def base_class_name(s: str) -> str:
        return _DECOR_RE.sub('', s or '').strip()

    # --- property_type の優先度（必要なら調整）---
    _PT_ORDER = {"CLASS": 0, "SPECIALIZED CLASS": 1, "ATTRIBUTE": 2, "REFERENCE ASSOCIATION": 3, "COMPOSITION": 4}
    def pt_rank(r):
        pt = (r.get("property_type") or "").strip().upper()
        return _PT_ORDER.get(pt, 99)

    # ここまでヘルパー。以下、出力前処理を置き換え
    bsm_out = []
    registered_bsm = []
    # BSM_FIELDS = [x for x in BSM_FIELDS if x != 'xpath']

    for record in bsm_records:
        # 欠落列の穴埋め
        data = {k: "" for k in BSM_FIELDS}
        if record.get("acronym") == "SC":
            continue
        if record.get("multiplicity_sme") == "0..0":
            continue
        for k in FSM_FIELDS:
            if k in record:
                data[k] = record[k]
        data = remove_selector(data)

        class_term = data.get("class_term", "")
        mbie_nr = data.get("mbie_nr", "")
        key = f"{class_term}_{mbie_nr}"
        if key in registered_bsm:
            continue
        registered_bsm.append(key)
        bsm_out.append(data)

    bsm_records_ = [{k: v for k, v in rec.items() if k in BSM_FIELDS} for rec in bsm_out]

    # --- ここをソートキー差し替え ---
    _bsm_records = sorted(
        bsm_records_,
        key=lambda r: (
            # 1) クラス名（装飾除去）の TitleCase 反転キー
            title_rev_key(base_class_name(r.get("class_term", ""))),
            # 2) タイブレーク：元のクラス名（装飾込み）
            r.get("class_term", "") or "",
            # 3) property_type の優先度
            pt_rank(r),
            # 4) sequence（既存のランク関数を使用）
            sequence_rank(r),
        ),
    )



    with open(bsm_file, mode="w", newline="", encoding="utf-8-sig") as bsmfile:
        writer = csv.DictWriter(bsmfile, fieldnames=BSM_FIELDS)
        writer.writeheader()
        writer.writerows(_bsm_records)

    trace_print(f'Wrote {bsm_file}')

    """
    Graph walk
    """
    object_class_dict = copy.deepcopy(bsm_dict)

    LHM_model = []
    LIFO_list = []
    selected_class = list(object_class_dict.keys())
    if root_term in selected_class:
        debug_print(f"- root_term parse_class('{root_term}')")
        parse_class(root_term)
    """
    Write to graphwalk result LHM
    """
    lhm_records = []
    csv_levels = [None]
    is_multiple = False
    for record in LHM_model:
        # Keep only requested fields
        data = {k: record.get(k) for k in LHM_FIELDS if k in record}

        if "multiplicity_csv" not in data:
            data["multiplicity_csv"] = ""

        acronym = data["acronym"]
        level = data["level"]
        element = data["element"]

        if "ASMA"==acronym:
            if not data["multiplicity"]:
                data["multiplicity"] = "0..1"
            if not data["multiplicity_sme"]:
                data["multiplicity_sme"] = "0..1"
            if not data["multiplicity_csv"]:
                data["multiplicity_csv"] = "0..1"

        # XPath
        ensure_level(path_list, level)
        
        data["xpath"] = ""
        if acronym == "MA":
            path_list[level] = f"rsm:{element}"
            data["xpath"] = "/".join(path_list)
        elif acronym == "ASMA":
            path_list[level] = f"rsm:{element}"
            data["xpath"] = "/".join(path_list)
        elif acronym == "ASBIE":
            path_list[level] = f"ram:{element}"
            data["xpath"] = "/".join(path_list)
        elif acronym == "ABIE":
            pass
        elif acronym in ["BBIE","SC"]:
            if "SC"==acronym:
                ensure_level(path_list, level + 1)
                path_list[1+level] = attribute
                attribute = element[element.index("@"):]
                data["XML_element_name"] = attribute
            else:
                path_list[level] = f"ram:{element}"
            data["xpath"] = "/".join(path_list)
        if data["xpath"]:
            debug_print(f'path_list {path_list}')
            debug_print(f'{data["DEN"]} xpath:{data["xpath"]}')

        if "MA"==acronym:
            ensure_level(csv_levels, level + 1)
            _level = level
            occurence = ""
            csv_levels[level] = _level
            csv_levels[level + 1] = _level + 1
        elif acronym in ["ASMA","ASBIE"]:
            ensure_level(csv_levels, level + 1)
            multiplicity_sme = data["multiplicity_sme"]
            check = check_muliplicity(data["DEN"], data["multiplicity"], multiplicity_sme)
            if check:
                data["multiplicity_sme"] = check
                if "*E" in check:
                    match = re.findall(r'\b\d+\.\.(?:\d+|n)\b', check, re.IGNORECASE)
                    if match:
                        multiplicity_sme = match[0]
            occurence_min = multiplicity_sme[0]
            occurence_max = multiplicity_sme[-1]
            is_multiple = "n"==occurence_max
            csv_level = csv_levels[level]
            if is_multiple:
                csv_levels[level+1] = csv_level + 1
                _level = csv_levels[level]
                occurence = f'{occurence_min}..{occurence_max}'
            else:
                csv_levels[level+1] = csv_level
                _level = ""
                occurence = ""
                data["label_csv"] = ""
        elif "ABIE"==acronym:
            _level = ""
            occurence = ""
            data["label_csv"] = ""
        elif acronym in ["BBIE","SC"]:
            _level = csv_levels[level]
            occurence = "0..1"
        else:
            _level = ""
            occurence = ""
            data["label_csv"] = ""
        data["level_csv"] = _level
        data["multiplicity_csv"] = occurence
        debug_print(f'csv_levels {csv_levels}')
        debug_print(f'{data["sme_nr"]} {level} [{multiplicity_sme}] {_level} [{occurence}] {data["acronym"]} {data["label_csv"]}')                      
        lhm_records.append(data)

    # _lhm_records = sorted(
    #     lhm_records,
    #     key=lambda r: (
    #         sme_rank(r),
    #     ),
    # )

    with open(lhm_file, mode="w", newline="", encoding="utf-8-sig") as lhmfile:
        writer = csv.DictWriter(lhmfile, fieldnames=LHM_FIELDS)
        writer.writeheader()
        writer.writerows(lhm_records)

    trace_print(f'Wrote {lhm_file}')

    trace_print("END")

if __name__=="__main__":
    main()
