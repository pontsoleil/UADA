#!/usr/bin/env python3
# coding: utf-8
"""
sme_graphwalk.py
Generates ADC Logical Hierarchical (LHM)  Model from Business Semantic Model (BSM) CSV with Graph Walk

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-01-17
Last Modified: 2025-05-20

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

This script specializes in constructing a hierarchical representation of the BSM, adhering to standards. It efficiently manages the complexities of class hierarchies, associations, and specializations to produce a structured Hierarchical Message Definition (HMD).
"""

import os
import sys
import argparse
import csv
import copy
import re
from collections import OrderedDict, Counter

from common.utils import (
    LC3,
    titleCase,
    SC, # snake concatenate
    file_path,
    is_file_in_use,
    split_camel_case,
    abbreviate_term,
    normalize_text
)

class Graphwalk:
    def __init__ (
            self,
            bsm_file,
            lhm_file,
            root_terms,
            level_num,
            remove_chars,
            option,
            encoding,
            trace,
            debug
        ):

        self.bsm_file = bsm_file.replace('/', os.sep)
        self.bsm_file = file_path(self.bsm_file)
        if not self.bsm_file or not os.path.isfile(self.bsm_file):
            print(f'[INFO] No input Semantic file {self.bsm_file}.')
            sys.exit()

        self.lhm_file = lhm_file.replace('/', os.sep)
        self.lhm_file = file_path(self.lhm_file)
        if 'IN_USE' == is_file_in_use(self.lhm_file):
            print(f'[INFO] Semantic file {self.lhm_file} is in use.')
            sys.exit()

        self.LEVEL_NUM = level_num
        self.REMOVE_CHARS = remove_chars
        self.encoding = encoding.strip() if encoding else 'utf-8-sig'

        # Set debug and trace flags, and file path separator
        self.root_terms = root_terms
        self.DNM = False
        self.SME_COMMON = False

        if option:
            if "D"==option.strip().upper():
                self.DNM = True
            elif "S"==option.strip().upper():
                self.SME_COMMON = True

        self.TRACE = trace
        self.DEBUG = debug

        self.base_dir = "SME_Common"

        # Initialize dictionaries and lists
        self.object_class_dict = {}
        self.LIFO_list = []
        self.LHM_model = []
        self.is_singular_association = False
        self.selected_class = None
        self.sequence = 1
        self.elementnames = set()
        self.class_id_map = {}

        self.current_multiplicity = None
        self.current_label = None
        self.current_definition = None
        self.levels = [None] * self.LEVEL_NUM

    def debug_print(self, text):
        if self.DEBUG:
            print(text)

    def trace_print(self, text):
        if self.TRACE or self.DEBUG:
            print(text)

    def normalize_text(self, text):
        if not text:
            return ""
        # Replace "-", ".", and "_" with a space
        replaced = text.translate(str.maketrans('', '', self.REMOVE_CHARS))
        # Replace multiple spaces with a single space and trim leading/trailing spaces
        normalized = re.sub(r'\s+', " ", replaced).strip()
        return normalized

    # def normalize_text(self, text):
    #     # remove_words = "(CIILB_|CIIL_|CIIH_|CI_|Applicable|Defined|Specified|Supply Chain|Additional|Including|Included|Processing|Details)"
    #     remove_chars = " ._"
    #     # _text = re.sub(remove_words, "", text).translate(
    #     #     str.maketrans("", "", remove_chars)
    #     # )
    #     _text = text.translate(
    #         str.maketrans("", "", remove_chars)
    #     )
    #     if _text.endswith("IdentificationIdentifier"):
    #         _text = _text.replace("IdentificationIdentifier", "ID")
    #     elif _text.endswith("IdentificationID"):
    #         _text = _text.replace("IdentificationID", "ID")        
    #     elif _text.endswith("Identifier"):
    #         _text = _text.replace("Identifier", "ID")
    #     elif _text.endswith("NameText"):
    #         _text = _text.replace("NameText", "Name")
    #     return _text

    def element_from_class(self, class_term):
        return self.normalize_text(class_term)

    def element_from_property(self, property):
        return self.normalize_text(property)

    # Utility function to update class term
    def update_class_term(self, row):
        # if "id" not in row or not row["id"]:
        #     return None
        property_type = row["property_type"]
        class_term = row['class_term']
        if "." in class_term:
            class_term = class_term[:class_term.index(".")]
            row["class_term"] = class_term
        property_term = row['property_term']
        associated_class = row['associated_class']
        if property_term:
            row["property_term"] = property_term
        if associated_class:
            row["associated_class"] = associated_class
        if property_type in ['Class','Specialized Class']:
            if not class_term in self.object_class_dict:
                self.object_class_dict[class_term] = row
        else:
            if "properties" not in self.object_class_dict[class_term]: #not class_term in self.object_class_dict:
                self.object_class_dict[class_term]['properties'] = []
            self.object_class_dict[class_term]['properties'].append(row)
        return class_term, property_term, associated_class

    # Function to transform hierarchical model to records suitable for CSV output
    def model2record(self):
        hierarchy_records = []
        for data in self.LHM_model:
            record = {
                "property_type": data["property_type"],
                "class_term": data['class_term'],
                "representation_term": data['representation_term'],
                "property_term": data['property_term'],
                "definition": data["definition"],
                "DEN": data["DEN"]
            }
            for key in self.header2:
                if key in data:
                    record[key] = data[key]
            _type = record["type"]
            label = den = record["DEN"]
            representation = record["representation_term"]
            if "C"==_type:
                if den.endswith(". Details"):
                    label = den[:den.rindex(".")]
            elif "A"==_type:
                label = den[2+den.index("."):den.rindex(".")]
                if "Identification"==label and "Identifier"==representation:
                    label = "ID"
                    record["identifier"] = "PK"
                elif "Identification" in label:
                    label = label.replace("_ Identification", " ID")
            record["label"] = label
            hierarchy_records.append(record)
        return hierarchy_records

    # Function to update the name field in the hierarchical records
    def update_name(self, hierarchy_records):
        records = []
        parent_class = [''] * self.LEVEL_NUM
        for record in hierarchy_records:
            property_type = record['property_type']
            class_term = record['class_term']
            representation_term = record['representation_term']
            property_term = record['property_term']
            name = ''
            data_type = ''
            if 'Class' == property_type:
                name = class_term.split("-")[-1]
            elif 'Attribute' == property_type:
                representation_map = {
                    "Identifier": "ID"
                }
                # Default to using the representation_term as data_type
                data_type = representation_map.get(representation_term, representation_term)
                # Construct the name
                name = f"{property_term} {data_type}"
                # Replace suffixes for specific cases
                if name.endswith("Identification ID"):
                    name = name.replace("Identification ID", "ID")
                elif name.endswith("Text"):
                    name = name.replace("Text", "")
            elif 'Reference Association' == property_type:
                record['identifier'] = ''
                name = class_term
            else:
                continue
            if "_" in name:
                name = f'{name[:name.index("_")]} {name[1 + name.index("_"):]}'
            record["label"] = name

            records.append(record)
        return records

    # Function to parse class terms and handle specializations
    def parse_class(self, class_term, REFERENCE_OF = False):
        """
        Step 1: Copy a class to the Hierarchical Message Definition and place it on the top of
        the LIFO list.
        """
        _class_term = class_term
        if "|" in _class_term: # romove originating class name for this associated class
            _class_term = class_term[1 + class_term.index("|"):]
            class_qualifier = class_term[:class_term.index("|")]
        else:
            class_qualifier = ""
        if _class_term not in self.object_class_dict:
            print(f"[ERROR] '{_class_term}' not in object_class_dict")
            return

        object_class = copy.deepcopy(self.object_class_dict[_class_term])
        if self.current_label:
            object_class["label"] = self.current_label
        if self.current_definition:
            object_class["definition_local"] = self.current_definition

        if REFERENCE_OF:
            object_class['property_type'] = 'Reference Association'

        _type = object_class['property_type']
        self.trace_print(f"{_type in ['Subclass','Specialized Class'] and '-' or ' '} {_type}: parse_class('{class_term}') check  '{_class_term}'{'['+self.current_multiplicity+']' if self.current_multiplicity else ''}\t{self.LIFO_list}")
        """
        A. Copy the class to the hierarchical logical data model.
        Copy all properties and associations to the hierarchical logical data model.
        Conventionally, properties not related to the associated object class should be placed
        before them, but this is not a requirement.

        B. Place the selected class on the top of the LIFO list if not Reference Association.
        """
        if REFERENCE_OF:
            level = 1 + len(self.LIFO_list)
        else:
            self.LIFO_list.append(class_term)
            level = len(self.LIFO_list)
        self.debug_print(f'  Update LIFO_list {self.LIFO_list}')
        object_class['level'] = level
        if level > 1:
            LIFO_term = "-".join(self.LIFO_list)
            object_class['class_term'] = LIFO_term
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
            object_class['class_term'] += f"-{class_term}"
            self.debug_print(f"class_term:{class_term} _class_term:{_class_term} object_class['class_term']:{object_class['class_term']}")
            definition = object_class['definition']
            definition = definition.replace('A class', f"The reference association to the {class_term.replace('_', ' ')} class, which is a class")
            object_class['definition'] = definition
            object_class['type'] = 'R'
            properties_list = []
            for key in self.object_class_dict:
                if key.startswith(_class_term):
                    properties = self.object_class_dict[_class_term].get('properties', [])
                    for prop in properties:
                        properties_list.append(prop)
            for prop in properties_list:
                object_class['properties'][key] = prop
            hasPK = any(property.get('identifier', '') == 'PK' for property in properties_list)
            if "-" not in object_class['class_term'] and not hasPK:
                print(f"[ERROR] Referenced class {object_class['class_term']} has no PK(primary Key).")
            else:
                pass
        else:
            object_class['type'] = 'C'
        if level > 1 and self.current_multiplicity:
            object_class['multiplicity'] = self.current_multiplicity
        
        den = object_class["DEN"]
        parts = [x.strip() for x in den.split(".")]
        _class_term = parts[0]
        object_class["DEN"] = object_class["class_term"] = object_class["label"] = _class_term
        if class_qualifier:
            _class_term = object_class["DEN"] = object_class["class_term"] = object_class["label"] = f'{class_qualifier}_ {_class_term}'

        self.LHM_model.append(object_class)

        self.debug_print(f"  {level} Class:'{object_class['class_term']}'")
        properties = copy.deepcopy(object_class['properties'])
        sorted_properties = sorted(
            properties,
            key=lambda p: (
                0 if p["property_term"] == "Identification" and p["representation_term"] == "Identifier"
                else 1 if p["property_type"] == "Attribute"
                else 2
            )
        )
        level += 1
        for property_ in sorted_properties:
            property = property_.copy()
            if not id:
                pass
            if _class_term!= property["class_term"]:
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
                if 'Active' in  property['property_term']:
                    # Skip 'xxActive' attribute, which indicates that the master record is active and not usable for LHM.
                    continue
                property['level'] = level
                property['type'] = 'A'
                LIFO_term = "-".join(self.LIFO_list)
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

                        self.LHM_model.append(property)

                        self.debug_print(f"  {level} {property['property_type']} {property['identifier']} [{property['multiplicity']}] {property['property_term']}{property['associated_class']}")
                elif property['property_type'] in ['Attribute(PK)','Attribute']:
                    den = property["DEN"]
                    parts = [x.strip() for x in den.split(".")]
                    property["label"] = parts[1]
                    if class_qualifier:
                        if class_qualifier not in _class_term:
                            class_term_ = property["class_term"] =f'{class_qualifier}_ {_class_term}'
                        else:
                            class_term_ = _class_term
                        den = property["DEN"]                        
                        property["DEN"] = f'{class_term_}. {den[2+den.index("."):]}'
                        if den.endswith("Identification. Identifier"):
                            property["label"] = f'{den[2+den.index("."):-26]}ID'

                    self.LHM_model.append(property)

                    self.debug_print(f"  {level} {property['property_type']} [{property['multiplicity']}] {property['property_term']}{property['associated_class']}")

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
        def traverse_associated_class(_class):
            class_term = _class["class_term"]
            property_type = _class['property_type']
            property_term = _class['property_term']
            associated_class = _class['associated_class']
            if self.DNM and associated_class in f"{class_term} Line":
                return
            self.current_label = None
            self.current_definition = None
            if associated_class:
                if property_term:
                    selectedclass_term = f"{property_term}|{associated_class}"
                else:
                    selectedclass_term = associated_class
                if self.SME_COMMON:
                    self.current_label = _class["label"]
                    self.current_definition = _class["definition_local"]
            else:
                print(f"[ERROR] {level} {property_type}[{self.current_multiplicity}] {class_term} {property_term} has no associated class")
            self.current_multiplicity = None
            if selectedclass_term and selectedclass_term not in self.LIFO_list:
                current_multiplicity = _class['multiplicity']
                self.current_multiplicity = current_multiplicity if current_multiplicity and '-'!=current_multiplicity else None
                self.debug_print(f"  {level} {property_type}[{self.current_multiplicity}] {selectedclass_term}")

                self.parse_class(selectedclass_term, 'Reference Association'==property_type and _class['class_term'] or None)

        if not self.SME_COMMON:
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
            for _class in mandate_classes:
                traverse_associated_class(_class)
            """
            C. Singular.
            Pick any navigable association that is (0,1) and leads to needed information.
            """
            for _class in singular_classes:
                traverse_associated_class(_class)
            """
            E. Other Plural.
            Pick any navigable association that leads to needed information.
            """
            for _class in other_classes:
                traverse_associated_class(_class)
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
            classes = [
                cls
                for cls in properties
                if cls["property_type"]
                in ["Reference Association", "Aggregation", "Composition"]
            ]
            for _class in classes:
                traverse_associated_class(_class)

        self.debug_print(f"-- Done: {self.LIFO_list[-1]}\n")
        self.LIFO_list.pop(-1)
        self.debug_print(f"POP LIFO_list: {class_term} type is '{_type}'\t{self.LIFO_list}")

    def graph_walk(self):
        """
        change, unid, acronym, DEN, Definition, Working_comments_and_instructions, Publication_comments, Object_Class_Term_Qualifier(s), Object_Class_Term, Property_Term_Qualifier(s), Property_Term, Datatype_Qualifier(s), Representation_Term, Qualified_Data_Type_UID, Associated_Object_Class_Term_Qualifier(s), Associated_Object_Class, Business_Term(s), Usage_Rule(s), Sequence_Number, Occurrence_Min, Occurrence_Max, Business_Process_Value, Business_Process_Meaning, Business_Process_Class.Schema, Product_Value, Product_Meaning, Product_Class.Schema, Industory_Value, Industory_Meaning, Industory_Class.Schema, Region_(Geo)_Value, Region_(Geo)_Meaning, Region_(Geo)_Class.Schema, Official_Constraints_Value, Official_Constraints_Meaning, Official_Constraints_Class.Schema, Role_Value, Role_Meaning, Role_Class.Schema, Supporting_Role_Value, Supporting_Role_Meaning, Supporting_Role_Class.Schema, System_Constraints_Value, System_Constraints_Meaning, System_Constraints_Class.Schema, "Facets To_restrict_the_set_of_values_of_Content_Component_or_Supplementary_Components", au, av, aw, ax, ay, az, ba, bb, bc, bd, be, bf, bg, bh, Example(s), BIE/CC/DT_Version, Ref_Library_Version, Submitter_Name, Ref_Component_UN_ID, Ref_CR_ID, Unique_submitter_ID, CR_Status_Date, CR_Status, Library_Maintenance_Comment, TDED, Submitted_Definition, Submitter_Comment, Submitted_DEN, Submission_Row_Number, Unique_CC/BIE_ID, CR_Storage_Date, Publication_Refs_--_Source, Persistent_Flag, cb, cc, Short_Name, ce
        """
        mbie_file = os.path.join(self.base_dir,"CCL 24A_21SEP24_MBIE.csv")
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
                    element = self.element_from_property(f'{property_term}. {row["Representation_Term"]}')
                elif "ASBIE"==acronym:
                    property_type = "Composition"
                    element = self.element_from_property(f'{property_term}. {associated_class}')
                else:
                    property_type = "Class"
                    element = self.element_from_class(class_term)
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
                self.mbie_dict[den] = {
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


            # read CSV file
            self.header = [
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

            # write CSV file
            self.header2 = [
                "version",
                "sequence",
                "level",
                "type",
                "identifier",
                "label",
                "representation_term",
                "multiplicity",
                "definition",
                "acronym",
                "DEN"
            ]

            with open(self.bsm_file, encoding = self.encoding, newline='') as f:
                reader = csv.DictReader(f, fieldnames = self.header)
                next(reader)
                for row in reader:
                    if "END"==row["level"]:
                        break
                    record = {}
                    # id = row["id"]
                    for key in self.header:
                        if key in row:
                            record[key] = row[key]
                        else:
                            record[key] = ''
                    result = self.update_class_term(record)
                    if result is not None:
                        class_term, property_term, associated_class = result
                    else:
                        # Handle the case where the function returns None
                        print(f"Error: update_class_term returned None for record {record}")

                    self.debug_print(f"{id}\t{record['property_type']}\t'{class_term}'\t'{property_term or 'n/a'}'\t'{associated_class or 'n/a'}'")

            self.LHM_model = []
            self.selected_class = self.object_class_dict.keys()

            root_found = False
            for root_term in self.root_terms:
                if root_term in self.selected_class:
                    root_found = True
                    self.debug_print(f"- root_term parse_class('{root_term}')")
                    self.parse_class(root_term)

            if not root_found:
                for class_term in self.selected_class:
                    self.debug_print(f"- parse_class({class_term})")
                    self.parse_class(class_term)

            hierarchy_records = self.model2record()

            out_records = [{k: v for k, v in d.items() if k in self.header2} for d in hierarchy_records]
            with open(self.lhm_file, 'w', encoding = self.encoding, newline='') as f:
                writer = csv.DictWriter(f, fieldnames = self.header2)
                writer.writeheader()
                writer.writerows(out_records)

            print(f'** END {self.lhm_file}')

# Main function to execute the script
def main():
    # Create the parser
    parser = argparse.ArgumentParser(
        prog='sme_graphwalk.py',
        usage='%(prog)s BSM_file LHM_file -r Root class term -e encoding [options] ',
        description='Converts logical model to HMD with graph walk.'
    )
    parser.add_argument('BSM_file', metavar='BSM_file', type = str, help='Business semantic model file path')
    parser.add_argument('LHM_file', metavar='LHM_file', type = str, help='LHM file path')
    parser.add_argument("-r", "--root", action="append", help="Root class term for LHM to process. Can be specified multiple times.")
    parser.add_argument('-o', '--option', required = False, help="Enable Dual Navigation Mode (DNM) or Sequensial copying (C)")
    parser.add_argument('-e', '--encoding', required = False, default='utf-8-sig', help='File encoding, default is utf-8-sig')
    parser.add_argument('-t', '--trace', required = False, action='store_true')
    parser.add_argument('-d', '--debug', required = False, action='store_true')

    args = parser.parse_args()

    LEVEL_NUM = 20
    REMOVE_CHARS = "-._"

    def normalize_text(text):
        # Replace "-", ".", and "_" with a space
        replaced = text.translate(str.maketrans('', '', REMOVE_CHARS))
        # Replace multiple spaces with a single space and trim leading/trailing spaces
        normalized = re.sub(r'\s+', " ", replaced).strip()
        return normalized

    root_terms = []
    if args.root:
        for val in args.root:
            if isinstance(val, str) and "+" in val:
                root_terms.extend(val.split("+"))
            else:
                root_terms.append(val)
    root_terms = [x for x in root_terms]

    processor = Graphwalk(
        bsm_file = args.BSM_file.strip(),
        lhm_file = args.LHM_file.strip(),
        root_terms = root_terms,
        level_num = LEVEL_NUM,
        remove_chars = REMOVE_CHARS,
        option = args.option if args.option else None,
        encoding = args.encoding.strip() if args.encoding else None,
        trace = args.trace,
        debug = args.debug
    )

    processor.graph_walk()

if __name__ == '__main__':
    main()
