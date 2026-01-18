#!/usr/bin/env python3
# coding: utf-8
"""
specialization.py

Generates Business Semantic Model (BSM) CSV file from Foundational Semantic Model (FSM) CSV file with Specialization

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-01-17
Last Modified: 2025-12-22

MIT License

(c) 2023-2025 SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

ABOUT THIS SCRIPT
This script, `specialization.py`, is the initial step in the ADS (Audit Data Collection) semantic transformation workflow. It processes the Foundational Semantic Model (FSM) to resolve class hierarchies and property extensions, ultimately generating a Business Semantic Model (BSM).

Specialization allows the model to:
- Inherit properties from superclasses (Abstract or Regular Classes).
- Override property definitions, including multiplicity changes.
- Remove properties by setting multiplicity to "0" or "0..0".
- Merge extension FSM files into a unified BSM structure.

Key Process Flow:
1. Two-Pass Record Processing:
   - Pass 1: Registers all classes (including Abstract Classes) to ensure all associations can be resolved regardless of row order.
   - Pass 2: Processes attributes, associations, and specializations, linking inherited properties to their respective subclasses.

2. Specialization Engine:
   - `parse_class`: Recursively resolves the hierarchy and populates the BSM list with specialized properties.
   - `populate_record`: Generates unique technical identifiers (IDs) based on module mapping and sequence.

3. Output Generation:
   - Validates rows for mandatory semantic fields.
   - Sorts the final model by module and class hierarchy for scannability.
   - Exports the BSM with technical metadata (IDs and XML element names).
"""

import os
import argparse
import sys
import csv
import re
import copy

# from common.utils import (
#     LC3,
#     file_path,
#     is_file_in_use,
#     split_camel_case
# )

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

