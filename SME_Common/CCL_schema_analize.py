import xml.etree.ElementTree as ET
import csv
from collections import OrderedDict

XSD_NS = "http://www.w3.org/2001/XMLSchema"

def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag

def pick_doc_fields(node):
    """
    annotation/documentation 直下の ccts:* を拾って辞書で返す
    """
    fields = {
        "Version": "",
        "UNID": "",
        "Acronym": "",
        "Dictionary Entry Name": "",
        "ObjectClassQualifierTerm": "",
        "Cardinality": "",
        "ObjectClassTerm": "",
        "PropertyTerm": "",
        "PrimaryRepresentationTerm": "",
        "AssociatedObjectClassQualifierTerm": "",
        "AssociatedObjectClassTerm": "",
        "Definition": "",
    }
    doc = node.find(f"{{{XSD_NS}}}annotation/{{{XSD_NS}}}documentation")
    if doc is None:
        return fields

    for child in doc:
        lname = localname(child.tag)
        txt = (child.text or "").strip()
        if not txt:
            continue
        if lname == "UniqueID":
            fields["UNID"] = txt
        elif lname == "Acronym":
            fields["Acronym"] = txt
        elif lname == "DictionaryEntryName":
            fields["Dictionary Entry Name"] = txt
        elif lname == "Version":
            fields["Version"] = txt
        elif lname == "Definition":
            fields["Definition"] = txt
        elif lname == "ObjectClassTerm":
            fields["ObjectClassTerm"] = txt
        elif lname == "ObjectClassQualifierTerm":
            fields["ObjectClassQualifierTerm"] = txt
        elif lname == "PropertyTerm":
            fields["PropertyTerm"] = txt
        elif lname == "PrimaryRepresentationTerm":
            fields["PrimaryRepresentationTerm"] = txt
        elif lname == "Cardinality":
            fields["Cardinality"] = txt
        elif lname == "AssociatedObjectClassTerm":
            fields["AssociatedObjectClassTerm"] = txt
        elif lname == "AssociatedObjectClassQualifierTerm":
            fields["AssociatedObjectClassQualifierTerm"] = txt
    return fields

def extract_rows_from_xsd(xsd_path):
    tree = ET.parse(xsd_path)
    root = tree.getroot()

    rows = []

    # 1) xsd:element（BBIE / ASBIE など）
    for el in root.findall(f".//{{{XSD_NS}}}element"):
        elem_name = el.get("name", "")
        elem_type = el.get("type", "")  # 匿名型なら空
        ccts = pick_doc_fields(el)
        if not (elem_name or any(ccts.values())):
            continue
        rows.append({
            **ccts,
            "XML element name": elem_name,
            "XML datatype": elem_type,
        })

    # 2) xsd:complexType（ABIE 本体）— datatype は空欄
    for ct in root.findall(f".//{{{XSD_NS}}}complexType"):
        ct_name = ct.get("name", "")
        ccts = pick_doc_fields(ct)
        if not (ct_name or any(ccts.values())):
            continue
        rows.append({
            **ccts,
            "XML element name": ct_name,   # complexType の @name
            "XML datatype": "",            # 指示どおり空欄
        })

    # 3) ★ ABIE の DEN 重複を統合（DEN 単位で 1 行に）
    abie_by_den = OrderedDict()  # 追加順を保持
    deduped = []

    for r in rows:
        if r.get("Acronym") == "ABIE":
            den = r.get("Dictionary Entry Name", "")
            if den in abie_by_den:
                base = abie_by_den[den]
                # 空欄を埋める形でマージ（先勝ち・空欄のみ上書き）
                for k, v in r.items():
                    if not base.get(k) and v:
                        base[k] = v
            else:
                abie_by_den[den] = r
        else:
            deduped.append(r)

    deduped.extend(abie_by_den.values())
    return deduped

def write_csv(rows, out_path):
    fieldnames = [
        "Version",
        "UNID",
        "Acronym",
        "Dictionary Entry Name",
        "ObjectClassQualifierTerm",
        "ObjectClassTerm",
        "Cardinality",
        "PropertyTerm",
        "PrimaryRepresentationTerm",
        "XML datatype",
        "AssociatedObjectClassQualifierTerm",
        "AssociatedObjectClassTerm",
        "XML element name",
        "Definition",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

# 使い方：
# 単一ファイル
# rows = extract_rows_from_xsd("SME_Common/15JUL23XMLSchemas-D23A/uncefact/data/standard/ReusableAggregateBusinessInformationEntity_33p0.xsd")
# write_csv(rows, "SME_Common/D23A_abie_mapping.csv")
rows = extract_rows_from_xsd("SME_Common/XMLSchemas-D23B/13DEC23/uncefact/data/standard/ReusableAggregateBusinessInformationEntity_34p0.xsd")
write_csv(rows, "SME_Common/D23B_abie_mapping.csv")

# フォルダ内の複数XSDをまとめて処理したい場合：
# rows_all = []
# for p in Path("schemas").glob("**/*.xsd"):
#     rows_all.extend(extract_rows_from_xsd(p))
# write_csv(rows_all, "abie_mapping_all.csv")
