"""
sme_prepare.py
Generates Business Semantic Model (BSM) and Logical Hierarchical Model (LHM) CSV

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-05-18
Last Modified: 2025-05-19

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

【凡例】
"中小企業共通EDIマッピング"
    ◎  適格請求書に記載が必要な「法的必須」情報項目
    （◎）同じクラス内のいずれかの情報項目の記載が「法的必須」
    ○中小企業共通EDI対応業務アプリの「共通必須」情報情報項目
    （○）同じクラス内のいずれかの情報項目の記載が「必須」
    ●「選択必須」情報項目。この情報項目を利用する場合は「必須」。利用しない場合はデフォルトで運用と見做す
    △ユーザー非公開。共通EDIプロバイダがデータセット
    ＊すべての業種に共通して利用する「共通任意」情報項目
    ◇「中小業界必須」情報項目
    ＋「中小業界任意」情報項目
    □税込会計対応のために追加した情報項目
    ■源泉所得税のために追加した情報項目
    ▼修正適格請求書等（修正差額調整）のために追加した情報項目
    ▶違算（請求と入金の不突合）のために追加した情報項目
    ▽取引と会計のデータ連携のために追加した情報項目
    ※税理士が会計システムへ取引データ入力時に利用する情報項目
    （※）将来取引データプラットフォームの確定時に利用する情報項目
    利用しない情報項目
JP-PINT_v1.0マッピング（参考）
☆JP-PINT対応業務アプリの「必須」実装情報項目
★JP-PINT対応業務アプリの「任意」実装情報項目。（★）は同じクラス内のいずれかの情報項目を利用する
空欄JP-PINTには該当する情報項目はない
共通EDIプロバイダはBIE表記載の全情報項目の共通EDIプロバイダ間交換が必須

【凡例２】制定/改定欄の黄色セル：標準ver.4.3で新設、又は改定された情報項目。v4.3と記載。
"""
import os
import re
import math
import csv

DEBUG = True
TRACE = True

character_list = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
unid_map = {}

def debug_print(message):
    if DEBUG:
        print(f"[DEBUG] {message}")

def trace_print(message):
    if TRACE:
        print(f"[TRACE] {message}")

def file_path(pathname):
    _pathname = pathname.replace("/", os.sep)
    if os.sep == _pathname[0]:
        return _pathname
    dir = os.path.dirname(__file__)
    return os.path.join(dir, _pathname)

# def normalize_text(text):
#     REMOVE_CHARS = " -._"
#     # Replace "-", ".", and "_" with a space
#     replaced = text.translate(str.maketrans('', '', REMOVE_CHARS))
#     # Replace multiple spaces with a single space and trim leading/trailing spaces
#     normalized = re.sub(r'\s+', " ", replaced).strip()
#     return normalized
# def encode_base62(number):
#     # Characters used in base62 encoding (0–9, a–z, A–Z)
#     # Special case for 0
#     if number == 0:
#         return character_list[0]
#     result = ""
#     # Convert the number to base62 by repeated division
#     while number > 0:
#         number, remainder = divmod(number, 62)
#         result = character_list[remainder] + result  # Prepend corresponding character
#     return result

# def decode_base62(encoded):
#     # Characters used in base62 encoding
#     base = 62
#     result = 0
#     # Convert base62 string back to a decimal number
#     for char in encoded:
#         result = result * base + character_list.index(char)
#     return result

# def revise_unid(acronym, unid):
#     if acronym in ["MA", "ABIE"]:
#         if unid[2:].isdigit():
#             num = int(unid[3:])
#             encoded = encode_base62(num)
#             class_unid = unid[:2] + encoded
#         else:
#             class_unid = unid
#         _unid = class_unid
#         suffix_num = 0
#     else:
#         suffix_num += 1
#         _unid = f"{class_unid}_{str(suffix_num).zfill(2)}"
#     return _unid, suffix_num

