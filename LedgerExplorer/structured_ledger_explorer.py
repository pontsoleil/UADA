import pandas as pd
import numpy as np
import csv
import json
import re
from collections import OrderedDict
from datetime import datetime
import sys
import os
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font

DEBUG = False
TRACE = False

def debug_print(message):
    if DEBUG:
        print(message)


def trace_print(message):
    if TRACE:
        print(message)


class LogTracker:
    def __init__(self):
        self.line = "0.0"
        self.start_time = None
        self.current_time = None
        self.start_time = datetime.now()
        with open(param_file_path, "r", encoding="utf-8-sig") as param_file:
            params = json.load(param_file)
        self.params = params
        self.DEBUG = 1 == params["DEBUG"]
        self.TRACE = 1 == params["TRACE"]
        self.lang = params["lang"]

    def debug_print(self, message):
        if self.DEBUG:
            print(message)

    def trace_print(self, message):
        if self.TRACE:
            print(message)

    def get_elapsed(self):
        start = self.get_start()
        current = self.get_current()
        if start and current:
            elapsed_time = current - start
            total_seconds = elapsed_time.total_seconds()
            minutes = int(total_seconds // 60)
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:.1f}"
        return None

    def get_start(self):
        return self.start_time

    def get_current(self):
        self.current_time = datetime.now()
        return self.current_time

    def write_log_text(self, message):
        line = self.line
        line = f"{int(line[:line.index('.')]) + 1}.0"
        log_tracker.line = line
        elapsed = log_tracker.get_elapsed()
        text = f"{elapsed} {message}\n"
        if None != gui and gui.log_text:
            gui.log_text.insert(line, text)
            # 最後の行にスクロールする
            gui.scroll_to_end()
        self.trace_print(text)


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
        self.LHM_path = None,
        self.LHM_dict = None,
        # self.account_category_dict = None
        self.beginning_balances = None
        self.amount_rows = None
        self.general_ledger_df = None
        self.summary_df = None
        self.bs_data_df = None
        self.pl_data_df = None
        self.account_dict = None
        # self.account_dict2 = None
        self.bs_dict = None
        self.pl_dict = None
        # 勘定科目ごとの貸借の増減方向を持つ辞書を定義
        self.account_direction_dict = {
            "資産": "借方増",
            "負債": "貸方増",
            "費用": "借方増",
            "収益": "貸方増"
        }
        with open(param_file_path, "r", encoding="utf-8-sig") as param_file:
            params = json.load(param_file)
        self.params = params
        self.DEBUG = 1 == params["DEBUG"]
        self.TRACE = 1 == params["TRACE"]
        self.file_path = params["e-tax_file_path"]
        self.etax_beginning_balance_path = params["e-tax_beginning_balance_path"]
        self.account_path = params["account_path"]
        self.tax_category_path = params["tax_category_path"]
        self.trading_partner_path = params["trading_partner_path"]
        self.LHM_path = params["LHM_path"]
        self.BS_path = params["HOT010_3.0_BS_10"]
        self.PL_path = params["HOT010_3.0_PL_10"]
        self.columns  = params["columns"]
        self.account_category = params["account_category"]
        self.lang = params["lang"]
        self.english_pattern = re.compile(r'^[a-zA-Z \-]+$')

    def debug_print(self, message):
        if self.DEBUG:
            print(message)

    def trace_print(self, message):
        if self.TRACE:
            print(message)

    def get_file_path(self):
        return self.file_path

    def get_columns(self):
        return self.columns

    def get_amount_rows(self):
        return self.amount_rows

    def replace_name(self, row):
        if "en"== self.lang:
            if not re.search(self.english_pattern, row['Ledger_Account_Name']):
                    # `bs_template_df` から置き換え値を取得
                    # Get replacement values from 'bs_template_df'
                    replacement = self.bs_template_df.loc[
                        self.bs_template_df['Ledger_Account_Number'] == row['Ledger_Account_Number'], 'Account_Name'
                    ]
                    if replacement.empty:
                        # `pl_template_df` から置き換え値を取得
                        # Get replacement values from 'pl_template_df'
                        replacement = self.pl_template_df.loc[
                            self.pl_template_df['Ledger_Account_Number'] == row['Ledger_Account_Number'], 'Account_Name'
                        ]
                    if not replacement.empty:
                        row['Ledger_Account_Name'] = replacement.values[0]
            if 'Counterpart_Account_Name' in row and not re.search(self.english_pattern, row['Counterpart_Account_Name']):
                # `bs_template_df` から置き換え値を取得
                # Get replacement values from 'bs_template_df'
                replacement = self.bs_template_df.loc[
                    self.bs_template_df['Ledger_Account_Number'] == row['Counterpart_Account_Number'], 'Account_Name'
                ]
                if replacement.empty:
                    # `pl_template_df` から置き換え値を取得
                    # Get replacement values from 'pl_template_df'
                    replacement = self.pl_template_df.loc[
                        self.pl_template_df['Ledger_Account_Number'] == row['Counterpart_Account_Number'], 'Account_Name'
                    ]
                if not replacement.empty:
                    row['Counterpart_Account_Name'] = replacement.values[0]
        return row

    def get_general_ledger_df(self):
        self.general_ledger_df = self.general_ledger_df.apply(self.replace_name, axis=1)
        return self.general_ledger_df

    def replace_category(self, row):
        if "en"== self.lang:
            if 'eTax_Category' in row and not re.search(self.english_pattern, row['eTax_Category']):
                category = row['eTax_Category']
                if not re.search(self.english_pattern, category):
                    if category and category in self.account_category:
                        row['eTax_Category'] = self.account_category[category]
            if 'eTax_Account_Name' in row and not re.search(self.english_pattern, row['eTax_Account_Name']):
                # `bs_template_df` から置き換え値を取得
                # Get replacement values from 'bs_template_df'
                replacement = self.bs_template_df.loc[
                    self.bs_template_df['Ledger_Account_Number'] == row['Ledger_Account_Number'], 'Account_Name'
                ]
                if replacement.empty:
                    # `pl_template_df` から置き換え値を取得
                    # Get replacement values from 'pl_template_df'
                    replacement = self.pl_template_df.loc[
                        self.pl_template_df['Ledger_Account_Number'] == row['Ledger_Account_Number'], 'Account_Name'
                    ]
                if not replacement.empty:
                    row['eTax_Account_Name'] = replacement.values[0]
            if 'Ledger_Account_Name' in row and not re.search(self.english_pattern, row['Ledger_Account_Name']):
                # `bs_template_df` から置き換え値を取得
                # Get replacement values from 'bs_template_df'
                replacement = self.bs_template_df.loc[
                    self.bs_template_df['Ledger_Account_Number'] == row['Ledger_Account_Number'], 'Account_Name'
                ]
                if replacement.empty:
                    # `pl_template_df` から置き換え値を取得
                    # Get replacement values from 'pl_template_df'
                    replacement = self.pl_template_df.loc[
                        self.pl_template_df['Ledger_Account_Number'] == row['Ledger_Account_Number'], 'Account_Name'
                    ]
                if not replacement.empty:
                    row['Ledger_Account_Name'] = replacement.values[0]
        return row

    def get_summary_df(self):
        self.summary_df = self.summary_df.apply(self.replace_category, axis=1)
        return self.summary_df

    def get_account_dict(self):
        account_dict = {}
        for id, d in self.account_dict.items():
            if len(id) > 3:
                match = re.match(r"([ 0-9a-zA-Z\-]+)", id[11:])
                if 'en' == self.lang:
                    if match:
                        account_dict[id] = d
                else:
                    if not match:
                        account_dict[id] = d
        return account_dict

    # 月初日を取得する関数
    def get_month_start(self, date):
        return pd.Timestamp(date.year, date.month, 1)

    def etax_template(self):
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
        if "en" == self.lang:
            self.bs_template_df.rename(
                columns={
                    "name": "Name",
                    "category": "Category",
                    "English_Label": "Account_Name",
                    "type": "Type",
                    "level": "Level"
                },
                inplace=True
            )
        else:
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
        if "en" == self.lang:
            # Replacing the "Category" values using the mapping dictionary
            self.bs_template_df["Category"] = self.bs_template_df["Category"].map(self.account_category)
            # Preserve the leading full-width spaces while replacing the rest of the "Name" with "Account_Name"
            self.bs_template_df["Name"] = self.bs_template_df.apply(
                lambda row: ''.join(ch for ch in row["Name"] if ch == '\u3000' or ch == ' ') + row["Account_Name"],
                axis=1
            )
        # Display the modified DataFrame
        self.debug_print(self.bs_template_df.head())
        # e-Tax CSV Sheet for PL
        input_PL_path = self.PL_path  # Replace with your input CSV file path
        # Load the CSV file
        self.pl_template_df = pd.read_csv(input_PL_path, header=0)
        # カラム名に余分なスペースがある場合の対応
        self.pl_template_df.columns = self.pl_template_df.columns.str.strip()
        # Ensure the Ledger_Account_Number column is present by checking its existence
        if "Ledger_Account_Number" not in self.pl_template_df.columns:
            raise KeyError("Ledger_Account_Number column is missing. Check the CSV file structure.")
        # Drop rows where Ledger_Account_Number is missing (i.e., NaN values in that column)
        self.pl_template_df = self.pl_template_df[["name", "category", "seq", "account_name", "type", "level", "Ledger_Account_Number", "English_Label"]].dropna(subset=["Ledger_Account_Number"])
        if "en" == self.lang:
            self.pl_template_df.rename(
                columns={
                    "name": "Name",
                    "category": "Category",
                    "English_Label": "Account_Name",
                    "type": "Type",
                    "level": "Level"
                },
                inplace=True
            )
        else:
            self.pl_template_df.rename(
                columns={
                    "name": "Name",
                    "category": "Category",
                    "account_name": "Account_Name",
                    "type": "Type",
                    "level": "Level"
                },
                inplace=True
            )
        self.pl_template_df["Level"] = self.pl_template_df["Level"].fillna(0).astype(int)
        if "en" == self.lang:
            # Replacing the "Category" values using the mapping dictionary
            self.pl_template_df["Category"] = self.pl_template_df["Category"].map(self.account_category)
            # Preserve the leading full-width spaces while replacing the rest of the "Name" with "Account_Name"
            self.pl_template_df["Name"] = self.pl_template_df.apply(
                lambda row: ''.join(ch for ch in row["Name"] if ch == '\u3000' or ch == ' ') + row["Account_Name"],
                axis=1
            )
        # Display the modified DataFrame
        self.debug_print(self.pl_template_df.head())

    def general_ledger(self):
        # 伝票単位で処理を行う
        df_temp = pd.DataFrame(self.amount_rows).copy()
        for transaction_id, group in df_temp.groupby(self.columns["伝票"]):
            # グループ内の先頭行の借方金額と貸方金額、摘要文を取得
            first_row = group.iloc[0]
            transction_date = first_row[self.columns["伝票日付"]]
            first_entry_id = first_row[self.columns["伝票番号"]]
            first_description = first_row[self.columns["摘要文"]]
            # 借方
            first_debit_acct_number = first_row[self.columns["借方科目コード"]]
            first_debit_acct_name = first_row[self.columns["借方科目名"]]
            first_debit_subacct_code = first_row[self.columns["借方補助科目コード"]]
            first_debit_subacct_name = first_row[self.columns["借方補助科目名"]]
            first_debit_department_code = first_row[self.columns["借方部門コード"]]
            first_debit_department_name = first_row[self.columns["借方部門名"]]
            first_debit_amount = first_row["Debit_Amount"] if pd.notna(first_row["Debit_Amount"]) else 0
            # 貸方
            first_credit_acct_number = first_row[self.columns["貸方科目コード"]]
            first_credit_acct_name = first_row[self.columns["貸方科目名"]]
            first_credit_subacct_code = first_row[self.columns["貸方補助科目コード"]]
            first_credit_subacct_name = first_row[self.columns["貸方補助科目名"]]
            first_credit_department_code = first_row[self.columns["貸方部門コード"]]
            first_credit_department_name = first_row[self.columns["貸方部門名"]]
            first_credit_amount = first_row["Credit_Amount"] if pd.notna(first_row["Credit_Amount"]) else 0
            # 借方と貸方の合計金額を計算
            total_debit_amount = total_credit_amount = 0
            for idx, row in group.iterrows():
                if pd.notna(row["Debit_Amount"]):
                    total_debit_amount += row["Debit_Amount"]
                if pd.notna(row["Credit_Amount"]):
                    total_credit_amount += row["Credit_Amount"]
            # 借方と貸方の合計金額が一致するか確認
            if total_debit_amount != total_credit_amount:
                self.trace_print(f"伝票貸借不一致 {transction_date} {transaction_id}: 借方金額 {total_debit_amount} 貸方金額 {total_credit_amount}")
            # 金額と摘要文の転記を行う
            for idx, row in group.iterrows():
                if first_debit_amount > first_credit_amount:
                    df_temp.at[idx, self.columns["借方科目コード"]] = first_debit_acct_number
                    df_temp.at[idx, self.columns["借方科目名"]] = first_debit_acct_name
                    df_temp.at[idx, "Debit_Amount"] = df_temp.at[idx, "Credit_Amount"]
                    df_temp.at[idx, self.columns["借方補助科目コード"]] = first_debit_subacct_code
                    df_temp.at[idx, self.columns["借方補助科目名"]] = first_debit_subacct_name
                    df_temp.at[idx, self.columns["借方部門コード"]] = first_debit_department_code
                    df_temp.at[idx, self.columns["借方部門名"]] = first_debit_department_name
                else:
                    df_temp.at[idx, self.columns["貸方科目コード"]] = first_credit_acct_number
                    df_temp.at[idx, self.columns["貸方科目名"]] = first_credit_acct_name
                    df_temp.at[idx, "Credit_Amount"] =  df_temp.at[idx, "Debit_Amount"]
                    df_temp.at[idx, self.columns["貸方補助科目コード"]] = first_credit_subacct_code
                    df_temp.at[idx, self.columns["貸方補助科目名"]] = first_credit_subacct_name
                    df_temp.at[idx, self.columns["貸方部門コード"]] = first_credit_department_code
                    df_temp.at[idx, self.columns["貸方部門名"]] = first_credit_department_name
                if pd.isna(row[self.columns["伝票番号"]]):
                    df_temp.at[idx, self.columns["伝票番号"]] = first_entry_id
                if pd.isna(row[self.columns["摘要文"]]):
                    df_temp.at[idx, self.columns["摘要文"]] = first_description
        self.debug_print("\n4. 最終的なDataFrame:")
        self.debug_print(df_temp.head())
        # 借方金額転記 Debit_Amountが記載されているエントリを選択し、コピーする
        debit_entry = df_temp[df_temp["Debit_Amount"].notna()].copy()
        # フィールド名を変更する
        debit_entry.rename(
            columns={
                self.columns["伝票日付"]: "Transaction_Date",
                self.columns["伝票番号"]: "Entry_ID",
                self.columns["摘要文"]: "Description",
                self.columns["借方科目コード"]: "Ledger_Account_Number",
                self.columns["借方科目名"]: "Ledger_Account_Name",
                self.columns["借方補助科目コード"]: "Subaccount_Code",
                self.columns["借方補助科目名"]: "Subaccount_Name",
                self.columns["借方部門コード"]: "Department_Code",
                self.columns["借方部門名"]: "Department_Name",
                self.columns["貸方科目コード"]: "Counterpart_Account_Number",
                self.columns["貸方科目名"]: "Counterpart_Account_Name",
                self.columns["貸方補助科目コード"]: "Counterpart_Subaccount_Code",
                self.columns["貸方補助科目名"]: "Counterpart_Subaccount_Name",
                self.columns["貸方部門コード"]: "Counterpart_Department_Code",
                self.columns["貸方部門名"]: "Counterpart_Department_Name",
            },
            inplace=True,
        )
        # Credit_Amountを0にする
        debit_entry["Credit_Amount"] = 0
        # 必要なカラムだけを選択
        debit_entry = debit_entry[
            [
                "Transaction_Date",
                "Entry_ID",
                "Description",
                "Ledger_Account_Number",
                "Ledger_Account_Name",
                "Subaccount_Code",
                "Subaccount_Name",
                "Department_Code",
                "Department_Name",
                "Debit_Amount",
                "Credit_Amount",
                "Counterpart_Account_Number",
                "Counterpart_Account_Name",
                "Counterpart_Subaccount_Code",
                "Counterpart_Subaccount_Name",
                "Counterpart_Department_Code",
                "Counterpart_Department_Name",
            ]
        ]
        self.debug_print("\n5D. 借方の転記結果:")
        self.debug_print(debit_entry.head())
        # 貸方金額転記 Creditt_Amountが記載されているエントリを選択し、コピーする
        credit_entry = df_temp[df_temp["Credit_Amount"].notna()].copy()
        # フィールド名を変更する
        credit_entry.rename(
            columns={
                self.columns["伝票日付"]: "Transaction_Date",
                self.columns["伝票番号"]: "Entry_ID",
                self.columns["摘要文"]: "Description",
                self.columns["貸方科目コード"]: "Ledger_Account_Number",
                self.columns["貸方科目名"]: "Ledger_Account_Name",
                self.columns["貸方補助科目コード"]: "Subaccount_Code",
                self.columns["貸方補助科目名"]: "Subaccount_Name",
                self.columns["貸方部門コード"]: "Department_Code",
                self.columns["貸方部門名"]: "Department_Name",
                self.columns["借方科目コード"]: "Counterpart_Account_Number",
                self.columns["借方科目名"]: "Counterpart_Account_Name",
                self.columns["借方補助科目コード"]: "Counterpart_Subaccount_Code",
                self.columns["借方補助科目名"]: "Counterpart_Subaccount_Name",
                self.columns["借方部門コード"]: "Counterpart_Department_Code",
                self.columns["借方部門名"]: "Counterpart_Department_Name",
            },
            inplace=True,
        )
        # Debit_Amountを0にする
        credit_entry["Debit_Amount"] = 0
        # 必要なカラムだけを選択
        credit_entry = credit_entry[
            [
                "Transaction_Date",
                "Entry_ID",
                "Description",
                "Ledger_Account_Number",
                "Ledger_Account_Name",
                "Subaccount_Code",
                "Subaccount_Name",
                "Department_Code",
                "Department_Name",
                "Debit_Amount",
                "Credit_Amount",
                "Counterpart_Account_Number",
                "Counterpart_Account_Name",
                "Counterpart_Subaccount_Code",
                "Counterpart_Subaccount_Name",
                "Counterpart_Department_Code",
                "Counterpart_Department_Name",
            ]
        ]
        self.debug_print("\n5C. 貸方の転記結果:")
        self.debug_print(credit_entry.head())
        # データフレームの数値列に対してNaNを0に変換
        debit_entry["Debit_Amount"] = debit_entry["Debit_Amount"].fillna(0).astype(int)
        debit_entry["Credit_Amount"] = debit_entry["Credit_Amount"].fillna(0).astype(int)
        credit_entry["Debit_Amount"] = credit_entry["Debit_Amount"].fillna(0).astype(int)
        credit_entry["Credit_Amount"] = credit_entry["Credit_Amount"].fillna(0).astype(int)
        # 借方と貸方の金額を集計する
        final_entry = pd.concat([debit_entry, credit_entry], ignore_index=True)
        # 月と科目番号でソート
        final_entry = final_entry.dropna(
            subset=[
                "Transaction_Date",
                "Entry_ID",
                "Ledger_Account_Number"
            ]
        ).sort_values(by=["Transaction_Date", "Entry_ID", "Ledger_Account_Number"])
        # 残高の計算
        balances = []
        balance_dict = {}  # 各勘定科目の残高を保持
        current_month = None
        for _, row in final_entry.iterrows():
            account_number = row["Ledger_Account_Number"]
            # 初期残高が存在しない場合、初期化
            if not account_number:
                self.trace_print(f"** general_ledger empty account_number{row}")
                continue
            if account_number not in balance_dict:
                balance_dict[account_number] = self.beginning_balances.get(account_number, 0)
        for _, row in final_entry.iterrows():
            account_number = row["Ledger_Account_Number"]
            if not account_number:
                self.trace_print(f"** general_ledger empty account_number{row}")
                continue
            transaction_date  = pd.Timestamp(row["Transaction_Date"])  # 日付をTimestamp型に変換
            transaction_month = transaction_date.strftime('%Y-%m')  # YYYY-MM形式の文字列に変換
            debit  = row["Debit_Amount"]
            credit = row["Credit_Amount"]
            # 月が変わったら月初残高を追加
            if current_month != transaction_month:
                current_month = transaction_month
                for acc_number in balance_dict:
                    # 各勘定科目について、月初残高を追加
                    account_name = self.etax_code_mapping_dict[acc_number]["eTax_Account_Name"]
                    if "en"== self.lang:
                        # `bs_template_df` から置き換え値を取得
                        replacement = self.bs_template_df.loc[
                            self.bs_template_df['Ledger_Account_Number'] == acc_number, 'Account_Name'
                        ]
                        if replacement.empty:
                            # `pl_template_df` から置き換え値を取得
                            replacement = self.pl_template_df.loc[
                                self.pl_template_df['Ledger_Account_Number'] == acc_number, 'Account_Name'
                            ]
                        if not replacement.empty:
                            account_name = replacement.values[0]
                    balances.append({
                        "Transaction_Date": self.get_month_start(transaction_date).strftime('%Y-%m-%d'),  # 月初日をYYYY-MM-DD形式で設定
                        "Description": "* beginning-of-month balance" if "en"==self.lang else "* 月初残高",
                        "Ledger_Account_Number": acc_number,
                        "Ledger_Account_Name": account_name,
                        "Subaccount_Code": "",
                        "Subaccount_Name": "",
                        "Department_Code": "",
                        "Department_Name": "",
                        "Debit_Amount": 0,
                        "Credit_Amount": 0,
                        "Counterpart_Account_Number": "",
                        "Counterpart_Account_Name": "",
                        "Counterpart_Subaccount_Code": "",
                        "Counterpart_Subaccount_Name": "",
                        "Counterpart_Department_Code": "",
                        "Counterpart_Department_Name": "",
                        "Balance": balance_dict[acc_number]
                    })
            # 勘定科目の種類に応じた残高計算
            account_category = self.etax_code_mapping_dict[account_number]['Category']
            # 勘定科目の方向に応じて残高を計算
            account_direction = self.account_direction_dict.get(account_category)
            if account_direction == "借方増":
                balance_dict[account_number] += debit - credit
            elif account_direction == "貸方増":
                balance_dict[account_number] += credit - debit
            else:
                # 例外処理やデフォルト動作を定義
                self.trace_print(f"未分類の勘定科目: {account_number}")
            balances.append({
                "Transaction_Date": transaction_date.strftime('%Y-%m-%d'),
                "Description": row["Description"],
                "Ledger_Account_Number": account_number,
                "Ledger_Account_Name": row["Ledger_Account_Name"],
                "Subaccount_Code": row["Subaccount_Code"],
                "Subaccount_Name": row["Subaccount_Name"],
                "Department_Code": row["Department_Code"],
                "Department_Name": row["Department_Name"],
                "Debit_Amount": debit,
                "Credit_Amount": credit,
                "Counterpart_Account_Number": row["Counterpart_Account_Number"],
                "Counterpart_Account_Name": row["Counterpart_Account_Name"],
                "Counterpart_Subaccount_Code": row["Counterpart_Subaccount_Code"],
                "Counterpart_Subaccount_Name": row["Counterpart_Subaccount_Name"],
                "Counterpart_Department_Code": row["Counterpart_Department_Code"],
                "Counterpart_Department_Name": row["Counterpart_Department_Name"],
                "Balance": balance_dict[account_number]
            })
        self.balances = balances
        final_entry = pd.DataFrame(balances)
        for column in final_entry:
            if pd.api.types.is_numeric_dtype(final_entry[column]):
                final_entry[column].fillna(0, inplace=True)
            else:
                final_entry[column].fillna("", inplace=True)
        # 最終結果を表示
        self.debug_print("\n6. 総勘定元帳最終結果:")
        self.debug_print(final_entry.head())
        self.general_ledger_df = final_entry.copy()

    def fill_account_dict(self):
        # 科目コードと科目名の対応辞書を作成
        account_dict = {
            f"{row['Ledger_Account_Number']} {row['Ledger_Account_Name']}": row[
                "Ledger_Account_Number"
            ]
            for _, row in self.general_ledger_df.iterrows()
            if pd.notna(row["Ledger_Account_Number"]) and pd.notna(row["Ledger_Account_Name"])
        }
        # Credit_Accountも含める
        account_dict.update(
            {
                f"{row['Counterpart_Account_Number']} {row['Counterpart_Account_Name']}": row[
                    "Counterpart_Account_Number"
                ]
                for _, row in self.general_ledger_df.iterrows()
                if pd.notna(row["Counterpart_Account_Number"]) and pd.notna(row["Counterpart_Account_Name"])
            }
        )
        self.account_dict = OrderedDict(sorted(account_dict.items()))

    def trial_balance_carried_forward(self):
        # 借方の金額を集計する
        debit_summary = (
            self.amount_rows.groupby(
                [
                    "Month",
                    self.columns["借方科目コード"],
                    self.columns["借方科目名"],
                ]
            )["Debit_Amount"]
            .sum()
            .reset_index()
        )
        debit_summary.rename(
            columns={
                self.columns["借方科目コード"]: "Ledger_Account_Number",
                self.columns["借方科目名"]: "Ledger_Account_Name",
            },
            inplace=True,
        )
        self.debug_print("\n4. 借方の集計結果:")
        self.debug_print(debit_summary.head())
        # 貸方の金額を集計する
        credit_summary = (
            self.amount_rows.groupby(
                [
                    "Month",
                    self.columns["貸方科目コード"],
                    self.columns["貸方科目名"],
                ]
            )["Credit_Amount"]
            .sum()
            .reset_index()
        )
        credit_summary.rename(
            columns={
                self.columns["貸方科目コード"]: "Ledger_Account_Number",
                self.columns["貸方科目名"]: "Ledger_Account_Name",
            },
            inplace=True,
        )
        self.debug_print("\n5. 貸方の集計結果:")
        self.debug_print(credit_summary.head())
        # データフレームの数値列に対してNaNを0に変換
        debit_summary["Debit_Amount"] = debit_summary["Debit_Amount"].fillna(0).astype(int)
        credit_summary["Credit_Amount"] = credit_summary["Credit_Amount"].fillna(0).astype(int)
        # 借方と貸方の金額を集計する
        temp_summary = pd.merge(
            debit_summary,
            credit_summary,
            on=[
                "Month",
                "Ledger_Account_Number",
            ],
            how="outer",
        )
        # NaNを0に変換し、借方金額および貸方金額の両方が0でない行のみを含める
        temp_summary["Debit_Amount"] = temp_summary["Debit_Amount"].fillna(0).astype(int)
        temp_summary["Credit_Amount"] = temp_summary["Credit_Amount"].fillna(0).astype(int)
        temp_summary = temp_summary[(temp_summary["Debit_Amount"] != 0) | (temp_summary["Credit_Amount"] != 0)]
        # Ledger_Account_Name列を統一
        if "Ledger_Account_Name_x" in temp_summary.columns and "Ledger_Account_Name_y" in temp_summary.columns:
            temp_summary["Ledger_Account_Name"] = temp_summary["Ledger_Account_Name_x"].fillna(temp_summary["Ledger_Account_Name_y"])
            temp_summary.drop(columns=["Ledger_Account_Name_x", "Ledger_Account_Name_y"], inplace=True)
        # 月と科目番号でソート
        temp_summary = temp_summary.sort_values(by=["Month", "Ledger_Account_Number"])
        # temp_summaryを表示する
        self.debug_print("\ntemp_summary:")
        self.debug_print(temp_summary.head())
        # 月ごとのユニークな値を取得
        unique_months = sorted(temp_summary["Month"].unique())
        # 科目ごとにグループ化
        grouped = temp_summary.groupby("Ledger_Account_Number")
        # 各科目のBeginning_BalanceとEnding_Balanceを保存する辞書
        beginning_balances = {account_number: [0] * len(unique_months) for account_number in temp_summary["Ledger_Account_Number"].unique()}
        ending_balances = {account_number: [0] * len(unique_months) for account_number in temp_summary["Ledger_Account_Number"].unique()}
        # 各グループごとに計算を実行
        for account_number, group in grouped:
            # 科目ごとの月データを既存の月に基づいてソート
            group = group.sort_values(by="Month").set_index("Month")
            # 初期値の設定
            previous_ending_balance = self.beginning_balances.get(account_number, 0)
            # 全てのunique_monthsを順番に処理
            for month in unique_months:
                if month in group.index:
                    # 該当月のデータが存在する場合
                    row = group.loc[month]
                    beginning_balance = previous_ending_balance  # 前月のEnding_BalanceをBeginning_Balanceに設定
                    # 勘定科目の種類に応じた残高計算
                    account_category = self.etax_code_mapping_dict.get(account_number, {}).get('Category', "Unknown")
                    account_direction = self.account_direction_dict.get(account_category)
                    # 勘定科目の方向に応じて残高を計算
                    if account_direction == "借方増":
                        ending_balance = beginning_balance + row["Debit_Amount"] - row["Credit_Amount"]
                    elif account_direction == "貸方増":
                        ending_balance = beginning_balance + row["Credit_Amount"] - row["Debit_Amount"]
                    else:
                        # 未分類の場合は残高を変更しない
                        self.debug_print(f"未分類の勘定科目: {account_number}")
                        ending_balance = beginning_balance
                else:
                    # 該当月のデータが存在しない場合、前月のEnding_Balanceを引き継ぐ
                    beginning_balance = previous_ending_balance
                    ending_balance = beginning_balance  # 取引がないため残高に変化なし
                # 結果を辞書に保存
                month_index = unique_months.index(month)
                beginning_balances[account_number][month_index] = beginning_balance
                ending_balances[account_number][month_index] = ending_balance
                # 現在のEnding_Balanceを次の月のBeginning_Balanceに使用するため更新
                previous_ending_balance = ending_balance
        # DataFrameに新しい列を追加
        temp_summary["Beginning_Balance"] = temp_summary.apply(
            lambda row: beginning_balances[row["Ledger_Account_Number"]][unique_months.index(row["Month"])],
            axis=1,
        )
        temp_summary["Ending_Balance"] = temp_summary.apply(
            lambda row: ending_balances[row["Ledger_Account_Number"]][unique_months.index(row["Month"])],
            axis=1,
        )
        # eTax_Categoryを計算して列を追加
        temp_summary["eTax_Category"] = temp_summary.apply(
            lambda row: self.etax_code_mapping_dict.get(row["Ledger_Account_Number"], {}).get("eTax_Category", None),
            axis=1,
        )
        # 集計結果を保存
        for column in temp_summary:
            if pd.api.types.is_numeric_dtype(temp_summary[column]):
                temp_summary[column].fillna(0, inplace=True)
            else:
                temp_summary[column].fillna("", inplace=True)
        self.summary_df = temp_summary.copy()
        # temp_summaryを表示する
        self.debug_print("\nself.summary_df:")
        self.debug_print(self.summary_df.head())

    def bs_pl(self):
        # Debit
        debit_summary = (
            self.amount_rows.groupby(
                [
                    self.columns["借方科目コード"],
                    self.columns["借方科目名"],
                ]
            )["Debit_Amount"]
            .sum()
            .astype("int64")  # Ensure the result is stored as int64
            .reset_index()
        )
        debit_summary.rename(
            columns={
                self.columns["借方科目コード"]: "Ledger_Account_Number",
                self.columns["借方科目名"]: "Ledger_Account_Name",
            },
            inplace=True,
        )
        # Add Category and eTax_Category to debit_summary
        debit_summary["Category"] = debit_summary["Ledger_Account_Number"].map(
            lambda code: self.etax_code_mapping_dict.get(code, {}).get("Category", "Unknown")
        )
        debit_summary["eTax_Category"] = debit_summary["Ledger_Account_Number"].map(
            lambda code: self.etax_code_mapping_dict.get(code, {}).get("eTax_Category", "Unknown")
        )
        # Credit
        credit_summary = (
            self.amount_rows.groupby(
                [
                    self.columns["貸方科目コード"],
                    self.columns["貸方科目名"],
                ]
            )["Credit_Amount"]
            .sum()
            .astype("int64")  # Ensure the result is stored as int64
            .reset_index()
        )
        credit_summary.rename(
            columns={
                self.columns["貸方科目コード"]: "Ledger_Account_Number",
                self.columns["貸方科目名"]: "Ledger_Account_Name",
            },
            inplace=True,
        )
        # Add Category and eTax_Category to credit_summary
        credit_summary["Category"] = credit_summary["Ledger_Account_Number"].map(
            lambda code: self.etax_code_mapping_dict.get(code, {}).get("Category", "Unknown")
        )
        credit_summary["eTax_Category"] = credit_summary["Ledger_Account_Number"].map(
            lambda code: self.etax_code_mapping_dict.get(code, {}).get("eTax_Category", "Unknown")
        )
        # Merge debit_summary and credit_summary on Ledger_Account_Number
        combined_summary = pd.merge(
            debit_summary,
            credit_summary,
            on=["Ledger_Account_Number", "Ledger_Account_Name", "Category", "eTax_Category"],
            how="outer"
        )
        # Ensure amounts are handled as int64 by replacing NaN with 0 and converting
        combined_summary["Debit_Amount"] = combined_summary["Debit_Amount"].fillna(0).astype("int64")
        combined_summary["Credit_Amount"] = combined_summary["Credit_Amount"].fillna(0).astype("int64")
        combined_summary.rename(
            columns={
                "Debit_Amount": "Total_Debit",
                "Credit_Amount": "Total_Credit"
            },
            inplace=True
        )
        # Remove rows where both Debit_Amount and Credit_Amount are 0
        combined_summary = combined_summary.loc[
            (combined_summary["Total_Debit"] != 0) | (combined_summary["Total_Credit"] != 0)
        ]
        # Convert self.beginning_balances (assumed to be a dictionary) to a DataFrame
        beginning_balances_df = pd.DataFrame.from_dict(
            self.beginning_balances,
            orient="index",
            columns=["Beginning_Balance"]
        )
        # Reset the index and rename columns
        beginning_balances_df.reset_index(inplace=True)
        beginning_balances_df.rename(columns={"index": "Ledger_Account_Number"}, inplace=True)
        # Ensure "Beginning_Balance" is of type int64
        beginning_balances_df["Beginning_Balance"] = beginning_balances_df["Beginning_Balance"].astype("int64")
        # Add Category and eTax_Category to beginning_balances_df
        beginning_balances_df["Category"] = beginning_balances_df["Ledger_Account_Number"].map(
            lambda code: self.etax_code_mapping_dict.get(code, {}).get("Category", "Unknown")
        )
        beginning_balances_df["eTax_Category"] = beginning_balances_df["Ledger_Account_Number"].map(
            lambda code: self.etax_code_mapping_dict.get(code, {}).get("eTax_Category", "Unknown")
        )
        beginning_balances_df["Ledger_Account_Name"] = beginning_balances_df["Ledger_Account_Number"].map(
            lambda code: self.etax_code_mapping_dict.get(code, {}).get("eTax_Account_Name", "Unknown")
        )
        # Merge the beginning balances into the combined_summary DataFrame
        combined_summary = pd.merge(
            combined_summary,
            beginning_balances_df,
            on=["Ledger_Account_Number", "Ledger_Account_Name", "Category", "eTax_Category"],
            how="outer"  # Use 'outer' to keep all rows from both
        )
        # Replace NaN values in Beginning_Balance with 0
        combined_summary["Beginning_Balance"] = combined_summary["Beginning_Balance"].fillna(0).astype("int64")
        combined_summary["Total_Debit"] = combined_summary["Total_Debit"].fillna(0).astype("int64")
        combined_summary["Total_Credit"] = combined_summary["Total_Credit"].fillna(0).astype("int64")
        #
        # BS
        #
        # Iterate through self.bs_template_df to populate the dictionary
        i = 0  # Initialize the sequence counter
        for _, row in self.bs_template_df.iterrows():
            ledger_account_number = row["Ledger_Account_Number"]
            if pd.notna(ledger_account_number):  # Only process rows with valid Ledger_Account_Number
                i += 1
                self.etax_code_mapping_dict[ledger_account_number] = {
                    "seq": i,
                    "Category": self.etax_code_mapping_dict.get(ledger_account_number, {}).get("Category", "Unknown"),
                    "eTax_Category": row["Category"] if pd.notna(row["Category"]) else "Unknown",
                    "eTax_Account_Name": row["Name"] if pd.notna(row["Name"]) else "Unknown",
                }
        # Separate into Balance Sheet and Income Statement items
        balance_sheet_df = combined_summary[combined_summary["Category"].isin(["資産", "負債"])][
            ["Ledger_Account_Number", "Ledger_Account_Name", "Category", "Beginning_Balance", "Total_Debit", "Total_Credit"]
        ]
        # Add the Ending_Balance column based on the Category
        balance_sheet_df["Ending_Balance"] = balance_sheet_df.apply(
            lambda row: (
                row["Beginning_Balance"] + row["Total_Debit"] - row["Total_Credit"]
                if row["Category"] == "資産"
                else row["Beginning_Balance"] + row["Total_Credit"] - row["Total_Debit"]
            ),
            axis=1
        )
        # Merge the sheet's Ledger_Account_Number with balance_sheet_df to get balances
        self.bs_data_df = pd.merge(
            self.bs_template_df,
            balance_sheet_df[["Ledger_Account_Number", "Beginning_Balance", "Total_Debit", "Total_Credit", "Ending_Balance"]],
            on="Ledger_Account_Number",
            how="left"
        )
        # Keep rows where `type` is "T" or both balances are not NaN
        self.bs_data_df = self.bs_data_df[
            (self.bs_data_df["Type"] == "T") |
            (~self.bs_data_df[["Beginning_Balance", "Total_Debit", "Total_Credit", "Ending_Balance"]].isna().all(axis=1))
        ]
        # Ensure these columns are of type int64, setting NaN to 0
        columns_to_convert = ["Beginning_Balance", "Total_Debit", "Total_Credit", "Ending_Balance"]
        for column in columns_to_convert:
            self.bs_data_df[column] = pd.to_numeric(self.bs_data_df[column], errors="coerce").fillna(0).astype("int64")
        # Set Beginning_Balance, Total_Debit, Total_Credit, and Ending_Balance to 0 for rows where Type is "T"
        self.bs_data_df.loc[self.bs_data_df["Type"] == "T", ["Beginning_Balance", "Total_Debit", "Total_Credit", "Ending_Balance"]] = 0
        # BSの親子関係を構築する関数
        def build_bs_parent_child_hierarcy(bs_data_df, level_range=(1, 10), exclude_empty_children=True):
            # 初期化: 各レベルの最新の要素を保持（レベル範囲を指定）
            level_list = {lvl: None for lvl in range(level_range[0], level_range[1] + 1)}
            children_list = {}  # 親要素とその子要素を保持する辞書
            for _, row in bs_data_df.iterrows():
                level = row["Level"]
                account = row["Ledger_Account_Number"]
                # 現在のレベルに対応する要素を更新
                level_list[level] = account
                # 子要素リストを初期化（もし未登録なら）
                if account not in children_list:
                    _type = row["Type"]
                    beginning_balance = 0 if "T"==_type else row["Beginning_Balance"] if not pd.isna(row["Beginning_Balance"]) else 0
                    total_debit = 0 if "T"==_type else row["Total_Debit"] if not pd.isna(row["Total_Debit"]) else 0
                    total_credit = 0 if "T"==_type else row["Total_Credit"] if not pd.isna(row["Total_Credit"]) else 0
                    ending_balance = 0 if "T"==_type else row["Ending_Balance"] if not pd.isna(row["Ending_Balance"]) else 0
                    children_list[account] = {"Level": level, "Type": _type, "Beginning_Balance": beginning_balance, "Total_Debit": total_debit, "Total_Credit": total_credit, "Ending_Balance": ending_balance, "children": []}
                # 親要素が存在する場合、その子要素として追加
                if level > 1 and level_list[level - 1] is not None:
                    parent = level_list[level - 1]
                    children_list[parent]["children"].append(account)
                    children_list[account]["parent"] = parent
                else:
                    continue
            # 空の子要素リストを持つ親要素を除外（オプション）
            if exclude_empty_children:
                filtered_list = {k: v for k, v in children_list.items() if "T"==v["Type"] or np.int64(v["Total_Debit"]) > 0 or np.int64(v["Total_Credit"]) > 0}
            else:
                filtered_list = children_list
            return filtered_list
        # BSの親子関係を構築 統合処理: bs_template_dfを基準にbs_data_dfで上書き
        # インデックスを基準に高速な検索を可能にする
        merge_keys = ["Ledger_Account_Number"]
        # bs_data_df を辞書に変換 (merge_keysをキーとして)
        bs_data_dict = self.bs_data_df.set_index(merge_keys).to_dict(orient="index")
        # 結果を格納するための DataFrame を初期化
        bs_result_df = self.bs_template_df.copy()
        # for ループで self.bs_template_df を処理
        for index, row in self.bs_template_df.iterrows():
            key = row["Ledger_Account_Number"]
            # データ辞書の行を取得
            bs_data_row = bs_data_dict.get(key, {})
            # 必要な列を更新
            for column in ["Beginning_Balance", "Total_Debit", "Total_Credit", "Ending_Balance"]:
                if column in row and not pd.isna(row[column]):
                    # 既存の値が存在する場合、値を保持
                    bs_result_df.at[index, column] = row[column]
                elif column in bs_data_row:
                    # bs_data_df の値で上書き
                    bs_result_df.at[index, column] = bs_data_row[column]
        bs_parent_child_hierarchy = build_bs_parent_child_hierarcy(bs_result_df, level_range=(1, 10), exclude_empty_children=True)
        # BSの結果を表示
        self.bs_dict = {}
        min_level = 10
        max_level = 0
        for parent, details in bs_parent_child_hierarchy.items():
            level = details["Level"]
            children = details["children"]
            self.debug_print(f"Level:{level} children:{children}")
            for child in children:
                if child in bs_parent_child_hierarchy:
                    result = bs_parent_child_hierarchy[child]
                    _type = result["Type"]
                    beginning_balance = result["Beginning_Balance"]
                    total_debit = result["Total_Debit"]
                    total_credit = result["Total_Credit"]
                    ending_balance = result["Ending_Balance"]
                    if level > max_level:
                        max_level = level
                    if min_level > level:
                        min_level = level
                    if "T"==_type or beginning_balance > 0 or total_debit > 0 or total_credit > 0 or ending_balance > 0:
                        self.debug_print(f"pl_parent_child_hierarchy level: {level}, Ledger_Account_Number: {child} Type:{_type} Parent: {parent}, Beginning_Balance: {beginning_balance} Total_Debit: {total_debit} Total_Credit: {total_credit} Ending_Balance: {ending_balance}")
                        self.bs_dict[child] = {
                            "Level": level,
                            "Type": _type,
                            "Ledger_Account_Number": child,
                            "Parent": parent,
                            "Beginning_Balance": beginning_balance,
                            "Total_Debit": total_debit,
                            "Total_Credit": total_credit,
                            "Ending_Balance": ending_balance
                        }
                else:
                    self.debug_print(f"B/S Ledger_Account_Number {child} not found.")
        # max_level から min_level の範囲でループ
        for level in range(max_level, min_level, -1):
            # target_level に該当する要素を抽出
            filtered_dict = {key: value for key, value in self.bs_dict.items() if value["Level"] == level}
            for key, row in filtered_dict.items():
                parent_key = row["Parent"]
                if not parent_key in self.bs_dict:
                    if 'None'==parent_key:
                        parent_key = "10X000000"
                    self.bs_dict[parent_key] = {"Level": level-1, "Parent": None, "Beginning_Balance": 0, "Total_Debit": 0, "Total_Credit": 0, "Ending_Balance": 0}
                parent = self.bs_dict[parent_key]
                if not parent:
                    continue
                beginning_balance = 0 if pd.isna(row["Beginning_Balance"]) else row["Beginning_Balance"]
                total_debit = 0 if pd.isna(row["Total_Debit"]) else row["Total_Debit"]
                total_credit = 0 if pd.isna(row["Total_Credit"]) else row["Total_Credit"]
                ending_balance = 0 if pd.isna(row["Ending_Balance"]) else row["Ending_Balance"]
                if beginning_balance > 0:
                    parent["Beginning_Balance"] += np.int64(beginning_balance)
                if total_debit > 0:
                    parent["Total_Debit"] += np.int64(total_debit)
                if total_credit > 0:
                    parent["Total_Credit"] += np.int64(total_credit)
                if ending_balance > 0:
                    parent["Ending_Balance"] += np.int64(ending_balance)
        # Filter bs_dict to remove entries with Beginning_Balance and Ending_Balance both 0
        self.bs_dict = {
            key: value
            for key, value in self.bs_dict.items()
            if not (value["Beginning_Balance"] == 0 and value["Ending_Balance"] == 0)
        }
        self.bs_dict = {
            key: {
                **value,
                "Ending_Balance": (
                    value["Beginning_Balance"] + value["Total_Credit"] - value["Total_Debit"]
                    if key.startswith("10A") and value.get("Type") == "T"
                    else value["Beginning_Balance"] + value["Total_Debit"] - value["Total_Credit"]
                    if (key.startswith("10B") or key.startswith("10C")) and value.get("Type") == "T"
                    else value["Ending_Balance"]
                )
            }
            for key, value in self.bs_dict.items()
            if not (value["Total_Debit"] == 0 and value["Total_Credit"] == 0)
        }
        # Add eTax_Category and eTax_Account_Name based on self.etax_code_mapping_dict
        for key, value in self.bs_dict.items():
            # Retrieve eTax_Category and eTax_Account_Name based on the Ledger_Account_Number (key)
            if key in self.etax_code_mapping_dict:
                etax_info = self.etax_code_mapping_dict[key]
                # Assuming etax_info contains "eTax_Category" and "eTax_Account_Name"
                value["seq"] = etax_info.get("seq", 0)
                value["eTax_Category"] = etax_info.get("eTax_Category", "Unknown")
                value["eTax_Account_Name"] = etax_info.get("eTax_Account_Name", "Unknown")
            else:
                # Default values if the key is not in etax_code_mapping_dict
                value["seq"] = 0
                value["eTax_Category"] = "Unknown"
                value["eTax_Account_Name"] = "Unknown"
        # Sort the dictionary by `seq`
        sorted_bs_dict = dict(
            sorted(self.bs_dict.items(), key=lambda item: item[1].get("seq", 0))
        )
        # Replace the original dictionary with the sorted one
        self.bs_dict = sorted_bs_dict
        #
        # PL
        #
        # Iterate through self.pl_template_df to populate the dictionary
        i = 0  # Initialize the sequence counter
        for _, row in self.pl_template_df.iterrows():
            ledger_account_number = row["Ledger_Account_Number"]
            if pd.notna(ledger_account_number):  # Only process rows with valid Ledger_Account_Number
                i += 1
                self.etax_code_mapping_dict[ledger_account_number] = {
                    "seq": i,
                    "Category": self.etax_code_mapping_dict.get(ledger_account_number, {}).get("Category", "Unknown"),
                    "eTax_Category": row["Category"] if pd.notna(row["Category"]) else "Unknown",
                    "eTax_Account_Name": row["Name"] if pd.notna(row["Name"]) else "Unknown",
                }
        income_statement_df = combined_summary[combined_summary["Category"].isin(["収益", "費用"])][
            ["Ledger_Account_Number", "Ledger_Account_Name", "Category", "Beginning_Balance", "Total_Debit", "Total_Credit"]
        ]
        # Add the Ending_Balance column based on the Category
        income_statement_df["Ending_Balance"] = income_statement_df.apply(
            lambda row: (
                row["Beginning_Balance"] + row["Total_Credit"] - row["Total_Debit"]  # For revenue (収益)
                if row["Category"] == "収益"
                else row["Beginning_Balance"] + row["Total_Debit"] - row["Total_Credit"]  # For expense (費用)
            ),
            axis=1
        )
        # Merge the sheet Ledger_Account_Number with the income_statement_df to get balances
        self.pl_data_df = pd.merge(
            self.pl_template_df,
            income_statement_df[["Ledger_Account_Number", "Beginning_Balance", "Total_Debit", "Total_Credit", "Ending_Balance"]],
            on="Ledger_Account_Number",
            how="left"
        )
        # Keep rows where `Type` is "T" or both balances are not NaN
        self.pl_data_df = self.pl_data_df[
            (self.pl_data_df["Type"] == "T") |
            (~self.pl_data_df[["Beginning_Balance", "Total_Debit", "Total_Credit", "Ending_Balance"]].isna().all(axis=1))
        ]
        # Ensure these columns are of type int64, setting NaN to 0
        columns_to_convert = ["Beginning_Balance", "Total_Debit", "Total_Credit", "Ending_Balance"]
        for column in columns_to_convert:
            self.pl_data_df[column] = pd.to_numeric(self.pl_data_df[column], errors="coerce").fillna(0).astype("int64")
        # Set Beginning_Balance, Total_Debit, Total_Credit, and Ending_Balance to 0 for rows where Type is "T"
        self.pl_data_df.loc[self.pl_data_df["Type"] == "T", ["Beginning_Balance", "Total_Debit", "Total_Credit", "Ending_Balance"]] = 0
        # 電子取引
        codes_to_check = [self.params["account"]["電子取引売上高"], self.params["account"]["電子取引以外売上高"]]
        # DataFrameに含まれているか確認
        missing_codes = [code for code in codes_to_check if code not in self.pl_data_df["Ledger_Account_Number"].values]
        # 結果を表示
        if missing_codes:
            self.debug_print(f"以下のコードはself.pl_data_dfに存在しません: {missing_codes}")
        else:
            self.debug_print(f"self.pl_data_dfには、{codes_to_check} が全て存在します。")
        # BSの親子関係を構築する関数
        def build_pl_parent_child_hierarcy(pl_result_df, level_range=(1, 10), exclude_empty_children=True):
            # 初期化: 各レベルの最新の要素を保持（レベル範囲を指定）
            level_list = {lvl: None for lvl in range(level_range[0], level_range[1] + 1)}
            children_list = {}  # 親要素とその子要素を保持する辞書
            for _, row in pl_result_df.iterrows():
                level = row["Level"]
                account = row["Ledger_Account_Number"]
                _type = row["Type"]
                # 現在のレベルに対応する要素を更新
                level_list[level] = account
                # 子要素リストを初期化（もし未登録なら）
                if account not in children_list:
                    total_debit = 0 if "T"==_type else row["Total_Debit"] if not pd.isna(row["Total_Debit"]) else 0
                    total_credit = 0 if "T"==_type else row["Total_Credit"] if not pd.isna(row["Total_Credit"]) else 0
                    ending_balance = 0 if "T"==_type else row["Ending_Balance"] if not pd.isna(row["Ending_Balance"]) else 0
                    children_list[account] = {"Level": level, "Type": _type, "Total_Debit": total_debit, "Total_Credit": total_credit, "Ending_Balance": ending_balance, "children": []}
                # 親要素が存在する場合、その子要素として追加
                if level > 1 and level_list[level - 1] is not None:
                    parent = level_list[level - 1]
                    children_list[parent]["children"].append(account)
                    children_list[account]["parent"] = parent
                else:
                    continue
            # Debit/Credtとも0の要素を除外
            if exclude_empty_children:
                filtered_list = {k: v for k, v in children_list.items() if "T"==v["Type"] or np.int64(v["Total_Debit"]) > 0 or np.int64(v["Total_Credit"]) > 0}
            else:
                filtered_list = children_list
            return filtered_list
        # PLの親子関係を構築 統合処理: pl_template_dfを基準にpl_data_dfで上書き
        # インデックスを基準に高速な検索を可能にする
        merge_keys = ["Ledger_Account_Number"]
        # pl_data_df を辞書に変換 (merge_keysをキーとして)
        pl_data_dict = self.pl_data_df.set_index(merge_keys).to_dict(orient="index")
        # 結果を格納するための DataFrame を初期化
        pl_result_df = self.pl_template_df.copy()
        # for ループで self.pl_template_df を処理
        for index, row in self.pl_template_df.iterrows():
            key = row["Ledger_Account_Number"]
            # データ辞書の行を取得
            pl_data_row = pl_data_dict.get(key, {})
            # 必要な列を更新
            for column in ["Total_Debit", "Total_Credit", "Ending_Balance"]:
                if column in row and not pd.isna(row[column]):
                    # 既存の値が存在する場合、値を保持
                    pl_result_df.at[index, column] = row[column]
                elif column in pl_data_row:
                    # pl_data_df の値で上書き
                    pl_result_df.at[index, column] = pl_data_row[column]
        pl_parent_child_hierarchy = build_pl_parent_child_hierarcy(pl_result_df, level_range=(1, 10), exclude_empty_children=True)
        # PLの結果を表示
        self.pl_dict = {}
        min_level = 10
        max_level = 0
        for parent, details in pl_parent_child_hierarchy.items():
            level = details["Level"]
            children = details["children"]
            self.debug_print(f"Level:{level} children:{children}")
            for child in children:
                if child in pl_parent_child_hierarchy:
                    result = pl_parent_child_hierarchy[child]
                    _type = result["Type"]
                    total_debit = result["Total_Debit"]
                    total_credit = result["Total_Credit"]
                    ending_balance = result["Ending_Balance"]
                    if level > max_level:
                        max_level = level
                    if min_level > level:
                        min_level = level
                    if "T"==_type or total_debit > 0 or total_credit > 0 or ending_balance > 0:
                        self.debug_print(f"pl_parent_child_hierarchy level: {level}, Ledger_Account_Number: {child} Type:{_type} Parent: {parent}, Beginning_Balance: {beginning_balance} Total_Debit: {total_debit} Total_Credit: {total_credit} Ending_Balance: {ending_balance}")
                        self.pl_dict[child] = {
                            "Level": level,
                            "Type": _type,
                            "Ledger_Account_Number": child,
                            "Parent": parent,
                            "Beginning_Balance": beginning_balance,
                            "Total_Debit": total_debit,
                            "Total_Credit": total_credit,
                            "Ending_Balance": ending_balance
                        }
                else:
                    self.debug_print(f"P/L Ledger_Account_Number {child} not found.")
        # # max_level から min_level の範囲でループ
        for level in range(max_level, min_level, -1):
            # target_level に該当する要素を抽出
            filtered_dict = {key: value for key, value in self.pl_dict.items() if value["Level"] == level}
            for key, row in filtered_dict.items():
                parent_key = row['Parent']
                if not parent_key in self.pl_dict:
                    if 'None'==parent_key:
                        parent_key = "10X000000"
                    self.pl_dict[parent_key] = {"Level": level-1, "Parent": None, "Beginning_Balance": 0, "Total_Debit": 0, "Total_Credit": 0, "Ending_Balance": 0}
                parent = self.pl_dict[row['Parent']]
                beginning_balance = 0 if pd.isna(row["Beginning_Balance"]) else row["Beginning_Balance"]
                total_debit = 0 if pd.isna(row["Total_Debit"]) else row["Total_Debit"]
                total_credit = 0 if pd.isna(row["Total_Credit"]) else row["Total_Credit"]
                ending_balance = 0 if pd.isna(row["Ending_Balance"]) else row["Ending_Balance"]
                if total_debit > 0:
                    parent["Total_Debit"] += np.int64(total_debit)
                if total_credit > 0:
                    parent["Total_Credit"] += np.int64(total_credit)
        # Filter pl_dict to remove entries with Total_Debit and Total_Credit both 0
        self.pl_dict = {
            key: value
            for key, value in self.pl_dict.items()
            if not (value["Total_Debit"] == 0 and value["Total_Credit"] == 0)
        }
        self.pl_dict = {
            key: {
                **value,
                "Ending_Balance": (
                    value["Total_Credit"] - value["Total_Debit"]
                    if key.startswith("10D") and value.get("Type") == "T"
                    else value["Total_Debit"] - value["Total_Credit"]
                    if key.startswith("10E") and value.get("Type") == "T"
                    else value["Ending_Balance"]
                )
            }
            for key, value in self.pl_dict.items()
            if not (value["Total_Debit"] == 0 and value["Total_Credit"] == 0)
        }
        # Add eTax_Category and eTax_Account_Name based on self.etax_code_mapping_dict
        for key, value in self.pl_dict.items():
            # Retrieve eTax_Category and eTax_Account_Name based on the Ledger_Account_Number (key)
            if key in self.etax_code_mapping_dict:
                etax_info = self.etax_code_mapping_dict[key]
                # Assuming etax_info contains "eTax_Category" and "eTax_Account_Name"
                value["seq"] = etax_info.get('seq', 0)
                value["eTax_Category"] = etax_info.get("eTax_Category", "Unknown")
                value["eTax_Account_Name"] = etax_info.get("eTax_Account_Name", "Unknown")
            else:
                # Default values if the key is not in etax_code_mapping_dict
                value["seq"] = 0
                value["eTax_Category"] = "Unknown"
                value["eTax_Account_Name"] = "Unknown"
        # Sort the dictionary by `seq`
        sorted_pl_dict = dict(
            sorted(self.pl_dict.items(), key=lambda item: item[1].get("seq", 0))
        )
        # Replace the original dictionary with the sorted one
        self.pl_dict = sorted_pl_dict

    def code2etax(self):
        # account_list.csv を読み込み、変換用の辞書を作成
        account_list_df = pd.read_csv(self.account_path, dtype={"Account_Code": str, "eTax_Account_Code": str})
        account_list_df.columns = account_list_df.columns.str.strip()  # 列名の空白を除去
        # Account_Code をキーにして eTax_Account_Code と eTax_Account_Name を持つ辞書を作成
        self.code_mapping_dict = account_list_df.set_index("Account_Code")[["eTax_Account_Code", "eTax_Account_Name"]].to_dict('index')
        # eTax_Account_Code をキーにして、'Category' と "eTax_Account_Name" を持つ辞書を作成
        # eTax_Account_Code で重複を排除し、最初の出現のみを残す
        etax_unique_df = account_list_df.drop_duplicates(subset="eTax_Account_Code", keep='first')
        # eTax_Account_Code をキーにして辞書を作成
        self.etax_code_mapping_dict = etax_unique_df.set_index("eTax_Account_Code")[['Category', "eTax_Account_Name", "eTax_Category"]].to_dict('index')
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
        # 辞書から dtype を生成
        dtype_dict = {}
        for column_id, properties in self.LHM_dict.items():
            datatype = properties.get('datatype', '')  # datatype を取得
            if datatype in datatype_mapping:  # マッピングに存在する場合のみ処理
                dtype_dict[column_id] = datatype_mapping[datatype]
        self.tidy_gl_df = pd.read_csv(self.file_path, dtype=dtype_dict)
        self.tidy_gl_df.columns = self.tidy_gl_df.columns.str.strip()  # 列名の空白を除去
        # beginning_balance_pathを読み込む
        beginning_balance_df = pd.read_csv(self.etax_beginning_balance_path, dtype={"Account_Code": str, "eTax_Account_Code": str})
        # 勘定科目の開始残高を辞書に変換
        beginning_balance_df["Account_Code"] = beginning_balance_df["Account_Code"].astype(str)
        # beginning_balance_dfに複数のAccount_Codeが存在する場合、それぞれのAccount_CodeごとにBeginning_Balanceを合計し、beginning_balancesを作成する
        beginning_balances = beginning_balance_df.groupby("Account_Code")['Beginning_Balance'].sum().to_dict()
        self.beginning_balances = beginning_balances

    def csv2dataframe(self, param_file_path):
        # 開始、終了、経過時間ラベルを追加
        # log_tracker.start()
        log_tracker.write_log_text("CSV to DataFrame")
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
        df = pd.read_csv(self.file_path, encoding="utf-8-sig", dtype=str) # f tidy data csv
        df.columns = df.columns.str.strip()
        # 関連する列を適切なデータ型に変換する
        df[self.columns["明細行"]] = pd.to_numeric(df[self.columns["明細行"]], errors="coerce").astype("Int64")  # 明細行
        df[self.columns["借方補助科目"]] = pd.to_numeric(df[self.columns["借方補助科目"]], errors="coerce").astype("Int64")  # 借方補助科目
        df[self.columns["貸方補助科目"]] = pd.to_numeric(df[self.columns["貸方補助科目"]], errors="coerce").astype("Int64")  # 貸方補助科目
        df[self.columns["借方部門"]] = pd.to_numeric(df[self.columns["借方部門"]], errors="coerce").astype("Int64")  # 借方部門
        df[self.columns["貸方部門"]] = pd.to_numeric(df[self.columns["貸方部門"]], errors="coerce").astype("Int64")  # 貸方部門
        df[self.columns["借方金額"]] = pd.to_numeric(df[self.columns["借方金額"]], errors="coerce").astype("Int64")  # 借方金額
        df[self.columns["貸方金額"]] = pd.to_numeric(df[self.columns["貸方金額"]], errors="coerce").astype("Int64")  # 貸方金額
        # JP04a_GL02_03（伝票日付）を日時に変換し、非標準の日付フォーマットを処理する
        if self.columns["伝票日付"] in df.columns:
            df[self.columns["伝票日付"]] = pd.to_datetime(df[self.columns["伝票日付"]], errors="coerce").dt.strftime('%Y-%m-%d')
        # 月を抽出し、新しい列に追加する
        df["Month"] = pd.to_datetime(df[self.columns["伝票日付"]], errors="coerce").dt.to_period("M").astype(str)
        self.debug_print("1. 初期のDataFrame:")
        columns_to_show_df = [
            self.columns["伝票"],
            self.columns["明細行"],
            self.columns["伝票日付"],
            self.columns["伝票番号"],
            self.columns["借方補助科目"],
            self.columns["貸方補助科目"],
            self.columns["借方部門"],
            self.columns["貸方部門"],
            self.columns["借方金額"],
            self.columns["貸方金額"],
            self.columns["摘要文"],
        ]
        self.debug_print("\ndf")
        self.debug_print(
            df[columns_to_show_df].head()
        )
        # 伝票と明細行に値があり、借方補助科目、貸方補助科目、借方部門、貸方部門がすべてNaNの行を抽出し、対象の借方金額と貸方金額の値を収集する
        initial_rows = df[
            (pd.notna(df[self.columns["伝票"]]))
            & (pd.notna(df[self.columns["明細行"]]))
            & (pd.isna(df[self.columns["借方補助科目"]]))
            & (pd.isna(df[self.columns["貸方補助科目"]]))
            & (pd.isna(df[self.columns["借方部門"]]))
            & (pd.isna(df[self.columns["貸方部門"]]))
        ][
            [
                self.columns["伝票"],
                self.columns["明細行"],
                self.columns["借方金額"],
                self.columns["貸方金額"],
            ]
        ].drop_duplicates()
        # マージ前に対象列を明確にするために列名を変更する
        initial_rows = initial_rows.rename(
            columns={
                self.columns["借方金額"]: "Debit_Amount",
                self.columns["貸方金額"]: "Credit_Amount"
            }
        )
        self.debug_print("\n2. initial_rows:")
        self.debug_print(initial_rows.head())
        # 伝票に値があり、明細行、借方補助科目、貸方補助科目、借方部門、貸方部門がすべてNaNの行を抽出し、伝票日付を取り出す。
        entry_df = df[
            (pd.notna(df[self.columns["伝票"]]))
            & (pd.isna(df[self.columns["明細行"]]))
            & (pd.isna(df[self.columns["借方補助科目"]]))
            & (pd.isna(df[self.columns["貸方補助科目"]]))
            & (pd.isna(df[self.columns["借方部門"]]))
            & (pd.isna(df[self.columns["貸方部門"]]))
        ][
            [self.columns["伝票"], self.columns["伝票日付"], self.columns["伝票番号"], "Month"]
        ].drop_duplicates()
        # マージ前に列名を明確にするために列名を変更する
        entry_df = entry_df.rename(
            columns={
                self.columns["伝票日付"]: f"{self.columns['伝票日付']}_value",
                self.columns["伝票番号"]: f"{self.columns['伝票番号']}_value",
                "Month": "Month_value",
            }
        )
        # 対象の金額の値をメインのDataFrameにマージする
        line_df = pd.merge(df, initial_rows, on=[self.columns["伝票"], self.columns["明細行"]], how="left")
        # JP04a_GL02_03（伝票日付）の値をメインのDataFrameにマージする
        line_df = pd.merge(line_df, entry_df, on=self.columns["伝票"], how="left")
        # 正しいJP04a_GL02_03（伝票日付）の値でメインのDataFrameを更新する
        line_df[self.columns["伝票日付"]] = line_df[f"{self.columns['伝票日付']}_value"].combine_first(line_df[self.columns["伝票日付"]])
        line_df[self.columns["伝票番号"]] = line_df[f"{self.columns['伝票番号']}_value"].combine_first(line_df[self.columns["伝票番号"]])
        line_df["Month"] = line_df["Month_value"].combine_first(line_df["Month"])
        # マージに使用した一時的な列を削除する
        line_df.drop(columns=[f"{self.columns['伝票日付']}_value", f"{self.columns['伝票日付']}_value", "Month_value"], inplace=True)
        self.debug_print("\nline_df")
        columns_to_show = [
            self.columns["伝票"],self.columns["明細行"],
            self.columns["借方補助科目"],self.columns["貸方補助科目"],
            self.columns["借方科目コード"], self.columns["借方補助科目コード"], "Debit_Amount",
            self.columns["貸方科目コード"], self.columns["貸方補助科目コード"], "Credit_Amount"
        ]  # 必要なカラムを指定
        self.debug_print(line_df[columns_to_show].head())
        # 借方補助科目コードに値があり、借方補助区分が["補助科目", "sub-account"]にある行を抽出し、借方補助科目コード、借方補助科目名を取り出す。
        self.debug_print("\ndf")
        columns_to_show_df = [
            self.columns["伝票"], self.columns["明細行"],
            self.columns["借方補助科目"], self.columns["貸方補助科目"],
            self.columns["借方科目コード"], self.columns["借方補助科目コード"], self.columns["借方補助区分"], self.columns["借方金額"],
            self.columns["貸方科目コード"], self.columns["貸方補助科目コード"], self.columns["貸方補助区分"], self.columns["貸方金額"]
        ]  # 必要なカラムを指定
        self.debug_print(df[columns_to_show_df].head())
        df[self.columns["借方補助区分"]] = df[self.columns["借方補助区分"]].fillna('')
        debit_subaccount_df = df[
            (pd.notna(df[self.columns["借方補助科目コード"]]))
            & (df[self.columns["借方補助区分"]].isin(["補助科目", "sub-account"]))
        ][
            [self.columns["伝票"], self.columns["明細行"], self.columns["借方補助科目コード"], self.columns["借方補助科目名"]]
        ].drop_duplicates()
        # マージ前に列名を明確にするために列名を変更する
        debit_subaccount_df = debit_subaccount_df.rename(
            columns={
                self.columns["借方補助科目コード"]: f"{self.columns['借方補助科目コード']}_value",
                self.columns["借方補助科目名"]: f"{self.columns['借方補助科目名']}_value",
            }
        )
        self.debug_print("\ndebit_subaccount_df")
        self.debug_print(debit_subaccount_df.head())
        # 補助科目の値をメインのDataFrameにマージする
        if not debit_subaccount_df.empty:
            line_df = pd.merge(line_df, debit_subaccount_df, on=[self.columns["伝票"], self.columns["明細行"]], how="left")
            line_df[self.columns["借方補助科目コード"]] = line_df[f"{self.columns['借方補助科目コード']}_value"].combine_first(line_df[self.columns["借方補助科目コード"]])
            line_df[self.columns["借方補助科目名"]] = line_df[f"{self.columns['借方補助科目名']}_value"].combine_first(line_df[self.columns["借方補助科目名"]])
            line_df.drop(columns=[
                f"{self.columns['借方補助科目コード']}_value", f"{self.columns['借方補助科目名']}_value"
            ], inplace=True)
            columns_to_show =[
                self.columns["伝票"], self.columns["明細行"],
                self.columns["借方補助科目"], self.columns["借方補助科目コード"], self.columns["借方補助科目名"],
            ]
            self.debug_print("\nline_df")
            self.debug_print(line_df[columns_to_show].head())
        # 貸方補助科目コードに値があり、貸方補助区分が["補助科目", "sub-account"]にある行を抽出し、貸方補助科目コード、貸方補助科目名を取り出す。
        df[self.columns["貸方補助区分"]] = df[self.columns["貸方補助区分"]].fillna('')
        credit_subaccount_df = df[
            (pd.notna(df[self.columns["貸方補助科目コード"]]))
            & (df[self.columns["貸方補助区分"]].isin(["補助科目", "sub-account"]))
        ][
            [
                self.columns["伝票"], self.columns["明細行"], self.columns["貸方補助科目コード"], self.columns["貸方補助科目名"],
            ]
        ].drop_duplicates()
        # マージ前に列名を明確にするために列名を変更する
        credit_subaccount_df = credit_subaccount_df.rename(
            columns={
                self.columns["貸方補助科目コード"]: f"{self.columns['貸方補助科目コード']}_value",
                self.columns["貸方補助科目名"]: f"{self.columns['貸方補助科目名']}_value",
            }
        )
        # 補助科目の値をメインのDataFrameにマージする
        if not credit_subaccount_df.empty:
            line_df = pd.merge(line_df, credit_subaccount_df, on=[self.columns["伝票"], self.columns["明細行"]], how="left")
            line_df[self.columns["貸方補助科目コード"]] = line_df[f"{self.columns['貸方補助科目コード']}_value"].combine_first(line_df[self.columns["貸方補助科目コード"]])
            line_df[self.columns["貸方補助科目名"]] = line_df[f"{self.columns['貸方補助科目名']}_value"].combine_first(line_df[self.columns["貸方補助科目名"]])
            line_df.drop(columns=[
                f"{self.columns['貸方補助科目コード']}_value",  f"{self.columns['貸方補助科目名']}_value"
            ], inplace=True)
            columns_to_show = [self.columns["伝票"],self.columns["明細行"],
                                self.columns["借方補助科目"],self.columns["貸方補助科目"],
                                self.columns["借方科目コード"], self.columns["借方補助科目コード"],"Debit_Amount",
                                self.columns["貸方科目コード"], self.columns["貸方補助科目コード"],"Debit_Amount"]  # 必要なカラムを指定
            self.debug_print("\nline_df")
            self.debug_print(line_df[columns_to_show].head())
        # BS04cZ（借方部門）に値があり、BS04cZ_03（借方部門区分）が"部門"の行を抽出し、借方部門コードと借方部門名を取り出す。
        debit_department_df = df[
            (df[self.columns["借方部門"]] > 0)
            & (df[self.columns["借方部門区分"]] == "部門")
        ][
            [
                self.columns["伝票"], self.columns["明細行"], self.columns["借方部門コード"], self.columns["借方部門名"],
            ]
        ].drop_duplicates()
        # マージ前に列名を明確にするために列名を変更する
        debit_department_df = debit_department_df.rename(
            columns={
                self.columns["借方部門コード"]: f"{self.columns['借方部門コード']}_value",
                self.columns["借方部門名"]: f"{self.columns['借方部門名']}_value",
            }
        )
        # 部門の値をメインのDataFrameにマージする
        if not debit_department_df.empty:
            line_df = pd.merge(line_df, debit_department_df, on=[self.columns["伝票"], self.columns["明細行"]], how="left")
            line_df[self.columns["借方部門コード"]] = line_df[f"{self.columns['借方部門コード']}_value"].combine_first(line_df[self.columns["借方部門コード"]])
            line_df[self.columns["借方部門名"]] = line_df[f"{self.columns['借方部門名']}_value"].combine_first(line_df[self.columns["借方部門名"]])
            line_df.drop(columns=[f"{self.columns['借方部門コード']}_value", f"{self.columns['借方部門名']}_value"], inplace=True)
            columns_to_show =[
                self.columns["伝票"], self.columns["明細行"],
                self.columns["借方部門"], self.columns["借方部門コード"], self.columns["借方部門名"],
            ]
            self.debug_print("\nline_df")
            self.debug_print(line_df[columns_to_show].head())
        # BS04c0（貸方部門）に値があり、BS04c0_03（貸方部門区分）が"部門"の行を抽出し、貸方部門コードと貸方部門名を取り出す。
        credit_department_df = df[
            (df[self.columns["貸方部門"]] > 0)
            & (df[self.columns["貸方部門区分"]] == "部門")
        ][
            [
                self.columns["伝票"], self.columns["明細行"], self.columns["貸方部門コード"], self.columns["貸方部門名"],
            ]
        ].drop_duplicates()
        # マージ前に列名を明確にするために列名を変更する
        credit_department_df = credit_department_df.rename(
            columns={
                self.columns["貸方部門コード"]: f"{self.columns['貸方部門コード']}_value",
                self.columns["貸方部門名"]: f"{self.columns['貸方部門名']}_value",
            }
        )
        # 補助科目の値をメインのDataFrameにマージする
        if not credit_department_df.empty:
            line_df = pd.merge(line_df, credit_department_df, on=[self.columns["伝票"], self.columns["明細行"]], how="left")
            line_df[self.columns["貸方部門コード"]] = line_df[f"{self.columns['貸方部門コード']}_value"].combine_first(line_df[self.columns["貸方部門コード"]])
            line_df[self.columns["貸方部門名"]] = line_df[f"{self.columns['貸方部門名']}_value"].combine_first(line_df[self.columns["貸方部門名"]])
            line_df.drop(columns=[f"{self.columns['貸方部門コード']}_value", f"{self.columns['貸方部門名']}_value"], inplace=True)
            columns_to_show =[
                self.columns["伝票"], self.columns["明細行"],
                self.columns["貸方部門"], self.columns["貸方部門コード"], self.columns["貸方部門名"],
            ]
            self.debug_print("\nline_df")
            self.debug_print(line_df[columns_to_show].head())
        # マージと更新後のDataFrameを表示する
        self.debug_print("\n3. マージと更新後のDataFrame:")
        self.debug_print(line_df.head())
        # OR条件で借方金額または貸方金額のいずれかに値があるものを抽出する
        self.amount_rows = line_df[
            (pd.notna(line_df[self.columns["伝票"]]))
            & (pd.notna(line_df[self.columns["明細行"]]))
            & (pd.isna(line_df[self.columns["借方補助科目"]]))
            & (pd.isna(line_df[self.columns["貸方補助科目"]]))
            & (pd.isna(line_df[self.columns["借方部門"]]))
            & (pd.isna(line_df[self.columns["貸方部門"]]))
            & (pd.notna(line_df["Debit_Amount"]) | pd.notna(line_df["Credit_Amount"]))
        ].drop_duplicates()
        self.debug_print("\namount_rows OR条件で借方金額または貸方金額のいずれかに値があるもの:")
        columns_to_show = [
            self.columns["伝票"],self.columns["明細行"],
            self.columns["借方補助科目"],self.columns["貸方補助科目"],
            self.columns["借方科目コード"], self.columns["借方補助科目コード"], "Debit_Amount",
            self.columns["貸方科目コード"], self.columns["貸方補助科目コード"], "Credit_Amount"
        ]
        self.debug_print(self.amount_rows[columns_to_show].head())
        # 貸方科目コードが self.params["account"]["売上高"]の場合にのみ、貸方補助科目の条件を適用（貸方補助科目が存在する場合のみ）
        # digital_transaction == 1 の電子取引の顧客コードリストを作成
        digital_transaction_customer_codes = [
            code for code, details in self.trading_partner_dict["customer"].items()
            if details.get("digital_transaction")
        ]
        self.amount_rows[self.columns["貸方科目コード"]] = np.where(
            (
                self.amount_rows[self.columns["貸方科目コード"]]
                == self.params["account"]["売上高"]
            )
            & (pd.notna(self.amount_rows[self.columns["借方補助科目コード"]]))
            & (
                self.amount_rows[self.columns["借方補助科目コード"]]
                .astype(str)
                .isin(digital_transaction_customer_codes)
            ),
            self.params["account"]["電子取引売上高"],
            np.where(
                (
                    self.amount_rows[self.columns["貸方科目コード"]]
                    == self.params["account"]["売上高"]
                )
                & (pd.notna(self.amount_rows[self.columns["借方補助科目コード"]]))
                & (
                    ~self.amount_rows[self.columns["借方補助科目コード"]]
                    .astype(str)
                    .isin(digital_transaction_customer_codes)
                ),
                self.params["account"]["電子取引以外売上高"],
                self.amount_rows[self.columns["貸方科目コード"]],
            ),
        )
        # 貸方科目名を変更
        self.amount_rows[self.columns["貸方科目名"]] = np.where(
            (self.amount_rows[self.columns["貸方科目コード"]] == self.params["account"]["電子取引売上高"]),
            "電子取引売上高",
            np.where(
                (self.amount_rows[self.columns["貸方科目コード"]] == self.params["account"]["電子取引以外売上高"]),
                "電子取引以外売上高",
                self.amount_rows[self.columns["貸方科目名"]]  # その他は変更しない
            )
        )
        codes_to_check = [self.params["account"]["電子取引売上高"], self.params["account"]["電子取引以外売上高"]]
        # DataFrameに含まれているか確認
        missing_codes = [code for code in codes_to_check if code not in self.amount_rows[self.columns["貸方科目コード"]].values]
        # 結果を表示
        if missing_codes:
            self.trace_print(f"以下のコードはself.pl_data_dfに存在しません: {missing_codes}")
        else:
            self.debug_print(f"self.pl_data_dfには、{codes_to_check} が全て存在します。")
        self.amount_rows = self.amount_rows[
            [
                self.columns["伝票"],
                self.columns["明細行"],
                "Month",
                self.columns["伝票日付"],
                self.columns["伝票番号"],
                self.columns["摘要文"],
                # 借方
                self.columns["借方科目コード"],
                self.columns["借方科目名"],
                "Debit_Amount",
                self.columns["借方税区分コード"],
                self.columns["借方税区分名"],
                self.columns["借方消費税額"],
                self.columns["借方補助科目コード"],
                self.columns["借方補助科目名"],
                self.columns["借方部門コード"],
                self.columns["借方部門名"],
                # 貸方
                self.columns["貸方科目コード"],
                self.columns["貸方科目名"],
                "Credit_Amount",
                self.columns["貸方税区分コード"],
                self.columns["貸方税区分名"],
                self.columns["貸方消費税額"],
                self.columns["貸方補助科目コード"],
                self.columns["貸方補助科目名"],
                self.columns["貸方部門コード"],
                self.columns["貸方部門名"],
            ]
        ]
        self.amount_rows[self.columns["借方消費税額"]] = self.amount_rows[self.columns["借方消費税額"]].fillna(0).astype(float).astype(int)
        self.amount_rows[self.columns["貸方消費税額"]] = self.amount_rows[self.columns["貸方消費税額"]].fillna(0).astype(float).astype(int)
        # List of columns to process
        columns_to_process = [
            self.columns['借方補助科目コード'],
            self.columns['貸方補助科目コード'],
            self.columns['借方部門コード'],
            self.columns['貸方部門コード']
        ]
        # Replace NaN with "" and keep 0 as "0"
        for column in columns_to_process:
            self.amount_rows[column] = (
                self.amount_rows[column]
                .apply(lambda x: "0" if x == 0 else "" if pd.isna(x) else str(int(float(x))))
            )
        self.debug_print(f"\nself.amount_rows \n{self.amount_rows}")
        log_tracker.write_log_text("e-Tax Template")
        self.etax_template()
        log_tracker.write_log_text("General Ledger")
        self.general_ledger()
        log_tracker.write_log_text("Account Dict")
        self.fill_account_dict()
        log_tracker.write_log_text("Trial Balance")
        self.trial_balance_carried_forward()
        log_tracker.write_log_text("BS/PL")
        self.bs_pl()
        for column in self.amount_rows:
            if pd.api.types.is_numeric_dtype(self.amount_rows[column]):
                self.amount_rows[column].fillna(0, inplace=True)
            else:
                self.amount_rows[column].fillna("", inplace=True)
        log_tracker.write_log_text("END CSV to DataFrame")


