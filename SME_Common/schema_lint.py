
# -*- coding: utf-8 -*-
"""
schema_lint.py

中小企業共通EDI などの項目定義CSVを機械検証するための汎用スクリプト。
(1) ヘッダ名のゆらぎに対応するため、列マッピングを先頭で設定
(2) 代表的な不整合・表記ゆれ・多重度の矛盾などを検出
(3) 結果を CSV（詳細） と TXT（サマリ） に出力

想定する代表的な列（例）：
- 行番号         : "No", "行", "seq", "Line"
- 要素種別       : "Kind", "種別", "ClassType"（ABIE/ASBIE/BBIE/SC など）
- 日本語名       : "Name", "項目名", "JapaneseName"
- 英語名         : "EnglishName"（任意）
- レベル（階層） : "Level", "level"
- 多重度         : "Multiplicity", "多重度"（例: "0..1","1..n" など）
- 説明           : "Description", "説明"

使い方（例）:
    python schema_lint.py input.csv

出力:
    input_lint_report.csv  … 行ごとの指摘一覧
    input_lint_summary.txt … 指摘件数のサマリとヒント
"""

import sys
import re
import pandas as pd
from pathlib import Path

# ====== 利用者向け設定（必要に応じて編集） =====================================

# 列名の自動マッピング候補（左が内部名、右がCSV中で想定される候補）
COLUMN_CANDIDATES = {
    "line": ["No", "行", "Line", "seq", "Seq", "行番号", "番号"],
    "kind": ["Kind", "種別", "ClassType", "Type"],
    "name": ["Name", "項目名", "JapaneseName", "和名", "ラベル"],
    "ename": ["EnglishName", "英名", "英語名", "DefinitionName"],
    "level": ["Level", "level", "階層", "レベル"],
    "multiplicity": ["Multiplicity", "多重度", "Cardinality", "Card."],
    "description": ["Description", "説明", "Definition", "定義", "備考", "Note"],
}

# ABIE/ASBIE/BBIE/SC を判定する文字（大文字小文字は無視）
KIND_KEYWORDS = {
    "ABIE": r"\\bABIE\\b",
    "ASBIE": r"\\bASBIE\\b",
    "BBIE": r"\\bBBIE\\b",
    "SC": r"\\bSC\\b|\\bSupplementary\\s*Component\\b",
}

# URL/URI の表記ゆれ検出
URL_URI_PAT = re.compile(r"\\bURL\\b", re.IGNORECASE)

# 代表的な誤字・用語ブレ（検出→修正候補）
TERM_FIX_LIST = [
    (re.compile("決裁"), "決済"),
    (re.compile("寧歳"), "明細"),
    (re.compile(r"ＵＲＬ"), "URI"),
    (re.compile(r"\\bURL_ID\\b", re.IGNORECASE), "URI"),
]

# Allowance/Charge の真偽判定の想定ルール（説明文に対するヒューリスティック）
# 例: 「true(Charge) / false(Allowance)」 でないパターンを検出
ALLOWANCE_CHARGE_TRUE_FALSE_HINT = [
    # "Allowance" と "true" が同時に現れたら警告
    (re.compile(r"Allowance", re.IGNORECASE), re.compile(r"\\btrue\\b", re.IGNORECASE), "Allowance は通常 false になる想定です（true↔false の取り違えかも）。"),
    # "Charge" と "false" が同時に現れたら警告
    (re.compile(r"Charge", re.IGNORECASE), re.compile(r"\\bfalse\\b", re.IGNORECASE), "Charge は通常 true になる想定です（true↔false の取り違えかも）。"),
]

# 添付ファイル周りのミスマッチ簡易検出
ATTACH_HEURISTICS = [
    # 「ファイル名」なのに「有無を指定」など布置が不一致
    (re.compile("ファイル名"), re.compile("有無|真偽|boolean|有り|無し"), "「ファイル名」と「有無(真偽)」の説明が不一致の可能性。"),
    # 「URI」なのに「形式」「MIME」の説明が紛れている
    (re.compile(r"\\bURI\\b", re.IGNORECASE), re.compile("形式|MIME|ファイル形式"), "「URI」と「形式(MIME)」の説明が入れ替わっている可能性。"),
    # 「説明文」なのに「所在 URI」等の説明
    (re.compile("説明文|説明"), re.compile(r"\\bURI\\b", re.IGNORECASE), "「説明」と「URI」の説明が逆転している可能性。"),
]

