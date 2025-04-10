#!/usr/bin/env python3
# coding: utf-8
"""
awi21926graphwalk.py
Generates ADC Logical Hierarchical (LHM)  Model from Business Semantic Model (BSM) CSV with Graph Walk

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-01-17

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
ABOUT THIS SCRIPT
This second Python script complements the first by further processing the Business Semantic Model (BSM),
specifically focusing on hierarchical relationships and generating a Logical Hierarchical Model (LHM) CSV 
from a BSM CSV. Here’s a detailed procedure description:

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

5. Decoupled Navigation Mode (DNM):
   - Graph walk supports Decoupled Navigation Mode, allowing both header and line classes to serve as root classes and be traversed independently in the graph walk.

6. Output Hierarchical Model to CSV:
   - Converts the hierarchical model into records suitable for LHM CSV output using model2record().
   - Writes these records to a CSV file in the specified directory.

7. Extension Handling (If BSM_file_extension is provided):
   - Reads an extended BSM CSV file.
   - Processes each record and updates object_class_dict and exception_class.
   - Repeats the hierarchical model generation process for the extended model.
   - Outputs the extended hierarchical model to a CSV file.

8. Debugging and Tracing:
   - Uses DEBUG and TRACE flags to control the output of diagnostic messages, aiding in understanding the process flow and troubleshooting.

   Example Usage:
python awi21926graphWalk.py AWI21926_BSM.csv AWI21926_DNM_LHM.csv -l BIS_BSM.csv -m BIS_DNM_LHM.csv -o

Where:
- The first parameter is the input BSM file.
- The second parameter is the output LHM file.
- `-l` option specifies the input extension BSM file.
- `-m` option specifies the output extension LHM file.

This script specializes in constructing a hierarchical representation of the BSM, adhering to standards. It efficiently manages the complexities of class hierarchies, associations, and specializations to produce a structured Hierarchical Message Definition (HMD).
"""

import os
import sys
import argparse
import csv
import copy
import re
from collections import OrderedDict, Counter

# Set debug and trace flags, and file path separator
DEBUG = False
TRACE = True
SEP = os.sep
DNM = False

# Initialize dictionaries and lists
object_class_dict = {}
LIFO_list = []
LHM_model = []
is_singular_association = False
exception_class = set()
sequence = 1000


# Utility function to create full file paths
def file_path(pathname):
    if SEP == pathname[0:1]:
        return pathname
    else:
        pathname = pathname.replace('/', SEP)
        dir = os.path.dirname(__file__)
        new_path = os.path.join(dir, pathname)
        return new_path


# Utility function to check if a file is in use
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
                pass  # Creating the file
            result = 'CREATED'
            print(f"File {file_path} has been created.")
        except Exception as e:
            print(f"Error while creating file: {e}")
            result = 'ERROR_CREATING_FILE'
    return result


# Utility function to update class term
def update_class_term(row):
    global object_class_dict
    global exception_class

    id = row['id']
    if not id:
        return None
    _type = row['property_type']
    class_term = row['class_term']
    if '.' in class_term:
        class_term = class_term[:class_term.index('.')]
    # associated_class_term = row['associated_class']
    if _type in ['Class','Specialized Class']:
        if not class_term in object_class_dict:
            object_class_dict[class_term] = row
            object_class_dict[class_term]['properties'] = {}
        if 'level' in row and int(row['level']) > 1:
            associated_class = object_class_dict[class_term]
            if 'Base' != associated_class['module']:
                exception_class.add(class_term)
    else:
        if not class_term in object_class_dict:
            object_class_dict[class_term] = row
            object_class_dict[class_term]['properties'] = {}
        object_class_dict[class_term]['properties'][id] = row
        object_class_dict[class_term]['properties'][id]['class_term'] = class_term
    return class_term


def extract_uppercase_and_digits(string):
    # Regular expression to match consecutive uppercase letters followed by consecutive digits
    match = re.match(r'([A-Z]+)(\d+)', string)
    if match:
        uppercase_part = match.group(1)
        digit_part = match.group(2)
        return uppercase_part + digit_part
    else:
        return None


