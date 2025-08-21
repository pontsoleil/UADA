import subprocess
from pathlib import Path

gs = r"C:\Program Files\gs\gs10.05.1\bin\gswin64c.exe"
inp = Path(r"C:\Users\nobuy\GitHub\UADA\PDF_A-3\output.pdf")
outp = Path(r"C:\Users\nobuy\GitHub\UADA\PDF_A-3\out_pdfa3.pdf")
icc = Path(r"C:\Windows\System32\spool\drivers\color\sRGB Color Space Profile.icm")  # 実在確認済み

cmd = [
    gs,
    "-dPDFA=3",
    "-dPDFACompatibilityPolicy=1",  # ← ここを -d に
    "-dBATCH",
    "-dNOPAUSE",
    "-sDEVICE=pdfwrite",
    f"-sOutputFile={str(outp)}",
    "-sColorConversionStrategy=RGB",
    f"-sOutputICCProfile={str(icc)}",
    # 追加候補:
    # "-dUseCIEColor",           # 必要なら
    # "-dEmbedAllFonts=true",    # フォント未埋め込み対策
    str(inp),
]

p = subprocess.run(cmd, capture_output=True, text=True)
print("returncode:", p.returncode)
print("STDERR:\n", p.stderr)
if p.returncode != 0:
    # 一旦ゆるめに生成できるか確認したい場合は 2 にして再試行
    cmd[1] = "-dPDFA=3"
    cmd[2] = "-dPDFACompatibilityPolicy=2"
    p2 = subprocess.run(cmd, capture_output=True, text=True)
    print("retry returncode:", p2.returncode)
    print("retry STDERR:\n", p2.stderr)