# =============================================================================

def smart_map_columns(df: pd.DataFrame):
    """
    入力CSVのヘッダから、内部で使うカラム名へ自動マッピングを作成。
    見つからない列は None を割り当てる。
    """
    mapping = {}
    cols = list(df.columns)
    for internal, candidates in COLUMN_CANDIDATES.items():
        found = None
        for c in candidates:
            for col in cols:
                if col.strip().lower() == c.strip().lower():
                    found = col
                    break
            if found:
                break
        mapping[internal] = found
    return mapping

def get_val(row, mapping, key, default=""):
    col = mapping.get(key)
    if col is None:
        return default
    v = row.get(col, default)
    return "" if pd.isna(v) else str(v)

def detect_kind(s: str):
    if not s:
        return ""
    s2 = s.strip()
    for k, pat in KIND_KEYWORDS.items():
        if re.search(pat, s2, re.IGNORECASE):
            return k
    return s2  # そのまま返す（未知の種別を可視化）

def normalize_name(s: str):
    if not s:
        return ""
    # 末尾の ".数字" を落として比較用に正規化（例: "xxx.1" → "xxx"）
    base = re.sub(r"\\.\d+$", "", s.strip())
    # 半角/全角スペースを統一
    base = re.sub(r"\\s+", " ", base)
    return base

