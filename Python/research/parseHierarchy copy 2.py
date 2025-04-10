import lxml.etree as ET
import pandas as pd
import os
import re
import csv
from collections import defaultdict

TRACE = True
DEBUG = True

def trace_print(text):
    if TRACE or DEBUG:
        print(text)

def debug_print(text):
    if DEBUG:
        print(text)

# Helper to clean label IDs
def clean_label_id(label_id):
    label_id = re.sub(r"^label_", "", label_id)
    label_id = re.sub(r"(_lbl|_\d+(_\d+)?)$", "", label_id)
    return label_id

# Base directory and schema path
base_dir = "XBRL-GL-PWD-2016-12-01"
xsd_path = os.path.join(base_dir, "gl/plt/case-c-b-m-u-e-t-s/gl-cor-content-2016-12-01.xsd")
namespaces = {
    'xs': "http://www.w3.org/2001/XMLSchema",
    'xbrli': "http://www.xbrl.org/2003/instance"
}
modules = ['gen', 'cor', 'bus', 'muc', 'usk', 'ehm', 'taf', 'srcd']

# Load base schemas and build type maps
element_type_map = {}
type_base_map = {}
for mod in modules:
    path = os.path.join(base_dir, f"gl/{mod}/gl-{mod}-2016-12-01.xsd")
    if os.path.exists(path):
        tree = ET.parse(path)
        root = tree.getroot()
        for el in root.xpath("//xs:element", namespaces=namespaces):
            name, type_ = el.get("name"), el.get("type")
            if name and type_:
                element_type_map[f"gl-{mod}:{name}"] = type_
        for tdef in root.xpath("//xs:simpleType | //xs:complexType", namespaces=namespaces):
            name = tdef.get("name")
            if name:
                restriction = tdef.find(".//xs:restriction", namespaces)
                if restriction is not None:
                    base = restriction.get("base")
                    if base:
                        type_base_map[name] = base

# Load content schemas
content_roots = {}
for mod in modules:
    path = os.path.join(base_dir, f"gl/plt/case-c-b-m-u-e-t-s/gl-{mod}-content-2016-12-01.xsd")
    if os.path.exists(path):
        content_roots[mod] = ET.parse(path).getroot()

# Load label linkbases
label_map = defaultdict(dict)
for mod in modules:
    lab_path = os.path.join(base_dir, f"gl/{mod}/lang/gl-{mod}-2016-12-01-label.xml")
    if not os.path.exists(lab_path):
        continue
    tree = ET.parse(lab_path)
    root = tree.getroot()
    ns = {'link': 'http://www.xbrl.org/2003/linkbase', 'xlink': 'http://www.w3.org/1999/xlink'}

    label_texts = defaultdict(dict)
    for label in root.xpath(".//link:label", namespaces=ns):
        role = label.get("{http://www.w3.org/1999/xlink}role")
        raw_id = label.get("{http://www.w3.org/1999/xlink}label")
        if raw_id.startswith("gl-"):
            cleaned_id = raw_id
        else:
            cleaned_id = f"gl-{mod}_{clean_label_id(raw_id)}"
        cleaned_id = clean_label_id(cleaned_id)
        text = label.text.strip() if label.text else ""
        if role.endswith("label"):
            label_texts[cleaned_id]["label"] = text
        elif role.endswith("documentation"):
            label_texts[cleaned_id]["documentation"] = text

    for loc in root.xpath(".//link:loc", namespaces=ns):
        href = loc.get("{http://www.w3.org/1999/xlink}href")
        raw_id = loc.get("{http://www.w3.org/1999/xlink}label")
        if '#' not in href:
            continue
        _, anchor = href.split("#")
        cleaned_anchor = clean_label_id(anchor)
        label_map[cleaned_anchor]["label"] = label_texts.get(cleaned_anchor, {}).get("label", "")
        label_map[cleaned_anchor]["documentation"] = label_texts.get(cleaned_anchor, {}).get("documentation", "")

# Helpers

def is_tuple_type(type_str):
    return type_str and not type_str.endswith("ItemType")

