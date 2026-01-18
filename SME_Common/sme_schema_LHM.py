#!/usr/bin/env python3
# coding: utf-8
"""
sme_schema.py
Generates Schema file for SME Common EDI from Logical Hierarchical Model (LHM) CSV

Designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
Written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-05-18
Last Modified: 2025-10-06

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
import os
import sys
import argparse
import csv
import re
from typing import List, Literal

def file_path(pathname):
    _pathname = pathname.replace("/", os.sep)
    if os.sep == _pathname[0:1]:
        return _pathname
    else:
        dir = os.path.dirname(__file__)
        return os.path.join(f"{dir}", _pathname)

class SchemaModule:
    def __init__ (
            self,
            lhm_file,
            DATE,
            root_term,
            remove_chars,
            encoding,
            annotation,
            trace,
            debug,
            html,
            dump,
        ):

        self.lhm_file = lhm_file.replace('/', os.sep)
        self.lhm_file = file_path(f'{self.lhm_file}')
        if not self.lhm_file or not os.path.isfile(self.lhm_file):
            self.print_error(f'No input Semantic file {self.lhm_file}.')
            sys.exit()

        self.REMOVE_CHARS = remove_chars
        self.encoding = encoding.strip() if encoding else 'utf-8-sig'

        # Set debug and trace flags, and file path separator
        self.root_element = self.normalize_text(root_term)

        self.schema_file = f'{self.root_element}_LHM_{DATE}.xsd'
        self.schema_file = file_path(self.schema_file)

        self.target_file = self.lhm_file[:self.lhm_file.index(".")]
        self.target_file = f'{self.target_file}_tgt.csv'
        self.target_file = file_path(self.target_file)

        self.ANNOTATION = annotation
        self.TRACE = trace
        self.DEBUG = debug
        self.HTML  = html
        self.DUMP  = dump
        self.LHM_FIELDS = [
            "version",
            "sme_nr",
            "mbie_nr",
            "acronym",
            "level",
            "multiplicity",
            "multiplicity_sme",
            "label_sme",
            "definition_sme",
            "level_csv",
            "multiplicity_csv",
            "label_csv",
            "label_ja",
            "definition_ja",
            "UNID",
            "DEN",
            "short_name",
            "definition",
            "property_type",
            "class_term",
            "sequence",
            "identifier",
            "property_term",
            "representation_term",
            "code_list",
            "XML_datatype",
            "associated_class",
            "selector",
            "fixed_value",
            "element",
            "XML_element_name",
            "xpath",
        ]

        WS = "  "
        self.version_date = "20250901"
        self.version_num = "4p3"
        self.html = [
            '<!-- ====================================================================== -->',
            f'<!-- ===== {self.root_element} Schema Module {" " * (59 - len(f"{self.root_element} Schema Module "))}===== -->',
            '<!-- ====================================================================== -->',
            '<!--',
            'Schema agency:  ITCA',
            'Schema version: ver 4.3',
            'Schema date:    2025-09-01',
            '-->',
            '<xsd:schema',
            2*WS + f'targetNamespace="urn:un:unece:uncefact:data:standard:{self.root_element}:{self.version_num}" ',
            2*WS + 'xmlns:xsd="http://www.w3.org/2001/XMLSchema"',
            2*WS + 'xmlns:ccts="urn:un:unece:uncefact:documentation:standard:CoreComponentsTechnicalSpecification:2" ',
            2*WS + 'xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:34"',
            2*WS + 'xmlns:qdt="urn:un:unece:uncefact:data:standard:QualifiedDataType:34"',
            2*WS + f'xmlns:rsm="urn:un:unece:uncefact:data:standard:{self.root_element}:{self.version_num}" ',
            2*WS + 'elementFormDefault="qualified" attributeFormDefault="unqualified" ',
            2*WS + f'version="{self.version_date}">',
            '<!-- ======================================================================= -->',
            '<!-- ===== Imports                                                     ===== -->',
            '<!-- ======================================================================= -->',
            '<!-- ======================================================================= -->',
            '<!-- ===== Import of Unqualified Data Type Schema Module               ===== -->',
            '<!-- ======================================================================= -->',
            WS + '<xsd:import namespace="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:34" schemaLocation="XMLSchemas-D23B/13DEC23/uncefact/data/standard/UnqualifiedDataType_34p0.xsd"/>',
            '<!-- ======================================================================= -->',
            '<!-- ===== Import of Qualified Data Type Schema Module                 ===== -->',
            '<!-- ======================================================================= -->',
            WS + '<xsd:import namespace="urn:un:unece:uncefact:data:standard:QualifiedDataType:34" schemaLocation="XMLSchemas-D23B/13DEC23/uncefact/data/standard/QualifiedDataType_34p0.xsd"/>',
            '<!-- ======================================================================= -->',
            '<!-- ===== Element Declarations                                        ===== -->',
            '<!-- ======================================================================= -->',
            '<!-- ===== Root Element Declarations                                   ===== -->',
            '<!-- ======================================================================= -->',
        ]

    def plain_print(self, message):
        if self.HTML:
            print(message)

    def debug_print(self, message):
        if self.DEBUG:
            print(f"[DEBUG] {message}")

    def error_print(self, message):
        if self.TRACE or self.DEBUG:
            print(f"[ERROR] {message}")

    def trace_print(self, message):
        if self.TRACE or self.DEBUG:
            print(f"[TRACE] {message}")

    def normalize_text(self, text):
        # remove_words = "(CIILB_|CIIL_|CIIH_|CI_|Applicable|Defined|Specified|Supply Chain|Additional|Including|Included|Processing|Details)"
        remove_words = r"<Hdr>|<Lin>"
        remove_chars = " ._/()-"
        _text = re.sub(remove_words, "", text).translate(
            str.maketrans("", "", remove_chars)
        )
        if _text.endswith("IdentificationIdentifier"):
            _text = _text.replace("IdentificationIdentifier", "ID")
        elif _text.endswith("IdentificationID"):
            _text = _text.replace("IdentificationID", "ID")
        elif _text.endswith("Identifier"):
            _text = _text.replace("Identifier", "ID")
        elif _text.endswith("Text"):
            _text = _text.replace("Text", "")
        return _text

    def last_part_without_brackets(self, part):
        if not part:
            return ""
        s = part.strip()
        # 先頭と末尾が括弧なら外す
        if s.startswith("(") and s.endswith(")"):
            s = s[1:-1].strip()
        # '/' で分割して最後を取る
        tail = s.split("/")[-1].strip()
        # 角括弧 [ ... ] を除去
        tail = re.sub(r"\[[^\]]*\]", "", tail).strip()
        # 念のため余分な閉じ括弧を除去
        tail = tail.rstrip(")")
        return tail

    def normalize_attribute(self, text):
        """
        re.X（verbose）で可読性を上げ、行内にコメントを記述
        全体像：
          ^\s*                     … 先頭の空白を許容
          (?P<class> … )           … 「クラス名＋[selector]」の塊（必須）
          \s*
          (?P<prop>  … )?          … 「(property path …)」の塊（任意）
          \s*
          (?P<cat>   … )?          … 「<category>」の塊（任意）
          \s*$                     … 末尾の空白を許容して終了
        """
        pat = re.compile(r"""
            ^\s*
            (?P<class>
                # class 部は、次に出てくる '('（property 開始）や '<'（category 開始）
                # までは取り込みたい。ただし、途中の '[ ... ]'（selector）は
                # かたまりとして残す必要がある。
                (?:                     # ← 非キャプチャで A|B の並びを 1 回以上
                    [^[(<]+             # A: '[', '(', '<' 以外の通常文字を 1 文字以上
                    |                   #    （空白含む。次の特別記号が来るまで貪欲に）
                    \[[^\]]*\]          # B: 角括弧ブロック全体 '[ ... ]' をまるごと
                                        #    （中に '(' や '<' があっても ']' まで飲み込む）
                )+
            )
            \s*
            (?P<prop>
                # prop 部は ( ... ) 全体を 1 かたまりで取得（任意）。
                # 丸括弧の内部に '[ ... ]' が来ても壊れないよう、
                #   ・ '[^\[\)]'  … '[' と ')' 以外なら 1 文字として消費
                #   ・ '\[[^\]]*\]' … 角括弧ブロックは ']' まで一気に消費
                \(
                    (?:[^\[\)]|\[[^\]]*\])*
                \)
            )?
            \s*
            (?P<cat>
                # cat 部は < ... > 全体（任意）
                <[^>]*>
            )?
            \s*$
        """, re.X)
        m = pat.match(text)
        if m:
            part1 = m.group("class").strip()
            part2 = (m.group("prop") or "").strip()
            part3 = (m.group("cat") or "").strip()
        base = part1 # re.sub(r"\[[^\]]*?\]\s*", "", part1)
        # ( ... ) から最後のパスを取り出し、末尾要素を prefix に
        prefix = self.last_part_without_brackets(part2)
        element = ("%s. %s" % (prefix, base)) if prefix else base
        element = re.sub(r"\[[^\]]*\]", "", element).strip()
        return element

    def annotation(self, unid, acronym, den, short_name, definition, label_sme, definition_sme, multiplicity, multiplicity_sme, leading_level=0):
        if not self.ANNOTATION:
            return ""
        WS = "  "
        html = [
            WS*(3*(leading_level - 1) + 2) + '<xsd:annotation>',
            WS*(3*(leading_level - 1) + 3) + '<xsd:documentation xml:lang="en">'
        ]
        if unid:
            html.append(WS*(3*(leading_level - 1) + 4) + f'<ccts:UniqueID>{unid}</ccts:UniqueID>')
        if acronym:
            html.append(WS*(3*(leading_level - 1) + 4) + f'<ccts:Acronym>{acronym}</ccts:Acronym>')
        if den:
            html.append(WS*(3*(leading_level - 1) + 4) + f'<ccts:DictionaryEntryName>{den}</ccts:DictionaryEntryName>')
        if short_name:
            html.append(WS*(3*(leading_level - 1) + 4) + f'<ccts:Name>{short_name}</ccts:Name>')
        if definition:
            # 改行文字を削除
            text = re.sub(r'[\r\n]+', '', definition)
            # 半角・全角スペースの連続を単一の半角スペースに変換
            text = re.sub(r'[ \u3000]+', ' ', text)
            text = text.strip()
            text = WS*(3*(leading_level - 1) + 4) + f'<ccts:Definition>{text}'

            if re.match(r".*([01]\.\.[1n]).*", multiplicity):
                min = multiplicity[0]
                max = multiplicity[-1]
                if "n"==max:
                    max="unbounded"
                text += f' [Occurence Min={min} Max={max}]'
            else:
                msg = f'"{den}"の多重度[{multiplicity}]不正'
                self.error_print(msg)

            text += '</ccts:Definition>'
            html.append(text)

        html += [
            WS*(3*(leading_level - 1) + 3) + '</xsd:documentation>',
            WS*(3*(leading_level - 1) + 3) + '<xsd:documentation xml:lang="ja">'
        ]

        if label_sme:
            html.append(WS*(3*(leading_level - 1) + 4) + f'<ccts:Name>{label_sme}</ccts:Name>')

        if definition_sme:
            # 改行文字を削除
            text = re.sub(r'[\r\n]+', '', definition_sme)
            # 半角・全角スペースの連続を単一の半角スペースに変換
            text = re.sub(r'[ \u3000]+', ' ', text)
            text = text.strip()
            text = WS*(3*(leading_level - 1) + 4) + f'<ccts:Definition>{text}'

            if re.match(r".*([01]\.\.[1n]).*", multiplicity_sme):
                min = multiplicity_sme[0]
                max = multiplicity_sme[-1]
                if "n"==max:
                    max="unbounded"
                text += f' [Occurence Min={min} Max={max}]'
            else:
                msg = f'"{den}"の多重度[{multiplicity_sme}]不正'
                self.error_print(msg)
            text += '</ccts:Definition>'
            html.append(text)

        html += [
            WS*(3*(leading_level - 1) + 3) + '</xsd:documentation>',
            WS*(3*(leading_level - 1) + 2) + '</xsd:annotation>'
        ]

        return html

    def normalize_mult(self, m):
        match = re.match(r".*([01]\.\.[1n]).*", m)
        if match:
            multiplicity = match.group(1)
        else:
            return "1..1"           
        lo, hi = multiplicity.split("..", 1)
        lo = "0" if lo == "0" else "1"
        hi = "n" if hi not in ("0","1") else hi
        return f"{lo}..{hi}"

    def merge_mult(self, a, b):
        a, b = self.normalize_mult(a), self.normalize_mult(b)
        alo, ahi = a.split(".."); blo, bhi = b.split("..")
        lo = "1" if ("1" in (alo, blo)) else "0"
        hi = "n" # if ("n" in (ahi, bhi)) else "1"
        return f"{lo}..{hi}"

    def ensure_level(self, path_list, level, val):
        """path_list の長さを level+1 に合わせる（短ければ埋め、長ければ詰める）"""
        while len(path_list) <= level:
            path_list.append(val)
        while len(path_list) > level + 1:
            del path_list[-1]

    def preprocess(self, rows, root_element):
        """
        Sequential copy with a for-loop:
        - Per-level name map to detect duplicates.
        - On duplicate: update ONLY existing multiplicity_sme (min rule + force 'n').
        - Otherwise: append a shallow copy of the source row.
        """
        target: list[dict] = []

        # One dict per level: name -> index into target
        name_idx_stack: list[dict[str, int]] = [ {} ]  # level 0 map
        element_idx: dict[str, int] = {}

        duplicate_lvl = None
        for row in rows:
            ac = row.get("acronym", "")
            if not ac or ac in ("ABIE", "SC"):
                continue
            if ac == "END":
                break

            # ----- level handling -----
            lvl_raw = row.get("level", 0)
            lvl = int(lvl_raw) if str(lvl_raw).isdigit() else 0
            while len(name_idx_stack) <= lvl:
                name_idx_stack.append({})
            while len(name_idx_stack) > lvl + 1:
                name_idx_stack.pop()
            name_map = name_idx_stack[lvl]

            # ----- resolve display name (by your existing conventions) -----
            if ac == "MA":
                name = root_element
            elif ac == "BBIE":
                if duplicate_lvl and lvl > duplicate_lvl:
                    continue
                name = row.get("XML_element_name") or row.get("element") or ""
            elif ac == "ABIE":
                continue
            else:  # ASBIE/ASMA
                if duplicate_lvl and lvl > duplicate_lvl:
                    continue
                element_idx: dict[str, int] = {}
                if row.get("associated_class"):
                    name = self.normalize_text(self.normalize_attribute(row["associated_class"]))
                else:
                    name = row.get("XML element name") or row.get("element") or ""

            # ----- duplicate by name at this level -----
            if name in name_map:
                duplicate_lvl = lvl
                idx = name_map[name]
                # merge ONLY multiplicity_sme (min → 0 if either is 0; max → n)
                existing_row = target[idx]
                existing_msme = self._normalize_mult(existing_row.get("multiplicity_sme"), "0..1")
                incoming_msme = self._normalize_mult(row.get("multiplicity_sme"), "0..1")
                min_part = "0" if (existing_msme[0] == "0" or incoming_msme[0] == "0") else "1"
                existing_row["multiplicity_sme"] = f"{min_part}..n"
                self.debug_print(
                    f"[MERGE] dup {ac}:'{name}' level:{lvl}: "
                    f"SME {existing_msme} & {incoming_msme} -> {existing_row['multiplicity_sme']}"
                )
                # Skip appending the duplicate
                continue
            elif name in element_idx:
                idx = element_idx[name]
                # merge ONLY multiplicity_sme (min → 0 if either is 0; max → n)
                existing_row = target[idx]
                existing_msme = self._normalize_mult(existing_row.get("multiplicity_sme"), "0..1")
                incoming_msme = self._normalize_mult(row.get("multiplicity_sme"), "0..1")
                min_part = "0" if (existing_msme[0] == "0" or incoming_msme[0] == "0") else "1"
                existing_row["multiplicity_sme"] = f"{min_part}..n"
                self.debug_print(
                    f"[MERGE] dup {ac}:'{name}' level:{lvl}: "
                    f"SME {existing_msme} & {incoming_msme} -> {existing_row['multiplicity_sme']}"
                )
                # Skip appending the duplicate
                continue

            # ----- first time for this name at this level -> append copy -----
            duplicate_lvl = None
            rec = dict(row)
            # normalise SME multiplicity baseline (we don't touch 'multiplicity' here)
            multiplicity_sme = self._normalize_mult(rec.get("multiplicity_sme"), "0..1")
            rec["multiplicity_sme"] = multiplicity_sme
            target.append(rec)
            if ac == "BBIE":
                element_idx[name] = len(target) - 1
            else:
                name_map[name] = len(target) - 1

        if self.DUMP:
            with open(self.target_file, mode="w", newline="", encoding="utf-8-sig") as targetfile:
                writer = csv.DictWriter(targetfile, fieldnames=self.LHM_FIELDS)
                writer.writeheader()
                writer.writerows(target)

        return target

    # minOccurs と maxOccurs のペア（順不同＆空白許容）を検出
    _PAT_OCCURS = re.compile(
        r'\s(?:'
        r'minOccurs="(?:0|1)"\s+maxOccurs="(?:1|unbounded)"'
        r'|'
        r'maxOccurs="(?:1|unbounded)"\s+minOccurs="(?:0|1)"'
        r')'
    )

    # def replace_occurs(self, line, min_val, max_val, count: int = 1):
    #     """
    #     min/maxOccurs のペアを指定値に置換。
    #     :param line: ターゲット行
    #     :param min_val: "0" または "1"
    #     :param max_val: "1" または "unbounded"
    #     :param count: 置換回数（既定=最初の1件。全件なら 0）
    #     """
    #     repl = f' minOccurs="{min_val}" maxOccurs="{max_val}"'
    #     return self._PAT_OCCURS.sub(repl, line, count=count)

    Mode = Literal["exact", "substring", "regex"]

    def find_last_index(self, lines: List[str], needle: str, *, mode: Mode = "exact", flags: int = 0) -> int:
        """
        最後に一致した行の 0-based インデックスを返す。見つからなければ -1。
        mode:
        - "exact"     : 行全体が一致
        - "substring" : 行内に needle を含む
        - "regex"     : needle を正規表現として評価（flags 使用可）
        """
        if mode == "regex":
            pat = re.compile(needle, flags)
            for i in range(len(lines) - 1, -1, -1):
                if pat.search(lines[i]):
                    return i
        elif mode == "substring":
            for i in range(len(lines) - 1, -1, -1):
                if needle in lines[i]:
                    return i
        else:  # exact
            for i in range(len(lines) - 1, -1, -1):
                if lines[i] == needle:
                    return i
        return -1

    def _normalize_mult(self, val: str | None, default: str = "0..1") -> str:
        # Accepts forms like "", "1", "0", "0..1", "1..n", "0..unbounded", "1..*", etc.
        _MULT_RE = re.compile(
            r'^\s*(?:(?P<min>[01])\s*(?:\.\.)\s*(?P<max>[1n\*]|unbounded)|(?P<single>[01]))\s*$',
            re.IGNORECASE
        )
        if not val:
            return default
        s = val.strip().lower().replace("unbounded", "n").replace("*", "n")
        m = _MULT_RE.match(s)
        if m:
            if m.group("single"):
                # "1" -> "1..1", "0" -> "0..1"
                return ("1" if m.group("single") == "1" else "0") + "..1"
            mn, mx = m.group("min"), m.group("max")
            mn = "0" if mn == "0" else "1"
            mx = "n" if mx in ("n",) else "1"
            return f"{mn}..{mx}"
        # Fallback heuristic if something odd slips through
        mn = "0" if "0" in s else "1"
        mx = "n" if ("n" in s) else "1"
        return f"{mn}..{mx}"

    def schema(self): 
        # read CSV file
        self.plain_print("\n".join(self.html))
        with open(self.lhm_file, encoding=self.encoding, newline="") as f:
            reader = csv.DictReader(f, fieldnames = self.LHM_FIELDS)
            next(reader)
            previous_level = 0
            # complex_tyle_level = [""]*10
            WS = "  "
            element = None
            multiplicity = None
            multiplicity_sme = None
            complex_multiplicity = None
            complex_multiplicity_sme = None

            d = []
            for row in reader:
                d.append(row)

            rows = self.preprocess(d, self.root_element)

            for row in rows:
                acronym = row["acronym"]
                if "END"==acronym:
                    break
                if not acronym or acronym in ["ABIE", "SC"]:
                    continue

                record = {}
                for key in self.LHM_FIELDS:
                    if key in row:
                        record[key] = row[key]
                    else:
                        record[key] = ''

                level = record["level"]
                if level.isdigit():
                    level = int(level)

                element = record["element"]
                xml_element = record["XML_element_name"]
                if not xml_element:
                    element = re.sub(r"\[.*?\]\s*", "", element).strip()
                    xml_element = element
                if xml_element != element:
                    self.debug_print(f"XML element name:{element} vs. {xml_element}")

                multiplicity            = self._normalize_mult(record.get("multiplicity"),     "")
                multiplicity_sme        = self._normalize_mult(record.get("multiplicity_sme"), "")
                complex_multiplicity    = self._normalize_mult(complex_multiplicity,           "")
                complex_multiplicity_sme= self._normalize_mult(complex_multiplicity_sme,       "")

                # self.debug_print(
                #     f"[mult] elem='{element}' "
                #     f"m={multiplicity} m_sme={multiplicity_sme} "
                #     f"cm={complex_multiplicity} cm_sme={complex_multiplicity_sme}"
                # )

                unid = record["UNID"]
                den = record[ "DEN"]
                short_name = record["short_name"] or den
                definition = record["definition"]
                label_sme = record["label_sme"]
                definition_sme = record["definition_sme"]
                # complex_tyle_level[level] = xml_element

                if "BBIE" == acronym:
                    if record["XML_datatype"]:
                        _type = record["XML_datatype"]
                    else:
                        representation_term = record["representation_term"]
                        _type = f'udt:{representation_term}Type'
                        self.debug_print(f'XML datatype not defined. element name="{xml_element}" type="{_type}"')

                    html = WS*(3*(level - 1) + 1) + f'<xsd:element name="{xml_element}" type="{_type}" '
                    if "0"==multiplicity[0]: # and level > 1:
                        html += 'minOccurs="0" '
                    if "n"==multiplicity[-1]:
                        html += 'maxOccurs="unbounded"'
                    if self.ANNOTATION:
                        html += ">"
                        self.plain_print(html)
                        self.html.append(html)
                        html = self.annotation(unid, acronym, den, short_name, definition, label_sme, definition_sme, multiplicity, multiplicity_sme, level)
                        self.plain_print("\n".join(html))
                        self.html += html
                        html = WS*(3*(level - 1) + 1) + f'</xsd:element>'
                        self.plain_print(html)
                        self.html.append(html)
                    else:
                        html += "/>"
                        self.plain_print(html)
                        self.html.append(html)
                else:
                    if record["associated_class"]:
                        associated_class = record["associated_class"]
                        attribute = self.normalize_attribute(associated_class)
                        complex_element = self.normalize_text(attribute)
                        complex_multiplicity = multiplicity
                        complex_multiplicity_sme = multiplicity_sme

                    if level < previous_level:
                        # self.debug_print(f'previous_level:{previous_level} level:{level} {xml_element}')
                        lvl = previous_level
                        while lvl > level:
                            html = [
                                WS*(3*(lvl-1)    ) + "</xsd:sequence>",
                                WS*(3*(lvl-1) - 1) + "</xsd:complexType>",
                                WS*(3*(lvl-1) - 2) + "</xsd:element>"
                            ]
                            self.plain_print("\n".join(html))
                            self.html += html
                            lvl -= 1

                    # complexType element
                    if "MA"==acronym:
                        html = WS + f'<xsd:element name="{self.root_element}" '
                    else:
                        html =WS*(3*(level - 1) + 1) + f'<xsd:element name="{xml_element}" '
                    if "MA" != acronym:
                        if 4==len(complex_multiplicity_sme):
                            if "0"==complex_multiplicity_sme[0]:
                                html += 'minOccurs="0" '
                            if "n"==complex_multiplicity_sme[-1]:
                                html += 'maxOccurs="unbounded"'
                    html += ">"
                    self.plain_print(html)
                    self.html.append(html)

                    if self.ANNOTATION:
                        multiplicity = record["multiplicity"]
                        html = self.annotation(unid, acronym, den, short_name, definition, label_sme, definition_sme, complex_multiplicity, complex_multiplicity_sme, level)
                        self.plain_print("\n".join(html))
                        self.html += html

                    html = [
                        WS*(3*(level - 1) + 2) + "<xsd:complexType>",
                        WS*(3*(level - 1) + 3) + "<xsd:sequence>"
                    ]
                    self.plain_print("\n".join(html))
                    self.html += html

                previous_level = level

        lvl = previous_level - 1
        while lvl > 1:
            html = [
                WS*(3*(lvl - 1) + 3) + "</xsd:sequence>",
                WS*(3*(lvl - 1) + 2) + "</xsd:complexType>",
                WS*(3*(lvl - 1) + 1) + "</xsd:element>"
            ]
            self.plain_print("\n".join(html))
            self.html += html
            lvl -= 1

        html = [
                WS*3 + "</xsd:sequence>",
                WS*2 + "</xsd:complexType>",
                WS + "</xsd:element>" ,
                "</xsd:schema>"
        ]

        self.plain_print("\n".join(html))
        self.html += html

        with open(self.schema_file, 'w', encoding=self.encoding) as f:
            for item in self.html:
                f.write(item + '\n')

        self.trace_print(f"Output file {self.schema_file}")

