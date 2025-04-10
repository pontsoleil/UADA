import pandas as pd
import numpy as np
import csv
import json
from collections import OrderedDict
from datetime import datetime
import sys
# import os
# import webbrowser
# import tkinter as tk
# from tkinter import ttk, filedialog, messagebox

DEBUG = True
TRACE = True

def debug_print(message):
    if DEBUG:
        print(message)


def trace_print(message):
    if TRACE:
        print(message)


class TidyData:
    def __init__(self):
        self.DEBUG = False
        self.TRACE = False
        self.params = None
        self.columns = None
        self.file_path = None
        self.BS_path = None,
        self.PL_path = None,
        self.trading_partner_path = None
        self.trading_partner_dict = None
        self.LHM_path = None
        self.LHM_dict = None
        self.bs_template_df = None
        self.pl_template_df = None
        self.combined_template_df = None
        self.beginning_balance_path = None
        self.etax_beginning_balance_path = None
        self.lang = "ja"
        self.etax_file_path = None

    def debug_print(self, message):
        if self.DEBUG:
            print(message)

    def trace_print(self, message):
        if self.TRACE:
            print(message)

    # Account_Codeを置き換え
    def map_account_code(self, code, errors):
        if pd.isna(code):
            return code
        try: # 小数の形式になっている場合は整数に変換
            code = str(int(code))
        except ValueError:
            errors.append(f"Error: Account_Code {code} is not a valid integer.")
            return code
        if code in self.code_mapping_dict:
            return self.code_mapping_dict[code]["eTax_Account_Code"]
        else:
            errors.append(f"Error: Account_Code {code} is not found in the mapping dictionary.")
            return code  # 未対応のコードはそのまま返す

    # Account_Name を置き換え
    def map_account_name(self, code, errors):
        if pd.isna(code):
            return code
        try: # 小数の形式になっている場合は整数に変換
            code = str(int(code))
        except ValueError:
            errors.append(f"Error: Account_Code {code} is not a valid integer.")
            return code
        if code in self.code_mapping_dict:
            if "en" == self.lang:
                return self.code_mapping_dict[code]["English_Label"]
            else:
                return self.code_mapping_dict[code]["eTax_Account_Name"]
        else:
            # エラーをリストに追加
            if code not in errors:  # 重複エラーを避ける
                errors.append(f"Error: Account_Code {code} is not found in the mapping dictionary.")
            return self.tidy_gl_df.loc[self.tidy_gl_df["Account_Code"] == code, 'Account_Name'].values[0]

    def map_tax_category_code(self, code, errors):
        if pd.isna(code):
            return code
        if code in self.tax_category_mapping_dict:
            return self.tax_category_mapping_dict[code]["Tax_Category_Code"]
        else:
            errors.append(f"Error: Tax_Code {code} is not found in the mapping dictionary.")
            return code  # 未対応のコードはそのまま返す

    def map_tax_category_name(self, code, errors):
        if pd.isna(code):
            return code
        if code in self.tax_category_mapping_dict:
            if "en" == self.lang:
                return self.tax_category_mapping_dict[code]["Tax_Category_Name_en"]
            else:
                return self.tax_category_mapping_dict[code]["Tax_Category_Name_ja"]
        else:
            errors.append(f"Error: Tax_Code {code} is not found in the mapping dictionary.")
            return code  # 未対応のコードはそのまま返す

    def beginning_balance(self):
        # beginning_balance_pathを読み込む
        # rows = []
        data = {}
        with open(self.beginning_balance_path, mode='r', encoding='utf-8-sig') as csv_file:
            reader = csv.DictReader(csv_file)  # ヘッダー行をキーとして利用
            for row in reader:
                account_code = row['Account_Code']
                mapping_row = self.code_mapping_dict[account_code]
                etax_account_code = mapping_row['eTax_Account_Code']
                balance = int(row['Beginning_Balance'])
                if etax_account_code in data:
                    balance += data[etax_account_code]['Beginning_Balance']
                else:
                    data[etax_account_code] = {}
                data[etax_account_code]['Account_Code'] = mapping_row['eTax_Account_Code']
                data[etax_account_code]['Account_Name'] = mapping_row['eTax_Account_Name']
                data[etax_account_code]['English_Label'] = mapping_row['English_Label']
                data[etax_account_code]['Beginning_Balance'] = balance
        # Save the dictionary as a CSV
        with open(self.etax_beginning_balance_path, mode='w', encoding='utf-8-sig', newline='') as etax_csv_file:
            writer = csv.writer(etax_csv_file)
            # Write the header row
            header = ['Account_Code', 'Account_Name', 'English_Label', 'Beginning_Balance']
            writer.writerow(header)
            # Write each row of data
            for key, row in data.items():
                writer.writerow([row['Account_Code'], row['Account_Name'], row['English_Label'], row['Beginning_Balance']])
        
    def code2etax(self):
        # e-Tax CSV Sheet for BS
        input_BS_path = self.BS_path  # BS Template CSV
        # Load the CSV file and use the first row as the header
        self.bs_template_df = pd.read_csv(input_BS_path, header=0)
        # カラム名に余分なスペースがある場合の対応
        self.bs_template_df.columns = self.bs_template_df.columns.str.strip()
        # Ensure the Ledger_Account_Number column is present by checking its existence
        if "Ledger_Account_Number" not in self.bs_template_df.columns:
            raise KeyError("Ledger_Account_Number column is missing. Check the CSV file structure.")
        # Select only the desired columns and drop rows where "Ledger_Account_Number" is NaN
        self.bs_template_df = self.bs_template_df[["name", "category", "seq", "account_name", "type", "level", "Ledger_Account_Number", "English_Label"]].dropna(subset=["Ledger_Account_Number"])
        self.bs_template_df.rename(
            columns={
                "name": "Name",
                "category": "Category",
                "account_name": "Account_Name",
                "type": "Type",
                "level": "Level"
            },
            inplace=True
        )
        self.bs_template_df["Level"] = self.bs_template_df["Level"].fillna(0).astype(int)
        # e-Tax CSV Sheet for PL
        input_PL_path = self.PL_path  # Replace with your input CSV file path
        # Load the CSV file and use the first row as the header
        self.pl_template_df = pd.read_csv(input_PL_path, header=0)
        # カラム名に余分なスペースがある場合の対応
        self.pl_template_df.columns = self.pl_template_df.columns.str.strip()
        # Ensure the Ledger_Account_Number column is present by checking its existence
        if "Ledger_Account_Number" not in self.pl_template_df.columns:
            raise KeyError("Ledger_Account_Number column is missing. Check the CSV file structure.")
        # Drop rows where Ledger_Account_Number is missing (i.e., NaN values in that column)
        self.pl_template_df = self.pl_template_df[["name", "category", "seq", "account_name", "type", "level", "Ledger_Account_Number", "English_Label"]].dropna(subset=["Ledger_Account_Number"])
        self.pl_template_df.rename(
            columns={
                "name": "Name",
                "category": "Category",
                "account_name": "Ledger_Account_Name",
                "type": "Type",
                "level": "Level"
            },
            inplace=True
        )
        self.pl_template_df["Level"] = self.pl_template_df["Level"].fillna(0).astype(int)
        # Combine self.bs_template_df and self.pl_template_df into a single DataFrame
        # Add a distinguishing column to identify the source of data
        self.bs_template_df['Source'] = 'BS'
        self.pl_template_df['Source'] = 'PL'
        # Combine both DataFrames using pd.concat
        self.combined_template_df = pd.concat([self.bs_template_df, self.pl_template_df], ignore_index=True)
        # Display the combined DataFrame
        self.debug_print(self.combined_template_df.head())
        # account_list.csv を読み込み、変換用の辞書を作成
        self.account_list_df = pd.read_csv(self.account_path, dtype={"Account_Code": str, "eTax_Account_Code": str})
        self.account_list_df.columns = self.account_list_df.columns.str.strip()  # 列名の空白を除去
        # Merge English_Label from self.pl_template_df
        self.account_list_df = self.account_list_df.merge(
            self.combined_template_df[['Ledger_Account_Number', 'English_Label']],
            left_on='eTax_Account_Code',
            right_on='Ledger_Account_Number',
            how='left'
        )
        # Display the combined DataFrame
        self.debug_print(self.account_list_df.head())
        # Account_Code をキーにして eTax_Account_Code と eTax_Account_Name を持つ辞書を作成
        self.code_mapping_dict = self.account_list_df.set_index("Account_Code")[["eTax_Account_Code", "eTax_Account_Name", "English_Label"]].to_dict('index')
        # eTax_Account_Code をキーにして、'Category' と "eTax_Account_Name" を持つ辞書を作成
        # eTax_Account_Code で重複を排除し、最初の出現のみを残す
        etax_unique_df = self.account_list_df.drop_duplicates(subset="eTax_Account_Code", keep='first')
        # eTax_Account_Code をキーにして辞書を作成
        self.etax_code_mapping_dict = etax_unique_df.set_index("eTax_Account_Code")[['Category', "eTax_Account_Name", "eTax_Category", "English_Label"]].to_dict('index')
        # tidyGL.csv を読み込み、列名の空白を除去
        # Datatype を Pandas dtype に変換するマッピング
        datatype_mapping = {
            'Identifier': 'str',
            'Char': 'str',
            'Code': 'str',
            'Name': 'str',
            'Text': 'str',
            'Date': 'str',  # 日付形式は後で変換する場合に備えてstrにしておく
            'Time': 'str',
            'Decimal': 'float',
            'Integer': 'int64',
            'Indicator': 'str',
        }
        # # 辞書形式で取得
        # first_row_dict = pd.read_csv(self.file_path, nrows=1).iloc[0].to_dict()
        # 辞書から dtype を生成
        dtype_dict = {}
        for column_id, properties in self.LHM_dict.items():
            datatype = properties.get('datatype', '')  # datatype を取得
            if datatype in datatype_mapping:  # マッピングに存在する場合のみ処理
                dtype_dict[column_id] = datatype_mapping[datatype]
        self.tidy_gl_df = pd.read_csv(self.file_path, dtype=dtype_dict)
        self.tidy_gl_df.columns = self.tidy_gl_df.columns.str.strip()  # 列名の空白を除去
        # tax_category.csv を読み込み、変換用の辞書を作成
        tax_category_list_df = pd.read_csv(self.tax_category_path, dtype=str)
        tax_category_list_df.columns = tax_category_list_df.columns.str.strip()  # 列名の空白を除去
        # Account_Code をキーにして eTax_Account_Code と eTax_Account_Name を持つ辞書を作成
        self.tax_category_mapping_dict = tax_category_list_df.set_index('Tax_Code')[['Dr_Cr', 'Tax_Name', "Tax_Category_Code", "Tax_Category_Name_ja", "Tax_Category_Name_en"]].to_dict('index')
        # 対応先がない場合のエラーログリスト
        errors = []
        # 借方と貸方の科目コード及び税コードに対してコードのマッピングを適用
        # 行ごとに繰り返し処理を行い、借方と貸方の科目コード、名称、借方税区分コード、借方税区分名をマッピング
        def process_row(row):
            debit_account_code = row[self.columns["借方科目コード"]]
            credit_account_code = row[self.columns["貸方科目コード"]]
            debit_tax_category_code = row[self.columns["借方税区分コード"]]
            credit_tax_category_code = row[self.columns["貸方税区分コード"]]
            if pd.isna(debit_account_code) and pd.isna(credit_account_code):
                return row
            else:
                # 借方科目コードと名称の変換
                row[self.columns["借方科目コード"]] = self.map_account_code(debit_account_code, errors)
                row[self.columns["借方科目名"]] = self.map_account_name(debit_account_code, errors)
                # 貸方科目コードと名称の変換
                row[self.columns["貸方科目コード"]] = self.map_account_code(credit_account_code, errors)
                row[self.columns["貸方科目名"]] = self.map_account_name(credit_account_code, errors)
                # 借方科目コードと名称の変換
                row[self.columns["借方税区分コード"]] = self.map_tax_category_code(debit_tax_category_code, errors)
                row[self.columns["借方税区分名"]] = self.map_tax_category_name(debit_tax_category_code, errors)
                # 貸方科目コードと名称の変換
                row[self.columns["貸方税区分コード"]] = self.map_tax_category_code(credit_tax_category_code, errors)
                row[self.columns["貸方税区分名"]] = self.map_tax_category_name(credit_tax_category_code, errors)
                return row
        # データフレーム全体に行単位で関数を適用
        self.tidy_gl_df = self.tidy_gl_df.apply(process_row, axis=1)
        # エラーがあれば出力
        if errors:
            self.trace_print("\n".join(errors))
        # 結果を確認
        self.debug_print(self.tidy_gl_df.head())
        # 新しいe-Taxコードに変換したデータフレームを CSV に保存
        self.tidy_gl_df.to_csv(self.etax_file_path, index=False, encoding="utf-8-sig")

    def csv2dataframe(self, param_file_path):
        with open(param_file_path, "r", encoding="utf-8-sig") as param_file:
            params = json.load(param_file)
        self.params = params
        self.DEBUG = 1 == params["DEBUG"]
        self.TRACE = 1 == params["TRACE"]
        self.file_path = params["file_path"]
        self.etax_file_path = params["e-tax_file_path"]
        self.beginning_balance_path = params["beginning_balance_path"]
        self.etax_beginning_balance_path = params["e-tax_beginning_balance_path"]
        self.account_path = params["account_path"]
        self.tax_category_path = params["tax_category_path"]
        self.trading_partner_path = params["trading_partner_path"]
        self.LHM_path = params["LHM_path"]
        self.BS_path = params["HOT010_3.0_BS_10"]
        self.PL_path = params["HOT010_3.0_PL_10"]
        self.columns  = params["columns"]
        self.lang = params["lang"]

        self.trading_partner_dict = {"supplier":{}, "customer": {}, "bank": {}}
        with open(self.trading_partner_path, mode='r', encoding='utf-8-sig') as csv_file:
            reader = csv.DictReader(csv_file)  # ヘッダー行をキーとして利用
            for row in reader:
                category = row['category']
                code = row['code']
                if "仕入先" == category:
                    self.trading_partner_dict["supplier"][code] = row
                elif "得意先" == category:
                    self.trading_partner_dict["customer"][code] = row
                elif "預金" in category:
                    self.trading_partner_dict["bank"][code] = row

        self.LHM_dict = {}
        with open(self.LHM_path, mode='r', encoding='utf-8-sig') as csv_file:
            reader = csv.DictReader(csv_file)  # ヘッダー行をキーとして利用
            for row in reader:
                id = row['id']
                self.LHM_dict[id] = row

        self.code2etax()

        self.beginning_balance()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python script.py <parameters.jsonのパス>")
        sys.exit(1)
    param_file_path = sys.argv[1]

    # Then process the CSV
    tidy_data = TidyData()
    tidy_data.csv2dataframe(param_file_path)

    print(f"END: out put file {param_file_path}")
