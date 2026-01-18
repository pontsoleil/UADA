#!/usr/bin/env python3
# coding: utf-8
"""
bie_to_fsm.py

Generates Foundation Semantic Model (FSM) CSV file from UN/CEFACT CCL BIEs

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2026-01-13
Last Modified: 2026-01-13

MIT License

(c) 2023-2025 SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

ABOUT THIS SCRIPT
enerate a Foundational Semantic Model (FSM) CSV from UN/CEFACT CCL BIE rows.

This script:
- reads one or more BIE CSV files,
- registers all classes first (to allow forward references),
- registers properties and normalises property terms / associations,
- derives candidate abstract (super) classes from underscore-based class naming,
- classifies properties using inheritance status codes (e.g., Shared/Aligned/Extension/Inheritance/Modified/Prohibited),
- outputs a flattened FSM CSV with stable IDs.
"""

import os
import argparse
import sys
import csv
import re
import copy
from collections import OrderedDict
from collections.abc import Mapping, Sequence

def abbreviate_term(term: str, max_len: int = 6) -> str:
    """
    Abbreviates each word in the input term according to the following rules:

    - Remove common stop_words (e.g., to, with, on, of, etc.).
    - Remove any symbol characters: !"#$%&'()=~|\^-@`[]{}:;+*/?.,<>\_
    - Capitalize the first letter of each remaining word.
    - Keep the first vowel of each word, remove all other vowels.
    - If the abbreviation length is >= max_len:
        - Keep only the first vowel and remove the rest.
        - If the first character is a vowel and the result is still long,
          shorten further (preserving start/end).
    - Ensure the abbreviated word is shorter than the original word.
    - Words of length 3 or less are returned unchanged.
    """
    if max_len < 4:
        raise ValueError("max_len must be >= 4 to allow meaningful abbreviation.")

    stop_words = {
        'a', 'an', 'the',
        'to', 'with', 'on', 'of', 'in', 'for', 'at', 'by', 'from', 'as',
        'about', 'into', 'over', 'after', 'under', 'above', 'below'
    }
    vowels = 'aeiouAEIOU'

    # Remove symbols
    term = re.sub(r'[!"#$%&\'()=~|\\^\-@`\[\]{}:;+*/?,.<>\_]', '', term)

    def abbreviate_word(word: str) -> str:
        if len(word) <= 3:
            return word  # already short

        chars = [word[0]]  # keep first character
        first_vowel_found = word[0] in vowels

        # Keep consonants; keep only the first vowel encountered (if any)
        for c in word[1:]:
            if c.lower() not in vowels:
                chars.append(c)
            elif not first_vowel_found:
                chars.append(c)
                first_vowel_found = True

        abbr = ''.join(chars)

        # If abbreviation is still too long, remove all vowels except the first vowel
        if len(abbr) >= max_len:
            first_vowel_index = next((i for i, c in enumerate(abbr) if c.lower() in vowels), None)
            if first_vowel_index is not None:
                abbr = ''.join(
                    abbr[i] for i in range(len(abbr))
                    if abbr[i].lower() not in vowels or i == first_vowel_index
                )

            # If the first character is a vowel and abbreviation is still long,
            # preserve the start and end
            if abbr and abbr[0].lower() in vowels and len(abbr) > max_len:
                # keep (max_len-1) prefix + last char
                abbr = abbr[:max_len - 1] + abbr[-1]

        # Final fallback: truncate if still too long
        if len(abbr) > max_len:
            abbr = abbr[:max_len]

        # Must be shorter than original (otherwise return original word)
        return abbr if len(abbr) < len(word) else word

    # Tokenize and filter stop_words
    words = re.findall(r'\w+', term)
    filtered = [w.capitalize() for w in words if w.lower() not in stop_words]

    # Abbreviate remaining words
    abbreviated = [abbreviate_word(w) for w in filtered]
    return ' '.join(abbreviated)

def LC3(term):
    """
    Lower camel case converter (e.g., 'Entity Phone Number' → 'entityPhoneNumber')
    """
    parts = re.split(r'\s+', term.strip())
    return parts[0].lower() + ''.join(p.title() for p in parts[1:])

def split_camel_case(identifier):
    """
    Split camelCase or CamelCase into a list of words,
    allowing numbers and symbols to remain within each chunk.
    Splitting occurs at capital letters.
    """
    # term = re.findall(r'[^A-Z]*[A-Z][^A-Z]*', identifier)
    term = re.findall(r'[A-Z]?[a-z]+(?:[0-9]+)?|[A-Z]+(?:[0-9]+)?(?![a-z])', identifier)
    if not term:
        term = [identifier]
    return term

def normalize_text(text):
    # Remove (choice) or (sequence), including preceding space
    text = re.sub(r'\s*\((choice|sequence)\)', '', text, flags=re.IGNORECASE)
    # string to contain only alphanumeric characters (A–Z, a–z, 0–9)
    text = re.sub(r'[^A-Za-z0-9]+', ' ', text).strip()
    # Replace multiple spaces with a single space and trim leading/trailing spaces
    text = re.sub(r'\s+', ' ', text)
    return text

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

