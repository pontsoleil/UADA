import subprocess, shutil
from pathlib import Path

# 1) 実行ファイルの決定（フルパス推奨）
GS = Path(r"C:\Program Files\gs\gs10.05.1\bin\gswin64c.exe")  # ← 実在するか確認
if not GS.is_file():
    # 代替: PATH から探す
    alt = shutil.which("gswin64c")
    if alt:
        GS = Path(alt)
    else:
        raise FileNotFoundError("Ghostscript not found. Check GS path or add to PATH.")

inp = Path("PDF_A-3/output.pdf").resolve()
outp = Path("PDF_A-3/out.pdf").resolve()

# 2) 事前チェック
assert inp.is_file(), f"Input not found: {inp}"
assert outp.parent.exists(), f"Output dir missing: {outp.parent}"

# 3) コマンド（各引数を**要素ごと**に）
gs_command = [
    str(GS),
    "-dNOPAUSE", "-dBATCH",
    "-sDEVICE=pdfwrite",
    f"-sOutputFile={str(outp)}",
    str(inp),
]

# 4) 実行（失敗時のSTDERRを見たいので check=False で一旦実行）
proc = subprocess.run(gs_command, capture_output=True, text=True)
print("returncode:", proc.returncode)
print("STDERR >>>\n", proc.stderr)
if proc.returncode != 0:
    raise RuntimeError("Ghostscript failed")
