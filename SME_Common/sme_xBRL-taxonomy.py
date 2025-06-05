#!/usr/bin/env python3
# coding: utf-8
"""
generate Audit Data Collection xBRL-GD Taxonomy fron HMD CSV file and header files

designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

MIT License

(c) 2023,2024 SAMBUICHI Nobuyuki (Sambuichi Professional Engineers Office)

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
import re

from common.utils import (
    LC3,
    titleCase,
    SC, # snake concatenate
    file_path,
    is_file_in_use,
    split_camel_case,
    abbreviate_term,
    normalize_text,
)

DEBUG = False
TRACE = True
SEP = os.sep

core_xsd           = 'core.xsd'
core_label         = 'core-lbl'
core_presentation  = 'core-pre'
core_definition    = 'core-def'
core_reference     = 'core-ref'


datatypeMap = {
    "Amount": {"cor": "amountType", "xbrli": "monetaryItemType"},
    "Code": {"cor": "codeType", "xbrli": "tokenItemType"},
    "Date Time": {"cor": "datetimeType", "xbrli": "dateTimeItemType"},
    "Identifier": {"cor": "identifierType", "xbrli": "tokenItemType"},
    "Indicator": {"cor": "indicatorType", "xbrli": "booleanItemType"},
    "Percent": {"cor": "percentType", "xbrli": "pureItemType"},
    "Quantity": {"cor": "quantityType", "xbrli": "decimalItemType"},
    "Rate": {"cor": "rateType", "xbrli": "decimalItemType"},
    "Text": {"cor": "textType", "xbrli": "stringItemType"},
}

duplicateNames  = set()
names           = set()
adcDict         = {}
targetRefDict   = {}
associationDict = {}
referenceDict   = {}
sourceRefDict   = {}
locsDefined     = {}
arcsDefined     = {}
locsDefined     = {}
alias           = {}
targets         = {}
roleMap         = None
primaryKeys     = set()


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
        return record['children']
    return []


def checkAssociation(id,link_id,lines,source_id=None):
    global count
    child = getRecord(id)
    child_property = child['type']
    child_name = child['name']
    child_id = LC3(child_name)
    if 'C'==child_property and id in targetRefDict:
        # targetRole
        role_record = roleRecord(child)
        role_id     = role_record['role_id']
        URI         = role_record['URI']
        if DEBUG: print(f'domain-member: {link_id} to {child_id} ({child_name}) order={count} in {role_id} targetRole="http://www.iso.org/iso21926/role{URI}')
        lines.append(f'\t\t<!-- {child_id} targetRole {role_id} -->\n')
        if not child_id in locsDefined[link_id]:
            locsDefined[link_id].add(child_id)
            lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{child_id}" xlink:label="{child_id}" xlink:title="{child_id} ({child_name})"/>\n')
        count += 1
        arc_id = f'{link_id} {child_id}'
        if not arc_id in arcsDefined[link_id]:
            arcsDefined[link_id].add(arc_id)
            lines.append(f'\t\t<link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xbrldt:targetRole="http://www.iso.org/iso21926/role{URI}" xlink:from="{link_id}" xlink:to="{child_id}" xlink:title="domain-member: {link_id} to {child_id} in {role_id}" order="{count}"/>\n')
    else:
        if not source_id:
            source_id = link_id
        if DEBUG: print(f'domain-member: {source_id} to {child_id} ({child_name}) order={count}')
        if not child_id in locsDefined[link_id]:
            locsDefined[link_id].add(child_id)
            lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{child_id}" xlink:label="{child_id}" xlink:title="{child_id} ({child_name})"/>\n')
        count += 1
        arc_id = f'{source_id} {child_id}'
        if not arc_id in arcsDefined[link_id]:
            arcsDefined[link_id].add(arc_id)
            lines.append(f'\t\t<link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xlink:from="{source_id}" xlink:to="{child_id}" xlink:title="domain-member: {source_id} to {child_id} ({child_name})" order="{count}"/>\n')
    return lines


def defineHypercube(root):
    global lines
    global locsDefined
    global arcsDefined
    global targetRefDict
    global referenceDict

    dimension_id_list = []
    role = roleRecord(root)
    path = root['path']
    paths = path.strip('/').split('/')
    for id in paths:
        dimension_id = f"d_{id}"
        dimension_id_list.append(dimension_id)
    link_id = role['link_id']
    locsDefined[link_id] = set()
    arcsDefined[link_id] = set()
    URI = role['URI']
    role_id = role['role_id']
    hypercube_id = f"h_{link_id}"
    lines.append(f'\t<link:definitionLink xlink:type="extended" xlink:role="http://www.iso.org/iso21926/role{URI}">\n')
    # all (has-hypercube)
    lines.append(f'\t\t<!-- {link_id} all (has-hypercube) {hypercube_id} {role_id} -->\n')
    lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{link_id}" xlink:label="{link_id}" xlink:title="{link_id}"/>\n')
    lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{hypercube_id}" xlink:label="{hypercube_id}" xlink:title="{hypercube_id}"/>\n')
    lines.append(f'\t\t<link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/all" xlink:from="{link_id}" xlink:to="{hypercube_id}" xlink:title="all (has-hypercube): {link_id} to {hypercube_id}" order="1" xbrldt:closed="true" xbrldt:contextElement="segment"/>\n')
    if DEBUG:
        print(f'all(has-hypercube) {link_id} to {hypercube_id} ')
    # hypercube-dimension
    lines.append('\t\t<!-- hypercube-dimension -->\n')
    count = 0
    for id in dimension_id_list:
        dimension = getRecord(id[2:])
        dimension_name = dimension['name']
        dimension_id = f"d_{LC3(dimension_name)}"
        lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{dimension_id}" xlink:label="{dimension_id}" xlink:title="{dimension_id}"/>\n')
        count += 1
        lines.append(f'\t\t<link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/hypercube-dimension" xlink:from="{hypercube_id}" xlink:to="{dimension_id}" xlink:title="hypercube-dimension: {hypercube_id} to {dimension_id}" order="{count}"/>\n')
        if DEBUG:
            print(f'hypercube-dimension {hypercube_id} to {dimension_id} ')
    # domain-member
    lines.append('\t\t<!-- domain-member -->\n')
    if 'children' in root and len(root['children']) > 0:
        children = root['children']
        for child_id in children:
            lines = checkAssociation(child_id,link_id,lines)
    lines.append('\t</link:definitionLink>\n')


def lookupModule(class_id):
    module = None
    prefix = class_id[:2]
    if 'NC'==prefix:   module = 'Invoice'
    elif 'BS'==prefix: module = 'Base'
    elif 'GL'==prefix: module = 'GL'
    elif 'CM'==prefix: module = 'Common'
    return module


def roleRecord(record):
    cor_id      = record['name_id'] # record['cor_id']
    link_id     = cor_id
    role_id     = f'link_{link_id}'
    URI         = f'/{role_id}'
    role_record = {'cor_id':cor_id, 'link_id':link_id, 'URI':URI, 'role_id':role_id}
    return role_record


def get_element_datatype(cor_id,type,propertyType):
    if not type:
        type = 'xbrli:stringItemType'
        if DEBUG: print(f'{cor_id} [{propertyType}] type not defined assign xbrli:stringItemType.')
    elif not 'xbrli:' in type and not 'cor:'in type:
        if not type:
            type = 'xbrli:stringItemType'
            if DEBUG: print(f'{cor_id} [{propertyType}] type not defined assign xbrli:stringItemType.')
        else:
            type=F'cor:{type}'
    return type


def defineElement(id,record):
    global lines
    global elementsDefined
    if not id in elementsDefined:
        elementsDefined.add(id)
        name = record['name']
        cor_id = LC3(name)
        if not record:
            print(f'NOT DEFINED {cor_id} record')
            return
        propertyType = record['type']
        type = record['datatype'] if 'datatype' in record and record['datatype'] else ''
        if DEBUG: print(f'define {cor_id} [{propertyType}]')
        if "C"==propertyType:#.lower().endswith('class'):# or cor_id in targetRefDict or cor_id in referenceDict:
            line = f'\t<element name="{cor_id}" id="{cor_id}" abstract="true" type="xbrli:stringItemType" nillable="true" substitutionGroup="xbrli:item" xbrli:periodType="instant"/>\n'
        else:
            type = get_element_datatype(cor_id,type,propertyType)
            line = f'\t<element name="{cor_id}" id="{cor_id}" type="{type}" nillable="false" substitutionGroup="xbrli:item" xbrli:periodType="instant"/>\n'
        lines.append(line)


def linkLabel(id,label,desc,lang):
    global locsDefined
    global definedLabels
    global arcsDefined
    global definedDescs
    global definedDescArcs
    record = getRecord(id)
    name = record['name']
    cor_id = LC3(name)
    # label
    if label:
        lines.append(f'\t\t<!-- {cor_id} {label} -->\n')
        if not cor_id in locsDefined:
            locsDefined[cor_id] = cor_id
            line = f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{cor_id}" xlink:label="{cor_id}" xlink:title="{cor_id}"/>\n'
        else:
            line = f'\t\t\t<!-- link:loc defined -->\n'
        lines.append(line)
        # label
        if not cor_id in definedLabels:
            definedLabels[cor_id] = cor_id
            line = f'\t\t<link:label xlink:type="resource" xlink:label="label_{cor_id}" xlink:title="label_{cor_id}" id="label_{cor_id}" xml:lang="{lang}" xlink:role="http://www.xbrl.org/2003/role/label">{label}</link:label>\n'
        else:
            line = f'\t\t\t<!-- link:label http://www.xbrl.org/2003/role/label defined -->\n'
        lines.append(line)
        if not cor_id in arcsDefined:
            arcsDefined[cor_id] = cor_id
            line = f'\t\t<link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="{cor_id}" xlink:to="label_{cor_id}" xlink:title="label: {cor_id} to label_{cor_id}"/>\n'
        else:
            line = f'\t\t\t<!-- link:labelArc http://www.xbrl.org/2003/arcrole/concept-label defined -->\n'
        lines.append(line)
    # desc
    if desc:
        if not cor_id in definedDescs:
            definedDescs[cor_id] = cor_id
            line = f'\t\t<link:label xlink:type="resource" xlink:label="description_{cor_id}" xlink:title="description_{cor_id}" id="description_{cor_id}" xml:lang="{lang}" xlink:role="http://www.iso.org/iso21926/role/description">{desc}</link:label>\n'
        else:
            line = f'\t\t\t<!-- link:label http://www.iso.org/iso21926/role/description defined -->\n'
        lines.append(line)
        if not cor_id in definedDescArcs:
            definedDescArcs[cor_id] = cor_id
            line = f'\t\t<link:labelArc xlink:type="arc" xlink:arcrole="http://www.iso.org/iso21926/arcrole/concept-description" xlink:from="{cor_id}" xlink:to="description_{cor_id}" xlink:title="label: {cor_id} to label_{cor_id}"/>\n'
        else:
            line = f'\t\t\t<!-- link:labelArc http://www.iso.org/iso21926/arcrole/concept-description defined -->\n'
        lines.append(line)


def linkPresentation(id, children, n):
    global lines
    global count
    global locsDefined
    global arcsDefined
    record = getRecord(id)
    if not record:
        return
    name = record['name']
    cor_id = LC3(name)
    if not cor_id:
        return
    propertyType = record['type']
    name = record['name']
    if not cor_id in locsDefined:
        locsDefined[cor_id] = name
        lines.append(f'\t\t<!-- {propertyType} {cor_id} {name} -->\n')
        lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{cor_id}" xlink:label="{cor_id}" xlink:title="presentation: {cor_id} ({name})"/>\n')
    for id in children:
        child = getRecord(id)
        child_property = child['type']
        child_name = child['name']
        child_id = LC3(child_name)
        if "C"==child_property:#.lower().endswith('class'):
            target_id = child_id
            if not target_id in locsDefined:
                locsDefined[target_id] = child_name
                lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{target_id}" xlink:label="{target_id}" xlink:title="presentation parent: {target_id} ({child_name})"/>\n')
            arc_id = F'{cor_id} {target_id}'
            if not arc_id in arcsDefined and cor_id!=target_id:
                arcsDefined[arc_id] = f'{name} to {child_name}'
                count += 1
                lines.append(f'\t\t<link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="{cor_id}" xlink:to="{target_id}" order="{count}" xlink:title="presentation: {cor_id} ({name}) to {target_id} ({child_name})"/>\n')
                if 'children_pre' in child and len(child['children_pre']) > 0:
                    grand_children = child['children_pre']
                    linkPresentation(target_id,grand_children,n+1)
        else:
            if not child_id in locsDefined:
                locsDefined[child_id] = child_name
                lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{child_id}" xlink:label="{child_id}" xlink:title="presentation parent: {child_id} ({child_name})"/>\n')
            arc_id = F'{cor_id} {child_id}'
            if not arc_id in arcsDefined and cor_id!=child_id:
                arcsDefined[arc_id] = f'{name} to {child_name}'
                count += 1
                lines.append(f'\t\t<link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="{cor_id}" xlink:to="{child_id}" order="{count}" xlink:title="presentation: {cor_id} ({name}) to {child_id} {child_name}"/>\n')
                if 'children_pre' in child and len(child['children_pre']) > 0:
                    grand_children = child['children_pre']
                    linkPresentation(child_id, grand_children, n+1)
    children = None


def escape_text(str):
    if not str:
        return ''
    escaped = str.replace('<','&lt;')
    escaped = escaped.replace('>','&gt;')
    return escaped


if __name__ == '__main__':
    # Create the parser
    parser = argparse.ArgumentParser(prog='LHM2xBRL-taxonomy.py',
                                     usage='%(prog)s infile -s selected_roots -o outfile -e encoding [options] ',
                                     description='Audit data collection Convert definition CSV file to xBRL taxonomy')
    # Add the arguments
    parser.add_argument('inFile', metavar='infile', type=str, help='Audit data collection definition CSV file')
    parser.add_argument('-b', '--outdir')  # core.xsd
    parser.add_argument('-s', '--selected_roots')  # core.xsd e.g. GL02+GL03
    parser.add_argument('-e', '--encoding') # 'Shift_JIS' 'cp932' 'utf_8'
    parser.add_argument('-t', '--trace', action='store_true')
    parser.add_argument('-d', '--debug', action='store_true')

    args = parser.parse_args()

    in_file = None
    if args.inFile:
        in_file = args.inFile.strip()
        in_file = in_file.replace('/', SEP)
        in_file = file_path(args.inFile)
    if not in_file or not os.path.isfile(in_file):
        print('Input ADC definition CSV file is missing.')
        sys.exit()
    lhm_file = in_file

    if args.outdir:
        xbrl_base = file_path(args.outdir)
    if not os.path.isdir(xbrl_base):
        print('Taxonomy directory does not exist.')
        sys.exit()

    if args.selected_roots:
        selected_roots = args.selected_roots.strip()
        selected_roots = selected_roots.split('+')
    else:
        selected_roots = None

    ncdng = args.encoding
    if ncdng:
        ncdng = ncdng.lstrip()
    else:
        ncdng = 'UTF-8'
    TRACE = args.trace
    DEBUG = args.debug

    # ====================================================================
    # 1. csv -> schema
    ROOT_IDs  = selected_roots
    records   = []
    adcDict   = {}
    classDict = {}
    # associonDict = {}

    lhm_file = file_path(lhm_file)
    level_presentation = [None]*10

    header = [
        # 'sequence','level','type','identifier','name','datatype','multiplicity','domainName','definition','module','table','classTerm','id','path','semanticPath'
        "version",
        "sequence",
        "level",
        "type",
        "identifier",
        "label_local",
        "representation_term",
        "multiplicity",
        "code_list",
        "attribute",
        "definition_local",
        "acronym",
        "UNID",
        "class_term",
        "id",
        "path",
        "semantic_path",
        "abbreviation_path",
        "label",
        "definition",
        "name",
        "element",
        "xpath",
        "H"
    ]

    with open(lhm_file, encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        next(reader)
        semSort = 1000
        for cols in reader:
            data = {}
            for i in range(len(header)):
                col = cols[i]
                data[header[i]] = col.strip()

            path = data['path']
            if not path:
                continue

            # get root id from semantic path and check format
            id = path.strip('/').split('/')[0]
            match = re.search(r'([A-Z]+\d{2})', id)
            if match:
                root_id = match.group(1)
            else:
                continue

            if ROOT_IDs and root_id not in ROOT_IDs:
                continue

            # data = record.copy()
            cor_id = path[1+path.rindex('/'):]
            _type = data['type']
            identifier = data['identifier']
            level = int(data['level'])
            objectClass = data['class_term']
            semSort = data['sequence']
            data['semSort'] = int(semSort)
            if 'REF'==identifier:
                data['level'] = level - 1
            else:
                data['level'] = level
            data['cor_id'] = cor_id
            name = data['name']
            name_id = LC3(name)
            data['name_id'] = name_id
            data['objectClass'] = objectClass
            representation_term = data['representation_term']
            if representation_term in datatypeMap:
                data['datatype'] = f"cor:{datatypeMap[representation_term]['cor']}"
            else:
                data['datatype'] = f"xbrli:stringItemType"
            if 'C'==_type:
                class_id = cor_id
            data['definition'] = data['definition']
            parent = None
            level_presentation[level] = cor_id
            if int(level) > 0:
                """
                presentation link
                """
                if DEBUG:
                    print(f'{lhm_file[1+lhm_file.rindex(SEP):]} {level} {cor_id} {data["semantic_path"]}')
                if  'C'==_type:
                    data['children_pre'] = []
                    if level > 1:
                        parent = level_presentation[level-1]
                    data['parent_pre'] = parent
                    if parent:
                        if parent in adcDict and 'children_pre' not in adcDict[parent]:
                            adcDict[parent]['children_pre'] = []
                        adcDict[parent]['children_pre'].append(cor_id)
                else:
                    parent = level_presentation[level-1]
                    data['parent_pre'] = parent
                    if 'children_pre' not in adcDict[parent]:
                        adcDict[parent]['children_pre'] = []
                    adcDict[parent]['children_pre'].append(cor_id)
                """
                definition link
                """
                ancesters = path[1:].split("/")
                parent = None
                if len(ancesters)>1:
                    parent = ancesters[-2]
                if parent:
                    if  'C'==_type:
                        data['children'] = []
                        if 'children' not in adcDict[parent]:
                            adcDict[parent]['children'] = []                
                    data['parent'] = parent
                    adcDict[parent]['children'].append(cor_id)                   
            data['class_id'] = class_id
            adcDict[cor_id] = data
            records.append(data)
    # if DEBUG: print(records)

    targetRefDict = {} # child-parent
    for cor_id, record in adcDict.items():
        if 'C'==record['type'] and 'children' in record:
            children = record['children']
            for child_id in children:
                child = getRecord(child_id)
                if 'C'==child['type']:
                    if child['multiplicity'][-1] in ['*', 'n']:
                        targetRefDict[child_id] = cor_id

    roleMap = {}
    for cor_id,record in adcDict.items():
        if 'C'==record['type']:
            roleMap[cor_id] = record #roleRecord(record)

    ###################################
    # core.xsd
    #
    html_head = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<!-- (c) 2022 XBRL Japan  inc. -->\n',
        '<schema \n',
        '\ttargetNamespace="http://www.iso.org/iso21926" \n',
        '\telementFormDefault="qualified" \n',
        '\tattributeFormDefault="unqualified" \n',
        '\txmlns="http://www.w3.org/2001/XMLSchema" \n',
        '\txmlns:cor="http://www.iso.org/iso21926" \n',
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

    html_annotation_head = [
        '\t<annotation>\n',
        '\t\t<appinfo>\n',
        '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/labelLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-lbl-ja.xml"/>\n',
        '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/labelLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-lbl-en.xml"/>\n',
        '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/presentationLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-pre.xml"/>\n',
        '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/definitionLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-def.xml"/>\n',
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

    html = [
        '\t\t\t<!-- \n',
        '\t\t\t\trole type\n',
        '\t\t\t-->\n'
        f'\t\t\t<link:roleType id="iso21926-role" roleURI="http://www.iso.org/iso21926/role">\n',
        f'\t\t\t\t<link:definition>link iso21926</link:definition>\n',
        f'\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n',
        f'\t\t\t\t<link:usedOn>link:presentationLink</link:usedOn>\n',
        '\t\t\t</link:roleType>\n',
    ]
    for cor_id, record in roleMap.items():
        role = roleRecord(record)
        role_id = role["role_id"]
        URI     = role['URI']
        link_id = role['link_id']
        html.append(f'\t\t\t<link:roleType id="{role_id}" roleURI="http://www.iso.org/iso21926/role{URI}">\n')
        html.append(f'\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n')
        html.append('\t\t\t</link:roleType>\n')
    lines += html

    # html = [
    #     '\t\t\t<!-- \n',
    #     '\t\t\t\tsemantic binding: roleType for referemceLink \n',
    #     '\t\t\t--> \n',
    #     '\t\t\t<link:roleType id="semantic-binding" roleURI="http://www.iso.org/iso21926/role/semantic-binding"> \n',
    #     '\t\t\t\t<link:definition>semantic binding</link:definition> \n',
    #     '\t\t\t\t<link:usedOn>link:referenceLink</link:usedOn> \n',
    #     '\t\t\t</link:roleType> \n',
    #     '\t\t\t<!-- \n',
    #     '\t\t\t\tsyntax binding: roleType for referemceLink \n',
    #     '\t\t\t--> \n',
    #     '\t\t\t<link:roleType id="syntax-binding" roleURI="http://www.iso.org/iso21926/role/syntax-binding"> \n',
    #     '\t\t\t\t<link:definition>syntax binding</link:definition> \n',
    #     '\t\t\t\t<link:usedOn>link:referenceLink</link:usedOn> \n',
    #     '\t\t\t</link:roleType> \n',
    # ]
    # lines += html

    html = [
        '\t\t\t<!--\n',
        '\t\t\t\tdescription: roleType arcroleType\n',
        '\t\t\t-->\n'
        '\t\t\t<link:roleType id="description" roleURI="http://www.iso.org/iso21926/role/description">\n',
        '\t\t\t\t<link:definition>description</link:definition>\n',
        '\t\t\t\t<link:usedOn>link:label</link:usedOn>\n',
        '\t\t\t</link:roleType>\n',
        '\t\t\t<link:arcroleType id="concept-description" cyclesAllowed="undirected" arcroleURI="http://www.iso.org/iso21926/arcrole/concept-description">\n',
        '\t\t\t\t<link:definition>concept to description</link:definition>\n',
        '\t\t\t\t<link:usedOn>link:labelArc</link:usedOn>\n',
        '\t\t\t</link:arcroleType >\n',
    ]
    lines += html

    # html = [
    #     '\t\t\t<!--\n',
    #     '\t\t\t\tprimary key: roleType arcroleType\n',
    #     '\t\t\t-->\n'
    #     '\t\t\t<link:roleType id="primary-key" roleURI="http://www.iso.org/iso21926/role/primary-key">\n',
    #     '\t\t\t\t<link:definition>primary key</link:definition>\n',
    #     '\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n',
    #     '\t\t\t</link:roleType>\n',
    #     '\t\t\t<link:arcroleType id="concept-primary-key" cyclesAllowed="undirected" arcroleURI="http://www.iso.org/iso21926/arcrole/concept-primary-key">\n',
    #     '\t\t\t\t<link:definition>concept primary key</link:definition>\n',
    #     '\t\t\t\t<link:usedOn>link:definitionArc</link:usedOn>\n',
    #     '\t\t\t</link:arcroleType >\n',
    # ]
    # lines += html

    # html = [
    #     '\t\t\t<!--\n',
    #     '\t\t\t\treference identifier: roleType arcroleType\n',
    #     '\t\t\t-->\n'
    #     '\t\t\t<link:roleType id="reference-identifier" roleURI="http://www.iso.org/iso21926/role/reference-identifier">\n',
    #     '\t\t\t\t<link:definition>reference identifier</link:definition>\n',
    #     '\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n',
    #     '\t\t\t</link:roleType>\n',
    #     '\t\t\t<link:arcroleType id="concept-reference-identifier" cyclesAllowed="undirected" arcroleURI="http://www.iso.org/iso21926/arcrole/concept-reference-identifier">\n',
    #     '\t\t\t\t<link:definition>concept reference identifier</link:definition>\n',
    #     '\t\t\t\t<link:usedOn>link:definitionArc</link:usedOn>\n',
    #     '\t\t\t</link:arcroleType >\n',
    # ]
    # lines += html

    # html = [
    #     '\t\t\t<!--\n',
    #     '\t\t\t\trequire: roleType\n',
    #     '\t\t\t-->\n'
    #     '\t\t\t<link:roleType id="require" roleURI="http://www.iso.org/iso21926/role/require">\n',
    #     '\t\t\t\t<link:definition>require</link:definition>\n',
    #     '\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n',
    #     '\t\t\t</link:roleType>\n',
    # ]
    # lines += html

    html_annotation_tail = [
        '\t\t</appinfo>\n',
        '\t</annotation>\n'
    ]
    lines += html_annotation_tail

    html_type = [
        '\t<!-- typed dimension referenced element -->\n',
        '\t<element name="_v" id="_v">\n',
        '\t\t<simpleType>\n',
        '\t\t\t<restriction base="string"/>\n',
        '\t\t</simpleType>\n',
        '\t</element>\n',
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
    html_hypercube = [
        '\t<!-- Hypercube -->\n'
    ]
    for cor_id,record in roleMap.items():
        role = roleRecord(record)
        link_id = role['link_id']
        html_hypercube.append(f'\t<element name="h_{link_id}" id="h_{link_id}" substitutionGroup="xbrldt:hypercubeItem" type="xbrli:stringItemType" nillable="true" abstract="true" xbrli:periodType="instant"/>\n')
    lines += html_hypercube

    # Dimension
    html_dimension = [
        '\t<!-- Dimension -->\n'
    ]
    for cor_id,record in roleMap.items():
        role = roleRecord(record)
        link_id = role['link_id']
        html_dimension.append(f'\t<element name="d_{link_id}" id="d_{link_id}" substitutionGroup="xbrldt:dimensionItem" type="xbrli:stringItemType" abstract="true" xbrli:periodType="instant" xbrldt:typedDomainRef="#_v"/>\n')
    lines += html_dimension

    # item complexType
    html_itemtype = [
        '\t<!-- item type -->\n'
    ]
    complexType = [
        '\t<complexType name="stringItemType">\n',
        '\t\t<simpleContent>\n',
        '\t\t\t<restriction base="xbrli:stringItemType"/>\n',
        '\t\t</simpleContent>\n',
        '\t</complexType>\n',
    ]
    html_itemtype += complexType
    definedType = []
    for name,type in datatypeMap.items():
        cor = type['cor']
        xbrli = type['xbrli']
        if cor not in definedType:
            complexType = [
                f'\t<complexType name="{cor}">\n',
                '\t\t<simpleContent>\n',
                f'\t\t\t<restriction base="xbrli:{xbrli}"/>\n',
                '\t\t</simpleContent>\n',
                '\t</complexType>\n',
            ]
            definedType.append(cor)
            html_itemtype += complexType
    lines += html_itemtype

    # element
    lines.append('\t<!-- element -->\n')
    elementsDefined = set()
    primaryKeys = {}
    for cor_id,record in adcDict.items():
        defineElement(cor_id,record)

    lines.append('</schema>')

    cor_xsd_file = file_path(f'{xbrl_base}/{core_xsd}')
    with open(cor_xsd_file, 'w', encoding='utf-8-sig', newline='') as f:
        f.writelines(lines)
    if TRACE:
        print(f'-- {cor_xsd_file}')

    ###################################
    # labelLink en
    #
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<!--  (c) 2023 XBRL Japan inc. -->\n',
        '<link:linkbase\n',
        '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '\txmlns:xlink="http://www.w3.org/1999/xlink"\n',
        '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd">\n',
        f'\t<link:roleRef roleURI="http://www.iso.org/iso21926/role/description" xlink:type="simple" xlink:href="{core_xsd}#description"/>\n',
        f'\t<link:arcroleRef arcroleURI="http://www.iso.org/iso21926/arcrole/concept-description" xlink:type="simple" xlink:href="{core_xsd}#concept-description"/>\n',
        '\t<link:labelLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">\n'
    ]
    locsDefined = {}
    arcsDefined = {}
    definedLabels = {}
    definedDescs = {}
    definedDescArcs = {}

    for cor_id,record in adcDict.items():
        name = record['label']
        desc = record['definition']# if 'definition' in record else None
        linkLabel(cor_id,name,desc,'en')

    lines.append('\t</link:labelLink>\n')
    lines.append('</link:linkbase>\n')

    cor_label_file = file_path(f'{xbrl_base}/{core_label}-en.xml')
    with open(cor_label_file, 'w', encoding='utf-8-sig', newline='') as f:
        f.writelines(lines)
    if TRACE:
        print(f'-- {cor_label_file}')

    ###################################
    # labelLink ja
    #
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<!--  (c) 2023 XBRL Japan inc. -->\n',
        '<link:linkbase\n',
        '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '\txmlns:xlink="http://www.w3.org/1999/xlink"\n',
        '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd">\n',
        f'\t<link:roleRef roleURI="http://www.iso.org/iso21926/role/description" xlink:type="simple" xlink:href="{core_xsd}#description"/>\n',
        f'\t<link:arcroleRef arcroleURI="http://www.iso.org/iso21926/arcrole/concept-description" xlink:type="simple" xlink:href="{core_xsd}#concept-description"/>\n',
        '\t<link:labelLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">\n'
    ]
    locsDefined = {}
    arcsDefined = {}
    definedLabels = {}
    definedDescs = {}
    definedDescArcs = {}

    for cor_id,record in adcDict.items():
        # propertyType = record['type']
        name = record['label_local']
        desc = record['definition_local']# if 'desc' in record else None
        if len(name) > 0:
            linkLabel(cor_id,name,desc,'ja')

    lines.append('\t</link:labelLink>\n')
    lines.append('</link:linkbase>\n')

    cor_label_file = file_path(f'{xbrl_base}/{core_label}-ja.xml')
    with open(cor_label_file, 'w', encoding='utf-8-sig', newline='') as f:
        f.writelines(lines)
    if TRACE:
        print(f'-- {cor_label_file}')

    ###################################
    #   presentationLink
    #
    locsDefined = {}
    arcsDefined = {}
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<!--  (c) 2023 XBRL Japan inc. -->\n',
        '<link:linkbase\n',
        '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"\n',
        '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '\txmlns:xlink="http://www.w3.org/1999/xlink">\n',
        f'\t<link:roleRef roleURI="http://www.iso.org/iso21926/role" xlink:type="simple" xlink:href="{core_xsd}#iso21926-role"/>\n',
        '\t<link:presentationLink xlink:type="extended" xlink:role="http://www.iso.org/iso21926/role">\n',
    ]
    locsDefined = {}
    arcsDefined = {}
    class_records = [x for x in records if 'C'==x['type']]
    for record in class_records:
        cor_id = record['cor_id']
        propertyType = record['type']
        count = 0
        children = record['children_pre']
        linkPresentation(cor_id, children, 1)

    lines.append('\t</link:presentationLink>\n')
    lines.append('</link:linkbase>\n')

    cor_presentation_file = file_path(f'{xbrl_base}/{core_presentation}.xml')
    with open(cor_presentation_file, 'w', encoding='utf-8-sig', newline='') as f:
        f.writelines(lines)
    if TRACE:
        print(f'-- {cor_presentation_file}')

    ###################################
    # definitionLink
    #
    locsDefined = {}
    arcsDefined = {}
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<!--(c) 2023 XBRL Japan inc. -->\n',
        '<link:linkbase\n',
        '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"\n',
        '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '\txmlns:xbrldt="http://xbrl.org/2005/xbrldt"\n',
        '\txmlns:xlink="http://www.w3.org/1999/xlink">\n'
    ]
    lines.append('\t<!-- roleRef -->\n')

    for record in roleMap.values():
        role = roleRecord(record)
        role_id = role["role_id"]
        link_id = role['link_id']
        URI = f"/{role_id}"
        lines.append(f'\t<link:roleRef roleURI="http://www.iso.org/iso21926/role{URI}" xlink:type="simple" xlink:href="{core_xsd}#{role_id}"/>\n')
    html = [
        # f'\t<link:roleRef roleURI="http://www.iso.org/iso21926/role/primary-key" xlink:type="simple" xlink:href="{core_xsd}#primary-key"/>\n',
        # f'\t<link:roleRef roleURI="http://www.iso.org/iso21926/role/reference-identifier" xlink:type="simple" xlink:href="{core_xsd}#reference-identifier"/>\n',
        # f'\t<link:roleRef roleURI="http://www.iso.org/iso21926/role/require" xlink:type="simple" xlink:href="{core_xsd}#require"/>\n',
        '\t<!-- arcroleRef -->\n',
        '\t<link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/all" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#all"/>\n',
        '\t<link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/domain-member" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#domain-member"/>\n',
        '\t<link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/hypercube-dimension" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#hypercube-dimension"/>\n',
        '\t<link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/dimension-domain" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#dimension-domain"/>\n',
        # f'\t<link:arcroleRef arcroleURI="http://www.iso.org/iso21926/arcrole/concept-primary-key" xlink:type="simple" xlink:href="{core_xsd}#concept-primary-key"/>\n',
        # f'\t<link:arcroleRef arcroleURI="http://www.iso.org/iso21926/arcrole/concept-reference-identifier" xlink:type="simple" xlink:href="{core_xsd}#concept-reference-identifier"/>\n',
    ]
    lines += html

    for cor_id,record in roleMap.items():
        # role = roleRecord(record)
        count = 0
        defineHypercube(record)

    lines.append('</link:linkbase>\n')

    cor_definition_file = file_path(f'{xbrl_base}/{core_definition}.xml')
    with open(cor_definition_file, 'w', encoding='utf-8-sig', newline='') as f:
        f.writelines(lines)
    if TRACE:
        print(f'-- {cor_definition_file}')

    ###################################
    # referenceLink SME Common EDI
    #
    # lines = []
    # html = [
    #     '<?xml version="1.0" encoding="UTF-8"?>\n',
    #     '<!--  (c) 2023 XBRL Japan inc. -->\n',
    #     '<link:linkbase\n',
    #     '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
    #     '\txmlns:cor="http://www.iso.org/iso21926"\n',
    #     '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
    #     '\txmlns:xlink="http://www.w3.org/1999/xlink"\n',
    #     '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd http://www.iso.org/iso21926 core.xsd">\n',
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
    #         f'\t\t<link:reference xlink:type="resource" xlink:label="{cor_id}_REF" xlink:role="http://www.iso.org/iso21926/role/semantic-binding"> \n',
    #         f'\t\t\t<cor:id>{cor_id}</cor:id> \n',
    #         f'\t\t\t<!--cor:cardinality>1..1</cor:cardinality--> \n',
    #         f'\t\t\t<cor:business_term>{termSme}</cor:business_term> \n',
    #         f'\t\t\t<cor:business_term_ja>{termSme_ja}</cor:business_term_ja> \n',
    #         f'\t\t\t<!--cor:description>Commercial invoice</cor:description--> \n',
    #         f'\t\t\t<cor:description_ja>{defSme_ja}</cor:description_ja> \n',
    #         f'\t\t</link:reference> \n',
    #         f'\t\t<link:reference xlink:type="resource" xlink:label="{cor_id}_REF" xlink:role="http://www.iso.org/iso21926/role/syntax-binding"> \n',
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
    # if TRACE:
    #     print(f'-- {cor_referemce_file_sme}')

    ###################################
    # referenceLink JP PINT
    #
    # lines = []
    # html = [
    #     '<?xml version="1.0" encoding="UTF-8"?>\n',
    #     '<!--  (c) 2023 XBRL Japan inc. -->\n',
    #     '<link:linkbase\n',
    #     '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
    #     '\txmlns:cor="http://www.iso.org/iso21926"\n',
    #     '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
    #     '\txmlns:xlink="http://www.w3.org/1999/xlink"\n',
    #     '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd http://www.iso.org/iso21926 core.xsd">\n',
    #     '\t<link:roleRef roleURI="http://www.iso.org/iso21926/role/semantic-binding" xlink:type="simple" xlink:href="core.xsd#semantic-binding"/>\n',
    #     '\t<link:roleRef roleURI="http://www.iso.org/iso21926/role/syntax-binding" xlink:type="simple" xlink:href="core.xsd#syntax-binding"/>\n',
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
    #         f'\t\t<link:reference xlink:type="resource" xlink:label="{cor_id}_REF" xlink:role="http://www.iso.org/iso21926/role/semantic-binding"> \n',
    #         f'\t\t\t<cor:id>{cor_id}</cor:id> \n',
    #         f'\t\t\t<!--cor:cardinality>1..1</cor:cardinality--> \n',
    #         f'\t\t\t<cor:business_term>{termPint}</cor:business_term> \n',
    #         f'\t\t\t<cor:business_term_ja>{termPint_ja}</cor:business_term_ja> \n',
    #          f'\t\t\t<!--cor:description>Commercial invoice</cor:description--> \n',
    #         f'\t\t\t<!--cor:description_ja>defPint_ja</cor:description_ja--> \n',
    #         f'\t\t</link:reference> \n',
    #         f'\t\t<link:reference xlink:type="resource" xlink:label="{cor_id}_REF" xlink:role="http://www.iso.org/iso21926/role/syntax-binding"> \n',
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
    # if TRACE:
    #     print(f'-- {cor_referemce_file_jp_pint}')

    print('** END **')