# Main function to execute the script
def main():
    # # Create the parser
    # parser = argparse.ArgumentParser(
    #     prog='sme_schema_LHM.py',
    #     usage='%(prog)s LHM_file -r Root class term -e encoding [options] ',
    #     description='Generate XML schema based on the LHM.'
    # )
    # parser.add_argument('LHM_file', metavar='LHM_file', type = str, help='Logical Hierarchical Model definition file path')
    # parser.add_argument("-r", "--root", help="Root class term for schema module to process.")
    # parser.add_argument('-e', '--encoding', required = False, default='utf-8-sig', help='File encoding, default is utf-8-sig')
    # parser.add_argument('-a', '--annotation', required = False, action='store_true')
    # parser.add_argument('-t', '--trace', required = False, action='store_true')
    # parser.add_argument('-d', '--debug', required = False, action='store_true')

    # try:
    #     args = parser.parse_args()
    # except Exception as e:
    #     print(f"引数の解析でエラーが発生しました: {e}")
    #     sys.exit(1)  # または適切なエラー処理 

    LHM_file = "SME_common10-08_LHM.csv"

    root = "SMEConsolidatedSelfInvoice"
    encoding = 'utf-8-sig'
    DATE = "10-08"
    REMOVE_CHARS = " -._'"

    processor = SchemaModule(
        lhm_file = LHM_file,
        DATE = DATE,
        root_term = root,
        remove_chars = REMOVE_CHARS,
        encoding = encoding,
        annotation = True,
        trace = True,
        debug = False,
        html = True,
        dump = False,
    )

    processor.schema()

if __name__ == '__main__':
    main()
