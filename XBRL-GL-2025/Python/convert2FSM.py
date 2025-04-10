import csv

header_in = ["seq", "level", "module", "parent", "element", "label", "label_ja"]
header_out = [
    "seq",
    "level",
    "Property type",
    "Identifier",
    "class",
    "Property term",
    "representation",
    "Associate class",
    "multiplicity",
    "description",
    "module",
    "table",
    "domain_name",
    "element",
    "label_local",
    "definition_local",
    "note",
]

in_file = "XBRL-GL-2025/XBRL-GL-SRCD-2025.csv"
out_file = "XBRL-GL-2025/XBRL-GL-FSM-2025.csv"
encoding = "utf-8-sig"


def getRecord(id, key, list):
    record = next((x for x in list if id == x[key]), None)
    return record


def main():
    with open(in_file, encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, fieldnames=header_in)
        h = next(reader)
        element_list = []
        # First pass: Register Abstract Classes and Classes
        for row_number, row in enumerate(reader, start=1):
            if not row["seq"] and not row["level"]:
                continue
            record = {}
            for key in header_in:
                if key in row:
                    record[key] = row[key].rstrip()
                else:
                    record[key] = ""
            level = record["level"]
            if not level.isdigit():
                continue
            seq = record["seq"].lstrip("#")
            seq = int(seq)
            record["seq"] = seq
            level = int(level)
            parent = record["parent"]
            element = record["element"]
            if parent:
                parent_element = getRecord(parent, "element", element_list)
                if "children" not in parent_element:
                    parent_element["children"] = []
                parent_element["children"].append(element)
            element_list.append(record)

        class_list = []
        for record in element_list:
            if "children" in record:
                class_list.append(record)

        fsm_list = []
        seq = 1
        for record in class_list:
            out_record = {}
            seq += 1
            out_record["seq"] = seq
            out_record["level"] = 1
            out_record["Property type"] = "Class"
            element = record["element"]
            out_record["element"] = element
            class_term = record["label"]
            out_record["class"] = class_term
            out_record["Property term"] = ""
            out_record["module"] = record["module"]
            out_record["label_local"] = record["label_ja"]
            fsm_list.append(out_record)
            children = record["children"]
            for child_href in children:
                out_record = {}
                seq += 1
                child = getRecord(child_href, "element", element_list)
                out_record["seq"] = seq
                out_record["level"] = 2
                out_record["class"] = class_term
                out_record["module"] = child["module"]
                element = child["element"]
                out_record["element"] = element
                exists = any(item['element'] == element for item in class_list)
                if exists:
                    out_record["Property type"] = "Composition"
                    out_record["Associate class"] = child["label"]
                else:
                    out_record["Property type"] = "Attribute"
                    out_record["Property term"] = child["label"]
                out_record["label_local"] = child["label_ja"]
                fsm_list.append(out_record)

        # Write to CSV file
        with open(out_file, mode='w', newline='', encoding=encoding) as file:
            writer = csv.DictWriter(file, fieldnames=header_out)
            writer.writeheader()            
            for row in fsm_list:
                # Ensure all expected keys exist in row
                writer.writerow({key: row.get(key, "") for key in header_out})

        print(f"END {out_file}")


if __name__ == "__main__":
    main()
