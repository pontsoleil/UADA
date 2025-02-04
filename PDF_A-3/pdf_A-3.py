# import os
# import subprocess

# # 変換元 PDF と 変換後 PDF
# input_pdf = "PDF_A-3/output.pdf"
# output_pdfa = "PDF_A-3/output_pdfa3.pdf"

# # Ghostscript で PDF/A-3 に変換
# gs_command = ["C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe" --version

#     "gswin64",
#     "-dPDFA=3",
#     "-dBATCH",
#     "-dNOPAUSE",
#     "-sDEVICE=pdfwrite",
#     "-sOutputFile=" + output_pdfa,
#     "-sPDFACompatibilityPolicy=1",
#     input_pdf
# ]

# # コマンド実行
# subprocess.run(gs_command, check=True)

# print(f"PDF/A-3 変換完了: {output_pdfa}")
# import subprocess

# # Ghostscript のパス（確認済み）
# gs_path = r"C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe"

# # 入力 PDF と 出力 PDF
# input_pdf = "PDF_A-3/output.pdf"
# output_pdfa = "PDF_A-3/output_pdfa3.pdf"

# # Ghostscript コマンド
# gs_command = [
#     gs_path,  # gswin64c.exe を使用
#     "-dPDFA=3",
#     "-dBATCH",
#     "-dNOPAUSE",
#     "-sDEVICE=pdfwrite",
#     "-sOutputFile=" + output_pdfa,
#     "-sPDFACompatibilityPolicy=1",
#     input_pdf
# ]

# # コマンド実行（エラー出力も取得）
# try:
#     result = subprocess.run(gs_command, check=True, capture_output=True, text=True)
#     print("PDF/A-3 変換完了:", output_pdfa)
#     print(result.stdout)
# except subprocess.CalledProcessError as e:
#     print("エラーが発生しました:", e.stderr)

import subprocess

# Ghostscript のパスを指定
gs_path = r"C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe"

# 変換元 PDF と 変換後 PDF
input_pdf = "PDF_A-3/output.pdf"
output_pdfa = "PDF_A-3/output_pdfa3.pdf"

# Ghostscript コマンド
gs_command = [
    gs_path,
    "-dPDFA=3",
    "-dBATCH",
    "-dNOPAUSE",
    "-sDEVICE=pdfwrite",
    "-sOutputFile=" + output_pdfa,
    "-sPDFACompatibilityPolicy=1",
    "-sProcessColorModel=DeviceRGB",
    "-sPDFAOutputIntent=" + r"C:\Windows\System32\spool\drivers\color\sRGB Color Space Profile.icm",
    input_pdf
]

# コマンド実行 (エラーメッセージ取得)
try:
    result = subprocess.run(gs_command, capture_output=True, text=True, check=True)
    print("Success:", result.stdout)
except subprocess.CalledProcessError as e:
    print("Error:", e.stderr)
