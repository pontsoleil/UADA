#!/usr/bin/env python3
# coding: utf-8
"""
graphwalk.py

Performs a recursive graph walk on the Business Semantic Model (BSM) 
to generate a hierarchical Logical Data Model (LDM) CSV.

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-01-17
Last Modified: 2025-12-27

MIT License
(c) 2023-2025 SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

ABOUT THIS SCRIPT
This second Python script complements the first by further processing the Business Semantic Model (BSM), specifically focusing on hierarchical relationships and generating a Logical Hierarchical Model (LHM) CSV from a BSM CSV. Here’s a detailed procedure description:

1. Initial Setup:
   - Imports necessary modules and sets up debugging flags and file path separators.
   - Defines directories and filenames for logical and hierarchical model CSV files.

2. Utility Functions and utility class:
   - parse_class(class_term, SP_ID=''): Processes each class term and its properties, focusing on handling hierarchical relationships and associations.
   - file_path(pathname): Constructs full file paths from given pathnames.
   - update_class_term(row): Processes each row to construct an object class term.
   - model2record(LHM_model): Transforms the hierarchical model into a format suitable for CSV output.
   - set_path(data, aggregates): Set path for hierarchical model
   - get_semantic_path(record):Get semantic path
   - update_class_term(row): Update class term
   - update_name(hierarchy_records): Update the name field in the hierarchical records

   - IndexManager class to manage class and property indexing.

3. Building Hierarchical Model:
   - Reads the BSM CSV file and populate object_class_dict.
   - Iterates through each class in object_class_dict uses parse_class() to to build a hierarchical model.

4. Hierarchy Generation Logic:
   - Uses a Last-In-First-Out (LIFO) list to track the hierarchy of classes and their associations.
   - Applies rules for selecting classes and associations based on graph walk principles, such as handling specializations, mandatory associations, and navigating through class hierarchies.
   - Constructs the hierarchical model by recursively processing class terms and their associations.

5. Output Hierarchical Model to CSV:
   - Converts the hierarchical model into records suitable for LHM CSV output using model2record().
   - Writes these records to a CSV file in the specified directory.

6. Extension Handling (If BSM_file_extension is provided):
   - Reads an extended BSM CSV file.
   - Processes each record and updates object_class_dict.
   - Repeats the hierarchical model generation process for the extended model.
   - Outputs the extended hierarchical model to a CSV file.

7. Debugging and Tracing:
   - Uses DEBUG and TRACE flags to control the output of diagnostic messages, aiding in understanding the process flow and troubleshooting.

   Example Usage:
python graphWalk.py AAA_BSM.csv AAA_LHM.csv -l EXT_BSM.csv -m EXT_LHM.csv -o

Where:
- The first parameter is the input BSM file.
- The second parameter is the output LHM file.
- `-l` option specifies the input extension BSM file.
- `-m` option specifies the output extension LHM file.

This script specializes in constructing a hierarchical representation of the BSM, adhering to standards. 
It efficiently manages the complexities of class hierarchies, associations, and specializations to produce a structured Hierarchical Message Definition (HMD).
"""

import os
import sys
import argparse
import csv
import copy
import re
from collections import OrderedDict, Counter

# from common.utils import (
#     LC3,
#     file_path,
#     is_file_in_use,
#     split_camel_case,
#     abbreviate_term,
#     normalize_text
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
    # Replace /, _, -, (, ) with spaces
    text = re.sub(r'[\/_\-\(\)]', ' ', text)
    # Replace multiple spaces with a single space and trim leading/trailing spaces
    text = re.sub(r'\s+', ' ', text).strip()
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