# Utility function to create full file paths
def is_file_in_use(file_path):
    try:
        # Attempt to open the file in 'r+' mode (read/write mode)
        with open(file_path, 'r+'):
            result = 'OK'
    except PermissionError:
        # 'PermissionError' indicates the file is in use by another process
        print(f"The file {file_path} is in use.")
        result = 'IN_USE'
    except FileNotFoundError:
        # If the file does not exist, create it
        print(f"The file {file_path} does not exist. Creating new file...")
        try:
            # Open the file in 'w+' mode to create it if it doesn't exist
            with open(file_path, 'w+') as new_file:
                pass # Creating the file
            result = 'CREATED'
            print(f"File {file_path} has been created.")
        except Exception as e:
            print(f"Error while creating file: {e}")
            result = 'ERROR_CREATING_FILE'
    return result

def file_path(pathname):
    _pathname = pathname.replace("/", os.sep)
    if os.sep == _pathname[0:1]:
        return _pathname
    else:
        dir = os.path.dirname(__file__)
        return os.path.join(dir, _pathname)

class Processor:
    def __init__(
            self,
            bie_file,
            fsm_file,
            encoding,
            trace,
            debug
        ):
        """
        Initializes the Processor with file paths and configurations.
        """
        self.bie_file = file_path(bie_file)
        if not bie_file or not os.path.isfile(self.bie_file):
            print(f'[INFO] No input Business Entity Model (MBIE/RBIE) file {self.bie_file}.')
            sys.exit()

        self.fsm_file = fsm_file.replace('/', os.sep)
        self.fsm_file = file_path(self.fsm_file)
        if 'IN_USE' == is_file_in_use(self.fsm_file):
            print(f'[INFO] Foundation Semantic Model (FSM) file {self.fsm_file} is **IN USE**.')
            sys.exit()

        self.encoding = encoding if encoding else "utf-8-sig"
        self.TRACE = trace
        self.DEBUG = debug

        # Define CSV headers for internal processing and final BSM output
        self.bie_header = ['sequence', 'UNID', 'acronym', 'DEN', 'definition', 'class_term_qualifier', 'class_term', 'property_term_qualifier', 'property_term', 'datatype_qualifier', 'representation_term', 'qualified_data_type_UID', 'associated_class_qualifier', 'associated_class', 'business_term', 'usage_rule', 'sequence_number', 'occurrence_min', 'occurrence_max', 'context_categories', 'TDED', 'publication_source', 'short_name', 'BIE']
        self.header  = ['sequence', 'level', 'property_type', 'identifier', 'class_term', 'property_term', 'representation_term', 'associated_class', 'multiplicity', 'definition', 'module', 'label_local', 'definition_local']
        self.out_header = ['sequence', 'level', 'property_type', 'identifier', 'class_term', 'property_term', 'representation_term', 'associated_class', 'multiplicity', 'definition', 'module', 'label_local', 'definition_local', 'id', 'inherited']

        #  Initialize dictionaries and lists
        self.domain_dict = None

        self.object_class_dict = None

        self.current_module = None
        self.module_num = {}
        self.module_id = None
        # self.module_abbrev_dict = {}

        self.current_class = None
        self.class_num = None
        self.abstract_classes = set()

        self.LIFO_list = []
        self.FSM_list = []
        self.records = []

        # # Module dictionary for mapping module names to standardized codes
        # self.module_dict = {
        #     'Unit Type Registry': 'UT',
        #     'gen': 'GE',
        #     'cor': 'CO',
        #     'bus': 'BU',
        #     'muc': 'MC',
        #     'taf': 'TA',
        #     'ehm': 'EH',
        #     'usk': 'UK',
        #     'lnk': 'LK',
        #     'btx': 'BT',
        #     'sta': 'ST',
        #     'ext': 'EX',
        # }

        # self.module_dict = {
        #     "Accounting, audit and reporting": "AR",
        #     "Accounting, audit": "AA",
        #     "FLUX": "FX",
        #     "MSDS Reporting": "MS",
        #     "In All Contexts": "AL",
        #     "Trade": "TR",
        #     "Agricultural": "AG",
        #     "Crop Data Sheet": "CD",
        #     "Laboratory Observation": "LO",
        #     "Cattle Registration": "CR",
        #     "Traceability": "TA",
        #     "Tendering": "TN",
        #     "Pricing": "PR",
        #     "Project Management": "PM",
        #     "Customer to bank payment initiation": "CP",
        #     "Transport": "TP",
        #     "Cataloguing": "CG",
        #     "Delivering": "DV",
        #     "Invoicing": "IO",
        #     "Supply Chain": "SC",
        #     "Invoice": "IV",
        #     "Ordering": "OR",
        #     "Quotation": "QT",
        #     "Remittance": "RM",
        #     "Scheduling": "SD",
        #     "Cross Industry Trade": "CT",
        #     "Cross Industry": "CI",
        #     "Examination Notification": "EN",
        #     "Buy-Ship-Pay": "BS",
        #     "Market Survey": "MK",
        #     "Waste Movement": "WM",
        #     "Agriculture": "GR",
        #     "Partner Identification": "PI",
        #     "Procurement": "PC",
        #     "Rapid Alert System": "RA",
        #     "Rapid Alert System; MSDS Reporting": "RX",
        #     "Sanitary and Phytosanitary Measures": "SP",
        #     "Cross-Border": "CB",
        #     "Acquisition": "AQ",
        #     "Trade Billing": "TB",
        #     "Trade Finance": "TF",
        #     "Sustainability": "SU",
        #     "Negotiation": "NG",
        #     "Conformity": "CF",
        #     "Buy Ship Pay": "BY",
        #     "Statistics": "ST",
        #     "Acknowledgement": "AK",
        #     "Accounting Chart of Accounts": "CO",
        #     "Maritime Transportation": "MT",
        #     "Dangerous Goods": "DG",
        #     "Product Registration": "PD",
        #     "e-Certificate of Origin": "EO",
        # }

        # self.module_abbrev_dict = {
        #     "Accounting, audit and reporting": "aar",
        #     "Accounting, audit": "aad",
        #     "FLUX": "flx",
        #     "MSDS Reporting": "msd",
        #     "In All Contexts": "all",
        #     "Trade": "trd",
        #     "Agricultural": "agl",
        #     "Crop Data Sheet": "cds",
        #     "Laboratory Observation": "lab",
        #     "Cattle Registration": "cat",
        #     "Traceability": "trc",
        #     "Tendering": "tnd",
        #     "Pricing": "prc",
        #     "Project Management": "prj",
        #     "Customer to bank payment initiation": "cbp",
        #     "Transport": "trp",
        #     "Cataloguing": "ctl",
        #     "Delivering": "dlv",
        #     "Invoicing": "inv",
        #     "Supply Chain": "spc",
        #     "Invoice": "ivc",
        #     "Ordering": "ord",
        #     "Quotation": "quo",
        #     "Remittance": "rem",
        #     "Scheduling": "sch",
        #     "Cross Industry Trade": "cit",
        #     "Cross Industry": "cin",
        #     "Examination Notification": "exn",
        #     "Buy-Ship-Pay": "bsp",
        #     "Market Survey": "mks",
        #     "Waste Movement": "wsm",
        #     "Agriculture": "agr",
        #     "Partner Identification": "pid",
        #     "Procurement": "pcm",
        #     "Rapid Alert System": "ras",
        #     "Rapid Alert System; MSDS Reporting": "rms",
        #     "Sanitary and Phytosanitary Measures": "spm",
        #     "Cross-Border": "cbd",
        #     "Acquisition": "acq",
        #     "Trade Billing": "tbl",
        #     "Trade Finance": "tfn",
        #     "Sustainability": "sus",
        #     "Negotiation": "neg",
        #     "Conformity": "cnf",
        #     "Buy Ship Pay": "bsy",
        #     "Statistics": "sts",
        #     "Acknowledgement": "ack",
        #     "Accounting Chart of Accounts": "coa",
        #     "Maritime Transportation": "mar",
        #     "Dangerous Goods": "dgs",
        #     "Product Registration": "prd",
        #     "e-Certificate of Origin": "eco",
        # }

    def debug_print(self, text):
        if self.DEBUG:
            print(f"[DEBUG] {text}")

    def trace_print(self, text):
        if self.TRACE or self.DEBUG:
            print(f"[TRACE] {text}")

    def error_print(self, text):
        print(f"<ERROR> {text}")
        sys.exit()

    def print_record(self, record, extra=""):
        self.debug_print(
            f"{record['level']} {record['sequence']} {record['id']} {record['property_type'][:2]} {record['class_term']}. {record['property_term']}. {record['representation_term'] or record['associated_class']} {record['multiplicity']}"
            + extra
        )

    # def merge_class_term_with_element(self, class_term, element):
    #     """
    #     Generates a CamelCase XML element name by merging class terms and local names,
    #     ensuring duplicates are removed.
    #     """
    #     if not element or ':' not in element:
    #         return ""
    #     namespace, localname = element.split(':')
    #     if "_" in class_term:
    #         class_term_ = class_term[:class_term.rindex("_")]
    #         class_words = re.split(r'\s+', class_term_.strip())
    #         class_prefix = LC3(class_term_)
    #     else:
    #         class_words = re.split(r'\s+', class_term.strip())
    #         class_prefix = LC3(class_term)
    #     local_words = split_camel_case(localname)
    #     #  Remove duplicate words (case-insensitive)
    #     remaining_words = [w for w in local_words if w.lower() not in [cw.lower() for cw in class_words]]
    #     #  If all words are removed and the result is empty, keep the last word of the local name
    #     if not remaining_words and local_words:
    #         remaining_words = [local_words[-1]]
    #     #  LC3 conversion
    #     if remaining_words:
    #         suffix = remaining_words[0].capitalize() + ''.join(w.title() for w in remaining_words[1:])
    #         new_localname = class_prefix + suffix
    #     else:
    #         new_localname = class_prefix
    #     return new_localname

    def getproperty_term(self, record):
        """
        Formats the property term based on its type and associated class.
        """
        property_type = record['property_type']
        property_term = record['property_term']
        representation_term = record['representation_term']
        associated_class = record['associated_class']
        term = None
        if 'Class' in property_type:
            term = ''
        elif 'Attribute'==property_type:
            term = f"{property_term}. {representation_term}"
        else:
            if property_term and property_term not in associated_class:
                associated_class = associated_class[1+associated_class.index(":"):] if ":" in associated_class else associated_class
                term = f'{property_term}_ {associated_class}'
                record["property_term"] = ""
                record['associated_class'] = term
            else:
                term = associated_class
        return term

    def populate_record(self, record, seq):
        """
        Transforms a CSV row into a structured record and generates unique IDs (e.g., CO01_01)
        based on module and sequence.
        """
        sequence = record['sequence']
        property_type = record['property_type']
        module = record['module']
        # module_abbrev = self.module_abbrev_dict[module]

        property_term = (
            record["property_term"].replace("  ", " ").strip()
            if record["property_term"]
            else ""
        )

        associated_class = (
            record["associated_class"].replace("  ", " ").strip()
            if record["associated_class"]
            else ""
        )

        if 'Specialization' == property_type:
            id = f"{self.module_id}{str(self.class_num).zfill(3)}_00"
            level = 2
        else:
            if 'Class' in property_type:
                class_term = (
                    record["class_term"].replace("  ", " ").strip()
                    if record["class_term"]
                    else self.error_print("Invalid row no class term defined.\n{record}")
                )
                if 'Abstract Class'==property_type:
                    self.abstract_classes.add(class_term)
                if self.current_class != class_term:
                    self.module_id = "UN" # self.module_dict.get(module, 'UN')
                    if self.module_id not in self.module_num:
                        self.module_num[self.module_id] = []
                    if not class_term in self.module_num[self.module_id]:
                        self.module_num[self.module_id].append(class_term)
                    self.class_num = 1 + self.module_num[self.module_id].index(class_term)
                    self.current_class = class_term
                id = f"{self.module_id}{str(self.class_num).zfill(3)}"
                self.current_class = class_term
                seq = 0
                level = 1
            else:
                id = f"{self.module_id}{str(self.class_num).zfill(3)}_{str(seq).zfill(3)}"
                level = 2

            seq += 1

        record['id'] = id
        record['level'] = level
        record['class_term'] = self.current_class
        record['property_term'] = property_term
        record['associated_class'] = associated_class

        if associated_class:
            pass
            # self.debug_print(f"{sequence} {id} '{self.current_class}' {property_type} associated_class:'{associated_class}'")
        elif property_term:
            pass
            # self.debug_print(f"{sequence} {id} '{self.current_class}' property_term:'{property_term}'")
        else:
            self.debug_print(f"{sequence} {id} '{self.current_class}'")

        return seq, record

    def check_csv_row(self, row):
        """
        Validate an input CSV row.

        Rules:
        1) Mandatory fields:
        - 'module', 'property_type', 'class_term' must be present.

        2) Multiplicity:
        - For non-class rows, multiplicity must be one of:
            1, 1..1, 1..*, 0..1, 0..2, 0..*, 0..0, 0

        3) Conditional fields by property_type:
        - Class rows ('Class', 'Abstract Class', etc.):
            'property_term', 'representation_term', and 'associated_class' must be empty.
        - Attribute rows:
            if multiplicity is not 0 or 0..0, then 'property_term' and 'representation_term' must be present.
        - Association rows (Reference Association, Aggregation, Composition, Specialization):
            'associated_class' must be present.
        """
        status = False
        property_type = row['property_type']
        multiplicity = row['multiplicity']

        if 'Class' not in property_type:
            if not multiplicity or multiplicity not in ['1', '1..1', '1..*', '0..1', '0..2', '0..*', '0..0', '0']:
                return status, f"Multiplicity '{multiplicity}' is WRONG."
        #  Check for mandatory fields
        for field in ['module', 'property_type', 'class_term']:
            if not row.get(field):
                return status, f"Missing mandatory field '{field}'."
        #  Conditional checks based on 'property_type'
        if 'Class' in property_type:
            for field in ['property_term', 'representation_term', 'associated_class']:
                if row.get(field):
                    return status, f"Field '{field}' must be empty for type {property_type}."
        elif 'Attribute' in property_type:
            if multiplicity not in ['0..0', '0']:
                for field in ['property_term', 'representation_term']:
                    if not row.get(field):
                        return status, f"Field '{field}' cannot be empty for type {property_type}."
        elif property_type in ['Reference Association', 'Aggregation', 'Composition', 'Specialization']:
            for field in ['associated_class']:
                if not row.get(field):
                    return status, f"Field '{field}' cannot be empty for type {property_type}'."
        else:
            return status, f"Property type {property_type} is WRONG."
        if None in row:
            del row[None]
        status = True
        return status, "Row is valid."

    def deep_diff(self, a, b, path=""):
        diffs = []

        if type(a) != type(b):
            diffs.append((path, a, b, "type"))
            return diffs

        if isinstance(a, Mapping):
            a_keys, b_keys = set(a), set(b)
            for k in sorted(a_keys - b_keys):
                diffs.append((f"{path}.{k}" if path else str(k), a[k], None, "removed"))
            for k in sorted(b_keys - a_keys):
                diffs.append((f"{path}.{k}" if path else str(k), None, b[k], "added"))
            for k in sorted(a_keys & b_keys):
                subpath = f"{path}.{k}" if path else str(k)
                diffs.extend(self.deep_diff(a[k], b[k], subpath))
            return diffs

        if isinstance(a, Sequence) and not isinstance(a, (str, bytes, bytearray)):
            if len(a) != len(b):
                diffs.append((path, len(a), len(b), "len"))
            for i, (ai, bi) in enumerate(zip(a, b)):
                diffs.extend(self.deep_diff(ai, bi, f"{path}[{i}]"))
            return diffs

        if a != b:
            diffs.append((path, a, b, "value"))
        return diffs

    def process_record1(self, reader):
        """
        Pass 1: Read rows, assign IDs/levels, and register classes.

        This pass populates:
        - self.records: all rows with generated IDs and normalised fields,
        - self.object_class_dict: class entries only, with an empty 'properties' dict,
        so that associations can reference classes defined later in the file(s).
        """
        next(reader) # skip header
        self.current_class = ''
        seq = 0

        """
        First, register all Class rows so that associations to classes defined later can be resolved.
        Pass 1 registers:
        - Class / Abstract Class rows into self.object_class_dict,
        - keeps all rows in self.records for the second pass.
        """
        for row_number, row in enumerate(reader, start=1):
            """
            self.bie_header = ['sequence', 'UNID', 'acronym', 'DEN', 'definition', 'class_term_qualifier', 'class_term', 'property_term_qualifier', 'property_term', 'datatype_qualifier', 'representation_term', 'qualified_data_type_UID', 'associated_class_qualifier', 'associated_class', 'business_term', 'usage_rule', 'sequence_number', 'occurrence_min', 'occurrence_max', 'context_categories', 'TDED', 'publication_source', 'short_name', 'BIE']
            self.header = ['sequence', 'level', 'property_type', 'identifier', 'class_term', 'property_term', 'representation_term', 'associated_class', 'multiplicity', 'definition', 'module', 'label_local', 'definition_local']            
            """
            if not row['sequence']: continue

            data = {key: row.get(key, '') for key in self.bie_header}

            if 'ABIE'==data['acronym']:
                data['property_type'] = 'Class'
            elif 'ASBIE'==data['acronym']:
                data['property_type'] = 'Composition'
            elif 'BBIE'==data['acronym']:
                data['property_type'] = 'Attribute'
            elif 'END'==data['acronym']:
                break
            else:
                continue

            record = {
                "sequence": data["sequence"],
                "level": 1 if "Class" in data["property_type"] else 2,
                "property_type": data["property_type"],
                "identifier": "",
                "class_term": (
                    f"{data['class_term_qualifier']}_ {data['class_term']}"
                    if data["class_term_qualifier"]
                    else data["class_term"]
                ),
                "property_term": (
                    f"{data['property_term_qualifier']}_ {data['property_term']}"
                    if data["property_term_qualifier"]
                    else data["property_term"]
                ),
                "representation_term": (
                    f"{data['datatype_qualifier']}_ {data['representation_term']}"
                    if data["datatype_qualifier"]
                    else data["representation_term"]
                ),
                "associated_class": (
                    f"{data['associated_class_qualifier']}_ {data['associated_class']}"
                    if data["associated_class_qualifier"]
                    else data["associated_class"]
                ),
                "multiplicity": (
                    f"{data['occurrence_min']}..{'*' if 'unbounded'==data['occurrence_max'] else data['occurrence_max']}"
                ),
                "definition": data["definition"],
                "module": data["context_categories"],
                "label_local": "",
                "definition_local": "",
                "UNID": data["UNID"],
                "acronym": data["acronym"],
                "DEN": data["DEN"]
            }

            seq = int(record['sequence'])
            valid, msg = self.check_csv_row(record)
            if not valid: self.error_print(f"Invalid row {seq}: {msg}")

            seq, record = self.populate_record(record, seq)

            self.records.append(record)

            property_type = record['property_type'].strip()

            if 'Class' in property_type:
                class_term = record['class_term'].strip()
                if class_term in self.object_class_dict:
                    d1 = copy.deepcopy(self.object_class_dict[class_term])
                    del d1['sequence']
                    del d1['properties']
                    del d1['id']
                    d2 = copy.deepcopy(record)
                    del d2['sequence']
                    del d2['id']
                    if d1!=d2:
                        for item in self.deep_diff(d1, d2):
                            self.trace_print(f"object_class_dict[{class_term}'] defines {item} differently.")
                    continue
                self.object_class_dict[class_term] = record
                self.object_class_dict[class_term]['properties'] = {}
            else:
                p_term = self.getproperty_term(record)
                if class_term not in self.object_class_dict:
                    self.trace_print(f"self.object_class_dict[{class_term}'] is not defined for '{p_term}'.")
                    continue
                if p_term in self.object_class_dict[class_term]['properties']:
                    d1 = self.object_class_dict[class_term]['properties'][p_term]
                    del d1['sequence']
                    del d1['id']
                    d2 = copy.deepcopy(record)
                    del d2['sequence']
                    del d2['id']
                    if d1!=d2:
                        for item in self.deep_diff(d1, d2):
                            self.trace_print(f"object_class_dict['{class_term}']['properties']['{p_term}'] defines {item} differently.")
                            if "multiplicity" == item[0]:
                                d1_mult = item[1]
                                d1_min = d1_mult[0]
                                d1_max = d1_mult[-1]
                                d2_mult = item[2]
                                min = d2_mult[0]
                                max = d2_mult[-1]
                                if "0" == d1_min:
                                    min = d1_min
                                if "*" == d1_max:
                                    max = d1_max
                                elif "*" != max:
                                    if int(d1_max) > int(max):
                                        max = d1_max
                                multiplicity = f"{min}..{max}"
                                record["multiplicity"] = multiplicity
                                self.trace_print(f'record["multiplicity"] = {multiplicity}')
                            elif "definition" == item[0]:
                                record["definition"] = (
                                    f'{d1["definition"]}\n{record["definition"]}'
                                )
                self.object_class_dict[class_term]['properties'][p_term] = record

        return self.records

    def process_record2(self):
        """
        Pass 2: Register properties, derive abstract classes, and build the flattened FSM output.

        Main steps:
        1) Derive abstract (super) classes from underscore-based class-term chaining and
        aggregate inherited properties across subclasses.
        2) Filter abstract classes: keep only those having module "In All Contexts".
        3) Normalise association targets (associated_class) so they resolve to registered class terms.
        4) Build self.FSM_list:
        - emit abstract classes and their shared/aligned properties,
        - emit each concrete class,
        - emit a 'Specialized' marker when a class specialises an abstract superclass,
        - emit class properties with inheritance status flags:
            Shared, Aligned, Extension, Inheritance, Modified[...], Prohibited.
        """
        MORE_THAN = 2
        N = 1000
        N2 = 2000
        self.current_class = None

        # property_type priority (Attributes first)
        PT_ORDER = {
            "Attribute(PK)": 0,
            "Attribute": 1,
            # The rest are at the back (add here if necessary)
            "Reference": 2,
            "Reference Association": 2,
            "Aggregation": 3,
            "Composition": 4,
        }

        # multiplicity priority (Attributes first)
        MULT_ORDER = {
            "1": 0,
            "1..1": 0,
            "0..1": 1,
            "1..*": 2,
            "0..*": 3,
            "0": 4,
        }

        # inheritance priority (Attributes first)
        INHR_ORDER = {
            "Shared": 0,
            "Aligned": 1,
        }
        INHR_ORDER2 = {
            "Inheritance": 0,
            "Modified": 1,
            "Aligned": 2,
            "Extension": 3,
            "Prohibited": 4,
        }

        def sort_properties(d: dict) -> OrderedDict:
            def key_fn(item):
                k, v = item
                pt = v.get("property_type", "")
                mult = v.get("multiplicity", "")
                inhr = v.get("inherited", "")
                prop = v.get("property_term", "")
                assoc = v.get("associated_class", "")
                id = v.get("id", "")
                if str(inhr).startswith("Modified"): inhr = "Modified"
                # Since sequence is a string, convert it to an int
                # (if it is missing or invalid, convert it to a larger value)
                try:
                    seq = int(v.get("sequence", 10**9))
                except Exception:
                    seq = 10**9

                if "Abstract Class"==v.get("module", ""):
                    # if "Composition"==v.get("property_type", ""):
                    order = (
                        INHR_ORDER.get(inhr, 99),  # 1) Inheritance priority
                        PT_ORDER.get(pt, 99),      # 2) Attribute priority
                        seq                        # 4) sequence
                    )
                    # else:
                    #     order = (
                    #         INHR_ORDER.get(inhr, 99),  # 1) Inheritance priority
                    #         PT_ORDER.get(pt, 99),      # 2) Attribute priority
                    #         seq                        # 4) sequence
                    #     )
                else:
                    # if "Composition"==v.get("property_type", ""):
                    order = (
                        INHR_ORDER2.get(inhr, 99), # 1) Inheritance priority
                        PT_ORDER.get(pt, 99),      # 2) Attribute priority
                        (id or "").lower(),        # 4) property_term alphabetical
                    )
                    # else:
                    #     order = (
                    #         INHR_ORDER2.get(inhr, 99), # 1) Inheritance priority
                    #         PT_ORDER.get(pt, 99),      # 2) Attribute priority
                    #         (id or "").lower(),        # 4) property_term alphabetical
                    #         # seq                        # 4) sequence
                    #     )
                order = (
                    INHR_ORDER.get(inhr, 99),  # 1) Inheritance priority
                    PT_ORDER.get(pt, 99),      # 2) Attribute priority
                    (id or "").lower(),        # 4) property_term alphabetical
                )
                return order

            return OrderedDict(sorted(d.items(), key=key_fn))

        def _superclass_chain(class_term: str, SELF=False):
            """
            Yield superclass terms by repeatedly applying:
                term = term[2 + term.index("_"):]
            until no underscore remains.

            This matches the project's class naming convention where a specialised class term
            embeds its superclass term after the first underscore.
            """
            term = class_term
            if SELF: yield term  # include itself first
            while "_" in term:
                term = term[2 + term.index("_"):]
                yield term

        def _ensure_abstract_class(superclass_term: str, object_class: dict, N: int) -> int:
            """
            Create an entry in self.abstract_class_dict for the given superclass_term if it does not exist.
            Returns the updated N.
            """
            if superclass_term in self.abstract_class_dict:
                return N

            superclass = copy.deepcopy(object_class)
            superclass["property_type"] = "Abstract Class"
            superclass["class_term"] = superclass_term
            superclass["module"] = "Abstract Class"
            superclass["id"] = f"UN{N}"
            N += 1

            # Initialise container for aggregated properties.
            superclass["properties"] = {}

            self.abstract_class_dict[superclass_term] = superclass
            self.debug_print(f"{superclass['id']} self.abstract_class_dict['{superclass_term}']")

            return N

        def _merge_properties_into_abstract(superclass_term: str, properties: dict, N: int, Shared=False) -> int:
            """
            Merge properties into self.abstract_class_dict[superclass_term]['properties'].

            - If a property already exists (by p_term), increment 'inherited'.
            - Append the incoming definition as a new line only when it differs from the last line.
            - If the property does not exist yet, add it with inherited=1.
            - Copy each property before editing to avoid mutating the source dictionaries.
            """
            n = 1
            abs_props = self.abstract_class_dict[superclass_term]["properties"]
            for p_term, prop0 in properties.items():
                prop = copy.deepcopy(prop0)  # Do not mutate the source property object.
                p_term = self.getproperty_term(prop)
                if len(abs_props)==0 or p_term not in abs_props:
                    abs_props[p_term] = prop
                    abs_props[p_term]["inherited"] = 1
                else:
                    abs_props[p_term]["inherited"] += 1

                # Rewrite class/module/id for the abstract-class context.
                prop["class_term"] = superclass_term
                prop["module"] = "Abstract Class"
                prop["id"] = f"UN{N}_{str(n).zfill(3)}"

                if p_term not in abs_props:
                    abs_props[p_term] = prop

                if abs_props[p_term]["inherited"] > 1:
                    abs_mult = abs_props[p_term]['multiplicity']
                    abs_min = abs_mult[0]
                    abs_max = abs_mult[-1]
                    mult = prop['multiplicity']
                    min = mult[0]
                    max = mult[-1]
                    if "0"!=min:
                        min = abs_min
                    if "*"!=max:
                        if "*"!=abs_max:
                            if int(abs_max) > int(max):
                                max = abs_max
                    abs_props[p_term]['multiplicity'] = f'{min}..{max}'

                    # Append definition only if it is not a duplicate of the current last line.
                    new_def = prop.get("definition", "")
                    if new_def:
                        current_def = abs_props[p_term].get("definition", "")
                        last_line = current_def.split("\n")[-1] if current_def else ""
                        if new_def != last_line:
                            abs_props[p_term]["definition"] = (current_def + "\n" + new_def).strip()

                n += 1

            return N

        # ----------------------------
        # Define abstract class
        # ----------------------------
        self.trace_print("** Define abstract class.")

        self.abstract_class_dict = {}
        for class_term, object_class in self.object_class_dict.items():
            # Classes with class term containing "_" participate in the superclass chain.
            if "_" in class_term:
                # Take properties from the current object_class.
                properties = copy.deepcopy(object_class["properties"])

                # Build/merge abstract classes for every superclass term in the chain.
                for superclass_term in _superclass_chain(class_term):
                    N = _ensure_abstract_class(superclass_term, object_class, N)
                    N = _merge_properties_into_abstract(superclass_term, properties, N, True)

            # Classes that belongs to "In All Contexts" participate in the superclass chain.
            elif "In All Contexts"==object_class['module']:
                # Always take properties from the current object_class.
                properties = copy.deepcopy(object_class["properties"])
                if len(properties) < 3:
                    continue
                # Build/merge abstract classes for every superclass term in the chain.
                for superclass_term in _superclass_chain(class_term, True):
                    N = _ensure_abstract_class(superclass_term, object_class, N)
                    N = _merge_properties_into_abstract(superclass_term, properties, N, True)

        for class_term, object_class in self.object_class_dict.items():
            # Only classes not belongs to the superclass chain.
            if "_" not in class_term and "In All Contexts"!=object_class['module']:
                # Always take properties from the current object_class.
                properties = copy.deepcopy(object_class["properties"])
                # Build/merge abstract classes for every superclass term in the chain.
                for superclass_term in _superclass_chain(class_term):
                    N2 = _ensure_abstract_class(superclass_term, object_class, N2)
                    N2 = _merge_properties_into_abstract(superclass_term, properties, N2)

        remove_superclass_list = []
        for class_term, object_class in self.abstract_class_dict.items():
            props = {
                k: v
                for k, v in self.abstract_class_dict[class_term]
                .get("properties", {})
                .items()
                if v["inherited"] > MORE_THAN
            }
            if props:
                for k, prop in self.abstract_class_dict[class_term].get("properties", {}).items():
                    self.abstract_class_dict[class_term]['properties'][k]['inherited'] = 'Shared' if k in props.keys() else 'Aligned'
            else:
                remove_superclass_list.append(class_term)
        
        for class_term in remove_superclass_list:
            del self.abstract_class_dict[class_term]

        for class_term, object_class in self.object_class_dict.items():
            properties = copy.deepcopy(object_class['properties'])
            for _, property in properties.items():
                property_term = property['property_term']
                associated_class = property['associated_class']
                if associated_class:
                    a_class = [k for k in self.object_class_dict.keys() if k==associated_class] 
                    if a_class:
                        as_class = a_class[0]
                    else:
                        self.debug_print(f"Check super class of '{associated_class}'")
                        as_class = associated_class
                        while '_' in as_class:
                            as_class = as_class[2+as_class.index('_'):]
                            if as_class:
                                a_class = [k for k in self.object_class_dict.keys() if k==as_class]
                                if a_class:
                                    as_class = a_class[0]
                                    break
                    if as_class:
                        if associated_class != as_class:
                            property['property_term'] = associated_class.replace(as_class,"").strip()[:-1]
                            property['associated_class'] = as_class
                    else:
                        self.error_print(f"{property['associated_class']} not in self.object_class_dict.")

        """
        Prepare the FSM List.
        """
        self.trace_print("** Prepare the FSM output list.")
        # ----------------------------
        # Append abstract class to FSM_list
        # ----------------------------
        self.trace_print("** Append abstract class to FSM_list.")
        self.FSM_list = []
        for class_term, object_class in self.abstract_class_dict.items():
            self.debug_print(f"-- {class_term}")
            properties = copy.deepcopy(object_class['properties'])

            self.FSM_list.append(object_class)

            prop_dict = {}
            for p_term, property in properties.items():
                p_type = property['property_type']

                if 'Attribute'==p_type:
                    if property not in self.FSM_list:
                        prop_dict[p_term] = property
                else:
                    associated_class = property['associated_class']
                    if associated_class in self.abstract_class_dict:
                        if property not in self.FSM_list:
                            prop_dict[p_term] = property
                    elif '_' in associated_class:
                        a_class = associated_class[2+associated_class.rindex("_"):]
                        if a_class in self.abstract_class_dict:
                            if property not in self.FSM_list:
                                property_term = associated_class[:associated_class.rindex("_")]
                                property['property_term'] = property_term
                                property['associated_class'] = a_class
                                prop_dict[p_term] = property

            class_id = object_class['id']
            n = 0
            for p_term, property in sort_properties(prop_dict).items():
                n += 1
                p_id = f'{class_id}_{str(n).zfill(3)}'
                property['id'] = p_id
                self.FSM_list.append(property)

            if 'Class' in self.FSM_list[-1]['property_type']:
                del self.FSM_list[-1]

        # ----------------------------
        # Append object class to FSM_list
        # ----------------------------
        self.trace_print("** Append object class to FSM_list.")
        for class_term, object_class in self.object_class_dict.items():
            self.debug_print(f"-- {class_term}")

            self.FSM_list.append(object_class)

            specialized = None
            specialized_props = None

            if '_' in class_term:
                s_class_term = class_term[2+class_term.rindex("_"):]
                if s_class_term in self.abstract_class_dict:
                    specialized = copy.deepcopy(self.abstract_class_dict[s_class_term])
                    specialized['level'] = 2
                    specialized['property_type'] = 'Specialized'
                    specialized['class_term'] = class_term
                    specialized['associated_class'] = s_class_term
                    specialized['multiplicity'] = '1'

                    self.FSM_list.append(specialized)

                    specialized_props = copy.deepcopy(
                        self.abstract_class_dict[s_class_term]
                        .get("properties", {})
                    )

            prop_dict = {}
            properties = copy.deepcopy(object_class['properties'])
            for p_term, prop in properties.items():
                prop["inherited"] = "Distinct"

                if specialized_props:
                    if p_term in specialized_props:
                        specialized_mult = specialized_props[p_term].get("multiplicity", "0")
                        prop["inherited"] = (
                            "Inheritance"
                            if prop["multiplicity"] == specialized_mult
                            else f"Modified [{specialized_mult}]"
                        )
                    else:
                        prop["inherited"] = "Aligned"

                prop_dict[p_term] = prop

            for p_term, prop in sort_properties(prop_dict).items():
                self.FSM_list.append(prop)

            if specialized_props:
                for p_term, s_prop in sort_properties(specialized_props).items():
                    if p_term not in properties:
                        prop = copy.deepcopy(s_prop)
                        prop["class_term"] = class_term
                        prop["inherited"] = "Prohibited"

                        self.FSM_list.append(prop)

        return self.FSM_list

    def write_csv(self, csv_file):
        self.trace_print(f"Write {csv_file}")

        records = [{k: v for k, v in d.items() if k in self.out_header} for d in self.FSM_list]

        with open(csv_file, 'w', encoding = self.encoding, newline='') as f:
            writer = csv.DictWriter(f, fieldnames = self.out_header)
            writer.writeheader()
            writer.writerows(records)

    def analyze(self):
        """
        Main entry point for generating an FSM CSV from BIE input rows.

        High-level workflow:
        1) Initialise dictionaries:
        - self.object_class_dict: class registry
        - self.records: all parsed rows

        2) Two-pass processing:
        - Pass 1 (process_record1): read CSV rows, generate IDs/levels, and register all classes
            to enable forward reference resolution.
        - Pass 2 (process_record2): attach properties, derive abstract classes, normalise
            association targets, and build the flattened FSM list with inheritance status flags.

        3) Output:
        - Write self.FSM_list to the target FSM CSV with the extended header (out_header).
        """
        self.object_class_dict = {}
        self.trace_print(f"** READ {self.bie_file}")
        with open(self.bie_file, encoding=self.encoding, newline='') as f:
            reader = csv.DictReader(f, fieldnames=self.bie_header)
            self.trace_print(f"** Process record STEP 1.")
            self.process_record1(reader)

        self.trace_print(f"** Process record STEP 2.")
        self.process_record2()

        file = file_path(self.fsm_file)
        self.write_csv(file)
        print(f'-- END {file}')


