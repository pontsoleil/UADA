#!/usr/bin/env python3
# coding: utf-8
"""
generate Audit Data Collection xbrl-gl Taxonomy fron HMD CSV file and header files

designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-04-03

MIT License

(c) 2025 SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

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
import argparse
import os
import sys
import csv
import json
import re

DEBUG = False
TRACE = True
SEP = os.sep

duplicateNames = set()
names = set()
dimensionDict = {}
targetRefDict = {}
associationDict = {}
referenceDict = {}
sourceRefDict = {}
locsDefined = {}
arcsDefined = {}
locsDefined = {}
alias = {}
targets = {}
roleMap = None
primaryKeys = set()


def debug_print(text):
    if DEBUG:
        print(text)


def trace_print(text):
    if TRACE:
        print(text)


def file_path(pathname):
    if SEP == pathname[0:1]:
        file_path = pathname
    else:
        pathname = pathname.replace("/", SEP)
        dir = os.path.dirname(__file__)
        new_path = os.path.join(dir, pathname)
        file_path = new_path
    # Extract directory path from file path
    directory = os.path.dirname(file_path)
    # Create the directory if it doesn't exist
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        trace_print(f"Created directory: {directory}")
    return file_path


# lower camel case concatenate
def LC3(term):
    if not term:
        return ""
    terms = term.split(" ")
    name = ""
    for i in range(len(terms)):
        if i == 0:
            if "TAX" == terms[i]:
                name += terms[i].lower()
            elif len(terms[i]) > 0:
                name += terms[i][0].lower() + terms[i][1:]
        else:
            name += terms[i][0].upper() + terms[i][1:]
    return name


def titleCase(text):
    text = text.replace("ID", "Identification Identifier")
    # Example Camel case string
    camel_case_str = text  # "exampleCamelCaseString"
    # Use regular expression to split the string at each capital letter
    split_str = re.findall("[A-Z][a-z]*[_]?", camel_case_str)
    # Join the split string with a space and capitalize each word
    title_case_str = " ".join([x.capitalize() for x in split_str])
    title_case_str = title_case_str.replace("Identification Identifier", "ID")
    return title_case_str


# snake concatenate
def SC(term):
    if not term:
        return ""
    terms = term.split(" ")
    name = "_".join(terms)
    return name


def getRecord(element_id):
    if "$." in element_id:
        record = next((x for x in records if element_id == x["semPath"]), None)
        if not record:
            record = next((x for x in records if x["semPath"].endswith(element_id)), None)
    else:
        record = next((x for x in records if element_id == x["abbrevPath"]), None)
        if not record:
            record = next((x for x in records if x["abbrevPath"].endswith(element_id)), None)
        if not record:
            record = next((x for x in records if x["element_id"]==element_id), None)
    return record


def getParent(element_id):
    if element_id in dimensionDict:
        parent = dimensionDict[element_id]
    else:
        parent = None
    return parent


def getChildren(element_id):
    record = getRecord(element_id)
    if record:
        return record["children"]
    return []


def getElementID(cor_id):
    record = getRecord(cor_id)
    if record:
        return record["element_id"]
    return None


def domainMember(children, primary_id):
    global count
    lines = []
    for _child_element_id in children: # children are abbrebiated name list
        child = getRecord(_child_element_id)
        child_element_id = child['element_id']
        child_type = child["type"]
        child_name = child["name"]
        taxonomy_schema, link_id, href = roleRecord(child_element_id)
        if "C" == child_type:
            target_name = child_element_id[1+child_element_id.index('-'):]
            target_id = f"p_{target_name}"
            target_link = f"link_{target_name}"
            debug_print(
                f'domain-member: {primary_id} to {target_id} {child["name"]} order={count} in {target_link} targetRole="http://www.xbrl.org/xbrl-gl/role/{target_link}'
            )
            lines.append(f"    <!-- {primary_id} to targetRole {target_link} -->\n")
            if primary_id not in locsDefined:
                locsDefined[primary_id] = set()
            if not target_id in locsDefined[primary_id]:
                locsDefined[primary_id].add(target_id)
                lines.append(
                    f'    <link:loc xlink:type="locator" xlink:href="gl-plt-all-2025-12-01.xsd#{target_id}" xlink:label="{target_id}" xlink:title="{target_id} {child_name}"/>\n'
                )
            count += 1
            arc_id = f"{primary_id} TO {target_link}"
            if primary_id not in arcsDefined:
                arcsDefined[primary_id] = set()
            if not arc_id in arcsDefined[primary_id]:
                arcsDefined[primary_id].add(arc_id)
                lines.append(
                    f'    <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xbrldt:targetRole="http://www.xbrl.org/xbrl-gl/role/{target_link}" xlink:from="{primary_id}" xlink:to="{target_id}" xlink:title="domain-member: {primary_id} to {target_id} in {target_link}" order="{count}"/>\n'
                )
        else:
            debug_print(f'domain-member: {primary_id} to {child_element_id} {child["name"]} order={count}')
            if primary_id not in locsDefined:
                locsDefined[primary_id] = set()
            if not child_element_id in locsDefined[primary_id]:
                locsDefined[primary_id].add(child_element_id)
                lines.append(
                    f'    <link:loc xlink:type="locator" xlink:href="{taxonomy_schema}#{child_element_id}" xlink:label="{child_element_id}" xlink:title="{child_element_id} {child_name}"/>\n'
                )
            count += 1
            arc_id = f"{primary_id} TO {child_element_id}"
            if primary_id not in arcsDefined:
                arcsDefined[primary_id] = set()
            if arc_id not in arcsDefined[primary_id]:
                arcsDefined[primary_id].add(arc_id)
                lines.append(
                    f'    <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xlink:from="{primary_id}" xlink:to="{child_element_id}" xlink:title="domain-member: {primary_id} to {child_element_id} {child["name"]}" order="{count}"/>\n'
                )
    return lines


def defineHypercube(root):
    global lines
    global locsDefined
    global arcsDefined
    global targetRefDict
    global referenceDict

    dimension_id_list = []
    taxonomy_schema, link_id, href = roleRecord(root['element_id'])
    path = root["semPath"]
    paths = path.strip("/").split("/")
    for id in paths:
        schema_id = getElementID(id)
        dimension_id = f"d_{schema_id[3:]}"
        dimension_id_list.append(dimension_id)
    element_id = f"gl-{link_id[5:]}"
    locsDefined[link_id] = set()
    arcsDefined[link_id] = set()
    primary_name = element_id[1+element_id.index('-'):]
    hypercube_id = f"h_{primary_name}"
    primary_id = f"p_{primary_name}"
    lines += [
        f'  <link:definitionLink xlink:type="extended" xlink:role="http://www.xbrl.org/xbrl-gl/role/{link_id}">\n',
        # all (has-hypercube)
        f"    <!-- {primary_id} all (has-hypercube) {hypercube_id} {link_id} -->\n",
        f'    <link:loc xlink:type="locator" xlink:href="gl-plt-all-2025-12-01.xsd#{primary_id}" xlink:label="{primary_id}" xlink:title="{primary_id}"/>\n',
        f'    <link:loc xlink:type="locator" xlink:href="gl-plt-all-2025-12-01.xsd#{hypercube_id}" xlink:label="{hypercube_id}" xlink:title="{hypercube_id}"/>\n',
        f'    <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/all" xlink:from="{primary_id}" xlink:to="{hypercube_id}" xlink:title="all (has-hypercube): {primary_id} to {hypercube_id}" order="1" xbrldt:closed="true" xbrldt:contextElement="segment"/>\n',
    ]
    debug_print(f"all(has-hypercube) {primary_id} to {hypercube_id} ")
    # hypercube-dimension
    lines.append("    <!-- hypercube-dimension -->\n")
    count = 0
    for dimension_id in dimension_id_list:
        lines.append(
            f'    <link:loc xlink:type="locator" xlink:href="gl-plt-all-2025-12-01.xsd#{dimension_id}" xlink:label="{dimension_id}" xlink:title="{dimension_id}"/>\n'
        )
        count += 1
        lines.append(
            f'    <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/hypercube-dimension" xlink:from="{hypercube_id}" xlink:to="{dimension_id}" xlink:title="hypercube-dimension: {hypercube_id} to {dimension_id}" order="{count}"/>\n'
        )
        debug_print(f"hypercube-dimension {hypercube_id} to {dimension_id} ")
    # domain-member
    lines.append("    <!-- domain-member -->\n")
    element_id = root['element_id']
    record = next((x for x in records if element_id == x["element_id"]), None)
    abbreviation_path = record['abbrevPath']
    dimension = dimensionDict[abbreviation_path]
    if 'children' in dimension:
        children = dimension["children"]
        lines += domainMember(children, primary_id)
    lines.append("  </link:definitionLink>\n")


def roleRecord(_element_id):
    record = getRecord(_element_id)
    element_id = record["element_id"]
    module = element_id[3:element_id.index("_")]
    taxonomy_schema = f"../{module}/gl-{module}-2025-12-01.xsd"
    link_id = f"link_{element_id[3:]}"
    href = f"{taxonomy_schema}/{link_id}"
    return taxonomy_schema, link_id, href


def linkPresentation(_module, element_id, children, n):
    global lines
    global count
    global locsDefined
    global arcsDefined
    if not element_id:
        return
    order = 0
    record = next((x for x in records if element_id == x["element_id"]), None)
    if not record:
        return
    module = element_id[: element_id.index("_")][3:]
    name = record["name"]
    if not element_id in locsDefined:
        locsDefined[element_id] = name
        lines.append(f"    <!-- {name} -->\n")
        if _module==module:
            lines.append(
                f'    <loc xlink:type="locator" xlink:href="gl-{module}-2025-12-01.xsd#{element_id}" xlink:label="{element_id}" xlink:title="loc: {element_id}"/>\n'
            )
        else:
            lines.append(
                f'    <loc xlink:type="locator" xlink:href="../{module}/gl-{module}-2025-12-01.xsd#{element_id}" xlink:label="{element_id}" xlink:title="loc: {element_id}"/>\n'
            )
    for child_element_id in children:
        child = next((x for x in records if child_element_id == x["element_id"]), None)
        if not child:
            continue
        child_module = child_element_id[3:child_element_id.index("_")]
        child_name = child["name"]
        order += 10
        arc_id = f"{element_id} to {child_element_id}"
        if arc_id not in arcsDefined:
            arcsDefined[arc_id] = f"presentation: {element_id} to {child_element_id}"
            if _module==child_module:
                lines += [
                    f'    <loc xlink:type="locator" xlink:href="gl-{child_module}-2025-12-01.xsd#{child_element_id}" xlink:label="{child_element_id}" xlink:title="presentation: {element_id} to {child_element_id} {child_name}"/>\n',
                    f'    <presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="{element_id}" xlink:to="{child_element_id}" xlink:title="presentation: {element_id} to {child_element_id}" use="optional" order="{order}"/>\n',
                ]
            else:
                lines += [
                    f'    <loc xlink:type="locator" xlink:href="../{child_module}/gl-{child_module}-2025-12-01.xsd#{child_element_id}" xlink:label="{child_element_id}" xlink:title="presentation: {element_id} to {child_element_id} {child_name}"/>\n',
                    f'    <presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="{element_id}" xlink:to="{child_element_id}" xlink:title="presentation: {element_id} to {child_element_id}" use="optional" order="{order}"/>\n',
                ]
        if child_element_id in presentationDict:
            grand_children = presentationDict[child_element_id]
            linkPresentation(_module, child_element_id, grand_children, n + 1)
    children = None


def escape_text(str):
    if not str:
        return ""
    escaped = str.replace("<", "&lt;")
    escaped = escaped.replace(">", "&gt;")
    return escaped


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(
        prog="xBRL-GL-taxonomy.py",
        usage="%(prog)s infile -s selected_roots -o out -e encoding [options] ",
        description="Audit data collection Convert definition CSV file to xBRL taxonomy",
    )
    # Add the arguments
    parser.add_argument(
        "inFile",
        metavar="infile",
        type=str,
        help="Audit data collection definition CSV file",
    )
    parser.add_argument("-r", "--root")  # root id e.g. CO13
    parser.add_argument("-b", "--base_dir")  # ../XBRL-GL/
    parser.add_argument("-o", "--out")  # core
    parser.add_argument("-l", "--lang")  # 'ja'
    parser.add_argument("-c", "--currency")  # 'JPY'
    parser.add_argument("-n", "--namespace")  # 'xbrl-gl'
    parser.add_argument("-e", "--encoding")  # 'Shift_JIS' 'cp932' 'utf_8'
    parser.add_argument("-x", "--xpath", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")

    args = parser.parse_args()

    in_file = None
    if args.inFile:
        in_file = args.inFile.strip()
        in_file = in_file.replace("/", SEP)
        in_file = file_path(args.inFile)
    if not in_file or not os.path.isfile(in_file):
        print(f"Input ADC definition CSV file {in_file} is missing.")
        sys.exit()
    core_file = in_file

    if args.base_dir:
        base_dir = args.base_dir.strip()
    else:
        base_dir = ""

    xbrl_base = file_path(f"{base_dir}gl")
    xbrl_base = xbrl_base.replace("/", SEP)
    if not os.path.isdir(xbrl_base):
        print(f"Taxonomy directory {xbrl_base} does not exist.")
        sys.exit()

    root = args.root
    if root:
        root = root.lstrip()
    else:
        root = None

    lang = args.lang
    if lang:
        lang = lang.lstrip()
    else:
        lang = None

    currency = args.currency
    if currency:
        currency = currency.lstrip()
    else:
        currency = "JPY"

    namespace = args.namespace
    if namespace:
        namespace = namespace.lstrip()
    else:
        namespace = 'http://www.xbrl.org/xbrl-gl"'

    encoding = args.encoding
    if encoding:
        encoding = encoding.lstrip()
    else:
        encoding = "utf-8-sig"

    XPATH = args.xpath
    TRACE = args.verbose
    DEBUG = args.debug

    # ====================================================================
    # 1. csv -> schema
    # ROOT_IDs = selected_roots
    records = []
    dimensionDict = {}
    presentationDict = {}
    classDict = {}
    abbreviationDict = {}
    columnnameDict = {}
    xpathDict = {}

    level_presentation = [None] * 10
    level_dimension = [None] * 10

    header = [
        "sequence",
        "level",
        "type",
        "identifier",
        "name",
        "datatype",
        "multiplicity",
        "domainName",
        "definition",
        "module",
        "table",
        "classTerm",
        "id",
        "path",
        "semPath",
        "abbrevPath",
        "labelLocal",
        "definitionLocal",
        "element",
        "xpath",
    ]

    with open(core_file, encoding=encoding, newline="") as f:
        reader = csv.reader(f)
        next(reader)
        semSort = 1000
        for cols in reader:
            record = {}
            for i in range(len(header)):
                if i < len(cols):
                    col = cols[i]
                    record[header[i]] = col.strip()
            semPath = record["semPath"]
            abbrevPath = record["abbrevPath"]
            if not abbrevPath:
                continue
            d_level = len(abbrevPath.split("_"))
            # get root id from semantic path and check format
            this_root_id = abbrevPath.split(".")[0]
            _type = record["type"]
            if "_" in abbrevPath:
                cor_id = abbrevPath[1+abbrevPath.rindex("_"):]  # terminal is
            else:
                cor_id = abbrevPath
            if "C" == _type:
                class_id = cor_id
            semSort = record["sequence"]
            identifier = record["identifier"]
            level = int(record["level"])
            objectClass = record["classTerm"]
            multiplicity = record["multiplicity"]
            name = record["name"]
            datatype = record["datatype"]
            element = record["element"]
            element_id = element.replace(":", "_")
            xPath = record["xpath"]
            if "REF" == identifier:
                level = level - 1
            data = {
                "level": level,
                "semSort": int(semSort),
                "d_level": d_level,
                "type": _type,
                "class_id": class_id,
                "identifier": identifier,
                "name": name,
                "datatype": datatype,
                "element": element,
                "element_id": element_id,
                "objectClass": objectClass,
                "multiplicity": multiplicity,
                "semPath": semPath,
                "abbrevPath": abbrevPath,
                "xPath": xPath,
                "definition": record["definition"],
                "labelLocal": record["labelLocal"],
                "definitionLocal": record["definitionLocal"],
                "id": cor_id,
            }
            parent = None
            if 1 == int(level):
                level_presentation[level] = element_id
                if element_id not in presentationDict:
                    presentationDict[element_id] = []
                level_dimension[d_level] = cor_id
            elif int(level) > 1:
                """
                presentation link
                """
                level_presentation[level] = element_id
                if "C" == _type:
                    if level > 1:
                        parent_id = level_presentation[level - 1]
                        data["parent_id"] = parent_id
                        if parent_id not in presentationDict:
                            presentationDict[parent_id] = []
                        if element_id not in presentationDict[parent_id]:
                            presentationDict[parent_id].append(element_id)
                else:
                    parent_id = level_presentation[level - 1]
                    data["parent_id"] = parent_id
                    if parent_id not in presentationDict:
                        presentationDict[parent_id] = []
                    if element_id not in presentationDict[parent_id]:
                        presentationDict[parent_id].append(element_id)
                """
                definition link
                """
                _id = data["abbrevPath"]
                level_dimension[d_level] = _id
                d_parent = ""
                if "_" in abbrevPath:
                    d_parent = '_'.join(abbrevPath.split("_")[:-1])
                data["parent_sem_id"] = d_parent
                if d_parent and d_parent not in dimensionDict:
                    parent_record = next(
                        (x for x in records if x["abbrevPath"].endswith(d_parent)), None
                    )
                    parent_id = parent_record["abbrevPath"] #.split("_")[-1]
                    dimensionDict[d_parent] = {
                        "parent_id": parent_id,
                        "children": [],
                    }
                if d_parent and cor_id not in dimensionDict[d_parent]["children"]:
                    dimensionDict[d_parent]["children"].append(_id)
            records.append(data)

    targetRefDict = {}
    for cor_id, record in dimensionDict.items():
        if "children" in record:
            children = record["children"]
            for child_element_id in children:
                child = getRecord(child_element_id)
                if child and "C" == child["type"]:
                    if child["multiplicity"].endswith("*"):
                        child_element_id = child["element_id"]
                        parent_element_id = getElementID(cor_id)
                        targetRefDict[child_element_id] = parent_element_id

    roleMap = {}
    for cor_id, data in dimensionDict.items():
        record = getRecord(cor_id)
        roleMap[record["element_id"]] = record

    ###################################
    # xBRL GD Pallete Schema
    #
    elementsDefined = set()
    typesDefined = set()
    elementDict = {}
    for parent_id, children in presentationDict.items():
        parent_record = next((x for x in records if parent_id == x["element_id"]), None)
        if not parent_record:
            continue
        parent_element = parent_id.replace("_", ":")
        parent_module = parent_id[3:parent_id.index("_")]
        if parent_module not in elementDict:
            elementDict[parent_module] = []
        _parent_record = next((x for x in elementDict[parent_module] if parent_element == x["element"]), None)
        if not _parent_record:
            elementDict[parent_module].append(
                {
                    "element": parent_element,
                    "id": parent_record["id"],
                    "name": parent_record["name"],
                    "definition": parent_record["definition"],
                    "label_local": parent_record["labelLocal"],
                    "definition_local": parent_record["definitionLocal"],
                    "multiplicity": "",
                    "datatype": "",
                    "children": children,
                }
            )
        for element_id in children:
            record = next((x for x in records if element_id == x["element_id"]), None)
            if not record:
                continue
            element = record["element"]
            id = record["id"]
            module = element[3:element.index(":")]
            if module not in elementDict:
                elementDict[module] = []
            multiplicity = record["multiplicity"]
            datatype = record["datatype"]
            name = record["name"]
            definition = record["definition"]
            label_local = record["labelLocal"]
            definition_local = record["definitionLocal"]
            if element_id in presentationDict:
                _children = presentationDict[element_id]
                element_data = {
                    "element": element,
                    "id": id,
                    "name": name,
                    "definition": definition,
                    "label_local": label_local,
                    "definition_local": definition_local,
                    "multiplicity": multiplicity,
                    "datatype": datatype,
                    "children": _children,
                }
                if element_data not in elementDict[module]:
                    elementDict[module].append(element_data)
            else:
                element_data = {
                    "element": element,
                    "id": id,
                    "name": name,
                    "definition": definition,
                    "label_local": label_local,
                    "definition_local": definition_local,
                    "multiplicity": multiplicity,
                    "datatype": datatype,
                }
                if element_data not in elementDict[module]:
                    elementDict[module].append(element_data)
    for _module, data in elementDict.items():
        modules = set()
        for record in data:
            datatype = record["element"]
            module = datatype[3:datatype.index(":")]
            modules.add(module)
        """
        Module taxonomy schema
        """
        html = [
            '<?xml version="1.0" encoding="UTF-8"?>\n',
            "<!-- (c) XBRL International.  See http://www.xbrl.org/legal -->\n",
            f'<schema targetNamespace="http://www.xbrl.org/int/gl/{module}/2025-12-01" attributeFormDefault="unqualified" elementFormDefault="qualified"\n',
            '  xmlns="http://www.w3.org/2001/XMLSchema"\n',
            '  xmlns:link="http://www.xbrl.org/2003/linkbase"\n'
            '  xmlns:xlink="http://www.w3.org/1999/xlink"\n',
            '  xmlns:xbrli="http://www.xbrl.org/2003/instance"\n',
            '  xmlns:xbrldt="http://xbrl.org/2005/xbrldt"\n',
        ]
        for module in modules:
            html.append(
                f'  xmlns:gl-{module}="http://www.xbrl.org/int/gl/{module}/2025-12-01"\n'
            )
        html.append(
            ">\n"
        )

        html += [
            '  <import namespace="http://www.xbrl.org/2003/instance" schemaLocation="http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd"/>\n',
            '  <import namespace="http://www.xbrl.org/2003/linkbase" schemaLocation="http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"/>\n',
            '  <import namespace="http://xbrl.org/2005/xbrldt" schemaLocation="http://www.xbrl.org/2005/xbrldt-2005.xsd"/>\n',
        ]

        for module in modules:
            if _module != module:
                html.append(
                    f'  <import namespace="http://www.xbrl.org/int/gl/{module}/2025-12-01" schemaLocation="../gen/gl-gen-2025-12-01.xsd"/>\n'
                )

        html += [
            "  <annotation>\n",
            "    <appinfo>\n",
            f'      <link:linkbaseRef xlink:type="simple" xlink:href="gl-{module}-2025-12-01-presentation.xml" xlink:title="Presentation Links, all" xlink:role="http://www.xbrl.org/2003/role/presentationLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase"/>\n'
        ]

        html += [
            "    </appinfo>\n",
            "  </annotation>\n"
        ]

        html.append("  <!-- item element -->\n")
        for line in data:
            element = line["element"]
            name = element[1 + element.index(":"):]
            element_id = element.replace(":", "_")
            multiplicity = line["multiplicity"]
            datatype = line["datatype"]
            if element in elementsDefined:
                continue
            elementsDefined.add(element)
            if datatype:
                html.append(
                    f'  <element name="{name}" id="{element_id}" type="{datatype}" substitutionGroup="xbrli:item" nillable="true" xbrli:periodType="instant"/>\n'
                )
            else:
                html.append(
                    f'  <element name="{name}" id="{element_id}" type="{element}ComplexType" substitutionGroup="xbrli:tuple" nillable="false"/>\n'
                )
        html.append("</schema>")
        """
        Write module taxonomy schema file
        """
        xsd_file = file_path(f"{xbrl_base}/{module}/gl-{module}-2025-12-01.xsd")
        with open(xsd_file, "w", encoding=encoding, newline="") as f:
            f.writelines(html)
        trace_print(f"-- {xsd_file}")

    for _module, data in elementDict.items():
        modules = set()
        for record in data:
            if "children" in record:
                children = record["children"]
                for child in children:
                    module = child[3:child.index("_")]
                    modules.add(module)
            else:
                continue
        html = [
            '<?xml version="1.0" encoding="UTF-8"?>\n',
            "<!-- (c) XBRL International.  See http://www.xbrl.org/legal -->\n",
            f'<schema targetNamespace="http://www.xbrl.org/int/gl/{_module}/2025-12-01" elementFormDefault="qualified" attributeFormDefault="unqualified"\n',
            '  xmlns="http://www.w3.org/2001/XMLSchema"\n',
            '  xmlns:xlink="http://www.w3.org/1999/xlink"\n',
            '  xmlns:xbrli="http://www.xbrl.org/2003/instance"\n',
        ]
        for module in modules:
            if _module != module:
                html.append(
                    f'  xmlns:gl-{module}="http://www.xbrl.org/int/gl/{module}/2025-12-01"\n'
                )
        html.append(
            f'  xmlns:gl-{_module}="http://www.xbrl.org/int/gl/{_module}/2025-12-01">\n'
        )
        html.append(
            '  <import namespace="http://www.xbrl.org/2003/instance" schemaLocation="http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd"/>\n'
        )
        for module in modules:
            if _module != module:
                html.append(
                    f'  <import namespace="http://www.xbrl.org/int/gl/{module}/2025-12-01" schemaLocation="gl-{module}-content-2025-12-01.xsd"/>\n'
                )
        html.append(
            f'  <include schemaLocation="../{_module}/gl-{_module}-2025-12-01.xsd"/>\n'
        )
        html.append("  <!-- tuple data type -->\n")
        for record in data:
            element = record["element"]
            if record["datatype"]:
                continue
            element_name = element[1 + element.index(":"):]
            module = element[3:element.index(":")]
            html += [
                f'  <group name="{element_name}Group">\n',
                "    <sequence>\n",
            ]
            if "children" in record:
                children = record["children"]
                for child_element_id in children:
                    child_name = child_element_id[1 + child_element_id.index("_"):]
                    child_module = child_element_id[3:child_element_id.index("_")]
                    child_record = next(
                        (x for x in records if child_element_id == x["element_id"]), None
                    )
                    if not child_record:
                        continue
                    child_multiplicity = child_record["multiplicity"]
                    min_occurs = child_multiplicity[0]
                    max_occurs = child_multiplicity[3]
                    if "*" == max_occurs:
                        max_occurs = "unbounded"
                    child_datatype = child_record["datatype"]
                    if child_datatype:
                        html.append(
                            f'    <element ref="gl-{child_module}:{child_name}" minOccurs="{min_occurs}" maxOccurs="{max_occurs}"/>\n'
                        )
                    else:
                        if "1" == max_occurs:
                            html.append(
                                f'    <group ref="gl-{child_module}:{child_name}Group" minOccurs="{min_occurs}" maxOccurs="1"/>\n'
                            )
                        else:
                            html += [
                                "    <choice>\n",
                                f'    <group ref="gl-{child_module}:{child_name}Group" minOccurs="0" maxOccurs="1"/>\n',
                                f'    <element ref="gl-{child_module}:{child_name}" minOccurs="2" maxOccurs="unbounded"/>\n',
                                "    </choice>\n",
                            ]
            html += [
                "  </sequence>\n",
                "  </group>\n",
                f'  <complexType name="{element_name}ComplexType">\n',
                "    <complexContent>\n",
                '      <restriction base="anyType">\n',
                "        <sequence>\n",
                f'          <group ref="gl-{module}:{element_name}Group"/>\n',
                "        </sequence>\n",
                '        <attribute name="id" type="ID"/>\n',
                "      </restriction>\n",
                "    </complexContent>\n",
                "  </complexType>\n",
            ]
        html.append("</schema>")
        """
        Write module schema file
        """
        xsd_file = file_path(f"{xbrl_base}/plt/gl-{_module}-content-2025-12-01.xsd")
        with open(xsd_file, "w", encoding=encoding, newline="") as f:
            f.writelines(html)
        trace_print(f"-- {xsd_file}")

    """
    Palette schema
    """
    modules = elementDict.keys()
    html = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        "<!-- (c) XBRL International.  See http://www.xbrl.org/legal -->\n",
        '<schema targetNamespace="http://www.xbrl.org/int/gl/plt/2025-12-01" attributeFormDefault="unqualified" elementFormDefault="qualified"\n',
        '  xmlns="http://www.w3.org/2001/XMLSchema"\n',
        '  xmlns:xbrli="http://www.xbrl.org/2003/instance"\n',
        '  xmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '  xmlns:xlink="http://www.w3.org/1999/xlink"\n',
        '  xmlns:xbrldt="http://xbrl.org/2005/xbrldt"\n',
        '  xmlns:gl-plt="http://www.xbrl.org/int/gl/plt/2025-12-01">\n'
    ]

    for module in modules:
        if _module != module:
            html.append(
                f'  <import namespace="http://www.xbrl.org/int/gl/{module}/2025-12-01" schemaLocation="../{module}/gl-{module}-2025-12-01.xsd"/>\n'
            )

    html += [
        '  <import namespace="http://www.xbrl.org/2003/instance" schemaLocation="http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd"/>\n',
        '  <import namespace="http://www.xbrl.org/2003/linkbase" schemaLocation="http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"/>\n',
        '  <import namespace="http://xbrl.org/2005/xbrldt" schemaLocation="http://www.xbrl.org/2005/xbrldt-2005.xsd"/>\n',
        '  <import namespace="http://www.xbrl.org/int/gl/cor/2025-12-01" schemaLocation="gl-cor-content-2025-12-01.xsd"/>\n'
    ]

    html += [
        "  <annotation>\n",
        "    <appinfo>\n"
    ]
    for module in modules:
        html += [
            f'      <link:linkbaseRef xlink:type="simple" xlink:href="../{module}/lang/gl-{module}-2025-12-01-label.xml" xlink:title="Label Links, all" xlink:role="http://www.xbrl.org/2003/role/labelLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase"/>\n',
            f'      <link:linkbaseRef xlink:type="simple" xlink:href="../{module}/lang/gl-{module}-2025-12-01-label-ja.xml" xlink:title="Label Links, ja" xlink:role="http://www.xbrl.org/2003/role/labelLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase"/>\n'
        ]
    html.append(
        f'      <link:linkbaseRef xlink:type="simple" xlink:href="gl-plt-def-2025-12-01.xml" xlink:title="Definition" xlink:role="http://www.xbrl.org/2003/role/definitionLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase"/>\n',
    )

    html += [
        "      <!-- \n",
        "        role type\n",
        "      -->\n",
        '      <link:roleType id="xbrl-gl-role" roleURI="http://www.xbrl.org/xbrl-gl/role">\n',
        "        <link:definition>link xbrl-gl</link:definition>\n",
        "        <link:usedOn>link:definitionLink</link:usedOn>\n",
        "        <link:usedOn>link:presentationLink</link:usedOn>\n",
        "      </link:roleType>\n"
    ]

    for element_id in roleMap.keys():
        element_name = element_id[3:]
        html += [
            f'      <link:roleType id="link_{element_name}" roleURI="http://www.xbrl.org/xbrl-gl/role/link_{element_name}">\n',
            "        <link:usedOn>link:definitionLink</link:usedOn>\n",
            "      </link:roleType>\n"
        ]

    html += [
        "    </appinfo>\n",
        "  </annotation>\n"
    ]

    modules = set()
    for record in data:
        datatype = record["element"]
        module = datatype[3:datatype.index(":")]
        modules.add(module)

    html += [
        "  <!-- typed dimension referenced element -->\n",
        '  <element name="_v" id="_v">\n',
        "    <simpleType>\n",
        '    <restriction base="string"/>\n',
        "    </simpleType>\n",
        "  </element>\n"
    ]

    html.append("  <!-- Hypercube -->\n")
    for element_id in roleMap.keys():
        element_name = element_id[3:]
        html.append(
            f'  <element name="h_{element_name}" id="h_{element_name}" substitutionGroup="xbrldt:hypercubeItem" type="xbrli:stringItemType" nillable="true" abstract="true" xbrli:periodType="instant"/>\n'
        )

    html.append("  <!-- Dimension -->\n")
    for element_id in roleMap.keys():
        element_name = element_id[3:]
        html.append(
            f'  <element name="d_{element_name}" id="d_{element_name}" substitutionGroup="xbrldt:dimensionItem" type="xbrli:stringItemType" abstract="true" xbrli:periodType="instant" xbrldt:typedDomainRef="#_v"/>\n'
        )

    html.append("  <!-- Primary -->\n")
    for element_id in roleMap.keys():
        element_name = element_id[3:]
        html.append(
            f'  <element name="p_{element_name}" id="p_{element_name}" substitutionGroup="xbrli:item" type="xbrli:stringItemType" nillable="true" xbrli:periodType="instant"/>\n'
        )

    html.append(
        "</schema>\n"
    )

    """
    Write palette schema file
    """
    xsd_file = file_path(f"{xbrl_base}/plt/gl-plt-all-2025-12-01.xsd")
    with open(xsd_file, "w", encoding=encoding, newline="") as f:
        f.writelines(html)
    trace_print(f"-- {xsd_file}")

    ###################################
    # labelLink en
    #
    for module, data in elementDict.items():
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>\n',
            "<!-- (c) XBRL International.  See http://www.xbrl.org/legal -->\n",
            '<linkbase xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"\n',
            '    xmlns="http://www.xbrl.org/2003/linkbase"\n',
            '    xmlns:xlink="http://www.w3.org/1999/xlink">\n',
            '    <labelLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">\n',
        ]

        for record in data:
            element = record["element"]
            name = record["name"]
            desc = record["definition"].replace('\\n','\n') if "definition" in record else None
            module = element[3:element.index(":")]
            element_name = element[1 + element.index(":"):]
            lines += [
                f"        <!-- {element} {name} -->\n",
                f'        <loc xlink:type="locator" xlink:href="../gl-{module}-2025-12-01.xsd#gl-{module}_{element_name}" xlink:label="{element_name}"/>\n',
                f'        <label xlink:type="resource" xlink:label="{element_name}_lbl" xlink:role="http://www.xbrl.org/2003/role/label" xlink:title="gl-{module}_{element_name}_en" xml:lang="en">{name}</label>\n',
                f'        <label xlink:type="resource" xlink:label="{element_name}_lbl" xlink:role="http://www.xbrl.org/2003/role/documentation" xml:lang="{lang}">{desc}</label>\n',
                f'        <labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="{element_name}" xlink:to="{element_name}_lbl"/>\n',
            ]

        lines.append("  </labelLink>\n")
        lines.append("</linkbase>\n")
        """
        Write label linkbase file
        """
        label_file = file_path(
            f"{xbrl_base}/{module}/lang/gl-{module}-2025-12-01-label.xml"
        )
        with open(label_file, "w", encoding=encoding, newline="") as f:
            f.writelines(lines)
        trace_print(f"-- {label_file}")

    ###################################
    # labelLink lang
    #
    for module, data in elementDict.items():
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>\n',
            "<!-- (c) XBRL International.  See http://www.xbrl.org/legal -->\n",
            '<linkbase xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"\n',
            '    xmlns="http://www.xbrl.org/2003/linkbase"\n',
            '    xmlns:xlink="http://www.w3.org/1999/xlink">\n',
            '    <labelLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">\n',
        ]

        for record in data:
            element = record["element"]
            label_local = record["label_local"]
            definition_local = (
                record["definition_local"].replace('\\n','\n') if "definition_local" in record else None
            )
            module = element[3:element.index(":")]
            element_name = element[1 + element.index(":"):]
            lines += [
                f"        <!-- {element} {label_local} -->\n",
                f'        <loc xlink:type="locator" xlink:href="../gl-{module}-2025-12-01.xsd#gl-{module}_{element_name}" xlink:label="{element_name}"/>\n',
                f'        <label xlink:type="resource" xlink:label="{element_name}_lbl" xlink:role="http://www.xbrl.org/2003/role/label" xlink:title="gl-{module}_{element_name}_{lang}" xml:lang="en">{label_local}</label>\n',
                f'        <label xlink:type="resource" xlink:label="{element_name}_lbl" xlink:role="http://www.xbrl.org/2003/role/documentation" xml:lang="{lang}">{definition_local}</label>\n',
                f'        <labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="{element_name}" xlink:to="{element_name}_lbl"/>\n',
            ]

        lines.append("  </labelLink>\n")
        lines.append("</linkbase>\n")
        """
        Write label linkbase file
        """
        label_file = file_path(
            f"{xbrl_base}/{module}/lang/gl-{module}-2025-12-01-label-{lang}.xml"
        )
        with open(label_file, "w", encoding=encoding, newline="") as f:
            f.writelines(lines)
        trace_print(f"-- {label_file}")

    ###################################
    #   presentationLink
    #
    for module, data in elementDict.items():
        locsDefined = {}
        arcsDefined = {}
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>\n',
            "<!-- (c) XBRL International.  See http://www.xbrl.org/legal -->\n",
            '<linkbase xmlns="http://www.xbrl.org/2003/linkbase"\n',
            '  xmlns:xlink="http://www.w3.org/1999/xlink"\n',
            '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd">\n',
            '  <presentationLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">\n',
        ]
        class_records = [x for x in data if not x["datatype"]]
        for record in class_records:
            element = record["element"]
            element_id = element.replace(":", "_")
            count = 0
            if "children" in record:
                children = record["children"]
                linkPresentation(module, element_id, children, 1)

        lines.append("  </presentationLink>\n")
        lines.append("</linkbase>\n")

        """
        Write presentation linkbase file
        """
        presentation_file = file_path(
            f"{xbrl_base}/{module}/gl-{module}-2025-12-01-presentation.xml"
        )
        with open(presentation_file, "w", encoding=encoding, newline="") as f:
            f.writelines(lines)
        trace_print(f"-- {presentation_file}")

    ###################################
    # definitionLink
    #
    locsDefined = {}
    arcsDefined = {}
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        "<!-- (c) XBRL International.  See http://www.xbrl.org/legal -->\n",
        "<link:linkbase\n",
        '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"\n',
        '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '\txmlns:xbrldt="http://xbrl.org/2005/xbrldt"\n',
        '\txmlns:xlink="http://www.w3.org/1999/xlink">\n',
    ]
    lines.append("  <!-- roleRef -->\n")
    # 	<link:roleRef roleURI="http://www.xbrl.org/xbrl-gl/role/link_cor_accontingEntries" xlink:type="simple" xlink:href="core.xsd#link_cor_accontingEntries"/>
    for record in roleMap.values():
        taxonomy_schema, link_id, href = roleRecord(record['element_id'])
        lines.append(
            f'  <link:roleRef roleURI="http://www.xbrl.org/xbrl-gl/role/{link_id}" xlink:type="simple" xlink:href="gl-plt-all-2025-12-01.xsd#{link_id}"/>\n'
        )

    lines += [
        # f'  <link:roleRef roleURI="{namespace}/role/primary-key" xlink:type="simple" xlink:href="{taxonomy_schema}#primary-key"/>\n',
        # f'  <link:roleRef roleURI="{namespace}/role/reference-identifier" xlink:type="simple" xlink:href="{taxonomy_schema}#reference-identifier"/>\n',
        # f'  <link:roleRef roleURI="{namespace}/role/require" xlink:type="simple" xlink:href="{taxonomy_schema}#require"/>\n',
        "  <!-- arcroleRef -->\n",
        '  <link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/all" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#all"/>\n',
        '  <link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/domain-member" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#domain-member"/>\n',
        '  <link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/hypercube-dimension" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#hypercube-dimension"/>\n',
        '  <link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/dimension-domain" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#dimension-domain"/>\n',
        # f'  <link:arcroleRef arcroleURI="{namespace}/arcrole/concept-primary-key" xlink:type="simple" xlink:href="{taxonomy_schema}#concept-primary-key"/>\n',
        # f'  <link:arcroleRef arcroleURI="{namespace}/arcrole/concept-reference-identifier" xlink:type="simple" xlink:href="{taxonomy_schema}#concept-reference-identifier"/>\n',
    ]

    for cor_id, record in roleMap.items():
        # role = roleRecord(record)
        count = 0
        defineHypercube(record)

    lines.append("</link:linkbase>\n")

    cor_definition_file = file_path(f"{xbrl_base}/plt/gl-plt-def-2025-12-01.xml")

    with open(cor_definition_file, "w", encoding=encoding, newline="") as f:
        f.writelines(lines)
    trace_print(f"-- {cor_definition_file}")

    json_meta = {
        "documentInfo": {
            "documentType": "https://xbrl.org/2021/xbrl-csv",
            "namespaces": {
                "ns0": "http://www.example.com",
                "link": "http://www.xbrl.org/2003/linkbase",
                "iso4217": "http://www.xbrl.org/2003/iso4217",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xbrli": "http://www.xbrl.org/2003/instance",
                "xbrldi": "http://xbrl.org/2006/xbrldi",
                "xlink": "http://www.w3.org/1999/xlink",
                "gl-gen": "http://www.xbrl.org/int/gl/gen/2025-12-01",
                "gl-cor": "http://www.xbrl.org/int/gl/cor/2025-12-01",
                "gl-bus": "http://www.xbrl.org/int/gl/bus/2025-12-01",
                "gl-muc": "http://www.xbrl.org/int/gl/muc/2025-12-01",
                "gl-usk": "http://www.xbrl.org/int/gl/usk/2025-12-01",
                "gl-taf": "http://www.xbrl.org/int/gl/taf/2025-12-01",
                "gl-ehm": "http://www.xbrl.org/int/gl/ehm/2025-12-01",
                "gl-srcd": "http://www.xbrl.org/int/gl/srcd/2025-12-01",
                "gl-plt": "http://www.xbrl.org/int/gl/plt/2025-12-01"
            },
            "taxonomy": [
                "plt/gl-plt-all-2025-12-01.xsd"
            ]
        },
        "tableTemplates": {
            "xbrl-gl_template": {
                "dimensions": {
                    "period": "2025-05-17T00:00:00",
                    "entity": "ns0:Example Co.",
                },
                "columns": {},
            }
        },
        "tables": {"xbrl-gl_table": {"template": "xbrl-gl_template"}},
    }

    if root:
        dimension_columns = []
        property_columns = []
        root_id = next((x for x in dimensionDict.keys() if root in x), None)
        root_element_id = next((x for x in records if root_id == x["id"]), None)[
            "element_id"
        ]
        root_name = root_element_id[1 + root_element_id.index("-"):]
        dimensions = [
            dimensionDict[x]["parent_id"] for x in dimensionDict.keys() if root not in x
        ]
        properties = [
            x["element_id"]
            for x in records
            if x["element_id"] not in dimensions and "A" == x["type"]
        ]

        json_meta["tableTemplates"]["xbrl-gl_template"]["dimensions"][
            f"gl-plt:d_{root_name}"
        ] = f"${root_name}"
        json_meta["tableTemplates"]["xbrl-gl_template"]["columns"][root_name] = {}

        for dimension in dimensions:
            dimension_column = dimension[1 + dimension.index("_"):]
            dimension_name = dimension[1 + dimension.index("-"):]
            dimension_columns.append(dimension_name)
            json_meta["tableTemplates"]["xbrl-gl_template"]["dimensions"][
                f"gl-plt:d_{dimension_name}"
            ] = f"${dimension_name}"
            json_meta["tableTemplates"]["xbrl-gl_template"]["columns"][
                dimension_name
            ] = {}

        for property in properties:
            property_column = property[1 + property.index("_"):]
            property_name = property[1 + property.index("-"):]
            property_columns.append(property_name)
            property_module = property[: property.index("_")]
            if property.endswith("Amount"):
                json_meta["tableTemplates"]["xbrl-gl_template"]["columns"][
                    property_name
                ] = {
                    "dimensions": {
                        "concept": f"{property_module}:{property_column}",
                        "unit": f"iso4217:{currency}",
                    }
                }
            else:
                json_meta["tableTemplates"]["xbrl-gl_template"]["columns"][
                    property_name
                ] = {"dimensions": {"concept": f"{property_module}:{property_column}"}}

        out = "xbrl-gl"
        csv_file = f"{out}_skeleton.csv"
        json_meta["tables"]["xbrl-gl_table"]["url"] = csv_file

        json_meta_file = file_path(f"{xbrl_base}/{out}.json")
        try:
            with open(json_meta_file, "w", encoding="utf-8") as file:
                json.dump(json_meta, file, ensure_ascii=False, indent=4)
            print(f"JSON file '{json_meta_file}' has been created successfully.")
        except Exception as e:
            print(f"An error occurred while creating the JSON file: {e}")
        trace_print(f"-- JSON meta file {json_meta_file}")

        out_file = file_path(f"{xbrl_base}/{csv_file}")
        header_list = [root_name] + dimension_columns + property_columns
        try:
            with open(out_file, "w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                # Write the header and columnname rows
                writer.writerow(header_list)
            print(f"CSV template file '{out_file}' has been created successfully.")
        except Exception as e:
            print(f"An error occurred while creating the JSON file: {e}")
        trace_print(f"-- CSV file with header {csv_file}")

    print("** END **")
