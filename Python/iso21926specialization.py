#!/usr/bin/env python3
# coding: utf-8
"""
awi21926specialization.py
Generates ADC Business Semantic Model (BSM) CSV file from Foundational Semantic Model (FSM) CSV file with Specialization

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2024-05-12

MIT License

(c) 2023, 2024 SAMBUICHI Nobuyuki (Sambuichi Professional Engineers Office)

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
These Python scripts are specifically designed for handling the ADS graph walk in two distinct steps, namely `awi21926specialization.py` and `awi21926graphwalk.py`.

This first program, `awi21926specialization.py`, has a primary focus on specialization and property extension within the Foundational Semantic Model (FSM), efficiently processing these aspects to generate a Business Semantic Model (BSM) suitable for further usage or analysis. Specialization allows adding, changing, or removing properties defined in the superclass. Removing a property involves defining its multiplicity as "0..0" or "0" for attributes or associations in the subclass.

Key Features:
1. Initial Setup:
   - Imports necessary modules and sets up debugging flags and file path separators.
   - Defines directories and filenames for both FSM and BSM CSV files.

2. Utility Functions:
   - parse_class(class_term, SP_ID=''): Function to parse class terms and handle specializations.
   - file_path(pathname): Creates full file paths from given pathnames, considering relative and absolute paths.
   - is_file_in_use(file_path): Checks if a file is currently in use.
   - getproperty_term(record): Forms a property term from the record, appending 'associated_class' if it exists.
   - populate_record(row, seq): Transforms a CSV row into a record, updating module and class identifiers accordingly.
   - check_csv_row(row): Validates the CSV row against mandatory and conditional checks.

3. Specialization Handling:
   - Read the Foundational Semantic Model (FSM) CSV and construct an object class dictionary with class terms and their properties.
   - Parse each class term, focusing on handling specializations with parse_class().
   - Process subclass properties and handle the hierarchy of properties and associations.

4. Business Semantic Model Generation and Output:
   - After processing the specialization and extensions, the script generates the Business Semantic Model (BSM).
   - The BSM is then written to a CSV file, capturing the updated class hierarchy and property details.

5. Debugging and Tracing:
   - Uses DEBUG and TRACE flags to print diagnostic messages, aiding in understanding the flow and for troubleshooting purposes.

Example Usage:
Python awi21926specialization.py AWI21926_FSM.csv AWI21926_BSM.csv -s JP_FSM.csv -l JP_BSM.csv

Where:
- The first parameter is the input FSM file.
- The second parameter is the output BSM file.
- `-s` option specifies the input extension FSM file.
- `-l` option specifies the output extension BSM file.

This script is tailored to handle complex relationships in the Foundational Semantic Model (FSM), focusing on class specialization and property extension. It efficiently processes these aspects to generate a Business Semantic Model (BSM) suitable for further usage or analysis.
"""

import os
import argparse
import sys
import csv
import re
import copy

# Set debug and trace flags, and file path separator
DEBUG = False
TRACE = True
SEP = os.sep

# Define CSV headers
header  = ['sequence', 'level', 'property_type', 'identifier', 'class_term', 'property_term', 'representation_term', 'associated_class', 'multiplicity', 'definition', 'module', 'table', 'domain_name']
header2 = ['sequence', 'level', 'property_type', 'identifier', 'class_term', 'property_term', 'multiplicity', 'representation_term', 'domain_name', 'associated_class', 'definition', 'module', 'table', 'id']

# Initialize dictionaries and lists
domain_dict = None
object_class_dict = None
specialized_class = set()
LIFO_list = []
BSM_list = []

# Define module dictionary for mapping module names to codes
module_dict = {
    'Unit Type Registry': 'UT',
    'Core': 'CO',
    'General': 'GE',
    'Base': 'BS',
    'GL': 'GL',
    'General Ledger': 'GL',
    'AP': 'AP',
    'Accounts Payable': 'AP',
    'Purchase': 'PR',
    'AR': 'AR',
    'Accounts Receivable': 'AR',
    'Sales': 'SL',
    'Inventory': 'IV',
    'PPE': 'PE',
    'Property Plant Equipment': 'PE'
}

module_dict['JP'] = 'JP'

module_num = {}