# Function to set path for hierarchical model
def set_path(data, aggregates):
    global is_singular_association
    id = data['id']
    level = data['level']
    _type = data['type']
    multiplicity = data['multiplicity']

    if _type in ['C', 'R', 'DNM']:
        if level > 1 and '1' == multiplicity[-1]:
            is_singular_association = True
        else:
            is_singular_association = False

    id_ = index_manager.generate_indexed_code(id)

    if 1 == level:
        aggregates[level - 1] = {'id':id_, 'multiplicity': '0..*'}
    else:
        aggregates[level - 1] = {'id':id_, 'multiplicity': multiplicity}

    for i in range(level, 11 - level):
        aggregates[i] = None

    path = ''
    for i in range(level - 1):
        if 0 == i or '*' == aggregates[i]['multiplicity'][-1]:
            _id = aggregates[i]['id']
            path += f"/{_id}"
    path += f"/{id_}"

    return path


# Function to get semantic path
def get_semantic_path(record):
    class_term = record['class_term']
    class_list = class_term.split('-')
    class_list = [f"({x[:x.index('_')]}) {x[1 + x.index('_'):]}" if "_" in x else x for x in class_list]
    _class_term = ".".join(class_list)
    property_term = record['property_term']
    if property_term:
        semantic_path = f"$.{_class_term}.{property_term}"
    else:
        semantic_path = f"$.{_class_term}"
    return semantic_path


# Function to get abbreviate path
def get_abbreviate_path(record):
    class_term = record['class_term']
    class_list = class_term.split('-')
    class_list = [
        f"({x[:x.index('_')]}) {x[1 + x.index('_'):]}" if "_" in x else x for x in class_list
    ]
    # Generate abbreviations for the transformed list
    abbreviated_list = [
        abbreviation_generator.process_term(term)['Generated Abbreviation'] for term in class_list
    ]
    _abbreviated_term = ".".join(abbreviated_list)
    property_term = record['property_term']
    abbreviated_property_term = abbreviation_generator.process_term(property_term)['Generated Abbreviation']
    if property_term:
        abbreviated_path = f"{_abbreviated_term}.{abbreviated_property_term}"
    else:
        abbreviated_path = f"{_abbreviated_term}"
    return abbreviated_path


# Function to transform hierarchical model to records suitable for CSV output
def model2record(LHM_model):
    global sequence
    hierarchy_records = []
    aggregates = [''] * 10
    current_module = ''
    current_class = ''
    i = 0
    for data in LHM_model:
        level = int(data['level'])
        record = copy.deepcopy(data)

        if 1 == level:
            current_module = record['module']
        else:
            record['module'] = current_module

        semantic_path = get_semantic_path(record)
        record['semantic_path'] = semantic_path

        abbreviation_path = get_abbreviate_path(record)
        record['abbreviation_path'] = abbreviation_path

        path = set_path(data, aggregates)
        record['path'] = path

        id = path.split('/')[-1]
        record['id'] = id

        i += 1

        if 'A' == data['type']:
            class_term = semantic_path[:semantic_path.rindex('.')][2:].split('.')[-1]
        else:
            class_term = semantic_path[2:].split('.')[-1]
        if 'A' != data['type']:
            current_class = class_term
        record['class_term'] = class_term

        property_term = record['property_term']
        if 'Active Indicator' == property_term and not DNM:
            continue

        if current_class.endswith('Business Segment'):
            if level > 4: 
                continue
            elif level > 3 and record['type'] in ['C', 'R']:
                continue

        level = str(level)
        record['level'] = level

        if 'properties' in record:
            del record['properties']

        record['sequence'] = sequence
        sequence += 1

        hierarchy_records.append(record)

    return hierarchy_records


# Function to update the name field in the hierarchical records
def update_name(hierarchy_records):
    records = []
    parent_class = [''] * 7
    for record in hierarchy_records:
        property_type = record['property_type']
        level = int(record['level'])
        class_term = record['class_term']
        representation_term = record['representation_term']
        property_term = record['property_term']
        name = ''
        datatype = ''
        if 'Class' == property_type:
            name = class_term.split('-')[-1]
            for i in range(level, 7):
                parent_class[i] = ''
        elif 'Attribute' == property_type:
            name = property_term
            datatype = representation_term
        elif 'Reference Association' == property_type:
            record['identifier'] = ''
            name = class_term
            datatype = representation_term
        else:
            continue
        if '_' in name:
            name = f"({name[:name.index('_')]}) {name[1 + name.index('_'):]}"
        record['name'] = name
        record['datatype'] = datatype
        records.append(record)
    return records


