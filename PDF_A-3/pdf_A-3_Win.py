#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, io, shutil, subprocess, traceback, re
from pathlib import Path
from typing import Dict, List, Any, Iterable, Tuple
import pandas as pd

# ===================== 入出力 =====================
base = Path("PDF_A-3")

xml_src      = (base / "core_invoice_gateway/SME_Example1-minimum.xml").resolve()
csv_src      = (base / "core_invoice_gateway/SME_Example1-minimum.csv").resolve()
core_japan_src  = (base / "core_invoice_gateway/core_japan.csv").resolve()
    
# 生成物（BOM付きCSV）
csv_bom      = csv_src.with_name(csv_src.stem + ".bom.csv")
core_japan_bom  = core_japan_src.with_name(core_japan_src.stem + ".bom.csv")

# PDF 出力
raw_pdf      = (base / "invoice_from_csv.pdf").resolve()
pdfa_pdf     = (base / "invoice_from_csv_pdfa3.pdf").resolve()
final_pdf    = pdfa_pdf.with_name(pdfa_pdf.stem + "_final.pdf")

# ===================== Ghostscript / ICC 自動検出 =====================
if sys.platform.startswith("win"):
    gs_candidates = [
        r"C:\Program Files\gs\gs10.05.1\bin\gswin64c.exe",
        r"C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe",
        shutil.which("gswin64c"),
    ]
    icc_candidates = [
        r"C:\Windows\System32\spool\drivers\color\sRGB Color Space Profile.icm",
        r"C:\Windows\System32\spool\drivers\color\sRGB IEC61966-2.1.icm",
    ]
else:
    gs_candidates = ["/opt/homebrew/bin/gs", "/usr/local/bin/gs", shutil.which("gs")]
    icc_candidates = [
        "/System/Library/ColorSync/Profiles/sRGB Profile.icc",
        "/System/Library/ColorSync/Profiles/sRGB IEC61966-2.1.icc",
    ]

gs = next((Path(p) for p in gs_candidates if p and Path(p).is_file()), None)
icc = next((Path(p) for p in icc_candidates if p and Path(p).is_file()), None)
if not gs:  raise FileNotFoundError("Ghostscript not found. Install it or add to PATH.")
if not icc: raise FileNotFoundError("sRGB ICC profile not found.")
print("GS :", gs)
print("ICC:", icc)

# ===================== 入力存在チェック =====================
for p in [csv_src, core_japan_src, xml_src]:
    if not p.is_file():
        raise FileNotFoundError(f"Missing input: {p}")