# Utility function to create full file paths
def file_path(pathname):
    if SEP == pathname[0:1]:
        return pathname
    else:
        pathname = pathname.replace('/', SEP)
        dir = os.path.dirname(__file__)
        new_path = os.path.join(dir, pathname)
        return new_path


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
                pass  # Creating the file
            result = 'CREATED'
            print(f"File {file_path} has been created.")
        except Exception as e:
            print(f"Error while creating file: {e}")
            result = 'ERROR_CREATING_FILE'
    return result


# Utility function to form a property term
def getproperty_term(record):
    if len(record['associated_class']) > 0:
        return f"{record['property_term']}.{record['associated_class']}"
    else:
        return record['property_term']


# Utility function to transform a CSV row into a record
def populate_record(row, seq):
    global current_module
    global current_class
    global class_num
    record = {}
    _type = row['property_type']
    class_term = row['class_term'].replace('  ', ' ').strip()
    module = row['module']
    if module in module_dict:
        module_id = module_dict[module]
    if current_class != class_term:
        if module_id not in module_num:
            module_num[module_id] = []
        if not class_term in module_num[module_id]:
            module_num[module_id].append(class_term)
        class_num = 1 + module_num[module_id].index(class_term)
    if 'Specialization' == _type:
        id = f"{module_id}{str(class_num).zfill(2)}_00"
    else:
        if _type.lower().endswith('class'):
            seq = 0
            id = f"{module_id}{str(class_num).zfill(2)}"
        else:
            id = f"{module_id}{str(class_num).zfill(2)}_{str(seq).zfill(2)}"
        seq += 1
    record['id'] = id
    record['sequence'] = row['sequence']
    record['identifier'] = row['identifier']
    record['module'] = row['module']
    if row['table'].isdigit():
        table = int(row['table'])
    else:
        table = 0
    record['table'] = int(table)
    record['property_type'] = _type
    if 'class' in _type.lower():
        record['level'] = 1
    else:
        record['level'] = 2
    record['class_term'] = class_term
    property_term = row['property_term']
    record['property_term'] = property_term and property_term.replace('  ', ' ').strip() or ''
    associated_class = row['associated_class']
    record['associated_class'] = associated_class and associated_class.replace('  ', ' ').strip() or ''
    record['representation_term'] = row['representation_term']
    definition = row['definition']
    record['definition'] = definition
    record['multiplicity'] = row['multiplicity']
    record['domain_name'] = row['domain_name']
    current_module = module
    current_class = class_term
    if DEBUG:
        if associated_class:
            print(f"{seq} module:{module} class_term:'{class_term}' id:{id} {_type} associated_class:'{associated_class}'")
        elif property_term:
            print(f"{seq} module:{module} class_term:'{class_term}' id:{id} property_term:'{property_term}'")
        else:
            print(f"{seq} module:{module} class_term:'{class_term}' id:{id}")
    return seq, record