class Graphwalk:
    def __init__ (
            self,
            bsm_file,
            # bsm_file_extension,
            lhm_file,
            root_terms,
            option,
            encoding,
            trace,
            debug
        ):

        self.bsm_file = bsm_file.replace('/', os.sep)
        self.bsm_file = file_path(self.bsm_file)
        if not self.bsm_file or not os.path.isfile(self.bsm_file):
            print(f'[INFO] No input Basic Semantic Model (BSM) file {self.bsm_file}.')
            sys.exit()

        self.lhm_file = lhm_file.replace('/', os.sep)
        self.lhm_file = file_path(self.lhm_file)
        if 'IN_USE' == is_file_in_use(self.lhm_file):
            print(f'[INFO] Logical Hierarchical Model (FSM) file {self.lhm_file} is **IN USE**.')
            sys.exit()

        self.encoding = encoding.strip() if encoding else 'utf-8-sig'

        #  Set debug and trace flags, and file path separator
        self.root_terms = root_terms
        self.DNM = True if option else False
        self.TRACE = trace
        self.DEBUG = debug

        #  Initialize dictionaries and lists
        self.object_class_dict = {}
        self.LIFO_list = []
        self.LHM_model = []
        self.hierarchy_records = []
        self.is_singular_association = False
        self.selected_class = None
        self.sequence = 1
        self.elementnames = set()
        self.current_class = None

        self.index_manager = IndexManager()

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
        self.debug_print(f"{extra}{record['level']} {record['id']} {record['type']} {record['identifier'] or '   '} {record['class_term']}. {record['property_term']}. {record['representation_term'] or record['associated_class']} {record['multiplicity']}")

    def append_LHM_model(self, record, extra=""):
        self.print_record(record, f"LHM {extra}")
        self.LHM_model.append(record)

    def append_hierarchy_records(self, record, extra=""):
        self.print_record(record, f"record {extra}")
        self.hierarchy_records.append(record)

    def update_class_term(self, row):
        """
        Utility function to update class term
        """
        id = row['id']
        if not id:
            return None
        _type = row['property_type']
        class_term = row['class_term']
        # module = row['module']
        if '.' in class_term:
            class_term = class_term[:class_term.index('.')]
        if _type=='Class':
            if not class_term in self.object_class_dict:
                self.object_class_dict[class_term] = row
                self.object_class_dict[class_term]['properties'] = {}
        else:
            if not class_term in self.object_class_dict:
                self.error_print(f"{class_term} not defined in self.object_class_dict.\n{row}")
            self.object_class_dict[class_term]['properties'][id] = row
            self.object_class_dict[class_term]['properties'][id]['class_term'] = class_term
        return class_term

    def extract_uppercase_and_digits(self, string):
        # Regular expression to match consecutive uppercase letters followed by consecutive digits
        match = re.match(r'([A-Z]+)(\d+)', string)
        if match:
            uppercase_part = match.group(1)
            digit_part = match.group(2)
            return uppercase_part + digit_part
        else:
            return None

    def set_path(self, data, aggregates):
        """
        Function to set path for hierarchical model
        """
        id = data['id']
        level = data['level']
        _type = data['type']
        multiplicity = data['multiplicity']
        if _type in ['C', 'R', 'DNM']:
            if level > 1 and '1' == multiplicity[-1]:
                self.is_singular_association = True
            else:
                self.is_singular_association = False

        id_ = self.index_manager.generate_indexed_code(id)

        if 1 == level:
            aggregates[level - 1] = {'id':id_, 'multiplicity': '0..*'}
        else:
            aggregates[level - 1] = {'id':id_, 'multiplicity': multiplicity}
        for i in range(level, len(aggregates)):
            aggregates[i] = None

        path = ''
        for i in range(len(aggregates)):
            aggregate = aggregates[i]
            if aggregate and '*' == aggregate['multiplicity'][-1]:
                _id = aggregates[i]['id']
                path += f"/{_id}"

        if not path or id_ not in path:
            path += f"/{id_}"

        return path

    def get_semantic_path(self, record):
        """
        Function to get semantic path
        """
        _type = record['property_type']
        class_term = record['class_term']
        property_term = record['property_term']
        associated_class = record["associated_class"]
        class_list = class_term.split('-')
        _class_term = ".".join(class_list)
        if "Class"==_type or "Reference Association"==_type:
            if class_list[-1] not in _class_term:
                semantic_path = f"$.{_class_term}.{class_list[-1]}"
            else:
                semantic_path = f"$.{_class_term}"
        elif "Attribute"==_type:
            semantic_path = f"$.{_class_term}.{property_term}"
        elif _type in ["Composition", "Aggregation"]:
            if property_term:
                semantic_path = f"$.{_class_term}.{property_term} {associated_class[4:]}"
            else:
                semantic_path = f"$.{_class_term}.{associated_class}"
        return semantic_path

    def get_abbreviate_path(self, record):
        """
        Function to get abbreviate path
        """
        semantic_path = record['semantic_path']
        semantic_path_list = semantic_path[2:].split('.')
        #  Generate abbreviations for the transformed list
        abbreviated_list = [
            re.sub(r"[\s]", "", abbreviate_term(term, 4)) for term in semantic_path_list
        ]
        _abbreviated_term = ".".join(abbreviated_list)
        return _abbreviated_term

    def normalize_and_deduplicate(self, text):
        """
        Function to normalize and deduplicate text
        """
        # 1. Remove the leading "$.nnn:" prefix (e.g., "$.cor:")
        # Matches "$.", then any characters except ":", followed by ":" at the start of the string.
        text = re.sub(r'^\$\.[^:]+:', '', text)

        # 2. Replace intermediate ".nnn:" metadata tags with a single space
        # Matches ".", then any characters except ":", followed by ":".
        text = re.sub(r'\.[^:]+:', ' ', text)

        # 3. Remove all underscores ("_")
        text = text.replace('_', '')

        # 4. Remove all remaining periods (".")
        text = text.replace('.', '')

        # 5. Perform sequence-preserved deduplication
        # Split the cleaned text into words, then keep only the first occurrence of each word (case-insensitive).
        words = re.split(r'\s+', text.strip())
        seen = set()
        unique_words = []

        for w in words:
            # Check case-insensitively but preserve original casing for the output
            lower_w = w.lower()
            if lower_w not in seen:
                seen.add(lower_w)
                unique_words.append(w)

        # Join the unique words back into a single neutral string
        result = " ".join(unique_words)

        return result

    def set_element_by_path(self, semantic_path, record):
        """
        Calculates and sets the 'element' field in the record based on 
        the hierarchy found in the semantic_path and the record's level.
        """
        if not semantic_path:
            # Fallback if no path is provided
            record['element'] = LC3(record.get('property_term', ''))
            return
        level = int(record['level'])
        _type = record['type']
        class_term = record['class_term']
        name = element = None

        # 1. Extract basic components
        # Path format: "module:Class.module:SubClass.property"
        semantics = semantic_path.split('.')
        if _type in ['C', 'R']:
            class_term = semantics[-1]
        else:
            class_term = semantics[-2] if len(semantics) > 1 else semantics[0]

        # Extract 3-letter module prefix (e.g., 'bus' from 'bus:Accountant')
        module = class_term[:class_term.find(':')] if ':' in class_term else class_term[:3]
        level = record.get('level', 1)

        # 2. Determine depth of segments to include
        # Level 1 -> last 1, Level 2 -> last 2, etc.
        depth = min(level, len(semantics))
        path_segments = semantics[-depth:]

        # 3. Clean segments for the element name
        # Removes the "mod:" prefix from each segment (e.g., "bus:Accountant" -> "Accountant")
        text_parts = [
            segment[segment.find(':')+1:] if ':' in segment else segment 
            for segment in path_segments
        ]

        # 4. Final generation
        if level > 1:
            # Join parts (e.g., "Accountant Name"), deduplicate words,
            # and re-apply the current module prefix
            combined_text = " ".join(text_parts[1-level:])
            normalized_text = self.normalize_and_deduplicate(combined_text)
        else:
            # Level 1 or below: use the property term or the last segment directly
            normalized_text = record.get('property_term') or text_parts[-1]
        name = f"{module}:{normalized_text}"
        element = LC3(name)

        record['name'] = name
        record['element'] = element

        return class_term, name, element, record

    def model2record(self):
        """
        Function to transform hierarchical model to records suitable for CSV output
        """
        aggregates = [''] * 10

        for data in self.LHM_model:
            record = copy.deepcopy(data)
            level = int(record['level'])
            _type = record['type']
            class_term = record['class_term']
            identifier = record['identifier']
            property_term = record['property_term']
            datatype = record['representation_term']

            #  Generate semantic path and assign it to the record
            semantic_path = self.get_semantic_path(record)
            record['semantic_path'] = semantic_path

            name = ''
            datatype = ''
            if "REF"==identifier:
                index = semantic_path.rfind(".")
                if index != -1:
                    class_term, name, element, record = self.set_element_by_path(semantic_path, record)
                else:
                    name = property_term
            elif 'C'==_type:
                class_term, name, element, record = self.set_element_by_path(semantic_path, record)
            elif 'R' == _type:
                class_term, name, element, record = self.set_element_by_path(semantic_path, record)
                class_term = record['originating_class_term'].split('-')[-1]
                datatype = ''
            elif 'A' == _type:
                class_term, name, element, record = self.set_element_by_path(semantic_path, record)
            else:
                self.debug_print(f"Wrong data for {semantic_path}")

            record['class_term'] = class_term
            record['name'] = name
            record['datatype'] = datatype

            abbreviation_path = self.get_abbreviate_path(record)
            record['abbreviation_path'] = abbreviation_path
            path = self.set_path(data, aggregates)
            record['path'] = path
            id = path.split('/')[-1]
            record['id'] = id
            level = str(level)
            record['level'] = level
            if 'properties' in record:
                del record['properties']
            record['sequence'] = self.sequence
            self.sequence += 1

            self.append_hierarchy_records(record)

        if 'xpath' not in self.hierarchy_records[0]:
            records = []
            for record in self.hierarchy_records:
                semantic_path = record['semantic_path']
                path_list = semantic_path[2:].split('.')
                if len(path_list) > 1:
                    xpath = self.build_xpath(semantic_path)
                    if not xpath:
                        self.debug_print(f"Empty xpath for {semantic_path}")
                else:
                    xpath = f"/{path_list[0]}"
                record['xpath'] = xpath
                records.append(record)
        else:
            records = self.hierarchy_records

        return records

    def build_xpath(self, semantic_path):
        """
        Function for build xpath from semantic_path
        """
        #  Extract the top-level path from the semantic_path (e.g., '$.Accounting Entries')
        leading_path = '.'.join(semantic_path.split('.')[:2])
        #  Check if the semantic_path starts with the expected leading path
        if not semantic_path.startswith(leading_path):
            return None
        #  Extract the remaining parts of the path after the leading path
        path_suffix = semantic_path.replace(leading_path + '.', '').split('.')
        current_path = leading_path
        xpath_parts = []
        #  Find the root element corresponding to the top-level path
        root_record = next((r for r in self.hierarchy_records if r['semantic_path'] == current_path), None)
        if not root_record:
            return None
        xpath_parts.append(root_record['element'])
        #  Traverse through each level of the semantic path to collect element names
        for part in path_suffix:
            current_path += f'.{part}'
            record = next((r for r in self.hierarchy_records if r['semantic_path'] == current_path), None)
            if not record:
                return None        
            xpath_part = record['element']
            xpath_parts.append(xpath_part)
        xpath = '/' + '/'.join(xpath_parts) if xpath_parts else '/'
        return xpath

    def parse_class(self, class_term, REFERENCE_OF = False):
        """
        Function to parse class terms and handle specializations
        """        
        global current_multiplicity
        """
        Step 1: Copy a class to the Hierarchical Message Definition and place it on the top of 
        the LIFO list.

        Attempt to resolve the class term by stripping leading "<prefix>_ " segments up to three
        times. Some class terms are prefixed with module identifiers (e.g., "CI_ Trade_ Tax"), and
        the lookup must fall back to the base class term if the prefixed version is not registered.
        """
        _class_term = class_term
        for _ in range(4):
            #  initial attempt + up to 3 prefix removals
            if _class_term in self.object_class_dict:
                break
            #  If the term contains no further "_ ", no more prefixes can be removed.
            if "_ " not in _class_term:
                break
            #  Remove the first "<prefix>_ " to try the next simplified class term.
            _class_term = f'{_class_term[:3]}:{_class_term.split("_ ", 1)[1]}'

        if _class_term not in self.object_class_dict:
            candidates = [x for x in  self.object_class_dict.keys() if _class_term[4:] in x]
            if candidates:
                _class_term = candidates[0]
                self.current_class = _class_term
            else:
                self.error_print(f"'{_class_term}' from '{class_term}' not in object_class_dict.")
                return

        object_class = copy.deepcopy(self.object_class_dict[_class_term])
        if REFERENCE_OF:
            object_class['property_type'] = 'Reference Association'

        _type = object_class['property_type']
        self.LIFO_list.append(class_term)
        level = len(self.LIFO_list)
        self.trace_print(f"parse_class('{class_term}') REFERENCE_OF:{REFERENCE_OF}\n       check {_type} '{_class_term}'\n       LIFO_list: {self.LIFO_list}")
        """
        A. Copy the class to the hierarchical logical data model.
        Copy all properties and associations to the hierarchical logical data model.
        Conventionally, properties not related to the associated object class should be placed 
        before them, but this is not a requirement.
 
        B. Place the selected class on the top of the LIFO list if not Reference Association.
        """
        object_class['level'] = level
        if level > 1:
            LIFO_term = '-'.join(self.LIFO_list)
            object_class['class_term'] = LIFO_term

        if REFERENCE_OF:
            """
            iii) Reference Associations
            • Copy associated class with adding it to the LIFO (Last In, First Out) list.
            For copying reference association's associated class, the new entry in the LHM should 
            include:
                - Level: n
                - Type: 'R' (Relation)
                - Identifier: Empty
                - Name:
                - If an association role for the reference association is defined, format as 
                  "{association role}_{associated class}".
                - If no association role is defined, use "{associated class}".
                - Datatype: Leave empty as datatype is not applicable for reference association's 
                  associated class.
            """
            object_class['type'] = 'R'
            definition = object_class['definition']
            definition = definition.replace('A class', f"The reference association to the {class_term.replace('_', ' ')} class, which is a class")
            object_class['definition'] = definition

            LIFO_term = '-'.join(self.LIFO_list)
            if REFERENCE_OF:
                object_class['originating_class_term'] = LIFO_term

        else:
            object_class['type'] = 'C'

        if level > 1 and not object_class['multiplicity'] and current_multiplicity:
            object_class['multiplicity'] = current_multiplicity

        self.append_LHM_model(object_class)

        """
        a) Step 1: Copy class attributes from the BSM to the LHM.
        Procedure:
        In this step, all attributes and associations relevant to the class are incorporated, with 
        the 'level' of attribute entries incremented by 1. Let the resulting value of 'level' be n
        after the increment.
        Attributes and reference associations are prioritized over composition/aggregation 
        associations to maintain clarity and order. The copying logic is detailed as follows:
        """
        if REFERENCE_OF:

            copied_attributes = [
                copy.deepcopy(x)
                for x in object_class["properties"].values()
                if "Attribute" == x["property_type"] and "PK" == x["identifier"]
            ]
            if copied_attributes:
                for property in copied_attributes:
                    """
                    iii) Reference Associations
                    • Copy the unique identifier of the associated class.
                    Additionally, check for reference associations to identify the unique identifier of 
                    the associated class. If found, copy this identifier to the LHM as:
                        - Level: n + 1
                        - Type: 'A' (Attribute)
                        - Identifier: 'REF' (Reference Identifier)
                        - Name: The copied_property term of the found unique identifier.
                        - Datatype: The representation term of the found unique identifier.
                    Note: This entry in the LHM is a reference identifier, serving as a foreign key to 
                    the reference association class.
                    """
                    property['type'] = 'A'
                    property['level'] = 1+level
                    property['identifier'] = 'REF'
                    property['class_term'] = LIFO_term
                    definition = property['definition']
                    definition = definition.replace('unique identifier', 'reference identifier')
                    property['definition'] = definition

                    self.append_LHM_model(property)
        else:
            copied_attributes = [
                copy.deepcopy(x)
                for x in object_class["properties"].values()
                if "Attribute" == x["property_type"]
            ]
            if copied_attributes: 
                for property in copied_attributes:
                    property['type'] = 'A'
                    property['level'] = 1+level
                    property['identifier'] = ''
                    property['class_term'] = LIFO_term

                    self.append_LHM_model(property)
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
        copied_associations = [
            cls
            for cls in [copy.deepcopy(x) for x in object_class["properties"].values()]
            if cls["property_type"]
            in ["Reference Association", "Aggregation", "Composition"]
        ]
        if copied_associations:
            """
            B. Mandatory, Singular.
            Pick any 1..1 association that is navigable to needed information.
            """
            mandate_classes = [
                cls
                for cls in copied_associations
                if cls["multiplicity"] in ["1", "1..1"]
            ]
            """
            C. Singular.
            Pick any navigable association that is (0,1) and leads to needed information.
            """
            singular_classes = [
                cls
                for cls in copied_associations
                if "0..1" == cls["multiplicity"]
            ]
            """
            E. Other Plural.
            Pick any navigable association that leads to needed information.
            """
            other_classes = [
                cls
                for cls in copied_associations
                if cls["multiplicity"] in ["0..*", "1..*"]
            ]
            """
            B. Mandatory, Singular.
            Pick any 1..1 association that is navigable to needed information.
            """
            for _class in mandate_classes:
                property_type = _class['property_type']
                property_term = _class['property_term']
                associated_class = _class['associated_class']
                if property_term:
                    selectedclass_term = f"{property_term}_ {associated_class[4:]}"
                else:
                    selectedclass_term = associated_class
                if selectedclass_term and selectedclass_term not in self.LIFO_list:
                    current_multiplicity = _class['multiplicity']
                    if self.DEBUG:
                        if property_term:
                            self.debug_print(f"  {level} {_class['class_term']}. [{current_multiplicity}] {property_type} {property_term}_ {associated_class}")
                        else:
                            self.debug_print(f"  {level} {_class['class_term']}. [{current_multiplicity}] {property_type} {associated_class}")
                    self.parse_class(selectedclass_term, 'Reference Association'==property_type and _class['class_term'] or None)
            """
            C. Singular.
            Pick any navigable association that is (0,1) and leads to needed information.
            """
            for _class in singular_classes:
                property_type = _class['property_type']
                property_term = _class['property_term']
                associated_class = _class['associated_class']
                if property_term:
                    selectedclass_term = f"{property_term}_ {associated_class[4:]}"
                else:
                    selectedclass_term = associated_class
                if selectedclass_term and selectedclass_term not in self.LIFO_list:
                    current_multiplicity = _class['multiplicity']
                    if self.DEBUG:
                        if property_term:
                            self.debug_print(f"  {level} {_class['class_term']}. [{current_multiplicity}] {property_type} {property_term}_ {associated_class}")
                        else:
                            self.debug_print(f"  {level} {_class['class_term']}. [{current_multiplicity}] {property_type} {associated_class}")
                    self.parse_class(selectedclass_term, 'Reference Association'==property_type and _class['class_term'] or None)
            """
            E. Other Plural.
            Pick any navigable association that leads to needed information.
            """
            for _class in other_classes:
                property_type = _class['property_type']
                property_term = _class['property_term']
                associated_class = _class['associated_class']
                if property_term:
                    selectedclass_term = f"{property_term}_ {associated_class[4:]}"
                else:
                    selectedclass_term = associated_class
                if selectedclass_term and selectedclass_term not in self.LIFO_list:
                    current_multiplicity = _class['multiplicity']
                    if self.DEBUG:
                        if property_term:
                            self.debug_print(f"  {level} {_class['class_term']}. [{current_multiplicity}] {property_type} {property_term}_ {associated_class}")
                        else:
                            self.debug_print(f"  {level} {_class['class_term']}. [{current_multiplicity}] {property_type} {associated_class}")
                    self.parse_class(selectedclass_term, 'Reference Association'==property_type and _class['class_term'] or None)
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
        if self.LIFO_list:
            self.debug_print(f"-- Done: {self.LIFO_list[-1]}\n")
            self.LIFO_list.pop(-1)
        self.debug_print(f"POP LIFO_list: {class_term} type is '{_type}'\n       LIFO_list: {self.LIFO_list}")

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
            if property_term:
                term = f"{property_term}_ {associated_class[4:]}"
            else:
                term = associated_class
        return term

    def process_record(self, row, header):
        """
        Function for register row data to self.object_class_dict[class_term]
        """
        term = self.getproperty_term(row)
        record = {key: row.get(key, '') for key in header}
        p_type = record['property_type']
        class_term = record['class_term']

        if p_type=='Class':
            if not class_term in self.object_class_dict:
                self.object_class_dict[class_term] = record
                self.object_class_dict[class_term]['properties'] = {}
        else:
            if not class_term in self.object_class_dict:
                self.error_print(f"{class_term} not defined in self.object_class_dict.\n{record}")
            self.object_class_dict[class_term]['properties'][term] = record
            self.object_class_dict[class_term]['properties'][term]['class_term'] = class_term

        self.debug_print(f"{record['property_type'][:2]} '{class_term}' {p_type[:2]} '{record['associated_class'] or record['property_term']}'")

        return class_term

    def graph_walk(self):
        """
        Function to traverse associatins with graph walk method
        """
        self.selected_class = set()
        #  read CSV file
        header = [
            'sequence', 'level', 'property_type', 'identifier', 'class_term', 'property_term', 'representation_term', 'associated_class', 'multiplicity', 'definition', 'module', 'label_local', 'definition_local', 'id'
        ]
        #  write CSV file
        header2 = [
            'sequence', 'level', 'type', 'identifier', 'name', 'datatype', 'multiplicity', 'domain_name', 'definition', 'module', 'class_term', 'id', 'path', 'semantic_path', 'abbreviation_path', 'label_local', 'definition_local', 'element', 'xpath'
        ]

        if self.bsm_file:
            with open(self.bsm_file, encoding = self.encoding, newline='') as f:
                reader = csv.DictReader(f, fieldnames=header)
                next(reader)
                for row in reader:
                    self.process_record(row, header)

        self.selected_class = set(self.object_class_dict.keys())
        root_found = False
        self.LHM_model = []
        for root_term in self.root_terms:
            if root_term in self.selected_class:
                root_found = True
                self.debug_print(f"- root_term parse_class({root_term})")
                self.parse_class(root_term)      

        if not root_found:
            self.error_print(f"Root {self.root_terms} not found in object_class_dict.")

        records = self.model2record()

        # # records = self.update_name(hierarchy_records)
        out_records = [{k: v for k, v in d.items() if k in header2} for d in records]

        with open(self.lhm_file, 'w', encoding = self.encoding, newline='') as f:
            writer = csv.DictWriter(f, fieldnames = header2)
            writer.writeheader()
            writer.writerows(out_records)

        print(f'** END {self.lhm_file}')


