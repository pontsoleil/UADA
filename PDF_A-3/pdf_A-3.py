import os
import subprocess
import pikepdf

# # 変換元 PDF と 変換後 PDF
input_pdf = "PDF_A-3/output.pdf"
output_pdfa = "PDF_A-3/output_pdfa3.pdf"
csv_file = "PDF_A-3/timesheet.csv"  # 埋め込むCSV
json_file = "PDF_A-3/timesheet.json"  # 埋め込むJSON
final_output_pdf = "PDF_A-3/final_output.pdf"

gs_path = "/usr/local/bin/gs"

# Ghostscript で PDF を PDF/A-3 に変換
gs_command = [
    gs_path,
    "-dPDFA=3",
    "-dBATCH",
    "-dNOPAUSE",
    "-sDEVICE=pdfwrite",
    "-sOutputFile=" + output_pdfa,
    "-sPDFACompatibilityPolicy=1",
    "-sProcessColorModel=DeviceRGB",
    "-sColorConversionStrategy=RGB",
    '-sRGBProfile="/System/Library/ColorSync/Profiles/sRGB Profile.icc"',  # macOSのsRGBプロファイル
    input_pdf
]

try:
    result = subprocess.run(gs_command, check=True, capture_output=True, text=True)
    print("✅ PDF/A-3 変換成功！")
except subprocess.CalledProcessError as e:
    print("❌ Ghostscript エラー:", e)
    print(e.output)
    exit(1)

# pikepdf で埋め込み（XMP メタデータとして添付）
pdf = pikepdf.open(output_pdfa)
pdf.attachments[csv_file] = open(csv_file, "rb").read()
pdf.attachments[json_file] = open(json_file, "rb").read()
pdf.save(final_output_pdf)
pdf.close()

print("✅ CSV / JSON を PDF に埋め込みました！")

# qpdf で埋め込み確認
print("📄 埋め込まれたファイル:")
subprocess.run(["qpdf", "--json", final_output_pdf])
