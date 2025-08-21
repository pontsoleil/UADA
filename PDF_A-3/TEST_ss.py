import subprocess, os
from pathlib import Path



# 事前チェック
print("IN exists:", inp.exists(), inp)
print("OUT dir writable:", os.access(outp.parent, os.W_OK), outp.parent)

cmd = [
    gs,
    "-dNOPAUSE", "-dBATCH",
    "-sDEVICE=pdfwrite",
    f"-sOutputFile={str(outp)}",
    str(inp)
]

proc = subprocess.run(cmd, capture_output=True, text=True)  # check=False で必ず戻る
print("returncode:", proc.returncode)
print("STDOUT >>>\n", proc.stdout)
print("STDERR >>>\n", proc.stderr)
if proc.returncode != 0:
    raise RuntimeError("Ghostscript failed")