# Function to parse class terms and handle specializations
def parse_class(class_term, SP_ID=''):
    if DEBUG: print(f"\nparse_class('{class_term}')")
    """
    Step 1: Copy a class to the logical data model and place it on the top of 
    the LIFO list.
    """
    if class_term not in object_class_dict:
        if DEBUG or TRACE: print(f"#### '{class_term}' not in object_class_dict")
        return
    object_class = object_class_dict[class_term]
    classID = object_class['id']
    _type = object_class['property_type']
    if SP_ID:
        LIFO_list[-1] += f".{class_term}"
        classID = f"{SP_ID[:4]}{classID}"
        if DEBUG or TRACE: print(f"  '{class_term}' type:'{_type}' SP_ID:{SP_ID}\t{LIFO_list}")
    else:
        LIFO_list.append(class_term)
        if DEBUG or TRACE: print(f"  '{class_term}' type:'{_type}'\t{LIFO_list}")
    level = len(LIFO_list)
    properties = object_class['properties']
    object_class_ = {k: v for k, v in object_class.items() if k != 'properties'} # drop 'properties' from dict
    if 'Abstract Class' == object_class_['property_type']:
        if '.' in LIFO_list[0]:
            object_class_['property_type'] = 'Specialized Class'
            current_class_term = LIFO_list[0]
            class_term_ = current_class_term[:current_class_term.index('.')]
            if class_term_ not in object_class_dict:
                object_class_ = None
                print(f"ERROR: {class_term_} is not defined.")
            else:
                current_class = object_class_dict[class_term_]
                object_class_['associated_class'] = object_class_['class_term']
                object_class_['class_term'] = current_class_term
                object_class_['id'] = f"{current_class['id']}_{object_class_['id']}"
                object_class_['module'] = current_class['module']
        else:
            pass
    if object_class_:
        # if 'Specialization' != object_class_['property_type']:
        if not SP_ID:
            BSM_list.append(object_class_)
    """
    A. Specialization. 
    if it at least one of its specializations contains information that will be in the
    message format or is on a path of associations toward a class that contains such 
    information, then choose the specialized class.
    """
    subClasses = [property for property in properties.values() if 'Specialization' == property['property_type'] and 1 == level]
    for property in subClasses:
        specialized_class.add(class_term)
        superclass_term = property['associated_class']
        if not superclass_term in LIFO_list:
            parse_class(superclass_term, classID)
    """
    B. Copy the class to the logical data model. 
    Copy all properties and associations to the logical data model. 
    Conventionally, properties not related to the associated object class should be placed 
    before them, but this is not a requirement.
    """
    for property in [property for property in properties.values() if 'Specialization' != property['property_type']]:# or level > 1]:
        _property = copy.deepcopy(property)
        if SP_ID:
            current_class_term = LIFO_list[0]
            _property['class_term'] = current_class_term
            current_class = object_class_dict[current_class_term[:current_class_term.index('.')]]
        else:
            current_class = object_class
        current_class_id = current_class['id']
        if current_class_id not in _property['id']:
            _property['id'] = f"{current_class_id}_{_property['id']}"
        _property['module'] = current_class['module']
        # BSM_list.append(_property)
        """
        1. Searches for elements in BSM_list where:
            "class_term" start with _property["class_term"]
            "property_term" is _property["property_term"]
        2. If a match is found and its "multiplicity" is "0", the element is removed.
        3. If the "multiplicity" is not "0", the matching element is replaced with _property.
        4. If no matching element is found, the script adds _property to BSM_list.
        """
        # Check if there are any matching elements
        match_index = None
        for index, element in enumerate(BSM_list):
            if (
                element["property_type"] == _property["property_type"]
                and element["class_term"].startswith(_property["class_term"])
                and (
                    (
                        "Attribute" == _property["property_type"]
                        and element["property_term"] == _property["property_term"]
                    )
                    or (
                        _property["property_type"] in ["Reference Association", "Composition", "Aggregation"]
                        and element["property_term"] == _property["property_term"]
                        and element["associated_class"] == _property["associated_class"]
                    )
                )
            ):
                match_index = index
                break
        if match_index is not None:
            # If match found, check the multiplicity
            if "0" == _property["multiplicity"]:
                # Remove element if multiplicity is "0"
                del BSM_list[match_index]
            else:
                # Replace element with _property
                BSM_list[match_index] = _property
        else:
            # If no match is found, add _property
            if "0" != _property["multiplicity"]:
                BSM_list.append(_property)

        if DEBUG:
            print(f"  {_property['class_term']} | {_property['property_type']}: {_property['property_term']}.{_property['associated_class']}")
    if DEBUG: print(f"-- Done {LIFO_list[-1]}")
    if SP_ID:
        if DEBUG: print(f"Specialised Class: {class_term} type is '{_type}'\t{LIFO_list}")
    else:
        LIFO_list.pop(-1)
        if DEBUG: print(f"POP LIFO_list: '{class_term} type is '{_type}'\t{LIFO_list}")


