import csv

BASE_DIR = "XBRL-GL-2026"
INPUT_CSV = f"{BASE_DIR}/xbrl-gl.csv"                 # 元の定義CSV
OUTPUT_CSV = f"{BASE_DIR}/XBRL-GL_2016_FSM_ini.csv" # 出力CSV（tupleとその直下の子要素）

class_TYPE = "_"  # type列がこれならtupleとみなす

def parse_level(row):
    """level列をintに変換（空や不正値ならNone）"""
    try:
        return int(str(row.get("level", "")).strip())
    except ValueError:
        return None


def is_class_row(row):
    """tuple行かどうかを判定"""
    return (row.get("type") or "").strip() == class_TYPE


def main():
    # 入力 CSV 読み込み
    with open(INPUT_CSV, "r", encoding="utf-8-sig", newline="") as f_in:
        reader = csv.DictReader(f_in)
        rows = list(reader)
        fieldnames = reader.fieldnames

    # level をパースして保持
    for r in rows:
        r["_level_int"] = parse_level(r)

    output_rows = []

    # 各 tuple 行ごとに直下の子要素を探索
    class_dict = {}
    for i, row in enumerate(rows):
        if not is_class_row(row):
            continue
        class_level = row["_level_int"]
        if class_level is None:
            continue

        class_element = row.get("element", "")
        class_dict[class_element] = row
        class_dict[class_element]["property"] = []

        # i+1 以降を見て、自分よりlevelが小さい/同じになったらそこで終了
        j = i + 1
        while j < len(rows):
            property = rows[j]
            property_level = property["_level_int"]

            # level 未設定の行はスキップ
            if property_level is None:
                j += 1
                continue

            # 自分と同じか小さくなったら、この tuple の範囲は終了
            if property_level <= class_level:
                break

            # 直下の子: level がちょうど class_level + 1
            if property_level == class_level + 1:
                class_dict[class_element]["property"].append(property)

            j += 1

    for v in class_dict.values():
        class_term = v['label']
        class_element = v['element']
        output_rows.append({
            "seq": v["seq"],
            "level": 1,
            "Property_type": "Class",
            "identifier": "", 
            "class": class_term,
            "Property_term": "",
            "representation": "",
            "associated_class": "",
            "card": "",
            "description": v['description'],
            "module": v['module'],
            "element": class_element,
            "label_ja": v['label_ja'],
            "description_ja": v['description_ja']
        })

        for property in class_dict[class_element]["property"]:
            property_element = property['element']
            if property_element in class_dict:
                Property_type = "Composition"
            else:
                Property_type = "Attribute"
            output_rows.append({
                "seq":property["seq"],
                "level": 2,
                "Property_type": Property_type, 
                "identifier": "",
                "class": class_term,
                "Property_term": property['label'] if Property_type == "Attribute" else '',
                "representation": property['xbrli'],
                "associated_class": property['label'] if Property_type == "Composition" else '',
                "card": property['card'], 
                "description": property['description'],
                "module": property['module'],
                "element": property_element,
                "label_ja": property['label_ja'],
                "description_ja": property['description_ja']
            })

        # print(f"{class_term} {len(output_rows)} 行登録しました")

    # 出力CSVのヘッダ定義
    out_fields = [
        "seq", "level", "Property_type", "aligned", "identifier", "class", "Property_term", "representation", 
        "associated_class", "card", "description", "module", "element", "label_ja", "description_ja"
    ]
    
    # 書き出し
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"{len(output_rows)} 行出力しました: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
