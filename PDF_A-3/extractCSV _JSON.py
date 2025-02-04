import pikepdf
import os

# PDF ファイル
pdf_file = "PDF_A-3/final_output.pdf"
output_dir = "PDF_A-3/extracted_files"  # 抽出したファイルの保存先

# PDF を開く
pdf = pikepdf.open(pdf_file)

# 保存ディレクトリを作成（存在しない場合）
os.makedirs(output_dir, exist_ok=True)

# 添付ファイルを抽出（加工なし）
for name, file_obj in pdf.attachments.items():
    clean_name = os.path.basename(name)  # ファイル名を取得
    file_path = os.path.join(output_dir, clean_name)  # 保存先パス
    with open(file_path, "wb") as f:
        data = file_obj.read_from()
        f.write(data)

    print(f"✅ {clean_name} を {file_path} に保存しました")

print("🎯 全ての埋め込みファイルをそのまま抽出しました！")
