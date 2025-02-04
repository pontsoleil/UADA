import pandas as pd
from googletrans import Translator

def translate_csv(input_csv, output_csv, src_lang="et", dest_lang="en"):
    """
    CSVファイルの指定列を翻訳して新しいCSVとして保存する。

    Parameters:
        input_csv (str): 入力するCSVファイルのパス。
        output_csv (str): 出力する翻訳済みCSVファイルのパス。
        src_lang (str): 翻訳元の言語コード（デフォルト: エストニア語 'et'）。
        dest_lang (str): 翻訳先の言語コード（デフォルト: 英語 'en'）。
    """
    # 翻訳ツールの初期化
    translator = Translator()
    
    # CSVファイルを読み込む
    df = pd.read_csv(input_csv)
    
    # 各列を翻訳する
    for column in df.columns:
        print(f"翻訳中: {column}")
        df[column] = df[column].astype(str).apply(
            lambda x: translator.translate(x, src=src_lang, dest=dest_lang).text
            if x.strip() else x  # 空のセルは翻訳しない
        )
    
    # 翻訳済みCSVを保存する
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"翻訳済みファイルを保存しました: {output_csv}")
  

def excel_to_csv(input_excel, output_folder):
    # Excelファイルを読み込む
    xls = pd.ExcelFile(input_excel)
    
    # 各シートをCSVファイルとして出力する
    for sheet_name in xls.sheet_names:
        # シートをDataFrameとして読み込む
        df = pd.read_excel(input_excel, sheet_name=sheet_name)
        
        # CSVファイル名を設定する（シート名を使用する場合）
        csv_filename = f"{output_folder}/{sheet_name}.csv"
        
        # CSVファイルとして出力する
        df.to_csv(csv_filename, index=False)
        
        print(f"{sheet_name} を {csv_filename} に出力しました。")

        output_csv_file = f"{csv_filename[:-4]}_en.csv"  # 翻訳結果を保存するファイル

        translate_csv(csv_filename, output_csv_file)  

# 使用例
if __name__ == "__main__":


    # 使用例
    input_excel_file = 'OIM-CSV/Statistics_Estonia/APA_TAKSONOOMIA_KOONDFAIL_20241211.xlsx'  # 入力のExcelファイル名
    output_folder_path = 'OIM-CSV/Statistics_Estonia/output'    # 出力フォルダのパス

    # ExcelからCSVへの変換を実行する
    excel_to_csv(input_excel_file, output_folder_path)
