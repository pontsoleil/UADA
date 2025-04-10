#!/usr/bin/env python3
# coding: utf-8
"""
generate Audit Data Collection xBRL-GD Taxonomy fron HMD CSV file and header files

designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

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
# from cgi import print_directory
import argparse
import os
import sys
import csv
import json
import re

DEBUG = False
VERBOSE = True
SEP = os.sep

core_xsd = "core.xsd"
core_label = "core-lbl"
core_presentation = "core-pre"
core_definition = "core-def"
core_reference = "core-ref"


datatypeMap = {
    "Char": {"cor": "charType", "xbrli": "tokenItemType"},
    "Code": {"cor": "codeType", "xbrli": "tokenItemType"},
    "Identifier": {"cor": "identifierType", "xbrli": "tokenItemType"},
    "Name": {"cor": "nameType", "xbrli": "normalizedStringItemType"},
    "Text": {"cor": "textType", "xbrli": "stringItemType"},
    "Decimal": {"cor": "decimalType", "xbrli": "decimalItemType"},
    "Integer": {"cor": "integerType", "xbrli": "intItemType"},
    "Boolean": {"cor": "booleanType", "xbrli": "booleanItemType"},
    "Date": {"cor": "dateType", "xbrli": "dateItemType"},
    "Time": {"cor": "timeType", "xbrli": "timeItemType"},
    "DateTime": {"cor": "dateTimeType", "xbrli": "dateTimeItemType"},
    "Year": {"cor": "yearType", "xbrli": "gYearItemType"},
    "Amount": {"cor": "amountType", "xbrli": "monetaryItemType"},
}


abbreviationMap = {
    "ACC": "Account",
    "ADJ": "Adjustment",
    "BAS": "Base",
    "BEG": "Beginning",
    "CUR": "Currency",
    "CUS": "Customer",
    "FOB": "Free On Board",
    "FS": "Financial Statement",
    "INV": "Inventory",
    "IT": "Information Technology",
    "JE": "Journal Entry",
    "NUM": "Number",
    "ORG": "Organization",
    "PK": "Primary Key",
    "PO": "Purchase Order",
    "PPE": "Property, Plant and Equipment",
    "PRV": "Province",
    "PUR": "Purchase",
    "REF": "Reference Identifier",
    "RFC": "Request For Comments",
    "SAL": "Sales",
    "TIN": "Tax Identification Number",
    "TRX": "Transactional",
    "UOM": "Unit of Measurement",
    "WIP": "Work In Progress",
}

# targetTables    = ['GL02','GL03']

duplicateNames = set()
names = set()
adcDict = {}
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


def file_path(pathname):
    if SEP == pathname[0:1]:
        return pathname
    else:
        pathname = pathname.replace("/", SEP)
        dir = os.path.dirname(__file__)
        new_path = os.path.join(dir, pathname)
        return new_path


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
    # ChatGPT 2023-04-10 modified by Nobu
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


def getRecord(cor_id):
    if cor_id in adcDict:
        record = adcDict[cor_id]
    else:
        record = None
    return record


def getParent(cor_id):
    if cor_id in adcDict:
        parent = adcDict[cor_id]
    else:
        parent = None
    return parent


def getChildren(cor_id):
    record = getRecord(cor_id)
    if record:
        return record["children"]
    return []


def getSchemaID(cor_id):
    abbreviationName = abbreviationDict[cor_id]
    if XPATH:
        xpath = xpathDict[abbreviationName]
        return xpath
    return abbreviationName


def checkAssociation(child_id, link_id, lines, source_id=None):
    global count
    child = getRecord(child_id)
    child_property = child["type"]
    schema_id = getSchemaID(child_id)
    link_schema_id = getSchemaID(link_id)
    if "C" == child["type"] and child_id in targetRefDict:
        # targetRole
        role_record = roleRecord(child)
        role_id = role_record["role_id"]
        URI = role_record["URI"]
        if DEBUG:
            print(
                f'domain-member: {link_schema_id} to {schema_id} {child["name"]} order={count} in {role_id} targetRole="{namespace}/role{URI}'
            )
        lines.append(f"\t\t<!-- {schema_id} targetRole {role_id} -->\n")
        if not child_id in locsDefined[link_id]:
            locsDefined[link_id].add(child_id)
            lines.append(
                f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{schema_id}" xlink:label="{schema_id}" xlink:title="{schema_id} {child["name"]}"/>\n'
            )
        count += 1
        arc_id = f"{link_id} {child_id}"
        if not arc_id in arcsDefined[link_id]:
            arcsDefined[link_id].add(arc_id)
            lines.append(
                f'\t\t<link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xbrldt:targetRole="{namespace}/role{URI}" xlink:from="{link_schema_id}" xlink:to="{schema_id}" xlink:title="domain-member: {link_schema_id} to {schema_id} in {role_id}" order="{count}"/>\n'
            )
    else:
        if child_property.lower().endswith(
            "class"
        ):  # and '*'==child['multiplicity'][-1]:
            if "children" in child and len(child["children"]) > 0:
                if DEBUG:
                    print(
                        f'domain-member: {link_schema_id} to {schema_id} {child["name"]} order={count}'
                    )
                if not child_id in locsDefined[link_id]:
                    locsDefined[link_id].add(child_id)
                    lines.append(
                        f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{schema_id}" xlink:label="{schema_id}" xlink:title="{schema_id} {child["name"]}"/>\n'
                    )
                count += 1
                arc_id = f"{link_id} {child_id}"
                if not arc_id in arcsDefined[link_id]:
                    arcsDefined[link_id].add(arc_id)
                    lines.append(
                        f'\t\t<link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xlink:from="{link_schema_id}" xlink:to="{schema_id}" xlink:title="domain-member: {link_schema_id} to {schema_id} {child["name"]}" order="{count}"/>\n'
                    )
                grand_children = child["children"]
                for grand_child_id in grand_children:
                    lines = checkAssociation(grand_child_id, link_id, lines, child_id)
        else:
            if not source_id:
                source_id = link_id
            source_schema_id = getSchemaID(source_id)
            if DEBUG:
                print(
                    f'domain-member: {source_schema_id} to {schema_id} {child["name"]} order={count}'
                )
            if not child_id in locsDefined[link_id]:
                locsDefined[link_id].add(child_id)
                lines.append(
                    f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{schema_id}" xlink:label="{schema_id}" xlink:title="{schema_id} {child["name"]}"/>\n'
                )
            count += 1
            arc_id = f"{source_id} {child_id}"
            if not arc_id in arcsDefined[link_id]:
                arcsDefined[link_id].add(arc_id)
                lines.append(
                    f'\t\t<link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xlink:from="{source_schema_id}" xlink:to="{schema_id}" xlink:title="domain-member: {source_schema_id} to {schema_id} {child["name"]}" order="{count}"/>\n'
                )
    return lines


def defineHypercube(root):
    global lines
    global locsDefined
    global arcsDefined
    global targetRefDict
    global referenceDict
    dimension_id_list = []
    role = roleRecord(root)
    path = root["semPath"]
    paths = path.strip("/").split("/")
    for id in paths:
        schema_id = getSchemaID(id)
        dimension_id = f"d_{schema_id}"
        dimension_id_list.append(dimension_id)
    link_id = role["link_id"]
    link_schema_id = getSchemaID(link_id)
    locsDefined[link_id] = set()
    arcsDefined[link_id] = set()
    URI = role["URI"]
    role_id = role["role_id"]
    hypercube_abbreviation = f"h_{link_schema_id}"
    lines.append(
        f'\t<link:definitionLink xlink:type="extended" xlink:role="{namespace}/role{URI}">\n'
    )
    # all (has-hypercube)
    lines.append(
        f"\t\t<!-- {link_schema_id} all (has-hypercube) {hypercube_abbreviation} {role_id} -->\n"
    )
    lines.append(
        f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{link_schema_id}" xlink:label="{link_schema_id}" xlink:title="{link_schema_id}"/>\n'
    )
    lines.append(
        f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{hypercube_abbreviation}" xlink:label="{hypercube_abbreviation}" xlink:title="{hypercube_abbreviation}"/>\n'
    )
    lines.append(
        f'\t\t<link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/all" xlink:from="{link_schema_id}" xlink:to="{hypercube_abbreviation}" xlink:title="all (has-hypercube): {link_schema_id} to {hypercube_abbreviation}" order="1" xbrldt:closed="true" xbrldt:contextElement="segment"/>\n'
    )
    if DEBUG:
        print(f"all(has-hypercube) {link_schema_id} to {hypercube_abbreviation} ")
    # hypercube-dimension
    lines.append("\t\t<!-- hypercube-dimension -->\n")
    count = 0
    for dimension_id in dimension_id_list:
        lines.append(
            f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{dimension_id}" xlink:label="{dimension_id}" xlink:title="{dimension_id}"/>\n'
        )
        count += 1
        lines.append(
            f'\t\t<link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/hypercube-dimension" xlink:from="{hypercube_abbreviation}" xlink:to="{dimension_id}" xlink:title="hypercube-dimension: {hypercube_abbreviation} to {dimension_id}" order="{count}"/>\n'
        )
        if DEBUG:
            print(f"hypercube-dimension {hypercube_abbreviation} to {dimension_id} ")
    # domain-member
    lines.append("\t\t<!-- domain-member -->\n")
    if "children" in root and len(root["children"]) > 0:
        children = root["children"]
        for child_id in children:
            lines = checkAssociation(child_id, link_id, lines)
    lines.append("\t</link:definitionLink>\n")


def lookupModule(class_id):
    module = None
    prefix = class_id[:2]
    if "NC" == prefix:
        module = "Invoice"
    elif "BS" == prefix:
        module = "Base"
    elif "GL" == prefix:
        module = "GL"
    elif "CM" == prefix:
        module = "Common"
    return module


def roleRecord(record):
    cor_id = record["cor_id"]
    schema_id = getSchemaID(cor_id)
    link_id = cor_id
    role_id = f"link_{schema_id}"
    URI = f"/{role_id}"
    role_record = {
        "cor_id": cor_id,
        "link_id": link_id,
        "URI": URI,
        "role_id": role_id,
    }
    return role_record


def get_element_datatype(cor_id, type, propertyType):
    if not type:
        type = "xbrli:stringItemType"
        if DEBUG:
            print(
                f"{cor_id} [{propertyType}] type not defined assign xbrli:stringItemType."
            )
    elif not "xbrli:" in type and not "cor:" in type:
        if not type:
            type = "xbrli:stringItemType"
            if DEBUG:
                print(
                    f"{cor_id} [{propertyType}] type not defined assign xbrli:stringItemType."
                )
        else:
            type = f"cor:{type}"
    return type


def defineElement(cor_id, record):
    global lines
    global elementsDefined
    if not cor_id in elementsDefined:
        elementsDefined.add(cor_id)
        if not record:
            print(f"NOT DEFINED {cor_id} record")
            return
        propertyType = record["type"]
        if record['semanticPath'].endswith("Amount.Value"):
            type = "cor:amountType"
        else:
            type = record["datatype"] if "datatype" in record and record["datatype"] else ""
        schema_id = getSchemaID(cor_id)
        if DEBUG:
            print(f"define {cor_id} {schema_id} [{propertyType}]")
        if propertyType.lower().endswith(
            "class"
        ):  # or cor_id in targetRefDict or cor_id in referenceDict:
            line = f'\t<element name="{schema_id}" id="{schema_id}" abstract="true" type="xbrli:stringItemType" nillable="true" substitutionGroup="xbrli:item" xbrli:periodType="instant"/>\n'
        else:
            type = get_element_datatype(cor_id, type, propertyType)
            line = f'\t<element name="{schema_id}" id="{schema_id}" type="{type}" nillable="false" substitutionGroup="xbrli:item" xbrli:periodType="instant"/>\n'
        lines.append(line)


def linkLabel(cor_id, name, desc, lang):
    global locsDefined
    global definedLabels
    global arcsDefined
    global definedDescs
    global definedDescArcs
    # name
    schema_id = getSchemaID(cor_id)
    if name:
        lines.append(f"\t\t<!-- {cor_id} {name} -->\n")
        if not cor_id in locsDefined:
            locsDefined[cor_id] = cor_id
            line = f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{schema_id}" xlink:label="{schema_id}" xlink:title="{schema_id}"/>\n'
        else:
            line = f"\t\t\t<!-- link:loc defined -->\n"
        lines.append(line)
        # name
        if not cor_id in definedLabels:
            definedLabels[cor_id] = cor_id
            line = f'\t\t<link:label xlink:type="resource" xlink:label="label_{schema_id}" xlink:title="label_{schema_id}" id="label_{schema_id}" xml:lang="{lang}" xlink:role="http://www.xbrl.org/2003/role/label">{name}</link:label>\n'
        else:
            line = f"\t\t\t<!-- link:label http://www.xbrl.org/2003/role/label defined -->\n"
        lines.append(line)
        if not cor_id in arcsDefined:
            arcsDefined[cor_id] = cor_id
            line = f'\t\t<link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="{schema_id}" xlink:to="label_{schema_id}" xlink:title="label: {schema_id} to label_{schema_id}"/>\n'
        else:
            line = f"\t\t\t<!-- link:labelArc http://www.xbrl.org/2003/arcrole/concept-label defined -->\n"
        lines.append(line)
    # desc
    if desc:  # and name != desc:
        if not cor_id in definedDescs:
            definedDescs[cor_id] = cor_id
            line = f'\t\t<link:label xlink:type="resource" xlink:label="description_{schema_id}" xlink:title="description_{schema_id}" id="description_{schema_id}" xml:lang="{lang}" xlink:role="{namespace}/role/description">{desc}</link:label>\n'
        else:
            line = f"\t\t\t<!-- link:label {namespace}/role/description defined -->\n"
        lines.append(line)
        if not cor_id in definedDescArcs:
            definedDescArcs[cor_id] = cor_id
            line = f'\t\t<link:labelArc xlink:type="arc" xlink:arcrole="{namespace}/arcrole/concept-description" xlink:from="{schema_id}" xlink:to="description_{schema_id}" xlink:title="label: {cor_id} to label_{schema_id}"/>\n'
        else:
            line = f"\t\t\t<!-- link:labelArc {namespace}/arcrole/concept-description defined -->\n"
        lines.append(line)


def linkPresentation(cor_id, children, n):
    global lines
    global count
    global locsDefined
    global arcsDefined
    if not cor_id:
        return
    record = getRecord(cor_id)
    schema_id = getSchemaID(cor_id)
    if not record:
        return
    propertyType = record["type"]
    name = record["name"]
    if not cor_id in locsDefined:
        locsDefined[cor_id] = name
        lines.append(f"\t\t<!-- {propertyType} {schema_id} {name} -->\n")
        lines.append(
            f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{schema_id}" xlink:label="{schema_id}" xlink:title="presentation: {schema_id} {name}"/>\n'
        )
    for child_id in children:
        child_abbreviation = getSchemaID(child_id)
        child = getRecord(child_id)
        child_property = child["type"]
        child_name = child["name"]
        if child_property.lower().endswith("class"):
            target_id = child_id
            target_abbreviation = child_abbreviation
            if not target_id in locsDefined:
                locsDefined[target_id] = child_name
                lines.append(
                    f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{target_abbreviation}" xlink:label="{target_abbreviation}" xlink:title="presentation parent: {target_abbreviation} {child_name}"/>\n'
                )
            arc_id = f"{cor_id} {target_id}"
            if not arc_id in arcsDefined and cor_id != target_id:
                arcsDefined[arc_id] = f"{name} to {child_name}"
                count += 1
                lines.append(
                    f'\t\t<link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="{schema_id}" xlink:to="{target_abbreviation}" order="{count}" xlink:title="presentation: {schema_id} {name} to {target_abbreviation} {child_name}"/>\n'
                )
                if "children_pre" in child and len(child["children_pre"]) > 0:
                    grand_children = child["children_pre"]
                    linkPresentation(target_id, grand_children, n + 1)
        else:
            if not child_id in locsDefined:
                locsDefined[child_id] = child_name
                lines.append(
                    f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{child_abbreviation}" xlink:label="{child_abbreviation}" xlink:title="presentation parent: {child_abbreviation} {child_name}"/>\n'
                )
            arc_id = f"{cor_id} {child_id}"
            if not arc_id in arcsDefined and cor_id != child_id:
                arcsDefined[arc_id] = f"{name} to {child_name}"
                count += 1
                lines.append(
                    f'\t\t<link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="{schema_id}" xlink:to="{child_abbreviation}" order="{count}" xlink:title="presentation: {schema_id} {name} to {child_abbreviation} {child_name}"/>\n'
                )
                if "children_pre" in child and len(child["children_pre"]) > 0:
                    grand_children = child["children_pre"]
                    linkPresentation(child_id, grand_children, n + 1)
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
        prog="LHM2xBRL-taxonomy.py",
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
    # parser.add_argument("-s", "--selected_roots")  # core.xsd e.g. GL02+GL03
    parser.add_argument("-r", "--root")  # root id e.g. CO13
    parser.add_argument("-b", "--base_dir")  # ../XBRL-GL/
    parser.add_argument("-o", "--out")  # core
    parser.add_argument("-l", "--lang")  # 'ja'
    parser.add_argument("-c", "--currency")  # 'JPY'
    parser.add_argument("-n", "--namespace")  # 'iso21926'
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
        print("Input ADC definition CSV file is missing.")
        sys.exit()
    core_file = in_file

    if args.base_dir:
        base_dir = args.base_dir.strip()
    else:
        base_dir = ""

    if args.out:
        out = args.out.strip()
        core_xsd = f"{out}.xsd"
        core_label = f"{out}-lbl"
        core_presentation = f"{out}-pre"
        core_definition = f"{out}-def"
        core_reference = f"{out}-ref"
        out_file = f"{base_dir}{out}.xsd"
        out_file = file_path(out_file)
        xbrl_base = os.path.dirname(out_file)
    xbrl_base = xbrl_base.replace("/", SEP)
    if not os.path.isdir(xbrl_base):
        print("Taxonomy directory does not exist.")
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
        currency = 'JPY'

    namespace = args.namespace
    if namespace:
        namespace = namespace.lstrip()
    else:
        namespace = 'http://www.iso.org/iso21926"'

    ncdng = args.encoding
    if ncdng:
        ncdng = ncdng.lstrip()
    else:
        ncdng = "UTF-8"

    XPATH = args.xpath
    VERBOSE = args.verbose
    DEBUG = args.debug

    # ====================================================================
    # 1. csv -> schema
    # ROOT_IDs = selected_roots
    records = []
    adcDict = {}
    classDict = {}
    abbreviationDict = {}
    columnnameDict = {}
    xpathDict = {}

    core_file = file_path(core_file)
    level_presentation = [None] * 10

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
        "semanticPath",
        "abbreviationPath",
        "labelLocal",
        "definitionLocal",
        "xpath"
    ]

    with open(core_file, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader)
        semSort = 1000
        for cols in reader:
            record = {}
            for i in range(len(header)):
                col = cols[i]
                record[header[i]] = col.strip()
            semPath = record["path"]
            if not semPath:
                continue
            # get root id from semantic path and check format
            id = semPath.strip("/").split("/")[0]
            match = re.search(r"([A-Z]+\d{2})", id)
            if match:
                root_id = match.group(1)
                if root != root_id:
                    continue
            else:
                continue
            cor_id = semPath[1 + semPath.rindex("/") :]
            semSort = record["sequence"]
            _type = record["type"]
            identifier = record["identifier"]
            level = int(record["level"])
            objectClass = record["classTerm"]
            multiplicity = record["multiplicity"]
            name = record["name"]
            datatype = record["datatype"]
            semanticPath = record["semanticPath"]
            abbreviationPath = record["abbreviationPath"]
            data = {}
            data["semSort"] = int(semSort)
            if "REF" == identifier:
                data["level"] = level - 1
            else:
                data["level"] = level
            data["type"] = _type
            data["identifier"] = identifier
            data["name"] = name
            data["semPath"] = semPath
            data["cor_id"] = cor_id
            data["objectClass"] = objectClass
            data["multiplicity"] = multiplicity
            data["semanticPath"] = semanticPath
            data["abbreviationPath"] = abbreviationPath
            if datatype in datatypeMap:
                data["datatype"] = f"cor:{datatypeMap[datatype]['cor']}"
            else:
                data["datatype"] = f"xbrli:stringItemType"
            if "C" == _type:
                class_id = cor_id
            data["definition"] = record["definition"]
            data["labelLocal"] = record["labelLocal"]
            data["definitionLocal"] = record["definitionLocal"]
            abbreviationName = abbreviationPath.replace(".", "_")
            if '.' in abbreviationPath:
                abbreviationName = abbreviationName[1 + abbreviationName.index('_'):]
                column_name = semanticPath[3 + semanticPath[2:].index('.'):]
            else:
                column_name = semanticPath[2:]
            abbreviationDict[cor_id] = abbreviationName
            columnnameDict[abbreviationName] = column_name            
            if XPATH:
                xpath = None
                if record["xpath"]:
                    xpath = record["xpath"]
                    if ':' in xpath:
                        xpath = xpath[1+xpath.index(':'):]
                    if '@' in xpath:
                        xpath = xpath.replace('@','_')
                    data["xpath"] = xpath
                else:
                    xpath = abbreviationName
                xpathDict[abbreviationName] = xpath
            else:
                xpath = abbreviationPath          
            parent = None
            level_presentation[level] = cor_id
            if int(level) > 1:
                """presentation link"""
                if "C" == _type:
                    data["children_pre"] = []
                    if level > 1:
                        parent = level_presentation[level - 1]
                    data["parent_pre"] = parent
                    if "children_pre" not in adcDict[parent]:
                        adcDict[parent]["children_pre"] = []
                    adcDict[parent]["children_pre"].append(cor_id)
                else:
                    parent = level_presentation[level - 1]
                    data["parent_pre"] = parent
                    if "children_pre" not in adcDict[parent]:
                        adcDict[parent]["children_pre"] = []
                    adcDict[parent]["children_pre"].append(cor_id)
                """ definition link """
                if "C" == _type:
                    data["children"] = []
                ancestor = semPath[: semPath.rindex("/")]
                if ancestor:
                    parent = ancestor[1 + ancestor.rindex("/") :]
                data["parent"] = parent
                if "children" not in adcDict[parent]:
                    adcDict[parent]["children"] = []
                adcDict[parent]["children"].append(cor_id)
            data["class_id"] = class_id
            adcDict[cor_id] = data
            if DEBUG:
                print(
                    f"{core_file[1+core_file.rindex(SEP):]} {level} {cor_id} {semPath} {abbreviationPath}"
                )
            if '.' in abbreviationPath:
                abbreviationPath = abbreviationPath[1+abbreviationPath.index('.'):]
            records.append(data)

    targetRefDict = {}  # child-parent
    for cor_id, record in adcDict.items():
        if "C" == record["type"] and "children" in record:
            children = record["children"]
            for child_id in children:
                child = getRecord(child_id)
                if "C" == child["type"] and child["multiplicity"].endswith("*"):
                    targetRefDict[child_id] = getSchemaID(cor_id)

    roleMap = {}
    for cor_id, record in adcDict.items():
        if "C" == record["type"]:
            roleMap[abbreviationDict[cor_id]] = record  # roleRecord(record)

    ###################################
    # core.xsd
    #
    html_head = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        "<!-- (c) 2025 XBRL Japan  inc. -->\n",
        "<schema \n",
        f'\ttargetNamespace="{namespace}" \n',
        '\telementFormDefault="qualified" \n',
        '\tattributeFormDefault="unqualified" \n',
        '\txmlns="http://www.w3.org/2001/XMLSchema" \n',
        f'\txmlns:cor="{namespace}" \n',
        '\txmlns:xlink="http://www.w3.org/1999/xlink" \n',
        '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \n',
        '\txmlns:xl="http://www.xbrl.org/2003/XLink" \n',
        '\txmlns:xbrli="http://www.xbrl.org/2003/instance" \n',
        '\txmlns:link="http://www.xbrl.org/2003/linkbase" \n',
        '\txmlns:nonnum="http://www.xbrl.org/dtr/type/non-numeric" \n',
        '\txmlns:num="http://www.xbrl.org/dtr/type/numeric" \n',
        '\txmlns:xbrldt="http://xbrl.org/2005/xbrldt" \n',
        '\txmlns:label="http://xbrl.org/2008/label" \n',
        '\txmlns:reference="http://xbrl.org/2008/reference">\n',
        '\t<import namespace="http://www.xbrl.org/2003/instance" schemaLocation="http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd"/>\n',
        '\t<import namespace="http://www.xbrl.org/2003/linkbase" schemaLocation="http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"/>\n',
        '\t<import namespace="http://xbrl.org/2005/xbrldt" schemaLocation="http://www.xbrl.org/2005/xbrldt-2005.xsd"/>\n',
        '\t<import namespace="http://www.xbrl.org/dtr/type/numeric" schemaLocation="http://www.xbrl.org/dtr/type/numeric-2009-12-16.xsd"/>\n',
        '\t<import namespace="http://www.xbrl.org/dtr/type/non-numeric" schemaLocation="http://www.xbrl.org/dtr/type/nonNumeric-2009-12-16.xsd"/>\n',
        '\t<import namespace="http://xbrl.org/2008/label" schemaLocation="http://www.xbrl.org/2008/generic-label.xsd"/>\n',
        '\t<import namespace="http://xbrl.org/2008/reference" schemaLocation="http://www.xbrl.org/2008/generic-reference.xsd"/> \n',
    ]
    lines = html_head

    """ linkbaseRef """
    html_annotation_head = [
        "\t<annotation>\n",
        "\t\t<appinfo>\n",
        f'\t\t\t<link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/labelLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="{out}-lbl-en.xml"/>\n',
        f'\t\t\t<link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/labelLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="{out}-lbl-{lang}.xml"/>\n',
        f'\t\t\t<link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/presentationLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="{out}-pre.xml"/>\n',
        f'\t\t\t<link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/definitionLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="{out}-def.xml"/>\n',
        # '\t\t\t<!-- reference -->\n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/referenceLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-ref-sme.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/referenceLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-ref-jp-pint.xml"/> \n'
        # '\t\t\t<!-- formula -->\n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-Base.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-GL.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-O2C.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-P2P.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-Core.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-Base.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-GL.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-O2C.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-P2P.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-Core.xml"/> \n',
    ]
    lines += html_annotation_head

    """ role type """
    html = [
        "\t\t\t<!-- \n",
        "\t\t\t\trole type\n",
        "\t\t\t-->\n"
        f'\t\t\t<link:roleType id="core-role" roleURI="{namespace}/role">\n',
        f"\t\t\t\t<link:definition>link core</link:definition>\n",
        f"\t\t\t\t<link:usedOn>link:presentationLink</link:usedOn>\n",
        "\t\t\t</link:roleType>\n",
    ]
    for cor_id, record in roleMap.items():
        role = roleRecord(record)
        role_id = role["role_id"]
        URI = role["URI"]
        link_id = role["link_id"]
        html.append(
            f'\t\t\t<link:roleType id="{role_id}" roleURI="{namespace}/role{URI}">\n'
        )
        html.append(f"\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n")
        html.append("\t\t\t</link:roleType>\n")
    lines += html

    # html = [
    #     '\t\t\t<!-- \n',
    #     '\t\t\t\tsemantic binding: roleType for referemceLink \n',
    #     '\t\t\t--> \n',
    #     f'\t\t\t<link:roleType id="semantic-binding" roleURI="{namespace}/role/semantic-binding"> \n',
    #     '\t\t\t\t<link:definition>semantic binding</link:definition> \n',
    #     '\t\t\t\t<link:usedOn>link:referenceLink</link:usedOn> \n',
    #     '\t\t\t</link:roleType> \n',
    #     '\t\t\t<!-- \n',
    #     '\t\t\t\tsyntax binding: roleType for referemceLink \n',
    #     '\t\t\t--> \n',
    #     f'\t\t\t<link:roleType id="syntax-binding" roleURI="{namespace}/role/syntax-binding"> \n',
    #     '\t\t\t\t<link:definition>syntax binding</link:definition> \n',
    #     '\t\t\t\t<link:usedOn>link:referenceLink</link:usedOn> \n',
    #     '\t\t\t</link:roleType> \n',
    # ]
    # lines += html

    """ description: roleType arcroleType """
    html = [
        "\t\t\t<!--\n",
        "\t\t\t\tdescription: roleType arcroleType\n",
        "\t\t\t-->\n"
        f'\t\t\t<link:roleType id="description" roleURI="{namespace}/role/description">\n',
        "\t\t\t\t<link:definition>description</link:definition>\n",
        "\t\t\t\t<link:usedOn>link:label</link:usedOn>\n",
        "\t\t\t</link:roleType>\n",
        f'\t\t\t<link:arcroleType id="concept-description" cyclesAllowed="undirected" arcroleURI="{namespace}/arcrole/concept-description">\n',
        "\t\t\t\t<link:definition>concept to description</link:definition>\n",
        "\t\t\t\t<link:usedOn>link:labelArc</link:usedOn>\n",
        "\t\t\t</link:arcroleType >\n",
    ]
    lines += html

    # html = [
    #     '\t\t\t<!--\n',
    #     '\t\t\t\tprimary key: roleType arcroleType\n',
    #     '\t\t\t-->\n'
    #     f'\t\t\t<link:roleType id="primary-key" roleURI="{namespace}/role/primary-key">\n',
    #     '\t\t\t\t<link:definition>primary key</link:definition>\n',
    #     '\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n',
    #     '\t\t\t</link:roleType>\n',
    #     f'\t\t\t<link:arcroleType id="concept-primary-key" cyclesAllowed="undirected" arcroleURI="{namespace}/arcrole/concept-primary-key">\n',
    #     '\t\t\t\t<link:definition>concept primary key</link:definition>\n',
    #     '\t\t\t\t<link:usedOn>link:definitionArc</link:usedOn>\n',
    #     '\t\t\t</link:arcroleType >\n',
    # ]
    # lines += html

    # html = [
    #     '\t\t\t<!--\n',
    #     '\t\t\t\treference identifier: roleType arcroleType\n',
    #     '\t\t\t-->\n'
    #     f'\t\t\t<link:roleType id="reference-identifier" roleURI="{namespace}/role/reference-identifier">\n',
    #     '\t\t\t\t<link:definition>reference identifier</link:definition>\n',
    #     '\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n',
    #     '\t\t\t</link:roleType>\n',
    #     f'\t\t\t<link:arcroleType id="concept-reference-identifier" cyclesAllowed="undirected" arcroleURI="{namespace}/arcrole/concept-reference-identifier">\n',
    #     '\t\t\t\t<link:definition>concept reference identifier</link:definition>\n',
    #     '\t\t\t\t<link:usedOn>link:definitionArc</link:usedOn>\n',
    #     '\t\t\t</link:arcroleType >\n',
    # ]
    # lines += html

    # html = [
    #     '\t\t\t<!--\n',
    #     '\t\t\t\trequire: roleType\n',
    #     '\t\t\t-->\n'
    #     f'\t\t\t<link:roleType id="require" roleURI="{namespace}/role/require">\n',
    #     '\t\t\t\t<link:definition>require</link:definition>\n',
    #     '\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n',
    #     '\t\t\t</link:roleType>\n',
    # ]
    # lines += html

    html_annotation_tail = ["\t\t</appinfo>\n", "\t</annotation>\n"]
    lines += html_annotation_tail

    """ typed dimension referenced element """
    html_type = [
        "\t<!-- typed dimension referenced element -->\n",
        '\t<element name="_v" id="_v">\n',
        "\t\t<simpleType>\n",
        '\t\t\t<restriction base="string"/>\n',
        "\t\t</simpleType>\n",
        "\t</element>\n",
        # '\t<element name="_activity" id="_activity">\n',
        # '\t\t<simpleType>\n',
        # '\t\t\t<restriction base="string">\n',
        # '\t\t\t\t<pattern value="\s*(Created|Approved|LastModified|Entered|Posted)\s*"/>\n',
        # '\t\t\t</restriction>\n',
        # '\t\t</simpleType>\n',
        # '\t</element>\n'
    ]
    lines += html_type

    # html_part_type = [
    #     '\t<!-- reference part element -->\n',
    #     '\t<!-- semantic-model -->\n',
    #     '\t<element name="id" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="semantic_sort" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="section" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="cardinality" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="aligned_cardinality" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="semantic_datatype" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="business_term" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="business_term_ja" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="description" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="description_ja" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="example" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="xpath" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<!-- syntax-binding -->\n',
    #     '\t<element name="element" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="syntax_sort" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="syntax_cardinality" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="parent_xpath" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="syntax_parent_sort" type="string" substitutionGroup="link:part"/>\n',
    #     '\t<element name="syntax_parent_cardinality" type="string" substitutionGroup="link:part"/>\n',
    # ]
    # lines += html_part_type

    # Hypercube
    html_hypercube = ["\t<!-- Hypercube -->\n"]
    for cor_id, record in roleMap.items():
        role = roleRecord(record)
        link_id = role["link_id"]
        link_id = getSchemaID(link_id)
        html_hypercube.append(
            f'\t<element name="h_{link_id}" id="h_{link_id}" substitutionGroup="xbrldt:hypercubeItem" type="xbrli:stringItemType" nillable="true" abstract="true" xbrli:periodType="instant"/>\n'
        )
    lines += html_hypercube

    # Dimension
    html_dimension = ["\t<!-- Dimension -->\n"]
    for cor_id, record in roleMap.items():
        role = roleRecord(record)
        link_id = role["link_id"]
        link_id = getSchemaID(link_id)
        html_dimension.append(
            f'\t<element name="d_{link_id}" id="d_{link_id}" substitutionGroup="xbrldt:dimensionItem" type="xbrli:stringItemType" abstract="true" xbrli:periodType="instant" xbrldt:typedDomainRef="#_v"/>\n'
        )
    lines += html_dimension

    # item complexType
    html_itemtype = ["\t<!-- item type -->\n"]
    complexType = [
        '\t<complexType name="stringItemType">\n',
        "\t\t<simpleContent>\n",
        '\t\t\t<restriction base="xbrli:stringItemType"/>\n',
        "\t\t</simpleContent>\n",
        "\t</complexType>\n",
    ]
    html_itemtype += complexType
    definedType = []
    for name, type in datatypeMap.items():
        cor = type["cor"]
        xbrli = type["xbrli"]
        if cor not in definedType:
            complexType = [
                f'\t<complexType name="{cor}">\n',
                "\t\t<simpleContent>\n",
                f'\t\t\t<restriction base="xbrli:{xbrli}"/>\n',
                "\t\t</simpleContent>\n",
                "\t</complexType>\n",
            ]
            definedType.append(cor)
            html_itemtype += complexType
    lines += html_itemtype

    # element
    lines.append("\t<!-- element -->\n")
    elementsDefined = set()
    primaryKeys = {}
    for cor_id, record in adcDict.items():
        defineElement(cor_id, record)

    lines.append("</schema>")

    cor_xsd_file = file_path(f"{xbrl_base}/{core_xsd}")
    with open(cor_xsd_file, "w", encoding="utf-8-sig", newline="") as f:
        f.writelines(lines)
    if VERBOSE:
        print(f"-- {cor_xsd_file}")

    ###################################
    # labelLink en
    #
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        "<!--  (c) 2025 XBRL Japan inc. -->\n",
        "<link:linkbase\n",
        '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '\txmlns:xlink="http://www.w3.org/1999/xlink"\n',
        '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd">\n',
        f'\t<link:roleRef roleURI="{namespace}/role/description" xlink:type="simple" xlink:href="{core_xsd}#description"/>\n',
        f'\t<link:arcroleRef arcroleURI="{namespace}/arcrole/concept-description" xlink:type="simple" xlink:href="{core_xsd}#concept-description"/>\n',
        '\t<link:labelLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">\n',
    ]
    locsDefined = {}
    arcsDefined = {}
    definedLabels = {}
    definedDescs = {}
    definedDescArcs = {}

    for cor_id, record in adcDict.items():
        name = record["name"]
        desc = record["definition"] if "definition" in record else None
        linkLabel(cor_id, name, desc, "en")

    lines.append("\t</link:labelLink>\n")
    lines.append("</link:linkbase>\n")

    cor_label_file = file_path(f"{xbrl_base}/{core_label}-en.xml")
    with open(cor_label_file, "w", encoding="utf-8-sig", newline="") as f:
        f.writelines(lines)
    if VERBOSE:
        print(f"-- {cor_label_file}")

    ###################################
    # labelLink lang
    #
    if lang:
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>\n',
            "<!--  (c) 2025 XBRL Japan inc. -->\n",
            "<link:linkbase\n",
            '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
            '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
            '\txmlns:xlink="http://www.w3.org/1999/xlink"\n',
            '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd">\n',
            f'\t<link:roleRef roleURI="{namespace}/role/description" xlink:type="simple" xlink:href="{core_xsd}#description"/>\n',
            f'\t<link:arcroleRef arcroleURI="{namespace}/arcrole/concept-description" xlink:type="simple" xlink:href="{core_xsd}#concept-description"/>\n',
            '\t<link:labelLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">\n',
        ]
        locsDefined = {}
        arcsDefined = {}
        definedLabels = {}
        definedDescs = {}
        definedDescArcs = {}

        for cor_id, record in adcDict.items():
            name = record["labelLocal"] if "labelLocal" in record else None
            desc = record["definitionLocal"] if "definitionLocal" in record else None
            if len(name) > 0:
                linkLabel(cor_id, name, desc, lang)

        lines.append("\t</link:labelLink>\n")
        lines.append("</link:linkbase>\n")

        cor_label_file = file_path(f"{xbrl_base}/{core_label}-{lang}.xml")
        with open(cor_label_file, "w", encoding="utf-8-sig", newline="") as f:
            f.writelines(lines)
        if VERBOSE:
            print(f"-- {cor_label_file}")

    ###################################
    #   presentationLink
    #
    locsDefined = {}
    arcsDefined = {}
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        "<!--  (c) 2025 XBRL Japan inc. -->\n",
        "<link:linkbase\n",
        '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"\n',
        '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '\txmlns:xlink="http://www.w3.org/1999/xlink">\n',
        f'\t<link:roleRef roleURI="{namespace}/role" xlink:type="simple" xlink:href="{core_xsd}#core-role"/>\n',
        f'\t<link:presentationLink xlink:type="extended" xlink:role="{namespace}/role">\n',
    ]
    locsDefined = {}
    arcsDefined = {}
    class_records = [x for x in records if "C" == x["type"]]
    for record in class_records:
        cor_id = record["cor_id"]
        propertyType = record["type"]
        count = 0
        children = record["children_pre"]
        linkPresentation(cor_id, children, 1)

    lines.append("\t</link:presentationLink>\n")
    lines.append("</link:linkbase>\n")

    cor_presentation_file = file_path(f"{xbrl_base}/{core_presentation}.xml")
    with open(cor_presentation_file, "w", encoding="utf-8-sig", newline="") as f:
        f.writelines(lines)
    if VERBOSE:
        print(f"-- {cor_presentation_file}")

    ###################################
    # definitionLink
    #
    locsDefined = {}
    arcsDefined = {}
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        "<!--(c) 2025 XBRL Japan inc. -->\n",
        "<link:linkbase\n",
        '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"\n',
        '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '\txmlns:xbrldt="http://xbrl.org/2005/xbrldt"\n',
        '\txmlns:xlink="http://www.w3.org/1999/xlink">\n',
    ]
    lines.append("\t<!-- roleRef -->\n")

    for record in roleMap.values():
        role = roleRecord(record)
        role_id = role["role_id"]
        # link_id = role['link_id']
        URI = f"/{role_id}"
        lines.append(
            f'\t<link:roleRef roleURI="{namespace}/role{URI}" xlink:type="simple" xlink:href="{core_xsd}#{role_id}"/>\n'
        )
    html = [
        # f'\t<link:roleRef roleURI="{namespace}/role/primary-key" xlink:type="simple" xlink:href="{core_xsd}#primary-key"/>\n',
        # f'\t<link:roleRef roleURI="{namespace}/role/reference-identifier" xlink:type="simple" xlink:href="{core_xsd}#reference-identifier"/>\n',
        # f'\t<link:roleRef roleURI="{namespace}/role/require" xlink:type="simple" xlink:href="{core_xsd}#require"/>\n',
        "\t<!-- arcroleRef -->\n",
        '\t<link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/all" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#all"/>\n',
        '\t<link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/domain-member" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#domain-member"/>\n',
        '\t<link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/hypercube-dimension" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#hypercube-dimension"/>\n',
        '\t<link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/dimension-domain" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#dimension-domain"/>\n',
        # f'\t<link:arcroleRef arcroleURI="{namespace}/arcrole/concept-primary-key" xlink:type="simple" xlink:href="{core_xsd}#concept-primary-key"/>\n',
        # f'\t<link:arcroleRef arcroleURI="{namespace}/arcrole/concept-reference-identifier" xlink:type="simple" xlink:href="{core_xsd}#concept-reference-identifier"/>\n',
    ]
    lines += html

    for cor_id, record in roleMap.items():
        # role = roleRecord(record)
        count = 0
        defineHypercube(record)

    lines.append("</link:linkbase>\n")

    cor_definition_file = file_path(f"{xbrl_base}/{core_definition}.xml")
    with open(cor_definition_file, "w", encoding="utf-8-sig", newline="") as f:
        f.writelines(lines)
    if VERBOSE:
        print(f"-- {cor_definition_file}")

    ###################################
    # referenceLink SME Common EDI
    #
    # lines = []
    # html = [
    #     '<?xml version="1.0" encoding="UTF-8"?>\n',
    #     '<!--  (c) 2025 XBRL Japan inc. -->\n',
    #     '<link:linkbase\n',
    #     '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
    #     f'\txmlns:cor="{namespace}"\n',
    #     '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
    #     '\txmlns:xlink="http://www.w3.org/1999/xlink"\n',
    #     f'\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd {namespace} core.xsd">\n',
    #     '\t<link:roleRef roleURI="http://www.xbrl.jp/peppol/invoice" xlink:type="simple" xlink:href="core.xsd#invoice"/>\n',
    #     '\t<link:referenceLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">\n'
    # ]
    # lines += html

    # for record in adcDict.values():
    #     cor_id        = record['cor_id']
    #     seqSme        = record['seqSme'] # '1'
    #     idSme         = record['idSme'] # ''
    #     kindSme       = record['kindSme'] # 'MA'
    #     termSme       = record['termSme'] # 'Invoice'
    #     termSme_ja    = record['termSme_ja'] # '統合請求書'
    #     defSme_ja     = record['defSme_ja'] # '受注者が発注者に交付する統合請求文書（メッセージ）'
    #     cardSme       = record['cardSme'] if '-'!=record['cardSme'] else '' # '－'
    #     fixedValueSme = record['fixedValueSme'] # ''
    #     xPathSme      = record['xPathSme'] # '/SMEInvoice'
    #     html = [
    #         f'\t\t<!-- {cor_id} {termSme} --> \n',
    #         f'\t\t<link:loc xlink:type="locator" xlink:href="core.xsd#{cor_id}" xlink:label="{cor_id}"/> \n',
    #         f'\t\t<link:referenceArc xlink:type="arc" xlink:from="{cor_id}" xlink:to="{cor_id}_REF" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-reference"/> \n',
    #         f'\t\t<link:reference xlink:type="resource" xlink:label="{cor_id}_REF" xlink:role="{namespace}/role/semantic-binding"> \n',
    #         f'\t\t\t<cor:id>{cor_id}</cor:id> \n',
    #         f'\t\t\t<!--cor:cardinality>1..1</cor:cardinality--> \n',
    #         f'\t\t\t<cor:business_term>{termSme}</cor:business_term> \n',
    #         f'\t\t\t<cor:business_term_ja>{termSme_ja}</cor:business_term_ja> \n',
    #         f'\t\t\t<!--cor:description>Commercial invoice</cor:description--> \n',
    #         f'\t\t\t<cor:description_ja>{defSme_ja}</cor:description_ja> \n',
    #         f'\t\t</link:reference> \n',
    #         f'\t\t<link:reference xlink:type="resource" xlink:label="{cor_id}_REF" xlink:role="{namespace}/role/syntax-binding"> \n',
    #         f'\t\t\t<cor:element>{xPathSme}</cor:element> \n',
    #         f'\t\t\t<cor:syntax_sort>{seqSme}</cor:syntax_sort> \n',
    #         f'\t\t\t<cor:syntax_cardinality>{cardSme}</cor:syntax_cardinality> \n',
    #         f'\t\t</link:reference> \n',
    #     ]
    #     lines += html

    # lines.append('</link:referenceLink> \n')
    # lines.append('</link:linkbase> \n')

    # cor_referemce_file_sme = file_path(f'{xbrl_base}/{core_reference}-sme.xml')
    # with open(cor_referemce_file_sme, 'w', encoding='utf-8-sig', newline='') as f:
    #     f.writelines(lines)
    # if VERBOSE:
    #     print(f'-- {cor_referemce_file_sme}')

    ###################################
    # referenceLink JP PINT
    #
    # lines = []
    # html = [
    #     '<?xml version="1.0" encoding="UTF-8"?>\n',
    #     '<!--  (c) 2025 XBRL Japan inc. -->\n',
    #     '<link:linkbase\n',
    #     '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
    #     f'\txmlns:cor="{namespace}"\n',
    #     '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
    #     '\txmlns:xlink="http://www.w3.org/1999/xlink"\n',
    #     '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd {namespace} core.xsd">\n',
    #     f'\t<link:roleRef roleURI="{namespace}/role/semantic-binding" xlink:type="simple" xlink:href="core.xsd#semantic-binding"/>\n',
    #     f'\t<link:roleRef roleURI="{namespace}/role/syntax-binding" xlink:type="simple" xlink:href="core.xsd#syntax-binding"/>\n',
    #     '\t<link:referenceLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">\n'
    # ]
    # lines += html

    # for record in adcDict.values():
    #     cor_id         = record['cor_id']
    #     seqPint        = record['seqPint'] # '1'
    #     idPint         = record['idPint'] # ''
    #     levelPint      = record['levelPint'] # ''
    #     termPint_ja    = record['termPint_ja'] # '請求書'
    #     termPint       = record['termPint'] # ''
    #     cardPint       = record['cardPint'] # ''
    #     fixedValuePint = record['fixedValuePint'] # ''
    #     xPathPint      = record['xPathPint'] # ''
    #     if not xPathPint:
    #         continue
    #     html = [
    #         f'\t\t<!-- {cor_id} {termPint} --> \n',
    #         f'\t\t<link:loc xlink:type="locator" xlink:href="core.xsd#{cor_id}" xlink:label="{cor_id}"/> \n',
    #         f'\t\t<link:referenceArc xlink:type="arc" xlink:from="{cor_id}" xlink:to="{cor_id}_REF" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-reference"/> \n',
    #         f'\t\t<link:reference xlink:type="resource" xlink:label="{cor_id}_REF" xlink:role="{namespace}/role/semantic-binding"> \n',
    #         f'\t\t\t<cor:id>{cor_id}</cor:id> \n',
    #         f'\t\t\t<!--cor:cardinality>1..1</cor:cardinality--> \n',
    #         f'\t\t\t<cor:business_term>{termPint}</cor:business_term> \n',
    #         f'\t\t\t<cor:business_term_ja>{termPint_ja}</cor:business_term_ja> \n',
    #          f'\t\t\t<!--cor:description>Commercial invoice</cor:description--> \n',
    #         f'\t\t\t<!--cor:description_ja>defPint_ja</cor:description_ja--> \n',
    #         f'\t\t</link:reference> \n',
    #         f'\t\t<link:reference xlink:type="resource" xlink:label="{cor_id}_REF" xlink:role="{namespace}/role/syntax-binding"> \n',
    #         f'\t\t\t<cor:syntax_sort>{seqPint}</cor:syntax_sort> \n',
    #         f'\t\t\t<cor:element>{xPathPint}</cor:element> \n',
    #         f'\t\t\t<cor:syntax_cardinality>{cardPint}</cor:syntax_cardinality> \n',
    #         f'\t\t</link:reference> \n',
    #     ]
    #     lines += html

    # lines.append('\t</link:referenceLink>\n')
    # lines.append('</link:linkbase> \n')

    # cor_referemce_file_jp_pint = file_path(f'{xbrl_base}/{core_reference}-jp-pint.xml')
    # with open(cor_referemce_file_jp_pint, 'w', encoding='utf-8-sig', newline='') as f:
    #     f.writelines(lines)
    # if VERBOSE:
    #     print(f'-- {cor_referemce_file_jp_pint}')

    """
    xBRL-CSV
    {
        "documentInfo": {
            "documentType": "https://xbrl.org/2021/xbrl-csv",
            "namespaces": {
                "cor": "http://www.xbrl.org/int/gl/2025-03-31",
                "ns0": "http://www.example.com",
                "link": "http://www.xbrl.org/2003/linkbase",
                "iso4217": "http://www.xbrl.org/2003/iso4217",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xbrli": "http://www.xbrl.org/2003/instance",
                "xbrldi": "http://xbrl.org/2006/xbrldi",
                "xlink": "http://www.w3.org/1999/xlink",
            },
            "taxonomy": ["timesheet.xsd"],
        },
        "tableTemplates": {
            "xbrl-gl_template": {
                "dimensions": {
                    "cor:d_AccntEntrsTs": "$AccntEntrsTs",
                    "cor:d_AccntEntrsTs_DocInfrmTs": "$DocInfrmTs",
                    "period": "2025-01-17T00:00:00",
                    "entity": "ns0:Example Co.",
                },
                "columns": {
                    "AccntEntrsTs": {},
                    "DocInfrmTs": {},
                    "DocInfrmTs_DocTyp": {
                        "dimensions": {"concept": "cor:AccntEntrsTs_DocInfrmTs_DocTyp"}
                    },
                    "EntryHedrTs_EntryDetlTs_MesrbTs_UntPrc_ValAmt_Val": {
                        "dimensions": {
                            "concept": "cor:AccntEntrsTs_EntryHedrTs_EntryDetlTs_MesrbTs_UntPrc_ValAmt_Val",
                            "unit": "iso4217:USD"
                        }
                    },
                },
            }
        },
        "tables": {
            "xbrl-gl_table": {"template": "xbrl-gl_template", "url": "timesheet.csv"}
        },
    }
    """
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
            }
        },
        "tableTemplates": {
            "xbrl-gl_template": {
                "dimensions": {
                    "period": "2025-01-17T00:00:00",
                    "entity": "ns0:Example Co.",
                },
                "columns": {
                }
            }
        },
        "tables": {
            "xbrl-gl_table": {"template": "xbrl-gl_template"}
        }
    }
    json_meta["documentInfo"]["namespaces"]["cor"] = namespace
    json_meta["documentInfo"]["taxonomy"] = [f"{out}.xsd"]


    if root: 
        dimension_columns = []
        property_columns = []
        root_class = [abbreviationDict[r["cor_id"]] for r in adcDict.values() if root in r["semPath"] and not r["multiplicity"]][0]
        dimensions = [abbreviationDict[r["cor_id"]] for r in adcDict.values() if root in r["semPath"] and "A" != r["type"] and r["multiplicity"] and "*" == r["multiplicity"][-1]]
        properties = [abbreviationDict[r["cor_id"]] for r in adcDict.values() if root in r["semPath"] and "A" == r["type"]]
        if XPATH:
            root_class = xpathDict[root_class]
            dimensions = [xpathDict[d] for d in dimensions]
            properties = [xpathDict[p] for p in properties]

        json_meta["tableTemplates"]["xbrl-gl_template"]["dimensions"][f"cor:d_{root_class}"] = f"${root_class}"
        json_meta["tableTemplates"]["xbrl-gl_template"]["columns"][root_class] = {}

        for dimension in dimensions:
            dimension_column = dimension #[1+dimension.index('_'):]
            dimension_columns.append(dimension_column)
            json_meta["tableTemplates"]["xbrl-gl_template"]["dimensions"] [f"cor:d_{dimension}"] = f"${dimension_column}"
            json_meta["tableTemplates"]["xbrl-gl_template"]["columns"][dimension_column] = {}

        for property in properties:
            property_column = property #[1+property.index('_'):]
            property_columns.append(property_column)
            if property.endswith('Amt_Val'):
                json_meta["tableTemplates"]["xbrl-gl_template"]["columns"][property_column] = {"dimensions": {"concept": f"cor:{property}", "unit": f"iso4217:{currency}"}}
            else:
                json_meta["tableTemplates"]["xbrl-gl_template"]["columns"][property_column] = {"dimensions": {"concept": f"cor:{property}"}}

        csv_file = f"{out}_skeleton.csv"
        json_meta["tables"]["xbrl-gl_table"]["url"] = csv_file

        json_meta_file = file_path(f"{xbrl_base}/{out}.json")
        try:
            with open(json_meta_file, "w", encoding="utf-8") as file:
                json.dump(json_meta, file, ensure_ascii=False, indent=4)
            print(f"JSON file '{json_meta_file}' has been created successfully.")
        except Exception as e:
            print(f"An error occurred while creating the JSON file: {e}")
        if VERBOSE:
            print(f"-- JSON meta file {json_meta_file}")
        out_file = file_path(f"{xbrl_base}/{csv_file}")
        header_list = [root_class] + dimension_columns + property_columns
        if not XPATH:
            columnname_list = [columnnameDict[x] for x in header_list]
            xpath_list = [xpathDict[x.replace('_','.')] if x.replace('_','.') in xpathDict else "" for x in header_list]
        try:
            with open(out_file, "w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                # Write the header and columnname rows
                writer.writerow(header_list)
                if not XPATH:
                    writer.writerow(columnname_list)
                    writer.writerow(xpath_list)
            print(f"CSV template file '{out_file}' has been created successfully.")
        except Exception as e:
            print(f"An error occurred while creating the JSON file: {e}")
        if VERBOSE:
            print(f"-- CSV file with header {csv_file}")    

    print("** END **")