def resolve_base_type(type_str):
    module = type_str.split(":")[0][3:]
    type_name = type_str.split(":")[-1]
    for path in [
        os.path.join(base_dir, f"gl/{module}/gl-{module}-2016-12-01.xsd"),
        os.path.join(base_dir, f"gl/plt/case-c-b-m-u-e-t-s/gl-{module}-content-2016-12-01.xsd")
    ]:
        if os.path.exists(path):
            tree = ET.parse(path)
            nested = tree.xpath(f".//xs:complexType[@name='{type_name}']", namespaces=namespaces)
            if nested:
                element = nested[0]
                simple_content = element.find("xs:simpleContent", namespaces)
                if simple_content is not None:
                    for tag in ["xs:restriction", "xs:extension"]:
                        inner = simple_content.find(tag, namespaces)
                        if inner is not None:
                            return inner.get("base", "")
    return ""

# Traversal
records = []

def process_sequence(seq, _type, module, path, base, namespaces):
    for el in seq.findall("xs:element", namespaces=namespaces):
        ref = el.get("ref")
        name = el.get("name")
        el_name = ref or name
        el_type = element_type_map.get(el_name, "")
        is_tuple = is_tuple_type(el_type)
        path_str = f"gl-{module}:{path}" if "gl-" not in path else path
        new_path = f"{path_str}/{el_name}"
        min_occurs = el.get("minOccurs", "1")
        max_occurs = el.get("maxOccurs", "1")
        base_type = resolve_base_type(el_type) if not is_tuple and el_type else ""
        level = 1 + new_path.count("/")

        # element_local = el_name.split(":")[-1]
        raw_key = el_name.replace(':','_')
        # cleaned_key = clean_label_id(raw_key)
        label_info = label_map.get(raw_key, {})
        label = label_info.get("label", "")
        documentation = label_info.get("documentation", "")
        records.append({
            "Level": level,
            "Element": el_name,
            "Type": el_type,
            "Path": new_path,
            "isTuple": is_tuple,
            "minOccurs": min_occurs,
            "maxOccurs": max_occurs,
            "BaseType": base_type,
            "Label": label,
            "Documentation": documentation
        })

        if not el_type:
            continue
        type_name = el_type.split(":")[-1]
        if is_tuple:
            mod = el_type.split(":")[0][3:]
            for path in [
                os.path.join(base_dir, f"gl/{mod}/gl-{mod}-2016-12-01.xsd"),
                os.path.join(base_dir, f"gl/plt/case-c-b-m-u-e-t-s/gl-{mod}-content-2016-12-01.xsd")
            ]:
                if os.path.exists(path):
                    tree = ET.parse(path)
                    nested = tree.xpath(f".//xs:complexType[@name='{type_name}']", namespaces=namespaces)
                    if nested:
                        walk_complex_type(type_name, nested[0], "tuple", mod, new_path, namespaces)
                        break

def walk_complex_type(name, element, _type, module, path, namespaces):
    debug_print(f"Walking {_type}: {name} gl-{module}:{path}")
    sequence = element.find("xs:sequence", namespaces)
    if sequence is not None:
        process_sequence(sequence, _type, module, path, name, namespaces)
        return
    complex_content = element.find("xs:complexContent", namespaces)
    if complex_content is not None:
        for tag in ["xs:restriction", "xs:extension"]:
            inner = complex_content.find(tag, namespaces)
            if inner is not None:
                base = inner.get("base")
                seq = inner.find("xs:sequence", namespaces)
                if seq is not None:
                    process_sequence(seq, _type, module, path, base, namespaces)
                return

# Start with root complexType
root = content_roots["cor"]
complex_type_list = root.xpath(".//xs:complexType[@name='accountingEntriesComplexType']", namespaces=namespaces)
if complex_type_list:
    walk_complex_type("accountingEntriesComplexType", complex_type_list[0], "tuple", "cor", "accountingEntries", namespaces)
else:
    print("❌ Not found: accountingEntriesComplexType")

# Output
output_dir = "XBRL-GL-2025"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "XBRL_GL_Parsed_LHM_Structure.csv")
# with open(output_file, mode='w', newline='', encoding='utf-8') as f:
#     if records:
#         writer = csv.DictWriter(f, fieldnames=records[0].keys())
#         writer.writeheader()
#         writer.writerows(records)
#     else:
#         print("⚠️ No records to write.")
pd.DataFrame(records).to_csv(output_file, index=False)
trace_print(f"\n✅ Saved parsed structure to: {output_file}")