class Specialization:
    def __init__(
            self,
            fsm_files,
            bsm_file,
            encoding,
            trace,
            debug
        ):
        """
        Initializes the Specialization processor with file paths and configurations.
        """
        # dir = os.path.dirname(__file__)
        self.fsm_files = [file_path(x) for x in fsm_files]
        # self.fsm_files = [file_path(x.replace('/', os.sep)) for x in fsm_files]
        for fsm_file in self.fsm_files:
            if not fsm_file or not os.path.isfile(fsm_file):
                print(f'[INFO] No input Foundation Semantic Model (FSM) file {fsm_file}.')
                sys.exit()

        self.bsm_file = bsm_file.replace('/', os.sep)
        self.bsm_file = file_path(self.bsm_file)
        if 'IN_USE' == is_file_in_use(self.bsm_file):
            print(f'[INFO] Basic Semantic Model (BSM) file {self.bsm_file} is **IN USE**.')
            sys.exit()

        self.encoding = encoding if encoding else "utf-8-sig"
        self.TRACE = trace
        self.DEBUG = debug

        # Define CSV headers for internal processing and final BSM output
        self.header  = ['sequence', 'level', 'property_type', 'identifier', 'class_term', 'property_term', 'representation_term', 'associated_class', 'multiplicity', 'definition', 'module', 'label_local', 'definition_local']
        self.header2 = ['sequence', 'level', 'property_type', 'identifier', 'class_term', 'property_term', 'representation_term', 'associated_class', 'multiplicity', 'definition', 'module', 'label_local', 'definition_local', 'id']

        #  Initialize dictionaries and lists
        self.domain_dict = None

        self.object_class_dict = None

        self.current_module = None
        self.module_num = {}
        self.module_id = None

        self.current_class = None
        self.class_num = None
        self.abstract_classes = set()

        self.LIFO_list = []
        self.BSM_list = []
        self.records = []

        # Module dictionary for mapping module names to standardized codes
        self.module_dict = {
            'Unit Type Registry': 'UT',
            'gen': 'GE',
            'cor': 'CO',
            'bus': 'BU',
            'muc': 'MC',
            'taf': 'TA',
            'ehm': 'EH',
            'usk': 'UK',
            'lnk': 'LK',
            'btx': 'BT',
            'sta': 'ST',
            'ext': 'EX',
        }

    def debug_print(self, text):
        if self.DEBUG:
            print(f"DEBUG: {text}")

    def trace_print(self, text):
        if self.TRACE or self.DEBUG:
            print(f"TRACE: {text}")

    def error_print(self, text):
        print(f"** ERROR: {text}")
        sys.exit()

    def print_record(self, record, extra=""):
        self.debug_print(f"{record['level']} {record['id']} {record['property_type'][:2]} {record['class_term']}. {record['property_term']}. {record['representation_term'] or record['associated_class']} {record['multiplicity']}" + extra)


    def merge_class_term_with_element(self, class_term, element):
        """
        Generates a CamelCase XML element name by merging class terms and local names, 
        ensuring duplicates are removed.
        """
        if not element or ':' not in element:
            return ""
        namespace, localname = element.split(':')
        if "_" in class_term:
            class_term_ = class_term[:class_term.rindex("_")]
            class_words = re.split(r'\s+', class_term_.strip())
            class_prefix = LC3(class_term_)
        else:
            class_words = re.split(r'\s+', class_term.strip())
            class_prefix = LC3(class_term)
        local_words = split_camel_case(localname)
        #  Remove duplicate words (case-insensitive) 
        remaining_words = [w for w in local_words if w.lower() not in [cw.lower() for cw in class_words]]
        #  If all words are removed and the result is empty, keep the last word of the local name
        if not remaining_words and local_words:
            remaining_words = [local_words[-1]]
        #  LC3 conversion
        if remaining_words:
            suffix = remaining_words[0].capitalize() + ''.join(w.title() for w in remaining_words[1:])
            new_localname = class_prefix + suffix
        else:
            new_localname = class_prefix
        return new_localname


    def getproperty_term(self, record):
        """
        Formats the property term based on its type and associated class.
        """
        property_type = record['property_type']
        property_term = record['property_term']
        associated_class = record['associated_class']
        term = None
        if 'Class' in property_type:
            term = ''
        elif 'Attribute'==property_type:
            term = property_term
        else:
            if property_term and property_term not in associated_class:
                term = f"{property_term}_ {associated_class[4:]}"
                record['property_term'] = ''
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
        module = LC3(abbreviate_term(normalize_text(record['module']), 4))
     
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
            id = f"{self.module_id}{str(self.class_num).zfill(2)}_00"
            associated_class = f"{module}:{associated_class}"
            level = 2
        else:
            if 'Class' in property_type:
                class_term = (
                    record["class_term"].replace("  ", " ").strip()
                    if record["class_term"]
                    else self.error_print("Invalid row no class term defined.\n{record}")
                )
                class_term = f"{module}:{class_term}"

                if 'Abstract Class'==property_type:
                    self.abstract_classes.add(class_term)

                if self.current_class != class_term:
                    self.module_id = self.module_dict.get(module, 'NA')
                    if self.module_id not in self.module_num:
                        self.module_num[self.module_id] = []
                    if not class_term in self.module_num[self.module_id]:
                        self.module_num[self.module_id].append(class_term)
                    self.class_num = 1 + self.module_num[self.module_id].index(class_term)    
                    self.current_module = module
                    self.current_class = class_term

                id = f"{self.module_id}{str(self.class_num).zfill(2)}"
                self.current_class = class_term
                seq = 0
                level = 1
            else:
                id = f"{self.module_id}{str(self.class_num).zfill(2)}_{str(seq).zfill(2)}"
                if property_term:
                    property_term = f"{module}:{property_term}"
                if associated_class:
                    associated_class = f"{module}:{associated_class}"
                level = 2
            seq += 1

        record['id'] = id
        record['level'] = level
        record['module'] = module
        record['class_term'] = self.current_class #.replace("_","")
        record['property_term'] = property_term #.replace("_","")
        record['associated_class'] = associated_class #.replace("_","")

        if associated_class:
            self.debug_print(f"{sequence} {id} '{self.current_class}' {property_type} associated_class:'{associated_class}'")
        elif property_term:
            self.debug_print(f"{sequence} {id} '{self.current_class}' property_term:'{property_term}'")
        else:
            self.debug_print(f"{sequence} {id} '{self.current_class}'")

        return seq, record


    def check_csv_row(self, row):
        """
        Function to check the validity of CSV rows
        1. Check Mandatory Fields: Ensure that each row contains 'module', 'property_type',
        'class_term'.
        2. Conditional Checks Based on 'property_type':
        - If 'property_type' contains 'Class', then 'property_term', 'representation_term', and 
            'associated_class', should be empty.
        - If 'property_type' contains 'Attribute', then 'property_term' and 
            'representation_term' should not be empty.
        - Additional checking can be added for other types like 'Reference', 
            'Aggregation', 'Composition', 'Specialization' then 'associated_class', 
            should not be empty.
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


    def sort_records(self, data):
        """
        Function to sort rows between 'Class' entries
        Sorts the BSM records by Module, Base Class, and Property Type order.
        """
        property_type_order = ['Class', 'Attribute', 'Reference Association', 'Aggregation', 'Composition']
        #  Pre-sorting by 'module' and 'table'
        data_sorted_pre = sorted(data, key=lambda x: (x['module']))

        #  Extract base class terms and add sorting order for 'property_type' again
        for row in data_sorted_pre:
            class_term = row.get("class_term", "")
            row["base_class_term"] = (
                class_term.split(".")[0] if "." in class_term else class_term
            )
            row["property_type_order"] = (
                property_type_order.index(row["property_type"])
                if row["property_type"] in property_type_order
                else float("inf")
            )

        #  Perform the second sorting by 'base_class_term', 'property_type_order', and 'sequence'
        for item in data_sorted_pre:
            try:
                seq_int = int(item['sequence'])
            except ValueError:
                self.error_print(f"Invalid sequence value: {item['sequence']} in item with id {item['id']}")

        data_sorted_final = sorted(data_sorted_pre, key=lambda x: (x['base_class_term'], x['property_type_order'], int(x['sequence'])))

        # Remove helper fields used for sorting
        for row in data_sorted_final:
            row.pop('base_class_term', None)
            row.pop('property_type_order', None)

        return data_sorted_final


    def process_record1(self, reader):
        """
        Populate row data to record and register dict.
        Performs a two-pass processing of FSM rows:
        1. Class registration for forward reference resolution.
        2. Property and Specialization processing.
        """
        next(reader) # skip header
        self.current_class = ''
        seq = 0

        """
        Firstly, populate all classes so that associations to classes defined in later rows can be resolved.
        Pass 1: Register Classes and Abstract Classes
        """
        for row_number, row in enumerate(reader, start=1):
            if not row['sequence'] and not row['level']: continue
            if not row['module']: self.error_print(f"No module defined at row {row_number}")

            record = {key: row.get(key, '') for key in self.header}
            valid, msg = self.check_csv_row(row)
            if not valid: self.error_print(f"Invalid row {row_number}: {msg}")

            seq, record = self.populate_record(record, seq)

            self.records.append(record)

            property_type = record['property_type'].strip()
            class_term = record['class_term'].strip()
            if property_type in ['Abstract Class', 'Class']:
                if class_term not in self.object_class_dict:
                    self.object_class_dict[class_term] = record
                    self.object_class_dict[class_term]['properties'] = {}


    def process_record2(self):
        """
        Second pass: Register Properties
        """
        superclass_term = None
        self.current_class = None
        properties = {}
        for record in self.records:
            property_type = record['property_type']
            class_term = record['class_term']
            property_type = record['property_type']

            if 'Class' in property_type:
                if self.current_class:
                    for property in self.object_class_dict[class_term]['properties']:
                        if not property['use']:
                            del property
                properties = {}
                self.current_class = class_term
                current_class_id = record['id']
                record['use'] = True
                self.print_record(record)
            else: # propertytype is either 'Atribute', 'Composition', 'Reference Association'
                if class_term not in self.object_class_dict:
                    self.error_print(f"NOT REGISTERED '{class_term}' in object_class_dict\n{record}")
                p_term = self.getproperty_term(record)
                record['id'] = f"{current_class_id}_{record['id'][1 + record['id'].rindex('_'):]}"
                self.print_record(record)
                self.object_class_dict[class_term]['properties'][p_term] = record

        """
        Filters out abstract entries, and writes the BSM CSV.
        """
        self.BSM_list = []
        for class_term, object_class in self.object_class_dict.items():
            if class_term in self.abstract_classes:
                continue
            properties = copy.deepcopy(object_class['properties'])
            del object_class['properties']
            self.BSM_list.append(object_class)
            for property in properties.values():
                self.BSM_list.append(property)


    def write_csv(self, csv_file):

        records = [{k: v for k, v in d.items() if k in self.header2} for d in self.BSM_list]

        is_abstract_class = False
        out_records = []
        for record in records:
            property_type = record['property_type'].strip()
            if 1 == record['level']:
                if 'Abstract Class' == property_type:
                    is_abstract_class = True
                elif 'Class' == property_type:
                    is_abstract_class = False
            if not is_abstract_class:
                out_records.append(record)

        #  Apply the sorting function
        sorted_records = self.sort_records(out_records)

        with open(csv_file, 'w', encoding = self.encoding, newline='') as f:
            writer = csv.DictWriter(f, fieldnames = self.header2)
            writer.writeheader()
            writer.writerows(sorted_records)

    def specialization(self):
        """
        Main entry point for the specialization and model generation process.
        
        This method executes the high-level workflow to transform the FSM (Foundational 
        Semantic Model) into a BSM (Business Semantic Model) by resolving class 
        hierarchies and property extensions.

        Workflow Steps:
        1. Dictionary Initialization:
           - Initializes `self.object_class_dict` to store the semantic definitions.

        2. Record Processing (Two-Pass Logic inside process_record1 and process_record2):
           - First Pass: Reads the FSM CSV files and registers all "Abstract Class" and "Class" 
             entries into the dictionary to allow for forward-referencing associations.
           - Second Pass: Processes the loaded records from memory. It handles 
             Specializations by cloning superclass properties and manages Attributes or 
             Associations. 
           - Property Overrides: Identifies specialized properties using the "_" 
             naming convention and updates multiplicities directly in the 
             class property dictionary.
           - Flattens the hierarchical structure into `self.BSM_list`.

        3. BSM Generation:
           - Filters out internal Abstract Class definitions and sorts the result 
             by module and sequence for the final output.

        """
        self.object_class_dict = {}
        for fsm_file in self.fsm_files:
            self.trace_print(f"** READ {fsm_file}")
            with open(fsm_file, encoding=self.encoding, newline='') as f:
                reader = csv.DictReader(f, fieldnames=self.header)
                self.process_record1(reader)

        self.trace_print(f"** Process record STEP 2")
        self.process_record2()

        file = file_path(self.bsm_file)
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
            prog='specialization.py',
            usage='%(prog)s FSM_file+FSM_file_extension BSM_file -e encoding [options]',
            description='Converts Foundational Semantic Model (FSM) to Business Semantic Model (BSM) with specialization.'
        )
        parser.add_argument('fsm_file', metavar='fsm_file', type = str, help='Foundational Foundational Semantic Model (FSM) files')
        parser.add_argument('bsm_file', metavar='bsm_file', type = str, help='Business Semantic Model (BSM) file')
        parser.add_argument('-e', '--encoding', required = False, default='utf-8-sig', help='File encoding, default is utf-8-sig')
        parser.add_argument('-t', '--trace', required = False, action='store_true')
        parser.add_argument('-d', '--debug', required = False, action='store_true')

        args = parser.parse_args()

        # Flatten the list if necessary
        fsm_files = []
        if args.root:
            for val in args.fsm_file:
                if isinstance(val, str) and "+" in val:
                    fsm_files.extend(val.split("+"))
                else:
                    fsm_files.append(val)
        fsm_files = [x.strip() for x in fsm_files]

        processor = Specialization(
            fsm_file = args.fsm_files,
            bsm_file = args.BSM_file.strip(),
            encoding = args.encoding.strip() if args.encoding else None,
            trace = args.trace,
            debug = args.debug
        )
    else:
        BASE_DIR = "TEST/"
        args = {
            "FSM_files": [f"{BASE_DIR}FSM-D25A.csv"],
            "BSM_file": f"{BASE_DIR}BSM-D25A.csv",
            "encoding": "utf-8",
            # "FSM_files": [f"{BASE_DIR}xBRL-GL2.0_FSM_t.csv", f"{BASE_DIR}xBRL-GL2.0_FSM_btx_t.csv"],
            # "BSM_file": f"{BASE_DIR}xBRL-GL2.0_BSM_t.csv",
            # "encoding": "utf-8-sig",
        }
        processor = Specialization(
            fsm_files = args["FSM_files"],
            bsm_file = args["BSM_file"],
            encoding = args["encoding"],
            trace = True,
            debug = True
        )

    processor.specialization()

if __name__ == '__main__':
    main()
