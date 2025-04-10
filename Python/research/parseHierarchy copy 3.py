import lxml.etree as ET
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
label_texts = defaultdict(dict)
for mod in modules:
    lab_path = os.path.join(base_dir, f"gl/{mod}/lang/gl-{mod}-2016-12-01-label.xml")
    if not os.path.exists(lab_path):
        continue
    tree = ET.parse(lab_path)
    root = tree.getroot()
    ns = {'link': 'http://www.xbrl.org/2003/linkbase', 'xlink': 'http://www.w3.org/1999/xlink'}
    locator_map = {}
    label_resources = {}

    # Map locator label -> href target
    for loc in root.xpath(".//link:loc", namespaces=ns):
        label_id = loc.get("{http://www.w3.org/1999/xlink}label")
        href = loc.get("{http://www.w3.org/1999/xlink}href")
        _, anchor = href.split("#")
        if label_id and href and '#' in href:
            locator_map[label_id] = anchor

    # Collect label resources
    for label in root.xpath(".//link:label", namespaces=ns):
        label_id = label.get("{http://www.w3.org/1999/xlink}label")
        role = label.get("{http://www.w3.org/1999/xlink}role")
        label_text = label.text.strip() if label.text else ""
        if label_id not in label_resources:
            label_resources[label_id] = {}
        if role.endswith("label"):
            label_resources[label_id]["label"] = label_text
        elif role.endswith("documentation"):
            label_resources[label_id]["documentation"] = label_text

    # Resolve labelArcs and map labels to href anchors
    for arc in root.xpath(".//link:labelArc", namespaces=ns):
        from_label = arc.get("{http://www.w3.org/1999/xlink}from")
        to_label = arc.get("{http://www.w3.org/1999/xlink}to")
        href = locator_map.get(from_label)
        label = label_resources.get(to_label)
        if href and label is not None:
            if "label" in label:
                label_texts[href]["label"] = label["label"]
            if "documentation" in label:
                label_texts[href]["documentation"] = label["documentation"]


l_label_texts = defaultdict(dict)
for mod in modules:
    lab_path = os.path.join(base_dir, f"gl/{mod}/lang/gl-{mod}-2016-12-01-label-ja.xml")
    if not os.path.exists(lab_path):
        continue
    tree = ET.parse(lab_path)
    root = tree.getroot()
    ns = {'link': 'http://www.xbrl.org/2003/linkbase', 'xlink': 'http://www.w3.org/1999/xlink'}
    locator_map = {}
    label_resources = {}

    # Map locator label -> href target
    for loc in root.xpath(".//link:loc", namespaces=ns):
        label_id = loc.get("{http://www.w3.org/1999/xlink}label")
        href = loc.get("{http://www.w3.org/1999/xlink}href")
        _, anchor = href.split("#")
        if label_id and href and '#' in href:
            locator_map[label_id] = anchor

    # Collect label resources
    for label in root.xpath(".//link:label", namespaces=ns):
        label_id = label.get("{http://www.w3.org/1999/xlink}label")
        role = label.get("{http://www.w3.org/1999/xlink}role")
        label_text = label.text.strip() if label.text else ""
        if label_id not in label_resources:
            label_resources[label_id] = {}
        if role.endswith("label"):
            label_resources[label_id]["label"] = label_text
        elif role.endswith("documentation"):
            label_resources[label_id]["documentation"] = label_text

    # Resolve labelArcs and map labels to href anchors
    for arc in root.xpath(".//link:labelArc", namespaces=ns):
        from_label = arc.get("{http://www.w3.org/1999/xlink}from")
        to_label = arc.get("{http://www.w3.org/1999/xlink}to")
        href = locator_map.get(from_label)
        label = label_resources.get(to_label)
        if href and label is not None:
            if "label" in label:
                l_label_texts[href]["label"] = label["label"]
            if "documentation" in label:
                l_label_texts[href]["documentation"] = label["documentation"]

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
    debug_print(f"Process sequence {path}")
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

        raw_key = el_name.replace(":", "_")
        label_info = label_texts.get(raw_key)
        if not label_info:
            suffix = raw_key.split("_")[-1]
            for k, v in label_texts.items():
                if k.endswith(f"_{suffix}"):
                    label_info = v
                    debug_print(f"↪ Fallback label match: {k} → {raw_key}")
                    break
            else:
                label_info = {}

        l_label_info = l_label_texts.get(raw_key)
        if not l_label_info:
            suffix = raw_key.split("_")[-1]
            for k, v in l_label_texts.items():
                if k.endswith(f"_{suffix}"):
                    l_label_info = v
                    debug_print(f"↪ Fallback label match: {k} → {raw_key}")
                    break
            else:
                l_label_info = {}

        record = {
            "Level": level,
            "Element": el_name,
            "Type": el_type,
            "Path": f"/{new_path}",
            "isTuple": is_tuple,
            "minOccurs": min_occurs,
            "maxOccurs": max_occurs,
            "BaseType": base_type,
            "Label": label_info.get("label", ""),
            "Documentation": label_info.get("documentation", ""),
            "LocalLabel": l_label_info.get("label", ""),
            "LocalDocumentation": l_label_info.get("documentation", "")
        }
        records.append(record)
        if not el_type:
            continue
        type_name = el_type.split(":")[-1]
        if is_tuple:
            mod = el_type.split(":")[0][3:]
            for _path in [
                os.path.join(base_dir, f"gl/{mod}/gl-{mod}-2016-12-01.xsd"),
                os.path.join(base_dir, f"gl/plt/case-c-b-m-u-e-t-s/gl-{mod}-content-2016-12-01.xsd")
            ]:
                if os.path.exists(_path):
                    tree = ET.parse(_path)
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
    href = "gl-cor_accountingEntries"
    record = {
        "Level": 1,
        "Element": "accountingEntries",
        "Type": "gl-cor:accountingEntriesComplexType",
        "Path": "/gl-cor:accountingEntries",
        "isTuple": True,
        "minOccurs": "1",
        "maxOccurs": "unbounded",
        "BaseType": "",
        "Label": label_texts[href]["label"],
        "Documentation": label_texts[href]["documentation"],
        "LocalLabel": l_label_texts[href]["label"],
        "LocalDocumentation": l_label_texts[href]["documentation"]
    }
    records.append(record)

    walk_complex_type("accountingEntriesComplexType", complex_type_list[0], "tuple", "cor", "accountingEntries", namespaces)
else:
    print("❌ Not found: accountingEntriesComplexType")

# Output to CSV without pandas
output_dir = "XBRL-GL-2025"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "XBRL_GL_Parsed_LHM_Structure.csv")

with open(output_file, mode='w', newline='', encoding='utf-8-sig') as f:
    if records:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    else:
        print("⚠️ No records to write.")

trace_print(f"\n✅ Saved parsed structure to: {output_file}")