class GUI:
    def __init__(self, root):
        self.style = ttk.Style()
        self.root = root
        self.base_frame = None
        self.previous_selection = None
        self.original_data = []  # TreeViewの元のデータを保持するリスト
        self.params = None
        self.columns = None
        self.amount_df = None
        self.general_ledger_df = None
        self.summary_df = None
        self.log_text = None
        self.month_title = None
        self.month_combobox = None
        self.account_title = None
        self.account_combobox = None
        self.combobox = None
        self.menu = None
        self.frame0 = None
        self.frame1 = None
        self.frame2 = None
        self.frame3 = None
        self.frame4 = None
        self.frame_number = None
        self.result_tree0 = None
        self.result_tree1 = None
        self.result_tree2 = None
        self.result_tree3 = None
        self.result_tree4 = None
        self.columns0 = None
        self.columns1 = None
        self.columns2 = None
        self.columns3 = None
        self.columns4 = None
        self.result_tree1_data = None
        self.column_visible = False
        self.combobox_width = None
        self.width_dimension = 20
        self.width_code = 30
        self.width_account = 80
        self.width_subaccount = 40
        self.width_amount = 90
        self.width_taxamount = 40
        self.width_name = 180
        self.width_taxname = 80
        self.width_longname = 240
        self.width_codename = 120
        self.width_text = 360
        self.width_month = 60
        self.width_date = 80
        self.line = None
        self.no_account_label = None
        self.no_month_label = None

        self.style = ttk.Style()
        self.style.theme_use("default")  # 必要ならテーマを設定
        # カスタムスタイルを設定
        bg_color = self.get_background_color()
        self.style.configure("Background.TCombobox", fieldbackground=bg_color, background=bg_color)

        with open(param_file_path, "r", encoding="utf-8-sig") as param_file:
            params = json.load(param_file)
        self.params = params
        self.DEBUG = 1 == params["DEBUG"]
        self.TRACE = 1 == params["TRACE"]
        self.file_path = params["e-tax_file_path"]
        self.lang = params["lang"]

    def debug_print(self, message):
        if self.DEBUG:
            print(message)

    def trace_print(self, message):
        if self.TRACE:
            print(message)

    def debug_grid(self):
        # グリッドの行数と列数を指定（必要に応じて変更）
        num_rows = 6  # 仮の行数
        num_columns = 6  # 仮の列数
        # デバッグ用に各セルを塗り分ける
        for row in range(num_rows):
            for column in range(num_columns):
                # ラベルウィジェットを作成し、背景色を設定
                color = f'#{(row * 20 % 255):02x}{(column * 20 % 255):02x}AA'
                label = tk.Label(self.base_frame, text=f"R{row}C{column}", bg=color, relief="solid", width=10, height=2)
                # グリッドに配置
                label.grid(row=row, column=column, sticky="nsew")
        # グリッドの列と行のリサイズ設定
        for col in range(num_columns):
            self.base_frame.grid_columnconfigure(col, weight=1)
        for row in range(num_rows):
            self.base_frame.grid_rowconfigure(row, weight=1)

    def toggle_language(self):
        if self.lang == "en":
            self.lang = "ja"
            tidy_data.lang = "ja"
        else:
            self.lang = "en"
            tidy_data.lang = "en"
        self.update_labels()

    def update_labels(self):
        # Update labels based on the selected language
        if self.lang == "en":
            self.show_button.config(text="Show")
            self.account_title.config(text="Account:")
            self.month_title.config(text="Month:")
            self.load_button.config(text="Load Parameters")
            self.reset_button.config(text="Reset Selection")
            self.combobox["values"] = ["Journal Entry", "General Ledger", "Trial Balance", "Balance Sheet", "Profit and Loss"]
            if self.combobox.get() == "仕訳帳":
                self.combobox.set("Journal Entry")
            elif self.combobox.get() == "総勘定元帳画面":
                self.combobox.set("General Ledger")
            elif self.combobox.get() == "試算表画面":
                self.combobox.set("Trial Balance")
            elif self.combobox.get() == "貸借対照表":
                self.combobox.set("Balance Sheet")
            elif self.combobox.get() == "損益計算書":
                self.combobox.set("Profit and Loss")
            self.search_label.config(text="Search Term:")
            self.search_button.config(text="Search")
            self.reset_search_button.config(text="Reset Search")
            self.view_button.config(text="View Data")
            self.toggle_column_button.config(text="Toggle Code Columns")
            self.save_button.config(text="Save CSV")
            self.toggle_language_button.config(text="日本語/English")
        else:
            self.show_button.config(text="表示")
            self.account_title.config(text="科目:")
            self.month_title.config(text="対象月:")
            self.load_button.config(text="パラメタファイル")
            self.reset_button.config(text="選択解除")
            self.combobox["values"] = ["仕訳帳", "総勘定元帳画面", "試算表画面", "貸借対照表", "損益計算書"]
            if self.combobox.get() == "Journal Entry":
                self.combobox.set("仕訳帳")
            elif self.combobox.get() == "General Ledger":
                self.combobox.set("総勘定元帳画面")
            elif self.combobox.get() == "Trial Balance":
                self.combobox.set("試算表画面")
            elif self.combobox.get() == "Balance Sheet":
                self.combobox.set("貸借対照表")
            elif self.combobox.get() == "Profit and Loss":
                self.combobox.set("損益計算書")
            self.search_label.config(text="摘要文 検索語:")
            self.search_button.config(text="検索")
            self.reset_search_button.config(text="検索解除")
            self.view_button.config(text="データ参照")
            self.toggle_column_button.config(text="コード列の表示/非表示")
            self.save_button.config(text="CSV保存")
            self.toggle_language_button.config(text="日本語/English")
        self.update_tree_headings()

    def load_json(self):
        # Open file dialog to select a JSON file
        param_file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not param_file_path:
            return
        # Load the JSON file
        with open(param_file_path, "r", encoding="utf-8-sig") as param_file:
            params = json.load(param_file)
            self.columns = params['columns']
        tidy_data.csv2dataframe(param_file)

    def reset_filters(self, event=None):
        self.account_combobox.set('')
        self.month_combobox.set('')

    def show_frame(self, frame, frame_number):
        self.frame_number = frame_number
        frame.tkraise()
        if 0 == frame_number: # Journal Entry
            self.hide_account()
            self.show_month()
            self.show_reset()
        elif 1 == frame_number: # General Ledger
            self.show_account()
            self.show_month()
            self.show_reset()
        elif 2 == frame_number: # Trial Balance
            self.hide_account()
            self.show_month()
            self.show_reset()
        elif 3 == frame_number: # Balance Sheet
            self.hide_account()
            self.hide_month()
            self.hide_reset()
        elif 4 == frame_number: # Profit and Loss
            self.hide_account()
            self.hide_month()
            self.hide_reset()

    def get_cell_width_in_chars(self, frame, row, column, font_name="TkDefaultFont"):
        # セルのピクセル幅を取得
        bbox = frame.grid_bbox(row, column)
        if not bbox:
            return 0  # セルが存在しない場合
        cell_width_pixels = bbox[2]
        # フォントを作成
        current_font = font.Font(name=font_name, exists=True)  # 現在のフォントを取得
        char_width = current_font.measure("A")  # 'A' 1文字分の幅をピクセル単位で取得
        # 文字数に換算
        if char_width > 0:
            return cell_width_pixels // char_width
        return 0

    def get_background_color(self):
        # ttk.Frameの背景色を取得
        style = ttk.Style()
        return style.lookup("TFrame", "background") or "SystemButtonFace"

    def show_account(self):
        self.account_title.config(fg="black")
        account_dict = tidy_data.get_account_dict()
        accounts = [key.split(" ", 1)[1] for key in account_dict.keys()]
        self.account_combobox["values"] = accounts
        self.account_combobox.configure(style="TCombobox")

    def hide_account(self):
        self.account_title.config(fg=self.account_title.cget("bg"))
        bg_color = self.get_background_color()
        self.account_combobox["values"] = [""]
        self.account_combobox.set('')
        self.account_combobox.configure(style="Background.TCombobox")

    def show_month(self):
        self.month_title.config(fg="black")
        summary_df = tidy_data.get_summary_df()
        months = sorted(summary_df["Month"].unique())
        self.month_combobox["values"] = [""] + months
        self.month_combobox.configure(style="TCombobox")

    def hide_month(self):
        self.month_title.config(fg=self.month_title.cget("bg"))
        self.month_combobox["values"] = [""]
        self.month_combobox.set('')
        self.month_combobox.configure(style="Background.TCombobox")

    def show_reset(self):
        self.reset_button.config(fg="black")

    def hide_reset(self):
        self.reset_button.config(fg=self.reset_button.cget("bg"))

    def search_keyword(self):
        # columns = self.columns
        search_term = self.search_entry.get().lower()
        frame_number = self.frame_number
        if 0 == frame_number:
            result_tree = self.result_tree0
            """
            0   row[self.columns["伝票"]],
            1   row[self.columns["明細行"]],
            2   row[self.columns["伝票日付"]],
            3   row[self.columns["伝票番号"]],
            *4  row[self.columns["摘要文"]],
            5   row[self.columns["借方科目コード"]],
            *6  row[self.columns["借方科目名"]],
            7   row["Debit_Amount"],
            8   row[self.columns["借方税区分コード"]],
            9   row[self.columns["借方税区分名"]],
            10  row[self.columns["借方消費税額"]],
            11  row[self.columns["貸方科目コード"]],
            *12 row[self.columns["貸方科目名"]],
            13  row["Credit_Amount"],
            14  row[self.columns["貸方税区分コード"]],
            15  row[self.columns["貸方税区分名"]],
            16  row[self.columns["貸方消費税額"]],
            17  row[self.columns["借方補助科目コード"]],
            *18 row[self.columns["借方補助科目名"]],
            19  row[self.columns["借方部門コード"]],
            *20 row[self.columns["借方部門名"]],
            21  row[self.columns["貸方補助科目コード"]],
            *22 row[self.columns["貸方補助科目名"]],
            23  row[self.columns["貸方部門コード"]],
            *24 row[self.columns["貸方部門名"]],
            """
            n_description = 4 # 摘要文
            n_debit_account = 6 # 借方科目
            n_credit_account = 12 # 貸方科目
            n_debit_subaccount = 18 # 借方補助科目名
            n_debit_department = 20 # 借方部門名
            n_credit_subaccount = 22 # 貸方補助科目名
            n_credit_department = 24 # 貸方部門名
            filtered_data = []
            for row in self.original_data:
                if (
                    (
                        pd.notna(row[n_description]) and search_term in row[n_description].lower()
                    )
                    or (
                        pd.notna(row[n_debit_account]) and search_term in row[n_debit_account].lower()
                    )
                    or (
                        pd.notna(row[n_credit_account]) and search_term in row[n_credit_account].lower()
                    )
                    or (
                        pd.notna(row[n_debit_subaccount]) and search_term in row[n_debit_subaccount].lower()
                    )
                    or (
                        pd.notna(row[n_debit_department]) and search_term in row[n_debit_department].lower()
                    )
                    or (
                        pd.notna(row[n_credit_subaccount]) and search_term in row[n_credit_subaccount].lower()
                    )
                    or (
                        pd.notna(row[n_credit_department]) and search_term in row[n_credit_department].lower()
                    )
                ):
                    filtered_data.append(row)
        elif 1 == frame_number:
            result_tree = self.result_tree1
            """
            0   row["Transaction_Date"],  # オリジナルの日付列を使用
            *1  row["Description"],
            2   row["Debit_Amount"],
            3   row["Credit_Amount"],
            4   row["Balance"],
            5   row["Counterpart_Account_Number"],
            *6  row["Counterpart_Account_Name"],
            7   row["Subaccount_Code"],
            *8  row["Subaccount_Name"],
            9   row["Department_Code"],
            *10 row["Department_Name"],
            11  row["Counterpart_Subaccount_Code"],
            *12 row["Counterpart_Subaccount_Name"],
            13  row["Counterpart_Department_Code"],
            *14 row["Counterpart_Department_Name"],
            """
            n_description = 1 # 1 '制服代' 摘要文
            n_counterpart_account = 6 # 6 '福利厚生費' 相手科目
            n_subaccount = 8 # 8 補助科目名
            n_department = 10 # 10 '共通部門' 部門
            n_counterpart_subaccount = 12 # 12 相手補助科目名
            n_counterpart_department = 14 # 14 '札幌営業所' 相手部門
            filtered_data = []
            for row in self.original_data:
                if (
                    (
                        pd.notna(row[n_description]) and search_term in row[n_description].lower()
                    )
                    or (
                        pd.notna(row[n_counterpart_account]) and search_term in row[n_counterpart_account].lower()
                    )
                    or (
                        pd.notna(row[n_department]) and search_term in row[n_department].lower()
                    )
                    or (
                        pd.notna(row[n_counterpart_department]) and search_term in row[n_counterpart_department].lower()
                    )
                    or (
                        pd.notna(row[n_subaccount]) and search_term in row[n_subaccount].lower()
                    )
                    or (
                        pd.notna(row[n_counterpart_subaccount]) and search_term in row[n_counterpart_subaccount].lower()
                    )
                ):
                    filtered_data.append(row)
        else:
            return

        for i in result_tree.get_children():
            result_tree.delete(i)

        for row in filtered_data:
            result_tree.insert("", "end", values=self.format_searched_row(row, frame_number))

    def reset_search(self):
        frame_number = self.frame_number
        if 0 == frame_number:
            result_tree = self.result_tree0
        elif 1 == frame_number:
            result_tree = self.result_tree1
        else:
            return
        # TreeViewの内容をクリア
        for item in result_tree.get_children():
            result_tree.delete(item)
        # self.original_dataからデータを挿入
        for row in self.original_data:
            result_tree.insert("", "end", values=row)

    def view_data(self, event=None):
        frame_number = self.frame_number
        self.debug_print(f"frame number: {frame_number}")
        # Get the selected item
        if 0 == frame_number:
            item = self.result_tree0.selection()[0]
            row_data = self.result_tree0.item(item, "values")
            description = row_data[4]  # Assuming "Description" is the 4th column
        elif 1 == frame_number:
            item = self.result_tree1.selection()[0]
            row_data = self.result_tree1.item(item, "values")
            description = row_data[1]  # Assuming "Description" is the 2nd column
        else:
            return
        pdf_path = f'LedgerExplorer/slip/{description}.pdf'
        pdf_path = os.path.abspath(pdf_path)
        if os.path.isfile(pdf_path):
            webbrowser.open(f'file://{pdf_path}')
        else:
            if self.lang == "en":
                messagebox.showwarning("Warning", "No corresponding PDF found.")
            else:
                messagebox.showwarning("警告", "該当するPDFが見つかりませんでした。")

    def save_dict2csv(self, output_file, data_dict):
        # Save the dictionary as a CSV
        with open(output_file, mode='w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file)
            # Write the header row
            header = ["Ledger_Account_Number"] + list(next(iter(data_dict.values())).keys())
            writer.writerow(header)
            # Write each row of data
            for key, values in data_dict.items():
                row = [key] + [values.get(col, "") for col in header[1:]]
                writer.writerow(row)

    def save_csv(self):
        # ディレクトリダイアログを表示して保存ディレクトリを選択
        directory = filedialog.askdirectory()
        if directory:
            try:
                # DataFrameをCSVファイルに保存
                amount_path = os.path.join(directory, 'data_amount.csv')
                general_ledger_path = os.path.join(directory, 'data_general_ledger.csv')
                summary_path = os.path.join(directory, 'data_summary.csv')
                amount_rows = tidy_data.get_amount_rows()
                amount_df = pd.DataFrame(amount_rows).copy()
                amount_df.to_csv(amount_path, index=False, encoding="utf-8-sig")
                tidy_data.get_general_ledger_df().to_csv(general_ledger_path, index=False, encoding="utf-8-sig")
                tidy_data.get_summary_df().to_csv(summary_path, index=False, encoding="utf-8-sig")
                input_BS_path = tidy_data.BS_path[1+tidy_data.BS_path.index('/'):] # BS Template CSV
                output_BS_path = os.path.join(directory, input_BS_path)
                self.save_dict2csv(output_BS_path, tidy_data.bs_dict)
                input_PL_path = tidy_data.PL_path[1+tidy_data.PL_path.index('/'):]  # PL Template CSV
                output_PL_path = os.path.join(directory, input_PL_path)
                self.save_dict2csv(output_PL_path, tidy_data.pl_dict)
                if self.lang == "en":
                    messagebox.showinfo("Success", f"DataFrames have been saved as CSV files to {amount_path}, {general_ledger_path}, {summary_path}, {output_BS_path}, {output_PL_path}.")
                else:
                    messagebox.showinfo("成功", f"DataFrameをCSVファイルとして {amount_path}, {general_ledger_path}, {summary_path}, {output_BS_path}, {output_PL_path} に保存しました。")
            except Exception as e:
                if self.lang == "en":
                    messagebox.showerror("Error", f"Failed to save: {str(e)}")
                else:
                    messagebox.showerror("エラー", f"保存に失敗しました: {str(e)}")

    def on_combobox_select(self, event=None):
        selected_option = self.combobox.get()
        log_tracker.write_log_text(selected_option)
        if self.lang == "en":
            if selected_option == "Journal Entry":
                self.show_frame(self.frame0, 0)
            elif selected_option == "General Ledger":
                self.show_frame(self.frame1, 1)
            elif selected_option == "Trial Balance":
                self.show_frame(self.frame2, 2)
            elif selected_option == "Balance Sheet":
                self.show_frame(self.frame3, 3)
            elif selected_option == "Profit and Loss":
                self.show_frame(self.frame4, 4)
        else:
            if selected_option == "仕訳帳":
                self.show_frame(self.frame0, 0)
            elif selected_option == "総勘定元帳画面":
                self.show_frame(self.frame1, 1)
            elif selected_option == "試算表画面":
                self.show_frame(self.frame2, 2)
            elif selected_option == "貸借対照表":
                self.show_frame(self.frame3, 3)
            elif selected_option == "損益計算書":
                self.show_frame(self.frame4, 4)
        

    def create_base(self):
        root = self.root
        # 13インチMacBook Air（M2/M3）は1,470×956ピクセル、14インチMacBook Pro（M3/M3 Pro/M3 Max）は1,512×982ピクセルの解像度
        root.geometry("1450x950")
        root.update_idletasks()  # ウィンドウのレイアウトを更新
        root_width = root.winfo_width()  # rootウィンドウの幅を取得
        root_height = root.winfo_height()  # rootウィンドウの高さを取得

        self.previous_selection = None
        if self.lang == "en":
            root.title("Accounting Ledgers")
        else:
            root.title("会計帳簿")
        self.base_frame = tk.Frame(root)
        self.base_frame.pack(side="top", fill="x", padx=10, pady=10)
        # self.base_frameの幅と高さをrootのサイズに合わせる
        self.base_frame.config(width=root_width, height=root_height)

    def insert_data(self, filtered_df, result_tree, frame_number):
        # 元のデータを保存するリスト
        self.original_data = []
        for index, row in filtered_df.iterrows():
            # フォーマット済みのデータを取得
            formatted_row = self.format_row(row, frame_number)
            # TreeView にデータを挿入
            result_tree.insert("", "end", values=formatted_row)
            # フォーマット済みのデータを保存
            self.original_data.append(formatted_row)
            # レスポンス性を維持するための更新処理
            if index % 100 == 0:
                result_tree.update_idletasks()  # Update the GUI to keep it responsive

    def show_results(self, frame_number, event=None):
        if self.lang == "en":
            log_tracker.write_log_text(f"START {self.menu[frame_number]}")
        else:
            log_tracker.write_log_text(f" {self.menu[frame_number]} 開始")
        self.columns = tidy_data.get_columns()
        if 0 == frame_number: # Journal Entry
            selected_month = self.month_combobox.get()
            amount_rows = tidy_data.get_amount_rows()
            self.amount_df = pd.DataFrame(amount_rows).copy()
            result_tree = self.result_tree0
            if selected_month:
                target_month = pd.Period(selected_month)
                filtered_df = self.amount_df[self.amount_df['Month'] == str(target_month)].copy()
            else:
                filtered_df = self.amount_df.copy()
            if filtered_df.empty:
                if self.lang == "en":
                    messagebox.showwarning("Warning", "No data found.")
                else:
                    messagebox.showwarning("警告", "データが見つかりません。")
                return
        elif 1 == frame_number: # General Ledger
            selected_account = self.account_combobox.get()
            selected_month = self.month_combobox.get()
            account_dict = self.account_dict = tidy_data.get_account_dict()
            self.general_ledger_df = tidy_data.get_general_ledger_df().copy()
            # Transaction_Date列をdatetime型に変換してTransaction_Date_dtの列に保存
            self.general_ledger_df['Transaction_Date_dt'] = pd.to_datetime(self.general_ledger_df['Transaction_Date'])
            # Transaction_Date列をYYYY-MM形式に変換してTransaction_Monthの列に保存
            self.general_ledger_df['Transaction_Month'] = self.general_ledger_df['Transaction_Date_dt'].dt.to_period('M').astype(str)
            result_tree = self.result_tree1
            if selected_month:
                filtered_df = self.general_ledger_df[self.general_ledger_df['Transaction_Month'] == selected_month].copy()
            else:
                filtered_df = self.general_ledger_df.copy()
            if selected_account:
                account_number = next((v for k, v in account_dict.items() if selected_account in k.split(' ', 1)[1]), None)
                if account_number:
                    filtered_df = filtered_df[filtered_df["Ledger_Account_Number"] == account_number]
            else:
                if self.lang == "en":
                    messagebox.showwarning("Warning", "Please select an account name.")
                else:
                    messagebox.showwarning("警告", "科目名を選択してください。")
                return
            if filtered_df.empty:
                if self.lang == "en":
                    messagebox.showwarning("Warning", "No data found.")
                else:
                    messagebox.showwarning("警告", "データが見つかりません。")
                return
        elif 2 == frame_number: # Trial Balance
            selected_month = self.month_combobox.get()
            if not selected_month:
                if self.lang == "en":
                    messagebox.showwarning("Warning", "Please select a target month.")
                else:
                    messagebox.showwarning("警告", "対象月を選択してください。")
                return
            target_month = pd.Period(selected_month)
            self.summary_df = tidy_data.get_summary_df().copy()
            filtered_df = self.summary_df[self.summary_df['Month'] == str(target_month)]
            result_tree = self.result_tree2
        elif 3 == frame_number:  # Balance Sheet (BS)
            result_tree = self.result_tree3
            # Convert dictionary to DataFrame
            filtered_df = pd.DataFrame.from_dict(tidy_data.bs_dict, orient='index').reset_index()
            # Rename the index column to `Ledger_Account_Number`
            # filtered_df.rename(columns={'index': "Ledger_Account_Number"}, inplace=True)
        elif 4 == frame_number:  # Profit and Loss (PL)
            result_tree = self.result_tree4
            # Convert dictionary to DataFrame
            filtered_df = pd.DataFrame.from_dict(tidy_data.pl_dict, orient='index').reset_index()
            # Rename the index column to `Ledger_Account_Number`
            # filtered_df.rename(columns={'index': "Ledger_Account_Number"}, inplace=True)
        # Treeviewの行削除
        for i in result_tree.get_children():
            result_tree.delete(i)
        self.insert_data(filtered_df, result_tree, frame_number)
        if self.lang == "en":
            log_tracker.write_log_text(f"END {self.menu[frame_number]} listing")
        else:
            log_tracker.write_log_text(f"{self.menu[frame_number]} 表示終了")

    def update_tree_headings(self):
        if 0 == self.frame_number:
            tree = self.result_tree0
            if self.lang == "en":
                headings = {
                    "Journal": "JNL",
                    "DetailRow": "LN",
                    "TransactionDate": "Date",
                    "Description": "Description",
                    "DebitAccountCode": "Cebit Account Code",
                    "DebitAccountName": "Debit Account Name",
                    "Debit_Amount": "Debit Amount",
                    "DebitTaxCode": "Debit Tax Code",
                    "DebitTaxName": "Debit Tax Name",
                    "DebitTaxAmount": "Debit Tax Amount",
                    "DebitSubaccountCode": "Debit Sub Code ",
                    "DebitSubaccountName": "Debit Sub Name",
                    "DebitDepartmentCode": "Debit Dpt. Code",
                    "DebitDepartmentName": "Debit Dpt. Name",
                    "CreditAccountCode": "Credit Account Code",
                    "CreditAccountName": "Credit Account Name",
                    "Credit_Amount": "Credit Amount",
                    "CreditTaxCode": "Credit Tax Code",
                    "CreditTaxName": "Credit Tax Name",
                    "CreditTaxAmount": "Credit Tax Amount",
                    "CreditSubaccountCode": "Credit Sub Code",
                    "CreditSubaccountName": "Credit Sub Name",
                    "CreditDepartmentCode": "Credit Dpt. Code",
                    "CreditDepartmentName": "Credit Dpt. Name",
                }
            else:
                headings = {
                    "Journal": "伝票",
                    "DetailRow": "行",
                    "TransactionDate": "取引日",
                    "Description": "摘要文",
                    "DebitAccountCode": "コード",
                    "DebitAccountName": "借方科目",
                    "Debit_Amount": "借方金額",
                    "DebitTaxCode": "コード",
                    "DebitTaxName": "借方税区分",
                    "DebitTaxAmount": "借方消費税額",
                    "DebitSubaccountCode": "コード",
                    "DebitSubaccountName": "借方補助科目",
                    "DebitDepartmentCode": "コード",
                    "DebitDepartmentName": "借方部門",
                    "CreditAccountCode": "コード",
                    "CreditAccountName": "貸方科目",
                    "Credit_Amount": "貸方金額",
                    "CreditTaxCode": "コード",
                    "CreditTaxName": "貸方税区分",
                    "CreditTaxAmount": "貸方消費税額",
                    "CreditSubaccountCode": "コード",
                    "CreditSubaccountName": "貸方補助科目",
                    "CreditDepartmentCode": "コード",
                    "CreditDepartmentName": "貸方部門",
                }
        elif 1 == self.frame_number:
            tree = self.result_tree1
            if self.lang == "en":
                headings = {
                    "Transaction_Date":"Transaction Date",
                    "Ledger_Account_Number":"Ledger Account Number",
                    "Ledger_Account_Name":"Ledger Account Name",
                    "Subaccount_Code":"Subaccount Code",
                    "Subaccount_Name":"Subaccount Name",
                    "Department_Code":"Department Code",
                    "Department_Name":"Department Name",
                    "Debit_Amount":"Debit Amount",
                    "Credit_Amount":"Credit Amount",
                    "Balance": "Balance",
                    "Counterpart_Account_Number":"Counterpart Account Number",
                    "Counterpart_Account_Name":"Counterpart Account Name",
                    "Counterpart_Subaccount_Code":"Counterpart Subaccount Code",
                    "Counterpart_Subaccount_Name":"Counterpart_Subaccount Name",
                    "Counterpart_Department_Code":"Counterpart Department Code",
                    "Counterpart_Department_Name":"Counterpart Department Name",
                    "Description": "Description",
                }
            else:
                headings = {
                    "Transaction_Date": "伝票日付",
                    "Ledger_Account_Number": "コード",
                    "Ledger_Account_Name": "科目",
                    "Subaccount_Code": "コード",
                    "Subaccount_Name": "補助科目",
                    "Department_Code": "コード",
                    "Department_Name": "部門",
                    "Debit_Amount": "借方金額",
                    "Credit_Amount": "貸方金額",
                    "Balance": "残高",
                    "Counterpart_Account_Number": "コード",
                    "Counterpart_Account_Name": "相手科目",
                    "Counterpart_Subaccount_Code": "コード",
                    "Counterpart_Subaccount_Name": "相手補助科目",
                    "Counterpart_Department_Code": "コード",
                    "Counterpart_Department_Name": "相手部門",
                    "Description": "摘要文",
                }
        elif 2 == self.frame_number:
            tree = self.result_tree2
            if self.lang == "en":
                headings = {
                    "Month": "Month",
                    "Account_Number":"Account Number",
                    "eTax_Category": "Account Category",
                    "Account_Name":"Account Name",
                    "Beginning_Balance":"Starting Balance",
                    "Debit_Amount":"Debit Amount",
                    "Credit_Amount":"Credit Amount",
                    "Ending_Balance":"Ending Balance",
                }
            else:
                headings = {
                    "Month": "年月",
                    "Account_Number": "コード",
                    "eTax_Category": "勘定科目区分",
                    "Account_Name": "科目",
                    "Beginning_Balance": "月初残高",
                    "Debit_Amount": "借方金額",
                    "Credit_Amount": "貸方金額",
                    "Ending_Balance": "月末残高",
                }
        elif 3 == self.frame_number:
            tree = self.result_tree3
            if self.lang == "en":
                headings = {
                    "seq": "Seq",
                    "Account_Number":"Account Number",
                    "Level": "Level",
                    "eTax_Category": "Account Category",
                    "eTax_Account_Name":"Account Name",
                    "Beginning_Balance":"Starting Balance",
                    "Ending_Balance":"Ending Balance",
                }
            else:
                headings = {
                    "seq": "順序",
                    "Account_Number": "勘定科目番号",
                    "Level": "レベル",
                    "eTax_Category": "勘定科目区分",
                    "eTax_Account_Name": "勘定科目名",
                    "Beginning_Balance": "期初残高",
                    "Ending_Balance": "期末残高",
                }
        elif 4 == self.frame_number:
            tree = self.result_tree4
            if self.lang == "en":
                headings = {
                    "seq": "SEq",
                    "Account_Number":"Account Number",
                    "Level": "Level",
                    "eTax_Category": "Account Category",
                    "eTax_Account_Name":"Account Name",
                    "Debit_Amount":"Debit Amount",
                    "Credit_Amount":"Credit Amount",
                }
            else:
                headings = {
                    "seq": "順序",
                    "Account_Number": "勘定科目番号",
                    "Level": "レベル",
                    "eTax_Category": "勘定科目区分",
                    "eTax_Account_Name": "勘定科目名",
                    "Debit_Amount": "借方金額",
                    "Credit_Amount": "貸方金額",
                }
        else:
            return
        for col, text in headings.items():
            tree.heading(col, text=text)

    def format_searched_row(self, row, frame_number):
        if 0 == frame_number:
            formatted_row = (
                row[0], # 伝票
                row[1], # 明細行
                row[2], # 伝票日付
                row[3], # 伝票番号
                row[4], # 摘要文
                # 借方
                row[5], # 借方科目コード
                row[6], # 借方科目名
                (#'Debit_Amount'
                    f"{row[7]:,.0f}" if pd.notna(row[7]) and pd.notna(row[7]) and row[6] != 0 and isinstance(row[7], (int, float)) else ""
                ),
                row[8], # 借方税区分コード
                row[9], # 借方税区分名
                row[10], # 借方消費税額
                # 貸方
                row[11], # 貸方科目コード
                row[12], # 貸方科目名
                (# 'Credit_Amount'
                    f"{row[13]:,.0f}" if pd.notna(row[13]) and pd.notna(row[13]) and row[13] != 0 and isinstance(row[13], (int, float)) else ""
                ),
                row[14], # 貸方税区分コード
                row[15], # 貸方税区分名
                row[16], # 貸方消費税額
                row[17], # 借方補助科目コード
                row[18], # 借方補助科目名
                row[19], # 借方部門コード
                row[20], # 借方部門名
                row[21], # 貸方補助科目コード
                row[22], # 貸方補助科目名
                row[23], # 貸方部門コード
                row[24], # 貸方部門名
            )
        elif 1 == frame_number:
            formatted_row = (
                row[0], # Transaction_Date  # オリジナルの日付列を使用
                row[1], # Description
                ( # 'Debit_Amount'
                    f"{row[2]:,.0f}" if pd.notna(row[2]) and row[2] != 0 and isinstance(row[2], (int, float)) else ""
                ),
                ( # 'Credit_Amount'
                    f"{row[3]:,.0f}" if pd.notna(row[3]) and row[3] != 0 and isinstance(row[3], (int, float)) else ""
                ),
                ( # 'Balance'
                    f"{row[4]:,.0f}" if pd.notna(row[4]) and row[4] != 0 and isinstance(row[4], (int, float)) else ""
                ),
                row[5], # Counterpart_Account_Number
                row[6], # Counterpart_Account_Name
                row[7], # Subaccount_Code
                row[8], # Subaccount_Name
                row[9], # Department_Code
                row[10], # Department_Name
                row[11], # Counterpart_Subaccount_Code
                row[12], # Counterpart_Subaccount_Name
                row[13], # Counterpart_Department_Code
            )
        elif 2 == frame_number:
            formatted_row = (
                row[0], # Month
                row[1], # Ledger_Account_Number
                row[2], # Ledger_Account_Name
                row[3], # e-Tax Category
                ( # 'Beginning_Balance'
                    f"{row[4]:,.0f}" if pd.notna(row[4]) and row[4] != 0 and isinstance(row[4], (int, float)) else ""
                ),
                ( # 'Debit_Amount'
                    f"{row[5]:,.0f}" if pd.notna(row[5]) and row[5] != 0 and isinstance(row[5], (int, float)) else ""
                ),
                ( # 'Credit_Amount'
                    f"{row[6]:,.0f}" if pd.notna(row[6]) and row[6] != 0 and isinstance(row[6], (int, float)) else ""
                ),
                ( # 'Ending_Balance'
                    f"{float(row[7]):,.0f}" if pd.notna(row[7]) and row[7] != 0 and isinstance(row[7], (int, float)) else ""
                )
            )
        else:
            formatted_row = row
        return formatted_row

    def format_row(self, row, frame_number):
        if 0 == frame_number: # Journal Entry
            formatted_row = (
                # 0 ~ 3
                row[self.columns["伝票"]],
                row[self.columns["明細行"]],
                row[self.columns["伝票日付"]],
                row[self.columns["伝票番号"]],
                row[self.columns["摘要文"]],
                # 借方 4 ~ 9
                row[self.columns["借方科目コード"]],
                row[self.columns["借方科目名"]],
                (
                    f"{row['Debit_Amount']:,.0f}"
                    if pd.notna(row[self.columns["借方科目コード"]])
                    and pd.notna(row["Debit_Amount"])
                    and row["Debit_Amount"] != 0
                    else ""
                ),
                row[self.columns["借方税区分コード"]],
                row[self.columns["借方税区分名"]],
                row[self.columns["借方消費税額"]],
                # 貸方 10 ~ 15
                row[self.columns["貸方科目コード"]],
                row[self.columns["貸方科目名"]],
                (
                    f"{row['Credit_Amount']:,.0f}"
                    if pd.notna(row[self.columns["貸方科目コード"]])
                    and pd.notna(row["Credit_Amount"])
                    and row["Credit_Amount"] != 0
                    else ""
                ),
                row[self.columns["貸方税区分コード"]],
                row[self.columns["貸方税区分名"]],
                row[self.columns["貸方消費税額"]],
                # 16 ~ 19
                row[self.columns["借方補助科目コード"]],
                row[self.columns["借方補助科目名"]],
                row[self.columns["借方部門コード"]],
                row[self.columns["借方部門名"]],
                # 20 ~ 23
                row[self.columns["貸方補助科目コード"]],
                row[self.columns["貸方補助科目名"]],
                row[self.columns["貸方部門コード"]],
                row[self.columns["貸方部門名"]],
            )
        elif 1 == frame_number: # General Ledger
            formatted_row = (
                # 0 ~ 4
                row["Transaction_Date"],  # オリジナルの日付列を使用
                row["Description"],
                (
                    f"{row['Debit_Amount']:,.0f}"
                    if pd.notna(row["Debit_Amount"])
                    and row["Debit_Amount"] != 0
                    else ""
                ),
                (
                    f"{row['Credit_Amount']:,.0f}"
                    if pd.notna(row["Credit_Amount"])
                    and row["Credit_Amount"] != 0
                    else ""
                ),
                (
                    f"{row['Balance']:,.0f}"
                    if pd.notna(row["Balance"]) and row["Balance"] != 0
                    else ""
                ),
                # 5 ~ 14
                row["Counterpart_Account_Number"],
                row["Counterpart_Account_Name"],
                row["Subaccount_Code"],
                row["Subaccount_Name"],
                row["Department_Code"],
                row["Department_Name"],
                row["Counterpart_Subaccount_Code"],
                row["Counterpart_Subaccount_Name"],
                row["Counterpart_Department_Code"],
                row["Counterpart_Department_Name"],
            )
        elif 2 == frame_number: # Trial Balance
            formatted_row = (
                row["Month"],
                row["Ledger_Account_Number"],
                row["Ledger_Account_Name"],
                row["eTax_Category"],
                f"{row['Beginning_Balance']:,.0f}"
                if pd.notna(row["Beginning_Balance"]) and row["Beginning_Balance"] != 0
                else "",
                f"{row['Debit_Amount']:,.0f}"
                if pd.notna(row["Debit_Amount"]) and row["Debit_Amount"] != 0
                else "",
                f"{row['Credit_Amount']:,.0f}"
                if pd.notna(row["Credit_Amount"]) and row["Credit_Amount"] != 0
                else "",
                f"{row['Ending_Balance']:,.0f}"
                if pd.notna(row["Ending_Balance"]) and row["Ending_Balance"] != 0
                else "",
            )
        elif 3 == frame_number:  # Balance Sheet
            formatted_row = (
                row["seq"],
                row["Level"],
                row["Ledger_Account_Number"],
                row["eTax_Account_Name"],
                row["eTax_Category"],
                f"{row['Beginning_Balance']:,.0f}"
                if pd.notna(row["Beginning_Balance"]) and row["Beginning_Balance"] != 0
                else "",
                f"{row['Total_Debit']:,.0f}"
                if pd.notna(row["Total_Debit"]) and row["Total_Debit"] != 0
                else "",
                f"{row['Total_Credit']:,.0f}"
                if pd.notna(row["Total_Credit"]) and row["Total_Credit"] != 0
                else "",
                f"{row['Ending_Balance']:,.0f}"
                if pd.notna(row["Ending_Balance"]) and row["Ending_Balance"] != 0
                else "",
            )
        elif 4 == frame_number:  # Profit and Loss
            formatted_row = (
                row["seq"],
                row["Level"],
                row["Ledger_Account_Number"],
                row["eTax_Account_Name"],
                row["eTax_Category"],
                # f"{row['Beginning_Balance']:,.0f}"
                # if pd.notna(row["Beginning_Balance"]) and row["Beginning_Balance"] != 0
                # else "",
                f"{row['Total_Debit']:,.0f}"
                if pd.notna(row["Total_Debit"]) and row["Total_Debit"] != 0
                else "",
                f"{row['Total_Credit']:,.0f}"
                if pd.notna(row["Total_Credit"]) and row["Total_Credit"] != 0
                else "",
                f"{row['Ending_Balance']:,.0f}"
                if pd.notna(row["Ending_Balance"]) and row["Ending_Balance"] != 0
                else "",
            )
        return formatted_row

    def toggle_column(self):
        frame_number = self.frame_number
        if 0 == frame_number:
            frame = self.frame0
            tree = self.result_tree0
            columns = self.columns0
        elif 1 == frame_number:
            frame = self.frame1
            tree = self.result_tree1
            columns = self.columns1
        elif 2 == frame_number:
            frame = self.frame2
            tree = self.result_tree2
            columns = self.columns2
        elif 3 == frame_number:
            frame = self.frame3
            tree = self.result_tree3
            columns = self.columns3
        elif 4 == frame_number:
            frame = self.frame4
            tree = self.result_tree4
            columns = self.columns4
        else:
            return
        # コード列の表示/非表示を切り替える
        self.column_visible = not self.column_visible
        if self.column_visible:
            if 0 == frame_number:
                tree.column("DebitAccountCode", width=self.width_account, anchor="center", stretch=tk.NO)
                tree.column("DebitTaxCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                tree.column("DebitSubaccountCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                tree.column("DebitDepartmentCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                tree.column("CreditAccountCode", width=self.width_account, anchor="center", stretch=tk.NO)
                tree.column("CreditTaxCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                tree.column("CreditSubaccountCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                tree.column("CreditDepartmentCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
            elif 1 == frame_number:
                tree.column("Ledger_Account_Number", width=self.width_account, anchor="center", stretch=tk.NO)
                tree.column("Subaccount_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                tree.column("Department_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                tree.column("Counterpart_Account_Number", width=self.width_account, anchor="center", stretch=tk.NO)
                tree.column("Counterpart_Subaccount_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                tree.column("Counterpart_Department_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
            elif 2 == frame_number:
                self.result_tree2.column("Account_Number", width=self.width_account, stretch=tk.NO)
            elif 3 == frame_number:
                self.result_tree3.column("Ledger_Account_Number", width=self.width_account, anchor="center", stretch=tk.NO)
            elif 4 == frame_number:
                self.result_tree4.column("Ledger_Account_Number", width=self.width_account, anchor="center", stretch=tk.NO)
        else:
            if 0 == frame_number:
                tree.column("DebitAccountCode", width=0, stretch=tk.NO)
                tree.column("DebitTaxCode", width=0, stretch=tk.NO)
                tree.column("DebitSubaccountCode", width=0, stretch=tk.NO)
                tree.column("DebitDepartmentCode", width=0, stretch=tk.NO)
                tree.column("CreditAccountCode", width=0, stretch=tk.NO)
                tree.column("CreditTaxCode", width=0, stretch=tk.NO)
                tree.column("CreditSubaccountCode", width=0, stretch=tk.NO)
                tree.column("CreditDepartmentCode", width=0, stretch=tk.NO)
            elif 1 == frame_number:
                tree.column("Ledger_Account_Number", width=0, stretch=tk.NO)
                tree.column("Subaccount_Code", width=0, stretch=tk.NO)
                tree.column("Department_Code", width=0, stretch=tk.NO)
                tree.column("Counterpart_Account_Number", width=0, stretch=tk.NO)
                tree.column("Counterpart_Subaccount_Code", width=0, stretch=tk.NO)
                tree.column("Counterpart_Department_Code", width=0, stretch=tk.NO)
            elif 2 == frame_number:
                tree.column("Account_Number", width=0, stretch=tk.NO)
            elif 3 == frame_number:
                tree.column("Ledger_Account_Number", width=0, stretch=tk.NO)
            elif 4 == frame_number:
                tree.column("Ledger_Account_Number", width=0, stretch=tk.NO)
        # TreeviewまたはFrameの幅を更新する関数
        # 表示されている列の合計幅を計算
        total_width = sum(
            tree.column(col, option="width")
            for col in columns
            if tree.column(col, option="width") > 0
        )
        # Treeviewとフレームの幅を更新
        frame.config(width=total_width)
        # Treeviewのサイズ調整 (packの代わりにgridを使用)
        tree.grid(sticky="nsew")  # gridを統一して使用

    def create_frame0(self):
        # Frame 0: 仕訳帳表示 Journal entry
        frame = self.frame0
        self.columns0 = (
            "Journal",
            "DetailRow",
            "TransactionDate",
            "Entry_ID",
            "Description",
            "DebitAccountCode",
            "DebitAccountName",
            "Debit_Amount",
            "DebitTaxCode",
            "DebitTaxName",
            "DebitTaxAmount",
            "CreditAccountCode",
            "CreditAccountName",
            "Credit_Amount",
            "CreditTaxCode",
            "CreditTaxName",
            "CreditTaxAmount",
            "DebitSubaccountCode",
            "DebitSubaccountName",
            "DebitDepartmentCode",
            "DebitDepartmentName",
            "CreditSubaccountCode",
            "CreditSubaccountName",
            "CreditDepartmentCode",
            "CreditDepartmentName",
        )
        # Treeviewの作成
        self.result_tree0 = ttk.Treeview(
            frame,
            columns=self.columns0,
            show="headings",
            height=37
        )
        tree = self.result_tree0
        # width
        tree.column("Journal", width=self.width_dimension, anchor="e", stretch=tk.NO)
        tree.column("DetailRow", width=self.width_dimension, anchor="e", stretch=tk.NO)
        tree.column("TransactionDate", width=self.width_date, anchor="center", stretch=tk.NO)
        tree.column("Entry_ID", width=self.width_code, anchor="e", stretch=tk.NO)
        tree.column("Description", width=self.width_text, anchor="w", stretch=tk.NO)
        tree.column("DebitAccountCode", width=self.width_account, anchor="center", stretch=tk.NO)
        tree.column("DebitAccountName", width=self.width_longname, anchor="w", stretch=tk.NO)
        tree.column("Debit_Amount", width=self.width_amount, anchor="e", stretch=tk.NO)
        tree.column("DebitTaxCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        tree.column("DebitTaxName", width=self.width_taxname, anchor="w", stretch=tk.NO)
        tree.column("DebitTaxAmount", width=self.width_taxamount, anchor="e", stretch=tk.NO)
        tree.column("CreditAccountCode", width=self.width_account, anchor="center", stretch=tk.NO)
        tree.column("CreditAccountName", width=self.width_longname, anchor="w", stretch=tk.NO)
        tree.column("Credit_Amount", width=self.width_amount, anchor="e", stretch=tk.NO)
        tree.column("CreditTaxCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        tree.column("CreditTaxName", width=self.width_taxname, anchor="w", stretch=tk.NO)
        tree.column("CreditTaxAmount", width=self.width_taxamount, anchor="e", stretch=tk.NO)
        tree.column("DebitSubaccountCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        tree.column("DebitSubaccountName", width=self.width_codename, anchor="w", stretch=tk.NO)
        tree.column("DebitDepartmentCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        tree.column("DebitDepartmentName", width=self.width_codename, anchor="w", stretch=tk.NO)
        tree.column("CreditSubaccountCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        tree.column("CreditSubaccountName", width=self.width_codename, anchor="w", stretch=tk.NO)
        tree.column("CreditDepartmentCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        tree.column("CreditDepartmentName", width=self.width_codename, anchor="w", stretch=tk.NO)
        # text
        tree.heading("Journal", text="Journal" if self.lang=="en" else "仕訳")
        tree.heading("DetailRow", text="Detail Row" if self.lang=="en" else "明細行")
        tree.heading("TransactionDate", text="Date" if self.lang=="en" else "日付")
        tree.heading("Entry_ID", text="Entry ID" if self.lang=="en" else "仕訳番号")
        tree.heading("Description", text="Description" if self.lang=="en" else "摘要")
        tree.heading("DebitAccountCode", text="Debit Account Code" if self.lang=="en" else "借方科目コード")
        tree.heading("DebitAccountName", text="Debit Account Name" if self.lang=="en" else "借方科目名")
        tree.heading("Debit_Amount", text="Debit Amount" if self.lang=="en" else "借方金額")
        tree.heading("DebitTaxCode", text="Debit Tax Code" if self.lang=="en" else "借方税コード")
        tree.heading("DebitTaxName", text="Debit Tax Name" if self.lang=="en" else "借方税")
        tree.heading("DebitTaxAmount", text="Debit Tax Amount" if self.lang=="en" else "借方税額")
        tree.heading("CreditAccountCode", text="Credit Account" if self.lang=="en" else "貸方科目コード")
        tree.heading("CreditAccountName", text="貸方科目名" if self.lang=="ja" else "")
        tree.heading("Credit_Amount", text="Credit Amount" if self.lang=="en" else "貸方金額")
        tree.heading("CreditTaxCode", text="Credit Tax Code" if self.lang=="en" else "貸方税コード")
        tree.heading("CreditTaxName", text="Credit Tax Name" if self.lang=="en" else "貸方税")
        tree.heading("CreditTaxAmount", text="Credit Tax Amount" if self.lang=="en" else "貸方税額")
        tree.heading("DebitSubaccountCode", text="Debit Subaccount Code" if self.lang=="en" else "借方補助科目コード")
        tree.heading("DebitSubaccountName", text="Debit Subaccount Name" if self.lang=="en" else "借方補助科目名")
        tree.heading("DebitDepartmentCode", text="Debit Department Code" if self.lang=="en" else "借方部門コード")
        tree.heading("DebitDepartmentName", text="Debit epartment Name" if self.lang=="en" else "借方部門名")
        tree.heading("CreditSubaccountCode", text="Credit Subaccount Code" if self.lang=="en" else "貸方補助科目コード")
        tree.heading("CreditSubaccountName", text="Credit Subaccount Name" if self.lang=="en" else "貸方補助科目名")
        tree.heading("CreditDepartmentCode", text="Credit Department Code" if self.lang=="en" else "貸方部門コード")
        tree.heading("CreditDepartmentName", text="Credit Department Name" if self.lang=="en" else "貸方部門名")
        # Treeview を frame に配置
        tree.grid(row=0, column=0, sticky="nsew")
        # 水平スクロールバーの作成と配置
        scrollbar0x = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        scrollbar0x.grid(row=1, column=0, sticky="ew")
        # 垂直スクロールバーの作成と配置
        scrollbar0y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar0y.grid(row=0, column=1, sticky="ns")
        # Treeview にスクロールバーを関連付け
        tree.configure(xscrollcommand=scrollbar0x.set, yscrollcommand=scrollbar0y.set)
        # double click
        tree.bind("<Double-1>", self.view_data)

    def create_frame1(self):
        # Frame 1: 総勘定元帳表示 General Ledger
        frame = self.frame1
        self.columns1 = (
            "Transaction_Date",
            "Description",
            "Debit_Amount",
            "Credit_Amount",
            "Balance",
            "Counterpart_Account_Number",
            "Counterpart_Account_Name",
            "Subaccount_Code",
            "Subaccount_Name",
            "Department_Code",
            "Department_Name",
            "Counterpart_Subaccount_Code",
            "Counterpart_Subaccount_Name",
            "Counterpart_Department_Code",
            "Counterpart_Department_Name",
        )
        self.result_tree1 = ttk.Treeview(
            frame,
            columns=self.columns1,
            show="headings",
            height=37
        )
        tree = self.result_tree1
        # width
        tree.column("Transaction_Date", width=self.width_date, anchor="center", stretch=tk.NO)
        tree.column("Description", width=self.width_text, anchor="w", stretch=tk.NO)
        tree.column("Debit_Amount", width=self.width_amount, anchor="e", stretch=tk.NO)
        tree.column("Credit_Amount", width=self.width_amount, anchor="e", stretch=tk.NO)
        tree.column("Balance", width=self.width_amount, anchor="e", stretch=tk.NO)
        tree.column("Subaccount_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        tree.column("Subaccount_Name", width=self.width_codename, anchor="w", stretch=tk.NO)
        tree.column("Department_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        tree.column("Department_Name", width=self.width_codename, anchor="w", stretch=tk.NO)
        tree.column("Counterpart_Account_Number", width=0, anchor="center", stretch=tk.NO)
        tree.column("Counterpart_Account_Name", width=self.width_longname, anchor="w", stretch=tk.NO)
        tree.column("Counterpart_Subaccount_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        tree.column("Counterpart_Subaccount_Name", width=self.width_codename, anchor="w", stretch=tk.NO)
        tree.column("Counterpart_Department_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        tree.column("Counterpart_Department_Name", width=self.width_codename, anchor="w", stretch=tk.NO)
        # text
        tree.heading("Transaction_Date", text="Date" if self.lang=="en" else "日付")
        tree.heading("Description", text="Description" if self.lang=="en" else "摘要")
        tree.heading("Debit_Amount", text="Debit Amount" if self.lang=="en" else "借方金額")
        tree.heading("Credit_Amount", text="Credit Amount" if self.lang=="en" else "貸方金額")
        tree.heading("Balance", text="Balance" if self.lang=="en" else "残高")
        tree.heading("Counterpart_Account_Number", text="Counterpart Account Number" if self.lang=="en" else "相手科目コード")
        tree.heading("Counterpart_Account_Name", text="Counterpart Account Name" if self.lang=="en" else "相手科目名")
        tree.heading("Subaccount_Code", text="Subaccount Code" if self.lang=="en" else "補助科目コード")
        tree.heading("Subaccount_Name", text="Subaccount Name" if self.lang=="en" else "補助科目名")
        tree.heading("Department_Code", text="Department Code" if self.lang=="en" else "部門コード")
        tree.heading("Department_Name", text="Department name" if self.lang=="en" else "部門名")
        tree.heading("Counterpart_Subaccount_Code", text="Counterpart Subaccount Code" if self.lang=="en" else "相手補助科目コード")
        tree.heading("Counterpart_Subaccount_Name", text="Counterpart Subaccount Name" if self.lang=="en" else "相手補助科目名")
        tree.heading("Counterpart_Department_Code", text="Counterpart Department Code" if self.lang=="en" else "相手部門コード")
        tree.heading("Counterpart_Department_Name", text="CCounterpart Department Name" if self.lang=="en" else "相手部門名")
        # Treeview を frame に配置
        tree.grid(row=0, column=0, sticky="nsew")
        # 水平スクロールバーの作成と配置
        scrollbar1x = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        scrollbar1x.grid(row=1, column=0, sticky="ew")
        # 垂直スクロールバーの作成と配置
        scrollbar1y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar1y.grid(row=0, column=1, sticky="ns")
        # Treeview にスクロールバーを関連付け
        tree.configure(xscrollcommand=scrollbar1x.set, yscrollcommand=scrollbar1y.set)
        # double click
        tree.bind("<Double-1>", self.view_data)

    def create_frame2(self):
        # Frame 2: 残高試算表表示 Trial Balance
        frame = self.frame2
        self.columns2 = (
            "Month",
            "Account_Number",
            "Account_Name",
            "eTax_Category",
            "Beginning_Balance",
            "Debit_Amount",
            "Credit_Amount",
            "Ending_Balance"
        )
        self.result_tree2 = ttk.Treeview(
            frame,
            columns=self.columns2,
            show="headings",
            height=37
        )
        tree = self.result_tree2
        # width
        tree.column("Month", width=self.width_month, anchor="center")
        tree.column("Account_Number", width=0, anchor="center")
        tree.column("Account_Name", width=self.width_longname, anchor="w", stretch=tk.NO)
        tree.column("eTax_Category", width=self.width_name, anchor="w", stretch=tk.NO)
        tree.column("Beginning_Balance", width=self.width_amount, anchor="e", stretch=tk.NO)
        tree.column("Debit_Amount", width=self.width_amount, anchor="e", stretch=tk.NO)
        tree.column("Credit_Amount", width=self.width_amount, anchor="e", stretch=tk.NO)
        tree.column("Ending_Balance", width=self.width_amount, anchor="e", stretch=tk.NO)
        # text
        tree.heading("Month", text="Month" if self.lang=="en" else "日付")
        tree.heading("Account_Number", text="Account Num." if self.lang=="en" else "勘定科目")
        tree.heading("Account_Name", text="Account Name" if self.lang=="en" else "科目名")
        tree.heading("eTax_Category", text="Account Category" if self.lang=="en" else "勘定科目区分")
        tree.heading("Beginning_Balance", text="Starting Balance" if self.lang=="en" else "開始残高")
        tree.heading("Debit_Amount", text="Debit Amount" if self.lang=="en" else "借方金額")
        tree.heading("Credit_Amount", text="Credit Amount" if self.lang=="en" else "貸方金額")
        tree.heading("Ending_Balance", text="Ending Balance" if self.lang=="en" else "終了残高")
        # Treeview を frame2 に配置
        tree.grid(row=0, column=0, sticky="nsew")
        # 垂直スクロールバーの作成と配置
        scrollbar2y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar2y.grid(row=0, column=1, sticky="ns")
        # Treeview にスクロールバーを関連付け
        tree.configure(yscrollcommand=scrollbar2y.set)

    def create_frame3(self):
        # Frame 3: Balance Sheet (BS) Display
        frame = self.frame3
        self.columns3 = (
            "seq",
            "Level",
            "Ledger_Account_Number",
            "eTax_Account_Name",
            "eTax_Category",
            "Beginning_Balance",
            "Total_Debit",
            "Total_Credit",
            "Ending_Balance"
        )
        self.result_tree3 = ttk.Treeview(
            frame,
            columns=self.columns3,
            show="headings",
            height=37
        )
        tree = self.result_tree3
        # width
        tree.column("seq", width=self.width_dimension, anchor="e", stretch=tk.NO)
        tree.column("Level", width=self.width_dimension, anchor="e", stretch=tk.NO)
        tree.column("Ledger_Account_Number", width=0, anchor="w", stretch=tk.NO)
        tree.column("eTax_Account_Name", width=self.width_text, anchor="w", stretch=tk.NO)
        tree.column("eTax_Category", width=self.width_longname, anchor="w", stretch=tk.NO)
        tree.column("Beginning_Balance", width=self.width_amount, anchor="e", stretch=tk.NO)
        tree.column("Total_Debit", width=self.width_amount, anchor="e", stretch=tk.NO)
        tree.column("Total_Credit", width=self.width_amount, anchor="e", stretch=tk.NO)
        tree.column("Ending_Balance", width=self.width_amount, anchor="e", stretch=tk.NO)
        # text
        tree.heading("seq", text="Seq" if self.lang=="en" else "順序")
        tree.heading("Level", text="Level" if self.lang=="en" else "レベル")
        tree.heading("Ledger_Account_Number", text="Account Number" if self.lang=="en" else "勘定科目番号")
        tree.heading("eTax_Account_Name", text="Account Name" if self.lang=="en" else "勘定科目名")
        tree.heading("eTax_Category", text="Account Category" if self.lang=="en" else "勘定科目区分")
        tree.heading("Beginning_Balance", text="Starting Balance" if self.lang=="en" else "期首残高")
        tree.heading("Beginning_Balance", text="Starting Balance" if self.lang=="en" else "期首残高")
        tree.heading("Total_Debit", text="Debit" if self.lang=="en" else "借方")
        tree.heading("Total_Credit", text="Credit" if self.lang=="en" else "貸方")
        tree.heading("Ending_Balance", text="Ending Balance" if self.lang=="en" else "期末残高")
        # Treeview を frame3 に配置
        tree.grid(row=0, column=0, sticky="nsew")
        # 垂直スクロールバーの作成と配置
        scrollbar3y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar3y.grid(row=0, column=1, sticky="ns")
        # Treeview にスクロールバーを関連付け
        tree.configure(yscrollcommand=scrollbar3y.set)

    def create_frame4(self):
        # Frame 4: Profit and Loss (PL) Display
        frame = self.frame4
        self.columns4 = (
            "seq",
            "Level",
            "Ledger_Account_Number",
            "eTax_Account_Name",
            "eTax_Category",
            # "Beginning_Balance",
            "Total_Debit",
            "Total_Credit",
            "Ending_Balance"
        )
        self.result_tree4 = ttk.Treeview(
            frame,
            columns=self.columns4,
            show="headings",
            height=37
        )
        tree = self.result_tree4
        # width
        tree.column("seq", width=self.width_dimension, anchor="e", stretch=tk.NO)
        tree.column("Level", width=self.width_dimension, anchor="e", stretch=tk.NO)
        tree.column("Ledger_Account_Number", width=0, anchor="w", stretch=tk.NO)
        tree.column("eTax_Account_Name", width=self.width_text, anchor="w", stretch=tk.NO)
        tree.column("eTax_Category", width=self.width_longname, anchor="w", stretch=tk.NO)
        # tree.column("Beginning_Balance", width=self.width_amount, anchor="e", stretch=tk.NO)
        tree.column("Total_Debit", width=self.width_amount, anchor="e", stretch=tk.NO)
        tree.column("Total_Credit", width=self.width_amount, anchor="e", stretch=tk.NO)
        tree.column("Ending_Balance", width=self.width_amount, anchor="e", stretch=tk.NO)
        # text
        tree.heading("seq", text="Seq" if self.lang=="en" else "順序")
        tree.heading("Level", text="Level" if self.lang=="en" else "レベル")
        tree.heading("Ledger_Account_Number", text="Account Number" if self.lang=="en" else "勘定科目番号")
        tree.heading("eTax_Account_Name", text= "勘定科目名" if self.lang=="ja" else "Account Name")
        tree.heading("eTax_Category", text="Account Category" if self.lang=="en" else "勘定科目区分")
        # tree.heading("Beginning_Balance", text="Starting Balance" if self.lang=="en" else "期首残高")
        tree.heading("Total_Debit", text="Debit" if self.lang=="en" else "借方")
        tree.heading("Total_Credit", text="Credit" if self.lang=="en" else "貸方")
        tree.heading("Ending_Balance", text="Amount" if self.lang=="en" else "金額")
        # Treeview を frame4 に配置
        tree.grid(row=0, column=0, sticky="nsew")
        # 垂直スクロールバーの作成と配置
        scrollbar4y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar4y.grid(row=0, column=1, sticky="ns")
        # Treeview にスクロールバーを関連付け
        tree.configure(yscrollcommand=scrollbar4y.set)

    def scroll_to_end(self, event=None):
        self.log_text.see("end")

    def create_gui(self):
        # Combobox
        if self.lang == "en":
            self.show_button_text = "Show"
            self.account_title_text = "Account:"
            self.month_title_text = "Month:"
            self.load_button_text = "Load Parameters"
            self.reset_button_text = "Reset Selection"
            self.menu = ["Journal Entry", "General Ledger", "Trial Balance", "Balance Sheet", "Profit and Loss"]
            self.combobox = ttk.Combobox(
                self.base_frame,
                values=self.menu
            )
            self.combobox.set("Journal Entry")
        else:
            self.show_button_text = "表示"
            self.account_title_text = "科目:"
            self.month_title_text = "対象月:"
            self.load_button_text = "パラメタファイル"
            self.reset_button_text = "選択解除"
            self.menu = ["仕訳帳", "総勘定元帳画面", "試算表画面", "貸借対照表", "損益計算書"]
            self.combobox = ttk.Combobox(
                self.base_frame,
                values=self.menu
            )
            self.combobox.set("仕訳帳")
        self.combobox.grid(row=0, column=0, padx=(8, 4), pady=4, sticky="ew")
        self.combobox.bind("<<ComboboxSelected>>", self.on_combobox_select)
        # Show Button
        self.show_button = tk.Button(
            self.base_frame,
            text=self.show_button_text,
            command=lambda: self.show_results(self.frame_number)
        )
        self.show_button.grid(row=1, column=0, padx=(8, 4), pady=4, sticky="ew")
        # Account
        self.account_title = tk.Label(self.base_frame, text=self.account_title_text)
        self.account_title.grid(row=0, column=1, padx=(4, 4), pady=4, sticky="w")
        self.account_combobox = ttk.Combobox(
            self.base_frame,
            values=[""],
            width=20 # 幅を20文字分に指定
        )
        self.account_combobox.grid(row=0, column=2, padx=(4, 4), pady=4, sticky="ew")
        # Month
        self.month_title = tk.Label(self.base_frame, text=self.month_title_text)
        self.month_title.grid(row=1, column=1, padx=(4, 4), pady=4, sticky="w")
        self.month_combobox = ttk.Combobox(
            self.base_frame,
            values=[""],
            width=20 # 幅を20文字分に指定
        )
        self.month_combobox.grid(row=1, column=2, padx=(4, 4), pady=4, sticky="ew")
        # Load Button
        self.load_button = tk.Button(self.base_frame, text=self.load_button_text, command=lambda: self.load_json())
        self.load_button.grid(row=0, column=4, padx=(4, 4), pady=4, sticky="ew")
        # Reset filter Button
        self.reset_button = tk.Button(self.base_frame, text=self.reset_button_text, command=lambda: self.reset_filters())
        self.reset_button.grid(row=1, column=4, padx=(4, 4), pady=4, sticky="ew")

        # log_text
        self.log_text = tk.Text(
            self.base_frame,
            spacing1=3, spacing2=2, spacing3=3,
            height=4, width=140, wrap='char'
        )
        self.log_text.grid(row=0, column=5, rows=2, padx=(4, 8), pady=4, sticky="nsw")
        self.log_text.bind("<KeyRelease>", self.scroll_to_end)
        self.line = "0.0"
        log_tracker.write_log_text(self.file_path)
        # frameN
        self.base_frame.grid_columnconfigure(5, weight=1, minsize=12)
        for col in range(5):  # 列0から列4まで伸縮可能に設定
            self.base_frame.grid_columnconfigure(col, weight=1)
        self.frame0 = tk.Frame(self.base_frame)
        self.frame1 = tk.Frame(self.base_frame)
        self.frame2 = tk.Frame(self.base_frame)
        self.frame3 = tk.Frame(self.base_frame)
        self.frame4 = tk.Frame(self.base_frame)
        for fr in [self.frame0, self.frame1, self.frame2, self.frame3, self.frame4]:
            fr.grid(row=2, column=0, columnspan=6, sticky="nsew", padx=4, pady=4)
            fr.grid_rowconfigure(0, weight=1)  # TreeViewが縦方向に伸縮
            fr.grid_columnconfigure(0, weight=1)  # TreeViewが横方向に伸縮
        self.create_frame0()
        self.create_frame1()
        self.create_frame2()
        self.create_frame3()
        self.create_frame4()
        self.update_tree_headings()
        # Search Frtame
        search_frame = tk.Frame(self.base_frame)
        search_frame.grid(row=5, column=0, columnspan=6, padx=(4, 4), pady=(4, 4), sticky="nsew")
        # search label
        self.search_label = tk.Label(search_frame, text="摘要文 検索語:")
        self.search_label.pack(side="left")
        # search entry
        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side="left", padx=4)
        # search button
        self.search_button = tk.Button(search_frame, text="検索", command=self.search_keyword)
        self.search_button.pack(side="left", padx=4)
        # reset search
        self.reset_search_button = tk.Button(search_frame, text="検索解除", command=self.reset_search)
        self.reset_search_button.pack(side="left", padx=4)
        # view data
        self.view_button = tk.Button(search_frame, text="データ参照", command=self.view_data)
        self.view_button.pack(side="left", padx=4)
        # toggle code
        self.toggle_column_button = tk.Button(search_frame, text="コード列の表示/非表示", command=self.toggle_column)
        self.toggle_column_button.pack(side="left", padx=4)
        # save csv
        self.save_button = tk.Button(search_frame, text="CSV保存", command=self.save_csv)
        self.save_button.pack(side="left", padx=4)
        # toggle language
        self.toggle_language_button = tk.Button(search_frame, text="日本語/English", command=self.toggle_language)
        self.toggle_language_button.pack(side="left", padx=4)
        # account combobox
        account_dict = tidy_data.get_account_dict()
        accounts = [key.split(" ", 1)[1] for key in account_dict.keys()]
        self.account_combobox["values"] = accounts
        # month combobox
        self.summary_df = tidy_data.get_summary_df()
        months = sorted(self.summary_df["Month"].unique())
        self.month_combobox["values"] = [""] + months
        # show frame0
        self.show_frame(self.frame0, 0)
        self.update_labels()
        # self.debug_grid()
        if "en" == self.lang:
            log_tracker.write_log_text("window created.")
        else:
            log_tracker.write_log_text("ウィンドウ生成")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python script.py <parameters.jsonのパス>")
        sys.exit(1)
    param_file_path = sys.argv[1]
    # グローバル変数としてlog_trackerを定義
    log_tracker = LogTracker()
    # Initialize the GUI
    root = tk.Tk()
    gui = GUI(root)
    gui.create_base()
    # Then process the CSV
    tidy_data = TidyData()
    tidy_data.csv2dataframe(param_file_path)
    # Create the GUI
    gui.create_gui()
    # Main Loop
    root.mainloop()