def main():
    global TRACE, DEBUG
    """
    Read from the CSV file

    sequence group UNID acronym
    name1 name2 name3 name4 name5 name6 name7 name8 name9 name10 name11 name12 name13 name14
    label_local definition_local
    multiplicity example version code_list issueing_agency input value
    selfbilling_statement self_billing selfbilling_exception journal_entry
    ver1 AG JPPINT_ID business_term cardinality
    """
    lhm_records = []
    mbie_dict = {}
    bsm_dict = {}
    base_dir = "SME_Common"
    mbie_file = os.path.join(base_dir,"CCL 24A_21SEP24_MBIE.csv")

    def get_den(row):
        den = None
        l = None
        if row["name1"].strip():
            l = 1
            den = row["name1"].strip()
        elif row["name2"].strip():
            l = 2
            den = row["name2"].strip()
        elif row["name3"].strip():
            l = 3
            den = row["name3"].strip()
        elif row["name4"].strip():
            l = 4
            den = row["name4"].strip()
        elif row["name5"].strip():
            l = 5
            den = row["name5"].strip()
        elif row["name6"].strip():
            l = 6
            den = row["name6"].strip()
        elif row["name7"].strip():
            l = 7
            den = row["name7"].strip()
        elif row["name8"].strip():
            l = 8
            den = row["name8"].strip()
        elif row["name9"].strip():
            l = 9
            den = row["name9"].strip()
        elif row["name10"].strip():
            l = 10
            den = row["name10"].strip()
        elif row["name11"].strip():
            l = 11
            den = row["name11"].strip()
        elif row["name12"].strip():
            l = 12
            den = row["name12"].strip()
        elif row["name13"].strip():
            l = 13
            den = row["name13"].strip()
        elif row["name14"].strip():
            l = 14
            den = row["name14"].strip()
        return l, den

    def normalize_text(text):
        remove_words = "(CIILB_|CIIL_|CIIH_|CI_|Applicable|Defined|Specified|Supply Chain|Additional|Including|Included|Processing|Details)"
        remove_chars = " ._"
        _text = re.sub(remove_words, "", text).translate(
            str.maketrans("", "", remove_chars)
        )
        if _text.endswith("IdentificationIdentifier"):
            _text = _text.replace("IdentificationIdentifier", "ID")
        elif _text.endswith("IdentificationID"):
            _text = _text.replace("IdentificationID", "ID")        
        elif _text.endswith("Identifier"):
            _text = _text.replace("Identifier", "ID")
        elif _text.endswith("NameText"):
            _text = _text.replace("NameText", "Name")
        return _text

    def element_from_class(class_term):
        return normalize_text(class_term)

    def element_from_property(property):
        return normalize_text(property)

    def split_camel_case(text):
        if not text:
            return ""
        # 連続大文字（略語）とその直後の大文字小文字の区切りで分割
        pattern = r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])'
        splitted = re.split(pattern, text)
        return " ".join(splitted)

    def remove_duplicates(word_list):
        seen = set()
        result = []
        for word in word_list:
            if word not in seen:
                seen.add(word)
                result.append(word)
        return result

    def add_missing_prefix_words(prefix_word, name_word):
        prefix_list = [normalize_text(text) for text in prefix_word.split()]
        name_list = [normalize_text(text) for text in name_word.split()]
        # name_words に含まれていない prefix_words の単語を抽出
        missing = [word for word in remove_duplicates(prefix_list) if word not in remove_duplicates(name_list)]
        # それらを name_words の先頭に追加
        combined = missing + name_list
        return ' '.join(combined)

    def get_name(data, path_list, level):
        sequence = data["sequence"]
        acronym = data["acronym"]
        den = data["DEN"]
        _1st_prefix = split_camel_case(path_list[0])
        _2nd_prefix = split_camel_case(path_list[1])
        _3rd_prefix = split_camel_case(path_list[2])
        _4th_prefix = split_camel_case(path_list[3])
        _5th_prefix = split_camel_case(path_list[4])
        _6th_prefix = split_camel_case(path_list[5])
        _1st_text = normalize_text(
            add_missing_prefix_words(_1st_prefix, den) if 1 == level else _1st_prefix
        )
        _2nd_text = normalize_text(
            add_missing_prefix_words(_2nd_prefix, den) if 2 == level else _2nd_prefix
        )
        _3rd_text = normalize_text(
            add_missing_prefix_words(
                add_missing_prefix_words(_2nd_prefix, _3rd_prefix), den
            )
            if 3 == level
            else _3rd_prefix
        )
        _4th_text = normalize_text(
            add_missing_prefix_words(
                add_missing_prefix_words(_3rd_prefix, _4th_prefix), den
            )
            if 4 == level
            else _4th_prefix
        )
        _5th_text = normalize_text(
            add_missing_prefix_words(
                add_missing_prefix_words(
                    add_missing_prefix_words(_3rd_prefix, _4th_prefix), _5th_prefix
                ),
                den,
            )
            if 5==level
            else ""
        )
        _6th_text = normalize_text(
            add_missing_prefix_words(
                add_missing_prefix_words(
                    add_missing_prefix_words(
                        add_missing_prefix_words(_3rd_prefix, _4th_prefix), _5th_prefix
                    ),
                    _6th_prefix,
                ),
                den,
            )
            if level > 5
            else ""
        )
        den_text = normalize_text(den)
        if acronym in ["ASMA"]:#, "ABIE"]:
            debug_text = (f"level:{level}"
                + f" {'*' if 0==level else ''}1:'{_1st_text}'"
                + f" {'*' if 1==level else ''}2:'{_2nd_text}'"
                + f" {'*' if 2==level else ''}3:'{_3rd_text}'"
                + f" {'*' if 3==level else ''}4:'{_4th_text}'"
                + f" {'*' if 4==level  else ''}5:'{_5th_text}'"
                + f" {'*' if level>4  else ''}6:'{_6th_text}'"
                + f" {acronym} {den_text}"
            )
        else:
            debug_text = (f"level:{level}"
                + f" {'*' if 1==level else ''}1:'{_1st_text}'"
                + f" {'*' if 2==level else ''}2:'{_2nd_text}'"
                + f" {'*' if 3==level else ''}3:'{_3rd_text}'"
                + f" {'*' if 4==level else ''}4:'{_4th_text}'"
                + f" {'*' if 5==level else ''}5:'{_5th_text}'"
                + f" {'*' if level>5 else ''}6:'{_6th_text}'"
                + f" {acronym} {den_text}"
            )
        debug_print(debug_text)
        if 1==level:
            name = _1st_text
        else:
            if acronym in ["ASMA"]:
                if 2==level:
                    name = _3rd_text
                elif 3==level:
                    name = _4th_text
                elif 4==level:
                    name = _5th_text
                else:
                    name = _6th_text
            else:
                if 2==level:
                    name = _2nd_text
                elif 3==level:
                    name = _3rd_text
                elif 4==level:
                    name = _4th_text
                elif 5==level:
                    name = _5th_text
                else:
                    name = _6th_text
        if name.startswith("Agreement"):
            _name = name[9:]
        elif name.startswith("TransactionTradeLineItemTrade"):
            _name = name.replace("TransactionTradeLineItemTrade","Document")
        elif name.startswith("TradeTransactionTrade"):
            _name = name[21:]
        elif name.startswith("TransactionTradeSettlement"):
            _name = name[16:]
        elif name.startswith("TradeSettlement"):
            _name = name[15:]
        elif name.startswith("LineItemSettlementTrade"):
            _name = name.replace("LineItemSettlementTrade","Document")
        elif name.startswith("LineItemSettlement"):
            _name = name.replace("LineItemSettlement","Document")
        elif name.startswith("LineItemTrade"):
            _name = name.replace("LineItemTrade","Document")
        elif name.startswith("ItemTradeSettlement"):
            _name = name.replace("ItemTradeSettlement","Document")
        elif name.startswith("SubordinateLineItem"):
            _name = name.replace("SubordinateLineItem","Line")
        elif name.startswith("SubordinateLine"):
            _name = name.replace("SubordinateLine","Line")
        elif name.startswith("SubordinateTradeLineItem"):
            _name = name.replace("SubordinateTradeLineItem","Line")
        elif name.startswith("SubordinateDocumentTrade"):
            _name = name.replace("SubordinateDocumentTrade","Line")
        elif name.startswith("SubordinateDocumentFinancialAdjustmentTrade"):
            _name = name.replace("SubordinateDocumentFinancialAdjustmentTrade","LineFinancialAdjustment")
        elif name.startswith("SubordinateDocumentFinancialAdjustment"):
            _name = name.replace("SubordinateDocumentFinancialAdjustment","LineFinancialAdjustment")
        elif name.startswith("SubordinateDocument"):
            _name = name.replace("SubordinateDocument","Line")
        elif name.startswith("SubordinateItemTrade"):
            _name = name.replace("SubordinateItemTrade","Line")
        elif name.startswith("TransactionTradeLineItem"):
            _name = name.replace("TransactionTradeLineItem","Line")
        else:
            _name = name
        return _name

    with open(mbie_file, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)  # Uses first row as keys
        for row in reader:
            unid = row["unid"]
            mbie_dict[unid] = {
                "acronym": row["acronym"],
                "DEN": row["DEN"],
                "Definition": row["Definition"],
                "Occurrence_Min": row["Occurrence_Min"],
                "Occurrence_Max": row["Occurrence_Max"],
                "TDED": row["TDED"],
                "Short_Name": row["Short_Name"],
            }

    in_file = os.path.join(base_dir,"sme_common06-02.csv")
    lhm_file = os.path.join(base_dir,"SME_common06-02_LHM.csv")
    bsm_file = os.path.join(base_dir,"SME_common06-02_BSM.csv")
    with open(in_file, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)  # Uses first row as keys
        PATH_LENGTH = 15
        path_list = [None]*PATH_LENGTH

        for row in reader:
            acronym = row["acronym"]
            if "END"==acronym:
                break

            lhm_data = {
                "version": "",
                "sequence": "",
                "level": "",
                "type": "",
                "identifier": "",
                "UNID": "",
                "acronym": "",
                "label_local": "",
                "multiplicity": "",
                "class_term": "",
                "property_term": "",
                "representation_term": "",
                "associated_class": "",
                "definition_local": "",
                "code_list": "",
                "attribute": "",
                "DEN": "",
                "definition": "",
                "short_name": "",
                "element": "",
                "xpath": ""
            }

            bsm_data = {}

            for key in lhm_data.keys():
                if key in row:
                    lhm_data[key] = row[key].strip()

            l, den = get_den(row)

            lhm_data["DEN"] = den

            if "." in den:
                den = den.split(".")
                class_term = den[0].strip()
            else:
                class_term = den
            lhm_data["class_term"] = class_term

            level = math.floor((2 + l)/2)
            lhm_data["level"] = level

            unid = row["UNID"]
            if unid and unid in mbie_dict:
                mbie = mbie_dict[unid]
                if mbie:
                    lhm_data["definition"] = mbie["Definition"]
                    lhm_data["short_name"] = mbie["Short_Name"]

            if "MA"==acronym:
                lhm_data["type"] = "C"
                lhm_data["level"] = 0
                element = element_from_class(class_term)
                lhm_data["element"] = element
                xpath = f'/{element}'
                lhm_data["xpath"] = xpath
                path_list[0] = element
                bsm_data = lhm_data.copy()
                bsm_data["property_type"] = "Class"
                bsm_data["level"] = 1
            elif "ASMA"==acronym:
                lhm_data["type"] = "C"
                lhm_data["level"] = 1
                element = element_from_class(class_term)
                lhm_data["element"] = element
                path_list[1] = element
                xpath = f'/{path_list[0]}/{path_list[1]}'
                lhm_data["xpath"] = xpath
                bsm_data = lhm_data.copy()
                bsm_data["property_type"] = "Composition"
                bsm_data["level"] = 2
            elif "BBIE"==acronym:
                lhm_data["type"] = "A"
                lhm_data["property_term"] = den[1].strip()
                lhm_data["representation_term"] = den[2].strip()
                if "Identifier"==lhm_data["representation_term"] and "1..1"==lhm_data["multiplicity"]:
                    lhm_data["identifier"] = "PK"
                element = element_from_property(
                    f'{lhm_data["property_term"]}. {lhm_data["representation_term"]}'
                )
                if element.endswith("IdentificationIdentifier"):
                    element = element.replace("IdentificationIdentifier", "ID")
                elif element.endswith("Identifier"):
                    element = element.replace("Identifier", "ID")
                elif element.endswith("Text"):
                    element = element.replace("Text", "")
                lhm_data["element"] = element
                path_list[level] = element
                xpath = f'/{path_list[0]}'
                for i in range(1,1+level):
                    xpath += f'/{path_list[i]}'
                lhm_data["xpath"] = xpath
                bsm_data = lhm_data.copy()
                bsm_data["property_type"] = "Attribute"
                bsm_data["level"] = 2
            elif "ASBIE"==acronym:
                lhm_data["type"] = "C"
                lhm_data["property_term"] = den[1].strip()
                lhm_data["associated_class"] = den[2].strip()
                element = element_from_property(
                    f'{lhm_data["property_term"]}. {lhm_data["associated_class"]}'
                )
                lhm_data["element"] = element
                path_list[level] = element
                xpath = f"/{path_list[0]}"
                for i in range(1,1+level):
                    xpath += f'/{path_list[i]}'
                lhm_data["xpath"] = xpath
                bsm_data = lhm_data.copy()
                bsm_data["property_type"] = "Composition"
                bsm_data["level"] = 2
            elif "ABIE"==acronym:
                element = element_from_class(class_term)
                lhm_data["element"] = element
                bsm_data = lhm_data.copy()
                bsm_data["property_type"] = "Class"
                bsm_data["level"] = 1

            name = get_name(lhm_data, path_list, level)
            lhm_data["name"] = name

            if "ABIE"!=acronym:
                lhm_records.append(lhm_data)

            if "MA"==acronym and 1==level:
                root = class_term
                bsm_dict[root] = {}
                bsm_data["property_type"] = "Class"
                bsm_dict[root]["_data"] = bsm_data
            elif "ASMA"==acronym and 1==level:
                _bsm_data = bsm_data.copy()
                bsm_data["associated_class"] = class_term
                association = bsm_data["class_term"]
                bsm_dict[root][association] = bsm_data
                # Overwrite bsm_data
                _bsm_data["level"] = 1
                _bsm_data["property_type"] = "Class"
                _bsm_data["multiplicity"] = "-"
                if class_term not in bsm_dict:
                    bsm_dict[class_term] = {}
                bsm_dict[class_term]["_data"] = _bsm_data
            elif "ABIE"==acronym:
                if class_term not in bsm_dict:
                    bsm_dict[class_term] = {}
                bsm_dict[class_term]["_data"] = bsm_data
            elif "BBIE"==acronym and "property_term" in bsm_data:
                bsm_data["property_term"] = den[1].strip()
                bsm_data["representation_term"] = den[2].strip()
                attribute = f'{bsm_data["property_term"]}. {bsm_data["representation_term"]}'
                bsm_dict[class_term][attribute] = bsm_data
            elif "ASBIE"==acronym:
                bsm_data["property_term"] = den[1].strip()
                bsm_data["associated_class"] = den[2].strip()
                if "associated_class" in bsm_data:
                    association = f'{bsm_data["property_term"]}. {bsm_data["associated_class"]}'
                    if association not in bsm_dict[class_term]:
                        bsm_data["element"] = normalize_text(association) #.translate(str.maketrans('', '', remove_chars))
                        bsm_dict[class_term][association] = bsm_data
            # debug_print(
            #     f'{bsm_data["sequence"]} level:{bsm_data["level"]} {bsm_data["property_type"]} class_term:"{class_term}" property_term:"{bsm_data["property_term"]}" representation_term:"{bsm_data["representation_term"]}" multiplicity:{bsm_data["multiplicity"]} associated_class:"{bsm_data["associated_class"]}" "{bsm_data["label_local"]}" "{bsm_data["DEN"]}" {bsm_data["UNID"]}'
            # )

    bsm_records = []
    for class_term, c_data in bsm_dict.items():
        if "_data" in c_data:
            _data = c_data["_data"]
            _bsm_data = {
                "version": _data["version"],
                "sequence": _data["sequence"],
                "level": _data["level"],
                "property_type": _data["property_type"],
                "identifier": _data["identifier"],
                "class_term": class_term,
                "property_term": _data["property_term"],
                "representation_term": _data["representation_term"],
                "associated_class": _data["associated_class"],
                "multiplicity": _data["multiplicity"],
                "definition": "",
                "acronym": _data["acronym"],
                "code_list": _data["code_list"],
                "element": _data["element"],
                "label_local": _data["label_local"],
                "definition_local": _data["definition_local"],
                "DEN": _data["DEN"],
                "UNID": _data["UNID"]
            }
        else:
            print(f"[ERROR] {class_term} has no _data.")
        bsm_records.append(_bsm_data)

        for name, data in c_data.items():
            if "_data"==name:
                continue
            bsm_data = {
                "version": data["version"],
                "sequence": data["sequence"],
                "level": data["level"],
                "property_type": data["property_type"],
                "identifier": data["identifier"],
                "class_term": class_term,
                "property_term": data["property_term"],
                "representation_term": data["representation_term"],
                "associated_class": data["associated_class"],
                "multiplicity": data["multiplicity"],
                "definition": "",
                "acronym": data["acronym"],
                "code_list": data["code_list"],
                "element": data["element"],
                "label_local": data["label_local"],
                "definition_local": data["definition_local"],
                "DEN": data["DEN"],
                "UNID": data["UNID"]
            }
            bsm_records.append(bsm_data)

    # Write to a CSV file
    # lhm_field_names = list(lhm_records[0].keys())
    lhm_field_names = ["version", "sequence", "level", "type", "identifier", "UNID", "acronym", "label_local", "multiplicity", "class_term", "property_term", "representation_term", "associated_class", "definition_local", "code_list", "attribute", "DEN", "definition", "short_name", "name", "element", "xpath"]
    with open(lhm_file, mode="w", newline="", encoding="utf-8-sig") as lhmfile:
        writer = csv.DictWriter(lhmfile, fieldnames=lhm_field_names)
        writer.writeheader()
        writer.writerows(lhm_records)
    trace_print(f'Wrote {lhm_file}')

    bsm_field_names = list(bsm_records[0].keys())
    with open(bsm_file, mode="w", newline="", encoding="utf-8-sig") as bsmfile:
        writer = csv.DictWriter(bsmfile, fieldnames=bsm_field_names)
        writer.writeheader()
        writer.writerows(bsm_records)
    trace_print(f'Wrote {bsm_file}')

    trace_print("END")

if __name__=="__main__":
    main()