def run_lint(input_path: str):
    p = Path(input_path)
    if not p.exists():
        print(f"入力ファイルが見つかりません: {input_path}")
        return None, None

    try:
        df = pd.read_csv(p, dtype=str, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(p, dtype=str)  # フォールバック

    mapping = smart_map_columns(df)

    # レポート行の蓄積
    issues = []

    # 直前の BBIE を親として SC の必須矛盾をチェックするためのスタック
    last_non_sc = None  # (index, kind, multiplicity)

    # ABIE の重複（正規化名ベース）
    seen_abie_names = {}

    for idx, row in df.iterrows():
        line = get_val(row, mapping, "line", default=str(idx + 1))
        kind_raw = get_val(row, mapping, "kind")
        kind = detect_kind(kind_raw)
        name = get_val(row, mapping, "name")
        ename = get_val(row, mapping, "ename")
        level = get_val(row, mapping, "level")
        mult = get_val(row, mapping, "multiplicity")
        desc = get_val(row, mapping, "description")

        # 1) level 未設定
        if level.strip() == "":
            issues.append((line, "階層（level）が空です。自動生成や解析に支障が出ます。", kind, name))

        # 2) ASBIE の 1..1 強制が多い
        if kind.upper() == "ASBIE" and re.fullmatch(r"1\\..(1|1{1})", mult.replace(" ", "")):
            issues.append((line, "ASBIE の多重度が 1..1 です。必須化の妥当性を再確認してください。", kind, name))

        # 3) SC の必須矛盾：親が 0..* / 0..1 等のとき SC=1..1 だと矛盾
        if kind.upper() == "SC":
            if last_non_sc:
                parent_idx, parent_kind, parent_mult = last_non_sc
                parent_min = parent_mult.replace(" ", "").split("..")[0] if ".." in parent_mult else parent_mult
                if parent_min.startswith("0") and re.fullmatch(r"1\\..(1|1{1})", mult.replace(" ", "")):
                    issues.append((line, "親BBIEが任意(0..x)だが、子SCが 1..1（必須）です。矛盾の可能性。", kind, name))
        else:
            # SC 以外が来たら「最後に見た非SC」を更新
            if kind:
                last_non_sc = (idx, kind, mult)

        # 4) ABIE の重複（正規化名）
        if kind.upper() == "ABIE":
            base = normalize_name(name)
            seen_abie_names.setdefault(base, []).append(line)
            if len(seen_abie_names[base]) == 2:
                lines = ",".join(seen_abie_names[base])
                issues.append((line, f"ABIE 名の重複（基底名）: '{base}' が複数行 {lines} に出現。統合検討を。", kind, name))

        # 5) URL/URI の混在
        if URL_URI_PAT.search(name):
            issues.append((line, "名称に 'URL' が含まれています。URI への統一を検討してください。", kind, name))

        # 6) 誤字・用語ブレ
        for pat, fix in TERM_FIX_LIST:
            if pat.search(name) or pat.search(desc):
                issues.append((line, f"表記ゆれ/誤記の可能性: '{pat.pattern}' → '{fix}' を検討。", kind, name))
                break

        # 7) Allowance/Charge と true/false の取り違え
        for kw_pat, tf_pat, msg in ALLOWANCE_CHARGE_TRUE_FALSE_HINT:
            if kw_pat.search(desc) and tf_pat.search(desc):
                issues.append((line, f"Allowance/Charge 判定の真偽が不自然です: {msg}", kind, name))
                break

        # 8) 添付周りのミスマッチ
        for name_pat, desc_pat, msg in ATTACH_HEURISTICS:
            if name_pat.search(name) and desc_pat.search(desc):
                issues.append((line, f"添付関連の名称と説明が不一致の可能性: {msg}", kind, name))
                break

        # 9) コード値「0」のみ・意味未記載
        if re.fullmatch(r"\\s*0\\s*", desc or ""):
            issues.append((line, "説明が '0' のみで意味が不明確です。コード表と意味の紐付けを明記してください。", kind, name))

    # 結果の保存
    out_report = p.with_name(p.stem + "_lint_report.csv")
    out_summary = p.with_name(p.stem + "_lint_summary.txt")

    if issues:
        rep_df = pd.DataFrame(issues, columns=["行", "指摘", "種別", "項目名"])
        rep_df.to_csv(out_report, index=False, encoding="utf-8-sig")
    else:
        rep_df = pd.DataFrame(columns=["行", "指摘", "種別", "項目名"])
        rep_df.to_csv(out_report, index=False, encoding="utf-8-sig")

    # サマリ作成（安全なカウント）
    def count_contains(keyword):
        return sum(1 for x in issues if keyword in x[1])

    buckets = {
        "level空欄": count_contains("階層（level）が空"),
        "ASBIE_1..1": count_contains("ASBIE の多重度が 1..1"),
        "SC必須矛盾": count_contains("子SCが 1..1"),
        "ABIE重複": count_contains("ABIE 名の重複"),
        "URL_URI": count_contains("URI への統一"),
        "誤字表記ブレ": count_contains("表記ゆれ/誤記"),
        "A/C真偽": count_contains("Allowance/Charge 判定"),
        "添付ミスマッチ": count_contains("添付関連"),
        "説明0のみ": count_contains("説明が '0' のみ"),
    }

    with open(out_summary, "w", encoding="utf-8") as f:
        f.write("=== Lintサマリ ===\\n")
        f.write(f"ファイル: {p.name}\\n")
        f.write(f"総指摘件数: {len(issues)}\\n\\n")
        for k, v in buckets.items():
            f.write(f"- {k}: {v}\\n")
        f.write("\\n== ヒント ==\\n")
        f.write("1) 列マッピングは COLUMN_CANDIDATES で調整できます。\\n")
        f.write("2) Allowance/Charge の真偽は説明文からのヒューリスティックです。運用ルールに合わせて判定条件を変更してください。\\n")
        f.write("3) ABIE の重複は末尾の .数字 を無視して基底名で検出しています。\\n")
        f.write("4) SC の必須矛盾は直前の非SC行を親とみなす簡易判定です。厳密な親子関係がある場合は列を追加してください。\\n")
        f.write("5) URL→URI の統一、誤字（決裁→決済、寧歳→明細など）は組織の記述規約に合わせて TERM_FIX_LIST を調整してください。\\n")

    return str(out_report), str(out_summary)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python schema_lint.py 入力CSV")
    else:
        run_lint(sys.argv[1])


        