# ===================== 1) CSV を BOM 付き utf-8-sig で保存 =====================
def read_csv_guess(path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return pd.read_csv(path, dtype=str, encoding=enc)
        except Exception:
            continue
    data = path.read_bytes()
    try:
        return pd.read_csv(io.BytesIO(data.decode("utf-8").encode()), dtype=str)
    except Exception:
        return pd.read_csv(io.BytesIO(data.decode("cp932", errors="replace").encode()), dtype=str)

def write_csv_bom(df: pd.DataFrame, path: Path):
    df.to_csv(path, index=False, encoding="utf-8-sig")

df_raw   = read_csv_guess(csv_src)
df_bind  = read_csv_guess(core_japan_src)
write_csv_bom(df_raw, csv_bom)
write_csv_bom(df_bind, core_japan_bom)
print("✅ CSVをBOM付きで保存:", csv_bom.name, core_japan_bom.name)

# ===================== 2) ヘッダ日本語化（binding: B→E。d_は切ってlookup） =====================
def choose_cols_for_binding(df: pd.DataFrame):
    cols = list(df.columns)
    # if "C" in cols and "H" in cols:   # 典型
    #     return "C", "H"
    if len(cols) >= 5:
        return cols[2], cols[7]       # 2列目(C相当),7列目(H相当)
    # if len(cols) >= 2:
    #     return cols[0], cols[1]
    raise ValueError("core_japan.csv の列構成を解釈できません")

key_col, val_col = choose_cols_for_binding(df_bind)
bind_map = {str(k).strip(): str(v).strip() for k, v in zip(df_bind[key_col], df_bind[val_col])}

orig_cols = list(df_raw.columns)

def map_header(h: str) -> str:
    key = str(h)
    if key.startswith("d_"):
        key = key[2:]
    return bind_map.get(key, str(h))

jp_cols = [map_header(c) for c in orig_cols]
df = df_raw.copy()
df.columns = jp_cols
df = df.fillna("")  # NaN→空文字（重要）

# 診断
print("✅ ヘッダ日本語化（例）:", list(zip(orig_cols[:8], jp_cols[:8])))
print("✅ データ shape:", df.shape)
print("✅ 先頭5行:\n", df.head())

# ===================== 3) d_列ベースのグループ化（dict list で処理） =====================
# 元名→日本語名の対応（d_列解決に使用）
orig_to_jp: Dict[str, str] = dict(zip(orig_cols, jp_cols))

# 必須の Dimension（元名）
dim_keys = ["d_NC00", "d_NC39-NC57", "d_NC39-NC61"]  # group, tax, line
def resolve_jp_dim_cols(df: pd.DataFrame) -> Tuple[str, str, str]:
    resolved = []
    for k in dim_keys:
        jp = orig_to_jp.get(k)
        if not jp or jp not in df.columns:
            raise KeyError(f"必須の Dimension 列 {k}（日本語化後: {jp}）が見つかりません")
        resolved.append(jp)
    return tuple(resolved)

jp_d0, jp_dtax, jp_dline = resolve_jp_dim_cols(df)

# DataFrame → dict list
records: List[Dict[str, Any]] = df.to_dict(orient="records")

# d_NC00（日本語化後）を group id、d_NC39-NC57 を TAX、d_NC39-NC61 を LIN 判定に使用
groups: Dict[int, Dict[str, List[Dict[str, Any]]]] = {}
for row in records:
    raw_gid  = str(row.get(jp_d0, "")).strip()
    raw_tax  = str(row.get(jp_dtax, "")).strip()
    raw_line = str(row.get(jp_dline, "")).strip()

    gid = int(raw_gid) if raw_gid.isdigit() else None
    tax = int(raw_tax) if raw_tax.isdigit() else None
    lin = int(raw_line) if raw_line.isdigit() else None
    if gid is None:
        continue

    groups.setdefault(gid, {"HDR": [], "TAX": [], "LIN": []})
    if tax is None and lin is None:
        groups[gid]["HDR"].append(row)
    elif tax is not None:
        groups[gid]["TAX"].append(row)
    else:
        groups[gid]["LIN"].append(row)

print("🧭 グループ概要：")
for gid, sec in sorted(groups.items()):
    print(f"  gid={gid}: HDR={len(sec['HDR'])}, TAX={len(sec['TAX'])}, LIN={len(sec['LIN'])}")

# ===================== 4) セクション内「全行で空の列」を削除 =====================
def _is_blank_value(v: Any) -> bool:
    s = "" if v is None else str(v).strip()
    return (s == "" or s.lower() in {"nan", "none"})

def drop_all_blank_columns(
    rows: List[Dict[str, Any]],
    keep: Iterable[str] | None = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    if not rows:
        return rows, []
    keep_set = set(keep or [])
    all_keys = set()
    for r in rows:
        all_keys.update(r.keys())
    to_drop = []
    for k in sorted(all_keys - keep_set):
        if all(_is_blank_value(r.get(k)) for r in rows):
            to_drop.append(k)
    if to_drop:
        for r in rows:
            for k in to_drop:
                r.pop(k, None)
    return rows, to_drop

# 例：必ず残したいキー群（必要に応じて追記）
# must_keep_cols = {jp_d0, jp_dtax, jp_dline, "インボイス文書番号", "文書通貨コード"}
must_keep_cols = {jp_d0}

for gid, parts in groups.items():
    for section in ("HDR", "TAX", "LIN"):
        before_keys = set().union(*(r.keys() for r in parts[section])) if parts[section] else set()
        parts[section], dropped = drop_all_blank_columns(parts[section], keep=must_keep_cols)
        after_keys  = set().union(*(r.keys() for r in parts[section])) if parts[section] else set()
        if dropped:
            print(f"🧹 group {gid} {section}: dropped {len(dropped)} cols → {dropped}")
            print(f"    keys {len(before_keys)} → {len(after_keys)}")

# ===================== 5) ReportLab: 縦横反転テーブルでPDF化 =====================
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet

def register_jp_font() -> str:
    candidates = [
        (Path(r"C:\Windows\Fonts\YuGothR.ttc"), "YuGothic", 0),
        (Path(r"C:\Windows\Fonts\meiryo.ttc"),  "Meiryo",   0),
        (Path(r"C:\Windows\Fonts\msgothic.ttc"),"MSGothic", 0),
        (Path("fonts/NotoSansJP-Regular.otf"),  "NotoSansJP", None),
    ]
    for p, name, subidx in candidates:
        if p.is_file():
            if p.suffix.lower() == ".ttc":
                pdfmetrics.registerFont(TTFont(name, str(p), subfontIndex=subidx))
            else:
                pdfmetrics.registerFont(TTFont(name, str(p)))
            return name
    return "Helvetica"

font_name = register_jp_font()
styles = getSampleStyleSheet()
for k in ("Heading1","Heading2","BodyText","Normal","Title"):
    if k in styles: styles[k].fontName = font_name

def listdict_to_table_transposed(
    rows: List[Dict[str, Any]],
    *,
    keep_cols: Iterable[str] | None = None,
    drop_blank_cols: bool = False,  # 既に外で実施済み
    font_name: str = "Helvetica",
    styles_obj=None,
) -> Paragraph | Table:
    if not rows:
        return Paragraph("（データなし）", styles_obj["BodyText"] if styles_obj else None)

    # 全キー集合（行ごとに異なっていてもOK）
    all_keys = set()
    for r in rows:
        all_keys.update(r.keys())

    # 転置データ作成
    data: List[List[str]] = []
    record_ids = [f"#{i+1}" for i in range(len(rows))]
    for key in all_keys:
        row_data = [key]  # 項目名
        for r in rows:
            v = r.get(key, "")
            s = "" if _is_blank_value(v) else str(v)
            row_data.append(s)
        data.append(row_data)
    data.insert(0, ["項目名"] + record_ids)

    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), font_name),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    return t