# Function to parse class terms and handle specializations
def parse_class(class_term, REFERENCE_OF = False):
    global current_multiplicity
    """
    Step 1: Copy a class to the Hierarchical Message Definition and place it on the top of
    the LIFO list.
    """
    _class_term = class_term
    if '_' in _class_term: # romove originating class name for this associated class
        _class_term = _class_term[1+_class_term.index('_'):]
    if _class_term not in object_class_dict:
        print(f"#### '{_class_term}' not in object_class_dict")
        return
    object_class = copy.deepcopy(object_class_dict[_class_term])
    if REFERENCE_OF:
        object_class['property_type'] = 'Reference Association'
    _type = object_class['property_type']
    if DEBUG or TRACE:
        print(f"{_type in ['Subclass','Specialized Class'] and '-' or ' '} {_type}: parse_class('{class_term}') check  '{_class_term}'\t{LIFO_list}")
    """
    A. Copy the class to the hierarchical logical data model.
    Copy all properties and associations to the hierarchical logical data model.
    Conventionally, properties not related to the associated object class should be placed
    before them, but this is not a requirement.

    B. Place the selected class on the top of the LIFO list if not Reference Association.
    """
    if REFERENCE_OF:
        level = 1 + len(LIFO_list)
    else:
        LIFO_list.append(class_term)
        level = len(LIFO_list)
    if DEBUG:
        print(f'  Update LIFO_list {LIFO_list}\n')
    object_class['level'] = level
    if level > 1:
        LIFO_term = '-'.join(LIFO_list)
        object_class['class_term'] = LIFO_term
    if REFERENCE_OF:
        """
        iii)	Reference Associations
        •	Copy associated class with adding it to the LIFO (Last In, First Out) list.
        For copying reference association's associated class, the new entry in the LHM should include:
            - Level: n
            - Type: 'R' (Relation)
            - Identifier: Empty
            - Name:
            - If an association role for the reference association is defined, format as "{association role}_{associated class}".
            - If no association role is defined, use "{associated class}".
            - Datatype: Leave empty as datatype is not applicable for reference association's associated class.
        """
        object_class['class_term'] += f"-{class_term}"
        if DEBUG:
            print(f"class_term:{class_term} _class_term:{_class_term} object_class['class_term']:{object_class['class_term']}")
        definition = object_class['definition']
        definition = definition.replace('A class', f"The reference association to the {class_term.replace('_', ' ')} class, which is a class")
        object_class['definition'] = definition
        object_class['type'] = 'R'
        properties_list = {}
        for key in object_class_dict:
            if key.startswith(_class_term):
                properties = object_class_dict[_class_term].get('properties', [])
                for key, prop in properties.items():
                    properties_list[key] = prop
        for key, prop in properties_list.items():
            object_class['properties'][key] = prop
        hasPK = any(property.get('identifier', '') == 'PK' for property in properties_list.values())
        if '-' not in object_class['class_term'] and not hasPK:
            print(f"**ERROR Referenced class {object_class['class_term']} has no PK(primary Key).")
    else:
        object_class['type'] = 'C'
    if level > 1 and not object_class['multiplicity'] and current_multiplicity:
        object_class['multiplicity'] = current_multiplicity
    LHM_model.append(object_class)
    if DEBUG:
        print(f"  {level} {object_class['class_term']}")
    properties = copy.deepcopy(object_class['properties'])
    level += 1
    for id, property_ in properties.items():
        property = property_.copy()
        if not id:
            pass
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
            if 'Active' in  property['property_term']:
                continue
            property['level'] = level
            property['type'] = 'A'
            propertyclass_term = property['class_term']
            LIFO_term = '-'.join(LIFO_list)
            if propertyclass_term != LIFO_term:
                property['class_term'] = LIFO_term
            if REFERENCE_OF:
                LIFO_term += f"-{class_term}"
                """
                iii) Reference Associations
                 •	Copy the unique identifier of the associated class.
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
                    property['class_term'] = LIFO_term
                    definition = property['definition']
                    definition = definition.replace('unique identifier', 'reference identifier')
                    property['definition'] = definition
                    LHM_model.append(property)
                    if DEBUG: print(f"  {level} {property['class_term']} {property['property_type']} {property['identifier']} [{property['multiplicity']}] {property['property_term']}{property['associated_class']}")
            else:
                LHM_model.append(property)
                if DEBUG: print(f"  {level} {property['class_term']} {property['property_type']} [{property['multiplicity']}] {property['property_term']}{property['associated_class']}")

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

    B. Mandatory, Singular.
    Pick any 1..1 association that is navigable to needed information.
    """
    mandate_classes = [
        cls
        for cls in properties.values()
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
        for cls in properties.values()
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
        for cls in properties.values()
        if cls["property_type"]
        in ["Reference Association", "Aggregation", "Composition"]
        and cls["multiplicity"] in ["0..*", "1..*"]
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
            selectedclass_term = f"{property_term}_{associated_class}"
        else:
            selectedclass_term = associated_class
        if selectedclass_term and selectedclass_term not in LIFO_list:
            current_multiplicity = _class['multiplicity']
            if DEBUG:
                if property_term:
                    print(f"  {level} {_class['class_term']}. {property_type}[{current_multiplicity}] {property_term}_ {associated_class}")
                else:
                    print(f"  {level} {_class['class_term']}. {property_type}[{current_multiplicity}] {associated_class}")
            parse_class(selectedclass_term, 'Reference Association'==property_type and _class['class_term'] or None)
    """
    C. Singular.
    Pick any navigable association that is (0,1) and leads to needed information.
    """
    for _class in singular_classes:
        property_type = _class['property_type']
        property_term = _class['property_term']
        associated_class = _class['associated_class']
        if property_term:
            selectedclass_term = f"{property_term}_{associated_class}"
        else:
            selectedclass_term = associated_class
        if selectedclass_term and selectedclass_term not in LIFO_list:
            current_multiplicity = _class['multiplicity']
            if DEBUG:
                if property_term:
                    print(f"  {level} {_class['class_term']}. {property_type}[{current_multiplicity}] {property_term}_ {associated_class}")
                else:
                    print(f"  {level} {_class['class_term']}. {property_type}[{current_multiplicity}] {associated_class}")
            parse_class(selectedclass_term, 'Reference Association'==property_type and _class['class_term'] or None)
    """
    E. Other Plural.
    Pick any navigable association that leads to needed information.
    """
    for _class in other_classes:
        property_type = _class['property_type']
        property_term = _class['property_term']
        associated_class = _class['associated_class']
        if DNM and associated_class in f"{class_term} Line":
            continue
        if property_term:
            selectedclass_term = f"{property_term}_{associated_class}"
        else:
            selectedclass_term = associated_class
        if selectedclass_term and selectedclass_term not in LIFO_list:
            current_multiplicity = _class['multiplicity']
            if DEBUG:
                if property_term:
                    print(f"  {level} {_class['class_term']}. {property_type}[{current_multiplicity}] {property_term}_ {associated_class}")
                else:
                    print(f"  {level} {_class['class_term']}. {property_type}[{current_multiplicity}] {associated_class}")
            parse_class(selectedclass_term, 'Reference Association'==property_type and _class['class_term'] or None)
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
    if DEBUG: print(f"-- Done: {LIFO_list[-1]}\n")
    LIFO_list.pop(-1)
    if DEBUG: print(f"POP LIFO_list: {class_term} type is '{_type}'\t{LIFO_list}")

    if DNM and class_term.endswith(" Line"):
        """
        Line Class Handling:
        If a root class name ends with "Line," it is identified as the line class. In DNM, a reference association to the corresponding header class is presumed. The following actions are carried out after the normal graph walk.
        • Copy the header class.
            Name: Remove the trailing "Line" from the class term.
            Level: 2
            Type: 'DNM' (Decoupled Navigation Mode)
            Identifier: Empty
            Datatype: Leave empty as datatype is not applicable for reference association's associated class.
            Definition: Append ' This reference association is generated during the Decoupled Navigation Mode graph walk.'
        """
        header_class_term = class_term.replace(" Line", "")
        if header_class_term in object_class_dict:
            header_class = object_class_dict[header_class_term].copy()
            header_class['level'] = 2
            header_class['type'] = 'DNM'
            header_class['identifier'] = ''
            header_class['class_term'] = f"{object_class['class_term']}-{header_class_term}"
            header_class['representation_term'] = ''
            definition = header_class['definition']
            definition += ' This reference association is generated during the Decoupled Navigation Mode graph walk.'
            header_class['definition'] = definition
            LHM_model.append(header_class)
            """
            • Copy the unique identifier of the header class.
                - Name: "{The name of the line class}-{The name of the unique identifier of the header class}"
                - Level: 3
                - Type: 'A' (Attribute)
                - Identifier: ‘REF’
                - Datatype: ‘Identifier’
                - Definition: Replace 'unique identifier' with 'reference identifier.'
            """
            for id, property_ in header_class['properties'].items():
                property = property_.copy()
                if 'PK' == property['identifier']:
                    property['level'] = 1 + level
                    property['type'] = 'A'
                    property['identifier'] = 'REF'
                    property['class_term'] = f"{object_class['class_term']}-{header_class_term}"
                    definition = property['definition']
                    definition = definition.replace('unique identifier', 'reference identifier')
                    property['definition'] = definition
                    LHM_model.append(property)
                    if DEBUG: print(f"  {property['level']} {property['class_term']} {property['property_type']} {property['identifier']} [{property['multiplicity']}] {property['property_term']}{property['associated_class']}")


class AbbreviationGenerator:
    def __init__(self):
        """
        Initialize with a predefined abbreviation list if provided.
        :param abbreviation_list: A dictionary of terms and their abbreviations.
        """
        self.common_abbreviations = {
            "abbreviation": "Abrv",
            "academic": "Acad",
            "account": "Acnt",
            "accumulated": "Accum",
            "acquisition": "Acq",
            "activities": "Acts",
            "activity": "Act",
            "addition": "Add",
            "address": "Adr",
            "adjusted": "Adjd",
            "adjustment": "Adj",
            "after": "Aft",
            "allocation": "Alloc",
            "amount": "Amt",
            "application": "Apl",
            "approval": "Aprv",
            "approved": "Aprv",
            "balance": "Bal",
            "before": "Bef",
            "beginning": "Beg",
            "billing": "Bill",
            "branch": "Bra",
            "business": "Bus",
            "cancellation": "Cncl",
            "characteristic": "Char",
            "contact": "Cnt",
            "content": "Cont",
            "contract": "Contr",
            "corresponding": "Corr",
            "created": "Crea",
            "credit": "Cr",
            "currency": "Cur",
            "customer": "Cust",
            "date": "Dt",
            "debit": "Db",
            "default": "Dft",
            "department": "Dep",
            "depreciable": "Dprcbl",
            "depreciation": "Depre",
            "description": "Dscr",
            "details": "Dtls",
            "developer": "Dvlpr",
            "discount": "Dscnt",
            "dispatch": "Disp",
            "document": "Doc",
            "employee": "Emp",
            "employment": "Emplmnt",
            "encoding": "Enc",
            "ending": "End",
            "exclude": "Excl",
            "external": "Ext",
            "fiscal": "Fisc",
            "functional": "Func",
            "general": "Genr",
            "generated": "Gen",
            "grouping": "Grp",
            "hierarchy": "Hrchy",
            "impairment": "Impr",
            "include": "Incl",
            "indicator": "Ind",
            "inventory": "Inv",
            "invoice": "Invoi",
            "journal": "Jrn",
            "language": "Lang",
            "local": "Loc",
            "location": "Lct",
            "material": "Mat",
            "measurement": "Mea",
            "modified": "Mdf",
            "module": "Mod",
            "number": "Nr",
            "order": "Ord",
            "organization": "Org",
            "parent": "Par",
            "payable": "Pbl",
            "payment": "Pay",
            "percentage": "Perc",
            "period": "Per",
            "physical": "Phys",
            "primary": "Prim",
            "process": "Proc",
            "project": "Proj",
            "proportion": "Prop",
            "provision": "Prov",
            "purchase": "Pur",
            "purchasing": "Prchsng",
            "quantity": "Qt",
            "realized": "Rlzd",
            "receipt": "Rcpt",
            "receivable": "Rcvbl",
            "received": "Rcvd",
            "records": "Rec",
            "reference": "Ref",
            "regulator": "Rgltr",
            "remaining": "Rmng",
            "removal": "Rmv",
            "replacement": "Rplc",
            "report": "Rprt",
            "reporting": "Rprt",
            "requisition": "Rqstn",
            "residual": "Resi",
            "responsibility": "Resp",
            "reversal": "Rev",
            "sales": "Sal",
            "segment": "Sg",
            "sequence": "Sq",
            "service": "Srvc",
            "settlement": "Setl",
            "shipment": "Shp",
            "shipping": "Shpng",
            "software": "Sftw",
            "standard": "Std",
            "status": "Stat",
            "stocking": "Stck",
            "supplier": "Supl",
            "tax": "Tx",
            "total": "Tot",
            "transaction": "Tr",
            "version": "Vers",
            "year": "Yr",
        }
        # "identifier": "Id",

    def abbreviate(self, term, max_length=5):
        """
        Abbreviate a given term based on improved rules and track the rules applied.
        :param term: The term to abbreviate.
        :param max_length: Maximum allowed abbreviation length.
        :return: Generated abbreviation, rules applied, and reason if applicable.
        """
        rules_applied = []
        term_lower = term.lower()
        parts = term.split()  # Split the term into parts based on spaces
        abbreviated_parts = []
        max_length = max_length - 2 if len(term) <= max_length else max_length #if len(term) <= 8 else 6

        if term_lower in self.common_abbreviations:
            abbreviation = self.common_abbreviations[term_lower]
            rules_applied.append("a: Predefined abbreviation for common terms")
            return abbreviation, ", ".join(rules_applied)

        # Process each part of the term
        for part in parts:
            part_rules = []

            if part.lower() in self.common_abbreviations:
                # Rule a: Check predefined abbreviations for parts
                abbreviation = self.common_abbreviations[part.lower()]
                part_rules.append("a: Predefined abbreviation for common terms")
            else:
                # Rule b: Preserve critical consonants
                part = ''.join([ch for ch in part if ch.isalpha()])
                part_rules.append("b: Preserve critical consonants")
                
                # Rule c: Preserve the initial letter
                abbreviation = part[0]
                part_rules.append("c: Preserve the initial letter")

                # Rule d: Preserve the second letter if it is not vowel or term length > 6
                # if part[1] not in 'aeiou' or len(term) > max_length:
                if part[1] not in 'aeiou' or (part[1] not in 'iou' and len(term) > max_length):
                    abbreviation += part[1]
                    part_rules.append(f"d: Preserve the second letter if it is not in 'aeiou' or not in 'iou' for terms longer than {max_length}")

                # Rule e: Remove vowels after the third letter
                abbreviation += ''.join([ch for ch in part[2:] if ch not in 'aeiou'])
                part_rules.append("e: Remove vowels after the third letter")

                # Rule f: Truncate abbreviation to logical length
                abbreviation = abbreviation[:max_length]
                rules_applied.append(f"f: Truncate to max length {max_length}")

            # Add the rules applied for this part
            rules_applied.extend(part_rules)
            abbreviated_parts.append(abbreviation.capitalize())

        # Concatenate the abbreviated parts
        final_abbreviation = ''.join(abbreviated_parts)
        # Ensure abbreviation is unique
        if final_abbreviation in self.common_abbreviations.values():
            final_abbreviation = self._make_unique_abbreviation(final_abbreviation, term, max_length)

        return final_abbreviation, ", ".join(rules_applied)
    
    def register_abbreviation(self, term, abbreviation, max_length = 5):
        """
        Register a new abbreviation to self.common_abbreviations.
        :param term: The term to be abbreviated.
        :param abbreviation: The abbreviation to register.
        :param max_length: Maximum allowed abbreviation length.
        """
        term_lower = term.lower()
        if len(abbreviation) > max_length:
            raise ValueError("Abbreviation length must not exceed 5 characters.")
        if abbreviation in self.common_abbreviations.values():
            raise ValueError("Abbreviation already exists.")
        self.common_abbreviations[term_lower] = abbreviation

    def _make_unique_abbreviation(self, abbreviation, term, max_length=5):
        """
        Modify the abbreviation to make it unique by appending an unused consonant from the term.
        If no unique abbreviation can be generated, return the original term.
        :param abbreviation: The current abbreviation.
        :param term: The original term to extract available consonants.
        :param max_length: Maximum allowed abbreviation length.
        :return: A unique abbreviation or the original term.
        """
        all_consonants = 'bcdfghjklmnpqrstvwxyz'

        # Extract consonants from the original term in order of appearance
        term_consonants = [ch.lower() for ch in term if ch.lower() in all_consonants]

        # Track used consonants from the abbreviation
        used_consonants = [ch for ch in abbreviation.lower() if ch in term_consonants]

        # Determine remaining consonants in the term (preserving order)
        remaining_consonants = term_consonants[len(used_consonants):]

        # Try appending remaining consonants in order
        for consonant in remaining_consonants:
            new_abbreviation = abbreviation + consonant
            if new_abbreviation not in self.common_abbreviations.values():
                self.register_abbreviation(term, new_abbreviation, 1 + max_length)
                return new_abbreviation
            
        # Return the original term if no unique abbreviation can be generated
        return term

    def process_term(self, term):
        """
        Process a list of terms and validate against initial abbreviations.
        :param term: term to process.
        :return: Dictionary of term with their abbreviations and validation results.
        """
        generated_abbreviation, rules = self.abbreviate(term)
        processed_term = {
            "Term": term,
            "Generated Abbreviation": generated_abbreviation,
            "Applied Rules": rules,
        }
        return processed_term

abbreviation_generator = AbbreviationGenerator()


# IndexManager class to manage class and property indexing
class IndexManager:
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
            print(f"Warning: Duplicate suffix {current_suffix} for class {class_name}")
        self.previous_suffix[class_name] = current_suffix
        return current_suffix

    def int_to_custom_alpha(self, index):
        if index < 26:
            return self.base_map[index % 26]
        suffix = self.int_to_custom_alpha(index // 26 - 1) + self.extended_map[index % 62]
        return suffix

    def generate_indexed_code(self, item):
        if "_" not in item:
            # A new Class has been found
            self.current_suffix = self.get_suffix(item)
            modified = f"{item}{self.current_suffix}"
            self.last_base_class = item  # Update: Set new base class name
        else:
            # For property items, use the current Class suffix
            base, extension = item.split('_', 1)
            if base != self.last_base_class:
                # If it differs from the previous class, update the suffix
                self.current_suffix = self.get_suffix(base)
            modified = f"{base}{self.current_suffix}_{extension}"
        return modified

index_manager = IndexManager()


# Main function to execute the script
def main():
    global object_class_dict
    global LIFO_list
    global LHM_model
    global is_singular_association
    global sequence
    global selected_class
    global exception_class
    global DEBUG
    global TRACE
    global DNM

    # Create the parser
    parser = argparse.ArgumentParser(
        prog='AWI21926_Specialization.py',
        usage='%(prog)s BSM_file LHM_file -l BSM_file_extension -m LHM_file_extension -e encoding [options] ',
        description='Converts logical model to HMD with graph walk.'
    )
    parser.add_argument('BSM_file', metavar='BSM_file', type = str, help='Business semantic model file path')
    parser.add_argument('LHM_file', metavar='LHM_file', type = str, help='LHM file path')
    parser.add_argument('-l', '--BSM_file_extension', required = False, help='Business semantic model extension file path')
    parser.add_argument('-m', '--LHM_file_extension', required = False, help='LHM extension file path')
    parser.add_argument('-o', '--option', required = False, action='store_true')
    parser.add_argument('-e', '--encoding', required = False, default='utf-8-sig', help='File encoding, default is utf-8-sig')
    parser.add_argument('-t', '--trace', required = False, action='store_true')
    parser.add_argument('-d', '--debug', required = False, action='store_true')

    args = parser.parse_args()

    BSM_file = args.BSM_file.strip()
    BSM_file = BSM_file.replace('/', SEP)
    BSM_file = file_path(BSM_file)
    if not BSM_file or not os.path.isfile(BSM_file):
        print('No input Business semantic model file.')
        sys.exit()

    LHM_file = args.LHM_file.strip()
    LHM_file = LHM_file.replace('/', SEP)
    LHM_file = file_path(LHM_file)
    if 'IN_USE' == is_file_in_use(LHM_file):
        sys.exit()

    BSM_file_extension = None
    if args.BSM_file_extension:
        BSM_file_extension = args.BSM_file_extension.strip()
        BSM_file_extension = BSM_file_extension.replace('/', SEP)
        BSM_file_extension = file_path(BSM_file_extension)
        if not BSM_file_extension or not os.path.isfile(BSM_file_extension):
            print('Info: No input Business semantic model extension file.')

    LHM_file_extension = None
    if args.LHM_file_extension:
        LHM_file_extension = args.LHM_file_extension.strip()
        LHM_file_extension = LHM_file_extension.replace('/', SEP)
        LHM_file_extension = file_path(LHM_file_extension)
        if LHM_file_extension and (not BSM_file_extension or not os.path.isfile(BSM_file_extension)):
            print('No input Business semantic model extension file.')
            sys.exit()
        elif BSM_file_extension:
            print('Notice: Input Business semantic model extension file specified.')
        if 'IN_USE' == is_file_in_use(LHM_file_extension):
            sys.exit()

    if args.encoding:
        encoding = args.encoding.strip()
    else:
        encoding = 'utf-8-sig'

    TRACE = args.trace
    DEBUG = args.debug
    if args.option:
        DNM = True

    selected_class = set()
    exception_class = set()
    # read
    header =  ['sequence', 'level', 'property_type', 'identifier', 'class_term', 'property_term', 'representation_term', 'associated_class', 'multiplicity', 'definition', 'module', 'table', 'domain_name', 'element', 'label_local', 'definition_local', 'xpath', 'id']
    # ['sequence', 'level', 'property_type', 'identifier', 'class_term', 'property_term', 'multiplicity', 'representation_term', 'domain_name', 'associated_class', 'definition', 'module', 'table', 'id', 'label_local', 'definition_local', 'xpath']
    # write
    header2 = ['sequence', 'level', 'type', 'identifier', 'name', 'datatype', 'multiplicity', 'domain_name', 'definition', 'module', 'table', 'class_term', 'id', 'path', 'semantic_path', 'abbreviation_path', 'label_local', 'definition_local', 'element', 'xpath']
    with open(BSM_file, encoding = encoding, newline='') as f:
        reader = csv.DictReader(f, fieldnames = header)
        next(reader)
        business_segment_id = None
        for row in reader:
            record = {}
            for key in header:
                if key in row:
                    record[key] = row[key]
                else:
                    record[key] = ''
            class_term = update_class_term(record)
            property_type = row['property_type']
            associated_class = row['associated_class']
            if DEBUG:
                print(f"{class_term}({record['property_type']}) {record['associated_class'] or record['property_term']}")
            if class_term:
                if property_type in ['Composition']:#, 'Aggregation']:
                    if 'Base' != row['module']:
                        exception_class.add(associated_class)
                if 'General' != object_class_dict[class_term]['module']:
                    selected_class.add(class_term)

    LHM_model = []
    selected_class = object_class_dict.keys()

    sorted_classes = sorted(selected_class, key = lambda x: object_class_dict[x]['table'] if object_class_dict[x]['table'] else 0)
    if DNM:
        exception_class = [cls for cls in exception_class if not (cls.endswith(" Line") and cls.replace(" Line", "") in selected_class)]
    for class_term in sorted_classes:
        if class_term in exception_class:
            continue
        parse_class(class_term)

    hierarchy_records = model2record(LHM_model)

    records = update_name(hierarchy_records)

    out_records = [{k: v for k, v in d.items() if k in header2} for d in records]

    # Use Counter to count occurrences of each path id
    indexed_list = [x['path'].split('/')[-1] for x in out_records]
    count = Counter(indexed_list)
    # Find elements that are duplicated (those that appear more than once)
    duplicates = {item: count[item] for item in count if item and count[item] > 1}
    # Print the results
    print("Checking duplicated id and their counts:", duplicates)

    with open(LHM_file, 'w', encoding = encoding, newline='') as f:
        writer = csv.DictWriter(f, fieldnames = header2)
        writer.writeheader()
        writer.writerows(out_records)

    print(f'** END {LHM_file}')

    selected_class = set()
    exception_class = set()
    if BSM_file_extension:
        BSM_file_extension = file_path(BSM_file_extension)
        with open(BSM_file_extension, encoding = encoding, newline='') as f:
            reader = csv.DictReader(f, fieldnames = header)
            next(reader)
            for row in reader:
                record = {}
                for key in header:
                    if key in row:
                        record[key] = row[key]
                    else:
                        record[key] = ''
                class_term = update_class_term(record)
                if DEBUG:
                    print(f"{class_term}({record['property_type']}) {record['associated_class'] or record['property_term']}")
                if class_term:
                    if row['property_type'] in ['Composition', 'Aggregation']:
                        associated_class = object_class_dict[class_term]
                        if 'Base' != associated_class['module']:
                            exception_class.add(row['associated_class'])
                    if 'General' != object_class_dict[class_term]['module']:
                        selected_class.add(class_term)

        LHM_model = []
        sorted_classes = sorted(selected_class, key = lambda x: object_class_dict[x]['table'] if object_class_dict[x]['table'] else 0)
        if DNM:
            exception_class = [cls for cls in exception_class if not (cls.endswith(" Line") and cls.replace(" Line", "") in selected_class)]
        for class_term in sorted_classes:
            if class_term in exception_class:
                continue
            if DEBUG:
                print(f"- parse_class({class_term})")
            parse_class(class_term)

        hierarchy_records = model2record(LHM_model)

        records = update_name(hierarchy_records)

        out_records = [{k: v for k, v in d.items() if k in header2} for d in records]

        # Use Counter to count occurrences of each path id
        indexed_list = [x['path'].split('/')[-1] for x in out_records]
        count = Counter(indexed_list)
        # Find elements that are duplicated (those that appear more than once)
        duplicates = {item: count[item] for item in count if item and count[item] > 1}
        # Print the results
        print("Checking duplicated id and their counts:", duplicates)

        with open(LHM_file_extension, 'w', encoding = encoding, newline='') as f:
            writer = csv.DictWriter(f, fieldnames = header2)
            writer.writeheader()
            writer.writerows(out_records)

        print(f'** END {LHM_file_extension}')


if __name__ == '__main__':
    main()