# Function to check the validity of CSV rows
def check_csv_row(row):
    """
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
        if not multiplicity or multiplicity not in ['1', '1..1', '1..*', '0..1', '0..*', '0']:
            return status, f"Multiplicity '{multiplicity}' is WRONG."
    # Check for mandatory fields
    for field in ['module', 'property_type', 'class_term']:
        if not row.get(field):
            return status, f"Missing mandatory field '{field}'."
    # Conditional checks based on 'property_type'
    if 'Class' in property_type:
        for field in ['property_term', 'representation_term', 'associated_class']:
            if row.get(field):
                return status, f"Field '{field}' must be empty for type {property_type}."
    elif 'Attribute' in property_type:
        if '0' != multiplicity:
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


# Main function to execute the script
def main():
    global domain_dict
    global object_class_dict
    global specialized_class
    global LIFO_list
    global BSM_list
    global current_module
    global current_class
    global DEBUG
    global TRACE

    # Create the parser
    parser = argparse.ArgumentParser(
        prog='AWI21926_Specialization.py',
        usage='%(prog)s FSM_file BSM_file -s FSM_file_extension -l BSM_file_extension -e encoding [options] ',
        description='Converts Foundational Semantic Model (FSM) to Business Semantic Model (BSM) with specialization.'
    )
    parser.add_argument('FSM_file', metavar='FSM_file', type = str, help='Foundational Foundational Semantic Model (FSM) file path')
    parser.add_argument('BSM_file', metavar='BSM_file', type = str, help='Business Semantic Model (BSM) file path')
    parser.add_argument('-s', '--FSM_file_extension', required = False, help='Foundational Foundational Semantic Model (FSM) extension file path')
    parser.add_argument('-l', '--BSM_file_extension', required = False, help='Business Semantic Model (BSM) extension file path')
    parser.add_argument('-e', '--encoding', required = False, default='utf-8-sig', help='File encoding, default is utf-8-sig')
    parser.add_argument('-t', '--trace', required = False, action='store_true')
    parser.add_argument('-d', '--debug', required = False, action='store_true')

    args = parser.parse_args()

    FSM_file = args.FSM_file.strip()
    FSM_file = FSM_file.replace('/', SEP)
    FSM_file = file_path(FSM_file)
    if not FSM_file or not os.path.isfile(FSM_file):
        print('No input Semantic file.')
        sys.exit()

    BSM_file = args.BSM_file.strip()
    BSM_file = BSM_file.replace('/', SEP)
    BSM_file = file_path(BSM_file)
    if 'IN_USE' == is_file_in_use(BSM_file):
        sys.exit()

    FSM_file_extension = None
    if args.FSM_file_extension:
        FSM_file_extension = args.FSM_file_extension.strip()
        FSM_file_extension = FSM_file_extension.replace('/', SEP)
        FSM_file_extension = file_path(FSM_file_extension)
        if not FSM_file_extension or not os.path.isfile(FSM_file_extension):
            print('Info: No input Semantic extension file.')

    BSM_file_extension = None
    if args.BSM_file_extension:
        BSM_file_extension = args.BSM_file_extension.strip()
        BSM_file_extension = BSM_file_extension.replace('/', SEP)
        BSM_file_extension = file_path(BSM_file_extension)
        if BSM_file_extension and (not FSM_file_extension or not os.path.isfile(FSM_file_extension)):
            print('No input Semantic extension file.')
            sys.exit()
        elif FSM_file_extension:
            print('NOTICE: Input Semantic extension file exists')
        if 'IN_USE' == is_file_in_use(BSM_file_extension):
            sys.exit()

    encoding = args.encoding.strip()
    TRACE = args.trace
    DEBUG = args.debug

    object_class_dict = {}
    with open(FSM_file, encoding = encoding, newline='') as f:
        reader = csv.DictReader(f, fieldnames = header)
        h = next(reader)
        current_module = ''
        current_class = ''
        seq = 0
        for row_number, row in enumerate(reader, start=1):
            if '' == row['module']:
                continue
            record = {}
            for key in header:
                if key in row:
                    record[key] = row[key]
                else:
                    record[key] = ''

            status, result = check_csv_row(row)
            if result != "Row is valid.":
                print(f"** ERROR Row {row_number}: {result} {row}")
                break

            seq, record = populate_record(record, seq)

            _type = record['property_type'].strip()
            class_term = record['class_term'].strip()
            property_term = getproperty_term(record)
            if _type in ['Abstract Class', 'Class']:
                # if DEBUG: print(class_term)
                if not class_term in object_class_dict:
                    object_class_dict[class_term] = record
                    object_class_dict[class_term]['properties'] = {}
            else:
                if not class_term in object_class_dict:
                    print(f"** ERROR NOT REGISTERED {class_term} in object_class_dict\n{record}")
                property_term = getproperty_term(record)
                multiplicity = record['multiplicity']
                if multiplicity in ['0..0', '0']:
                    if property_term in object_class_dict[class_term]['properties'].keys():
                        del object_class_dict[class_term]['properties'][property_term]
                    else:
                        object_class_dict[class_term]['properties'][property_term] = record
                else:
                    object_class_dict[class_term]['properties'][property_term] = record

    BSM_list = []
    selected_classes = object_class_dict.keys()
    sorted_classes = sorted(selected_classes, key = lambda x: object_class_dict[x]['table'] if object_class_dict[x]['table'] else 0)
    for class_term in sorted_classes:
        parse_class(class_term)

    records = [{k: v for k, v in d.items() if k in header2} for d in BSM_list]

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

    BSM_file = file_path(BSM_file)
    with open(BSM_file, 'w', encoding = encoding, newline='') as f:
        writer = csv.DictWriter(f, fieldnames = header2)
        writer.writeheader()
        writer.writerows(out_records)

    print(f'-- END {BSM_file}')

    selected_class = []
    if FSM_file_extension:
        FSM_file_extension = file_path(FSM_file_extension)
        with open(FSM_file_extension, encoding = encoding, newline='') as f:
            reader = csv.DictReader(f, fieldnames = header)
            next(reader)
            current_module = ''
            current_class = ''
            current_class_id = ''
            seq = 0
            for row in reader:
                if '' == row['module']:
                    continue
                record = {}
                for key in header:
                    if key in row:
                        record[key] = row[key]
                    else:
                        record[key] = ''

                status, result = check_csv_row(row)
                if result != "Row is valid.":
                    print(f"** ERROR Row {row_number}: {result} {row}")
                    break

                seq, record = populate_record(row, seq)

                module = record['module'].strip()
                id = record['id'].strip()
                _type = record['property_type'].strip()
                class_term = record['class_term'].strip()
                if _type in ['Abstract Class', 'Class']:
                    if not class_term in object_class_dict:
                        selected_class.append(class_term)
                        object_class_dict[class_term] = record
                        object_class_dict[class_term]['properties'] = {}
                        current_module = module
                        current_class = class_term
                        current_class_id = record['id'].strip()
                else:
                    if 'Specialization' == _type:
                        superclass_term = record['associated_class']
                        if superclass_term not in object_class_dict:
                            print(f"ERROR: {superclass_term} is not defined.")
                            continue
                        super_class = object_class_dict[superclass_term]
                        record['id'] = f"{current_class_id}_{record['id'][1 + record['id'].rindex('_'):]}"
                        _class_term = f"{class_term}.{superclass_term}"
                        record['class_term'] = _class_term
                        _properties = copy.deepcopy(super_class['properties'])
                        for _property_term, _property in _properties.items():
                            _propertyID = _property['id']
                            _property['id'] = f"{current_class_id}_{_propertyID}"
                            _property['module'] = current_module
                            _property['class_term'] = _class_term
                            object_class_dict[class_term]['properties'][_property_term] = _property
                    else:
                        _class_term = f"{class_term}"
                        record['class_term'] = _class_term
                        property_term = getproperty_term(record)
                        multiplicity = record['multiplicity']
                        if multiplicity in ['0..0', '0']:
                            if property_term in object_class_dict[class_term]['properties'].keys():
                                del object_class_dict[class_term]['properties'][property_term]
                            else:
                                object_class_dict[class_term]['properties'][property_term] = record
                        else:
                            object_class_dict[class_term]['properties'][property_term] = record

        BSM_list = []
        selected_classes = object_class_dict.keys()
        sorted_classes = sorted(selected_classes, key = lambda x: object_class_dict[x]['table'] if object_class_dict[x]['table'] else 0)
        for class_term in sorted_classes:
            parse_class(class_term)

        records = [{k: v for k, v in d.items() if k != 'properties'} for d in BSM_list] # drop 'properties' from dict

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

        BSM_file_extension = file_path(BSM_file_extension)
        with open(BSM_file_extension, 'w', encoding = encoding, newline='') as f:
            writer = csv.DictWriter(f, fieldnames = header2)
            writer.writeheader()
            writer.writerows(out_records)

        print(f'** END {BSM_file_extension}')


if __name__ == '__main__':
    main()