class IndexManager:
    """
    IndexManager class to manage class and property indexing
    """
    def __init__(self):
        self.class_counter = {}
        self.previous_suffix = {}
        self.base_map = "abcdefghijklmnopqrstuvwxyz"
        self.extended_map = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" + self.base_map
        self.current_suffix = None
        self.last_base_class = None

    def get_suffix(self, class_name):
        if class_name not in self.class_counter:
            self.class_counter[class_name] = 0
        self.class_counter[class_name] += 1
        current_suffix = self.int_to_custom_alpha(self.class_counter[class_name] - 1)
        if class_name in self.previous_suffix and self.previous_suffix[class_name] == current_suffix:
            self.debug_print(f"Warning: Duplicate suffix {current_suffix} for class {class_name}")
        self.previous_suffix[class_name] = current_suffix
        return current_suffix

    def int_to_custom_alpha(self, index):
        if index < 26:
            return self.base_map[index % 26]
        suffix = self.int_to_custom_alpha(index // 26 - 1) + self.extended_map[index % 62]
        return suffix

    def generate_indexed_code(self, item):
        if "_" not in item:
            #  A new Class has been found
            self.current_suffix = self.get_suffix(item)
            modified = f"{item}{self.current_suffix}"
            self.last_base_class = item  # Update: Set new base class name
        else:
            #  For property items, use the current Class suffix
            base, extension = item.split('_', 1)
            if base != self.last_base_class:
                #  If it differs from the previous class, update the suffix
                self.current_suffix = self.get_suffix(base)
            modified = f"{base}{self.current_suffix}_{extension}"
        return modified


def main():
    """
    Main function to execute the script
    """
    RAESER = False
    if RAESER:
        """
        # Create the parser
        "args": ["../XBRL-GL-2025/BSM/xBRL-GL2.0_BSMa.csv", "../XBRL-GL-2025/LHM/xBRL-GL2.0_LHMa.csv", "-r Accounting Entries+Accounting Entries JPN", "-l", "../XBRL-GL-2025/BSM/xBRL-GL2.0_BSM_JPN.csv", "-m", "../XBRL-GL-2025/LHM/xBRL-GL2.0_LHM_JPN.csv", "-t", "-d"]
        """
        parser = argparse.ArgumentParser(
            prog='AWI21926_Specialization.py',
            usage='%(prog)s BSM_file LHM_file -l BSM_file_extension -m LHM_file_extension -e encoding [options] ',
            description='Converts logical model to HMD with graph walk.'
        )
        parser.add_argument('BSM_file', metavar='BSM_file', type = str, help='Business semantic model file path')
        parser.add_argument('LHM_file', metavar='LHM_file', type = str, help='LHM file path')
        # Allow multiple values with action='append' or nargs='+'
        parser.add_argument("-r", "--root", action="append", help="Root class term(s) for LHM to process. Can be specified multiple times.")
        #Other options
        parser.add_argument('-o', '--option', required = False, action='store_true')
        parser.add_argument('-e', '--encoding', required = False, default='utf-8-sig', help='File encoding, default is utf-8-sig')
        parser.add_argument('-t', '--trace', required = False, action='store_true')
        parser.add_argument('-d', '--debug', required = False, action='store_true')


        args = parser.parse_args()

        # Flatten the list if necessary
        root_terms = []
        if args.root:
            for val in args.root:
                if isinstance(val, str) and "+" in val:
                    root_terms.extend(val.split("+"))
                else:
                    root_terms.append(val)
        root_terms = [x.strip() for x in root_terms]

        processor = Graphwalk(
            bsm_file = args.BSM_file.strip(),
            lhm_file = args.LHM_file.strip(),
            root_terms = root_terms,
            option = args.option if args.option else False,
            encoding = args.encoding.strip() if args.encoding else None,
            trace = args.trace,
            debug = args.debug
        )
    else:
        EXTENSION = True
        BASE_DIR = ""
        args = {
            "BSM_file": f"{BASE_DIR}xBRL-GL2.0_BSM_t.csv",
            "LHM_file": f"{BASE_DIR}xBRL-GL2.0_LHM_t.csv" if not EXTENSION else f"{BASE_DIR}xBRL-GL2.0_LHM_btx_t.csv",
            "root_terms": ["cor:Accounting Entries"] if not EXTENSION else ["btx:Business Transactions"],
            "option": None,
            "encoding": "utf-8-sig",
        }

        processor = Graphwalk(
            bsm_file = args["BSM_file"],
            lhm_file = args["LHM_file"],
            root_terms = args["root_terms"],
            option = args["option"],
            encoding = args["encoding"],
            trace = True,
            debug = True
        )

    processor.graph_walk()

if __name__ == '__main__':
    main()
