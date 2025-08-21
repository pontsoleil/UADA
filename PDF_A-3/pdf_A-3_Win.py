import sys, shutil, subprocess
from pathlib import Path

# --- 入出力 ---
base = Path("PDF_A-3")
inp  = (base / "output.pdf").resolve()
outp_pdfa = (base / "output_pdfa3_2025-08-21.pdf").resolve()
final_pdf = (base / "final_output.pdf").resolve()

xml_file  = (base / "Japan_PINT_Invoice_UBL_Example.xml").resolve()
csv_file  = (base / "timesheet.csv").resolve()
json_file = (base / "timesheet.json").resolve()

assert inp.is_file(), f"Input not found: {inp}"
assert xml_file.is_file() and csv_file.is_file() and json_file.is_file(), "Attachment file missing"

# --- Ghostscript 実行ファイルの自動検出 ---
if sys.platform.startswith("win"):
    gs_candidates = [
        r"C:\Program Files\gs\gs10.05.1\bin\gswin64c.exe",
        r"C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe",
        shutil.which("gswin64c"),
    ]
else:
    gs_candidates = ["/usr/local/bin/gs", "/opt/homebrew/bin/gs", shutil.which("gs")]
gs = next((Path(p) for p in gs_candidates if p and Path(p).is_file()), None)
if not gs:
    raise FileNotFoundError("Ghostscript not found. Check installation and PATH.")

# --- sRGB ICC の自動検出（OS別） ---
if sys.platform.startswith("win"):
    icc_candidates = [
        r"C:\Windows\System32\spool\drivers\color\sRGB Color Space Profile.icm",
        r"C:\Windows\System32\spool\drivers\color\sRGB IEC61966-2.1.icm",
        r"C:\Windows\System32\spool\drivers\color\srgb Color Space Profile.icm",   # 稀な大小違い
    ]
else:
    icc_candidates = [
        "/System/Library/ColorSync/Profiles/sRGB Profile.icc",
        "/System/Library/ColorSync/Profiles/sRGB IEC61966-2.1.icc",
    ]
icc = next((Path(p) for p in icc_candidates if Path(p).is_file()), None)
if not icc:
    raise FileNotFoundError("sRGB ICC profile not found on this OS. Install or specify path manually.")

print(f"GS : {gs}")
print(f"ICC: {icc}")

# --- Ghostscript で PDF/A-3 へ ---
cmd = [
    str(gs),
    "-dPDFA=3",
    "-sPDFACompatibilityPolicy=1",   # 不適合なら非ゼロ終了
    "-dBATCH", "-dNOPAUSE",
    "-sDEVICE=pdfwrite",
    f"-sOutputFile={str(outp_pdfa)}",
    "-sProcessColorModel=DeviceRGB",
    "-sColorConversionStrategy=RGB",
    f"-sOutputICCProfile={str(icc)}",
    "-dEmbedAllFonts=true",
    str(inp),
]
proc = subprocess.run(cmd, capture_output=True, text=True)
print("returncode:", proc.returncode)
if proc.returncode != 0:
    print("STDERR:\n", proc.stderr)
    raise RuntimeError("Ghostscript failed")

print("✅ PDF/A-3 変換成功:", outp_pdfa)

# --- pikepdf で添付（AFRelationship を必ず付与） ---
import pikepdf

with pikepdf.open(outp_pdfa) as pdf:
    # pikepdf 7.2+ の高レベル API
    pdf.attachments.add(
        xml_file.name, open(xml_file, "rb"),
        mime_type="application/xml",
        afrelationship="Data",
        description="PINT UBL example"
    )
    pdf.attachments.add(
        csv_file.name, open(csv_file, "rb"),
        mime_type="text/csv",
        afrelationship="Data",
        description="Timesheet CSV"
    )
    pdf.attachments.add(
        json_file.name, open(json_file, "rb"),
        mime_type="application/json",
        afrelationship="Alternative",   # 用途に応じて Data/Source/Alternative など
        description="Timesheet JSON"
    )
    pdf.save(final_pdf)

print("✅ 添付完了:", final_pdf)