"""
Main function to execute the script
"""
def main():
    RAESER = False
    if RAESER:
        # Create the parser
        parser = argparse.ArgumentParser(
            prog='bie_to_bsm.py',
            usage='%(prog)s BIE_file FSM_file -e encoding [options]',
            description='Converts BIE to Foundational Semantic Model (FSM).'
        )
        parser.add_argument('bie_file', metavar='bie_file', type = str, help='Foundational Foundational Semantic Model (FSM) files')
        parser.add_argument('fsm_file', metavar='fsm_file', type = str, help='Business Semantic Model (BSM) file')
        parser.add_argument('-e', '--encoding', required = False, default='utf-8-sig', help='File encoding, default is utf-8-sig')
        parser.add_argument('-t', '--trace', required = False, action='store_true')
        parser.add_argument('-d', '--debug', required = False, action='store_true')

        args = parser.parse_args()

        # Flatten the list if necessary
        bie_files = []
        if args.root:
            for val in args.bie_file:
                if isinstance(val, str) and "+" in val:
                    bie_files.extend(val.split("+"))
                else:
                    bie_files.append(val)
        bie_files = [x.strip() for x in bie_files]

        processor = Processor(
            bie_file = args.bie_files,
            fsm_file = args.FSM_file.strip(),
            encoding = args.encoding.strip() if args.encoding else None,
            trace = args.trace,
            debug = args.debug
        )
    else:
        BASE_DIR = "TEST/"
        args = {
            "BIE_file": f"{BASE_DIR}MRBIE-D25A.csv",
            "FSM_file": f"{BASE_DIR}FSM-D25A.csv",
            "encoding": "utf-8",
        }
        processor = Processor(
            bie_file = args["BIE_file"],
            fsm_file = args["FSM_file"],
            encoding = args["encoding"],
            trace = True,
            debug = True
        )

    processor.analyze()

if __name__ == '__main__':
    main()