# ページ構成（各 gid につき HDR/TAX/LIN の順で転置テーブル）
elems = []
for gid in sorted(groups.keys()):
    parts = groups[gid]
    elems += [Paragraph(f"SME Example / Group {gid}（HDR）", styles["Heading2"]), Spacer(1, 6),
              listdict_to_table_transposed(parts["HDR"], font_name=font_name, styles_obj=styles), PageBreak()]
    elems += [Paragraph(f"SME Example / Group {gid}（TAX）", styles["Heading2"]), Spacer(1, 6),
              listdict_to_table_transposed(parts["TAX"], font_name=font_name, styles_obj=styles), PageBreak()]
    elems += [Paragraph(f"SME Example / Group {gid}（LIN）", styles["Heading2"]), Spacer(1, 6),
              listdict_to_table_transposed(parts["LIN"], font_name=font_name, styles_obj=styles), PageBreak()]

# 末尾 PageBreak 除去
if elems and isinstance(elems[-1], PageBreak):
    elems.pop()

raw_pdf.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(raw_pdf), pagesize=A4, rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
doc.build(elems)
print("✅ PDF 作成:", raw_pdf)

# ===================== 6) Ghostscript で PDF/A-3 変換 =====================
for p in [pdfa_pdf, final_pdf]:
    try: p.unlink(missing_ok=True)
    except Exception: pass

gs_cmd = [
    str(gs), "-dNOSAFER",
    "-dPDFA=3", "-dPDFACompatibilityPolicy=1",
    "-dBATCH","-dNOPAUSE",
    "-sDEVICE=pdfwrite",
    f"-sOutputFile={str(pdfa_pdf)}",
    "-sColorConversionStrategy=RGB",
    f"-sOutputICCProfile={str(icc)}",
    "-dEmbedAllFonts=true",
    str(raw_pdf),
]
p = subprocess.run(gs_cmd, capture_output=True, text=True)
print("GS(PDFA) returncode:", p.returncode)
if p.stdout.strip(): print("GS STDOUT:\n", p.stdout)
if p.stderr.strip(): print("GS STDERR:\n", p.stderr)
if p.returncode != 0:
    raise SystemExit("❌ Ghostscript failed in PDF/A-3 conversion")
print("✅ PDF/A-3:", pdfa_pdf)

# ===================== 7) PDF に XML と BOM付きCSV を添付（/AF 付与） =====================
import pikepdf
from pikepdf import Name, Array, Dictionary

def ensure_ef_names(pdf: pikepdf.Pdf):
    root = pdf.Root
    names = root.get('/Names', None)
    if names is None:
        root['/Names'] = Dictionary()
        names = root['/Names']
    if '/EmbeddedFiles' not in names:
        names['/EmbeddedFiles'] = Dictionary()
    ef_tree = names['/EmbeddedFiles']
    if '/Names' not in ef_tree:
        ef_tree['/Names'] = Array()
    return ef_tree['/Names']

try:
    with pikepdf.open(str(pdfa_pdf)) as pdf:
        # 添付（辞書代入で作成）
        pdf.attachments[xml_src.name] = xml_src.read_bytes()
        pdf.attachments[csv_bom.name] = csv_bom.read_bytes()
        pdf.attachments[core_japan_bom.name] = core_japan_bom.read_bytes()

        # /AFRelationship と /AF を後付け
        ef_names = ensure_ef_names(pdf)  # [name, filespec, ...]
        af_array = pdf.Root.get('/AF', None)
        if af_array is None:
            af_array = Array()
            pdf.Root['/AF'] = af_array

        meta = {
            xml_src.name:      ("Data",        "SME Example XML"),
            csv_bom.name:      ("Data",        "SME CSV (BOM UTF-8)"),
            core_japan_bom.name:  ("Data",        "core_japan CSV (BOM UTF-8)"),
        }
        seen = set()
        for i in range(0, len(ef_names), 2):
            fname_obj    = ef_names[i]
            filespec_ref = ef_names[i + 1]
            fname        = str(fname_obj)
            if fname not in meta or fname in seen:
                continue
            seen.add(fname)
            if hasattr(filespec_ref, "get_object"):
                filespec = filespec_ref.get_object()
                ref_for_af = filespec_ref
            else:
                filespec = filespec_ref
                ref_for_af = pdf.make_indirect(filespec)
            rel, desc = meta[fname]
            filespec['/Desc'] = desc
            filespec['/AFRelationship'] = Name('/' + rel)
            af_array.append(ref_for_af)

        try: final_pdf.unlink(missing_ok=True)
        except Exception: pass
        pdf.save(str(final_pdf))
    print("✅ 添付完了:", final_pdf)

except Exception as e:
    print("❌ 添付時エラー:", e)
    traceback.print_exc()
    raise
