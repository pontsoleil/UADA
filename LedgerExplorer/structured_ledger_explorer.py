import pandas as pd
import numpy as np
import csv
import json
from collections import OrderedDict
from datetime import datetime
import sys
import os
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
# import threading

DEBUG = False
TRACE = False

def debug_print(message):
    if DEBUG:
        print(message)


def trace_print(message):
    if TRACE:
        print(message)


class TimeTracker:
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def debug_print(message):
        if DEBUG:
            print(message)

    def trace_print(message):
        if TRACE:
            print(message)

    def start(self):
        self.start_time = datetime.now()

    def stop(self):
        self.end_time = datetime.now()

    def elapsed(self):
        if self.start_time and self.end_time:
            elapsed_time = self.end_time - self.start_time
            total_seconds = elapsed_time.total_seconds()
            minutes = int(total_seconds // 60)
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:.1f}"
        return None


# グローバル変数としてtime_trackerを定義
time_tracker = TimeTracker()


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
        self.account_category_dict = None
        self.beginning_balances = None
        self.amount_rows = None
        self.general_ledger_df = None
        self.summary_df = None
        self.bs_data_df = None
        self.pl_data_df = None
        self.account_dict = None
        self.account_dict2 = None
        self.bs_parent_dict = None
        self.pl_parent_dict = None
        # 勘定科目ごとの貸借の増減方向を持つ辞書を定義
        self.account_direction_dict = {
            "資産": "借方増",
            "負債": "貸方増",
            "費用": "借方増",
            "収益": "貸方増"
        }
        self.lang = "ja"

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

    def get_general_ledger_df(self):
        return self.general_ledger_df

    def get_summary_df(self):
        return self.summary_df

    def get_account_dict(self):
        return self.account_dict

    # 月初日を取得する関数
    def get_month_start(self, date):
        return pd.Timestamp(date.year, date.month, 1)

    def general_ledger(self):
        # 伝票単位で処理を行う
        df_temp = pd.DataFrame(self.amount_rows).copy()
        for transaction_id, group in df_temp.groupby(self.columns["伝票"]):
            # グループ内の先頭行の借方金額と貸方金額、摘要文を取得
            first_row = group.iloc[0]
            transction_date = first_row[self.columns["伝票日付"]]
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

            if first_debit_amount == total_debit_amount:
                self.debug_print(f"借方金額が合計金額 {transction_date} {transaction_id} {first_debit_acct_number} {first_debit_acct_name}: {total_debit_amount}")
            elif first_credit_amount == total_credit_amount:
                self.debug_print(f"貸方金額が合計金額 {transction_date} {transaction_id} {first_credit_acct_number} {first_credit_acct_name}: {total_credit_amount}")

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
                "Ledger_Account_Number",
                "Counterpart_Account_Number",
                "Transaction_Date",
            ]
        ).sort_values(by=["Transaction_Date", "Ledger_Account_Number"])

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
                    balances.append({
                        "Transaction_Date": self.get_month_start(transaction_date).strftime('%Y-%m-%d'),  # 月初日をYYYY-MM-DD形式で設定
                        "Description": "* 月初残高",
                        "Ledger_Account_Number": acc_number,
                        "Ledger_Account_Name": account_name, # account_name_dict[acc_number],
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
                # "Ledger_Account_Name",
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
        # # Add Category and eTax_Category to beginning_balances_df
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
            on=["Ledger_Account_Number","Ledger_Account_Name","Category","eTax_Category"],
            how="outer"  # Use 'outer' to keep all rows from both
        )
        # Replace NaN values in Beginning_Balance with 0
        combined_summary["Beginning_Balance"] = combined_summary["Beginning_Balance"].fillna(0).astype("int64")
        combined_summary["Total_Debit"] = combined_summary["Total_Debit"].fillna(0).astype("int64")
        combined_summary["Total_Credit"] = combined_summary["Total_Credit"].fillna(0).astype("int64")
        #
        # BS
        #
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
                else row["Beginning_Balance"] - row["Total_Debit"] + row["Total_Credit"]
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
            (~self.bs_data_df[["Beginning_Balance", "Ending_Balance"]].isna().all(axis=1))
        ]
        # Ensure these columns are of type int64, setting NaN to 0
        columns_to_convert = ["Beginning_Balance", "Total_Debit", "Total_Credit", "Ending_Balance"]
        for column in columns_to_convert:
            self.bs_data_df[column] = pd.to_numeric(self.bs_data_df[column], errors="coerce").fillna(0).astype("int64")
        # Set Beginning_Balance and Ending_Balance to 0 for rows where Type is "T"
        self.bs_data_df.loc[self.bs_data_df["Type"] == "T", ["Beginning_Balance", "Total_Debit", "Total_Credit", "Ending_Balance"]] = 0
        # BSの親子関係を構築する関数
        def build_bs_parent_child_relationship_with_level(bs_data_df, level_range=(1, 10), exclude_empty_children=True):
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
                    children_list[account] = {"Level": level, "Beginning_Balance": 0, "Ending_Balance": 0, "children": []}
                # 親要素が存在する場合、その子要素として追加
                if level > 1 and level_list[level - 1] is not None:
                    parent = level_list[level - 1]
                    children_list[parent]["children"].append(account)
            # 空の子要素リストを持つ親要素を除外（オプション）
            if exclude_empty_children:
                children_list = {k: v for k, v in children_list.items() if v["children"]}
            return children_list
        # BSの親子関係を構築
        bs_parent_child_hierarchy = build_bs_parent_child_relationship_with_level(self.bs_data_df, level_range=(1, 10), exclude_empty_children=True)
        # BSの結果を表示
        self.bs_parent_dict = {}
        min_level = 10
        max_level = 0
        for parent, details in bs_parent_child_hierarchy.items():
            level = details["Level"]
            children = details["children"]
            for child in children:
                # フィルタリングして Beginning_Balance と Ending_Balance を取得
                result = self.bs_data_df.loc[self.bs_data_df["Ledger_Account_Number"] == child, ["Beginning_Balance", "Ending_Balance"]]
                # 結果を表示
                if not result.empty:
                    beginning_balance, ending_balance = result.iloc[0]
                    if level > max_level:
                        max_level = level
                    if min_level > level:
                        min_level = level
                    self.debug_print(f"level: {level}, Ledger_Account_Number: {child} Parent: {parent}, Beginning_Balance: {beginning_balance} Ending_Balance: {ending_balance}")
                    self.bs_parent_dict[child] = {"Level": level, "Parent": parent, "Beginning_Balance": beginning_balance, "Ending_Balance": ending_balance}
                else:
                    self.trace_print(f"Ledger_Account_Number {child} not found.")
        # max_level から min_level の範囲でループ
        for level in range(max_level, min_level - 1, -1):
            # target_level に該当する要素を抽出
            filtered_dict = {key: value for key, value in self.bs_parent_dict.items() if value["Level"] == level}
            for key, row in filtered_dict.items():
                parent_key = row["Parent"]
                if not parent_key in self.bs_parent_dict:
                    self.bs_parent_dict[parent_key] = {"Level": level-1, "Parent": None, "Beginning_Balance": 0, "Ending_Balance": 0}
                parent = self.bs_parent_dict[row["Parent"]]
                beginning_balance = 0 if pd.isna(row["Beginning_Balance"]) else row["Beginning_Balance"]
                ending_balance = 0 if pd.isna(row["Ending_Balance"]) else row["Ending_Balance"]
                if beginning_balance > 0:
                    parent["Beginning_Balance"] += int(beginning_balance)
                if ending_balance > 0:
                    parent["Ending_Balance"] += int(ending_balance)
        # Filter bs_parent_dict to remove entries with Beginning_Balance and Ending_Balance both 0
        self.bs_parent_dict = {
            key: value
            for key, value in self.bs_parent_dict.items()
            if not (value["Beginning_Balance"] == 0 and value["Ending_Balance"] == 0)
        }
        # Add eTax_Category and eTax_Account_Name based on self.etax_code_mapping_dict
        for key, value in self.bs_parent_dict.items():
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
        sorted_bs_parent_dict = dict(
            sorted(self.bs_parent_dict.items(), key=lambda item: item[1].get("seq", 0))
        )
        # Replace the original dictionary with the sorted one
        self.bs_parent_dict = sorted_bs_parent_dict
        #
        # PL
        #
        # Paths for input and output PL files
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
            ["Ledger_Account_Number", "Ledger_Account_Name", "Category", "Total_Debit", "Total_Credit"]
        ]
        # Merge the sheet Ledger_Account_Number with the income_statement_df to get balances
        self.pl_data_df = pd.merge(
            self.pl_template_df,
            income_statement_df[["Ledger_Account_Number", "Total_Debit", "Total_Credit"]],
            on="Ledger_Account_Number",
            how="left"
        )
        # Keep rows where `type` is "T" or both balances are not NaN
        self.pl_data_df = self.pl_data_df[
            (self.pl_data_df["Type"] == "T") |
            (~self.pl_data_df[["Total_Debit", "Total_Credit"]].isna().all(axis=1))
        ]
        # Ensure these columns are of type int64, setting NaN to 0
        columns_to_convert = ["Total_Debit", "Total_Credit"]
        for column in columns_to_convert:
            self.pl_data_df[column] = pd.to_numeric(self.pl_data_df[column], errors="coerce").fillna(0).astype("int64")
        # Set Beginning_Balance and Ending_Balance to 0 for rows where Type is "T"
        self.pl_data_df.loc[self.pl_data_df["Type"] == "T", ["Total_Debit", "Total_Credit"]] = 0
        # PLの親子関係を構築する関数
        codes_to_check = [self.params["account"]["電子取引売上高"], self.params["account"]["電子取引以外売上高"]]
        # codes_to_check = ["10D100101", "10D100102"]
        # DataFrameに含まれているか確認
        missing_codes = [code for code in codes_to_check if code not in self.pl_data_df["Ledger_Account_Number"].values]
        # 結果を表示
        if missing_codes:
            self.debug_print(f"以下のコードはself.pl_data_dfに存在しません: {missing_codes}")
        else:
            self.debug_print(f"self.pl_data_dfには、{codes_to_check} が全て存在します。")

        def build_pl_parent_child_relationship_with_level(pl_data_df, level_range=(1, 10), exclude_empty_children=True):
            # 初期化: 各レベルの最新の要素を保持（レベル範囲を指定）
            level_list = {lvl: None for lvl in range(level_range[0], level_range[1] + 1)}
            children_list = {}  # 親要素とその子要素を保持する辞書
            for _, row in pl_data_df.iterrows():
                level = row["Level"]
                account = row["Ledger_Account_Number"]
                # 現在のレベルに対応する要素を更新
                level_list[level] = account
                # 子要素リストを初期化（もし未登録なら）
                if account not in children_list:
                    children_list[account] = {"Level": level, "Total_Debit": 0, "Total_Credit": 0, "children": []}
                # 親要素が存在する場合、その子要素として追加
                if level > 1 and level_list[level - 1] is not None:
                    parent = level_list[level - 1]
                    children_list[parent]["children"].append(account)
            # 空の子要素リストを持つ親要素を除外（オプション）
            if exclude_empty_children:
                children_list = {k: v for k, v in children_list.items() if v["children"]}
            return children_list

        # PLの親子関係を構築
        pl_parent_child_hierarchy = build_pl_parent_child_relationship_with_level(self.pl_data_df, level_range=(1, 10), exclude_empty_children=True)
        # PLの結果を表示
        self.pl_parent_dict = {}
        min_level = 10
        max_level = 0
        for parent, details in pl_parent_child_hierarchy.items():
            level = details["Level"]
            children = details["children"]
            for child in children:
                # フィルタリングして Total_Debit と Total_Credit を取得
                result = self.pl_data_df.loc[self.pl_data_df["Ledger_Account_Number"] == child, ["Total_Debit", "Total_Credit"]]
                # 結果を表示
                if not result.empty:
                    total_debit, total_credit = result.iloc[0]
                    if level > max_level:
                        max_level = level
                    if min_level > level:
                        min_level = level
                    self.debug_print(f"level: {level}, Ledger_Account_Number: {child} Parent: {parent}, Total_Debit: {total_debit} Total_Credit: {total_credit}")
                    self.pl_parent_dict[child] = {"Level": level, "Parent": parent, "Total_Debit": total_debit, "Total_Credit": total_credit}
                else:
                    self.trace_print(f"Ledger_Account_Number {child} not found.")
        # max_level から min_level の範囲でループ
        for level in range(max_level, min_level - 1, -1):
            # target_level に該当する要素を抽出
            filtered_dict = {key: value for key, value in self.pl_parent_dict.items() if value["Level"] == level}
            for key, row in filtered_dict.items():
                parent_key = row['Parent']
                if not parent_key in self.pl_parent_dict:
                    self.pl_parent_dict[parent_key] = {"Level": level-1, "Parent": None, "Total_Debit": 0, "Total_Credit": 0}
                parent = self.pl_parent_dict[row['Parent']]
                total_debit = 0 if pd.isna(row["Total_Debit"]) else row["Total_Debit"]
                total_credit = 0 if pd.isna(row["Total_Credit"]) else row["Total_Credit"]
                if total_debit > 0:
                    parent["Total_Debit"] += int(total_debit)
                if total_credit > 0:
                    parent["Total_Credit"] += int(total_credit)

        # Filter pl_parent_dict to remove entries with Total_Debit and Total_Credit both 0
        self.pl_parent_dict = {
            key: value
            for key, value in self.pl_parent_dict.items()
            if not (value["Total_Debit"] == 0 and value["Total_Credit"] == 0)
        }
        # Add eTax_Category and eTax_Account_Name based on self.etax_code_mapping_dict
        for key, value in self.pl_parent_dict.items():
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
        sorted_pl_parent_dict = dict(
            sorted(self.pl_parent_dict.items(), key=lambda item: item[1].get("seq", 0))
        )
        # Replace the original dictionary with the sorted one
        self.pl_parent_dict = sorted_pl_parent_dict

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
        # 辞書形式で取得
        first_row_dict = pd.read_csv(self.file_path, nrows=1).iloc[0].to_dict()
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

        # 新しいデータフレームを CSV に保存（必要に応じて）
        self.etax_file_path = f"{self.file_path[:-4]}_etax.csv"
        self.tidy_gl_df.to_csv(self.etax_file_path, index=False, encoding="utf-8-sig")

        # beginning_balance_pathを読み込む
        beginning_balance_df = pd.read_csv(self.beginning_balance_path, dtype={"Account_Code": str, "eTax_Account_Code": str})

        # エラーログを初期化
        errors = []

        # Account_Codeをマッピングして置き換え
        # Account_Code, Account_Name, Beginning_Balance
        def process_balance(row):
            account_code = row["Account_Code"]
            if pd.isna(account_code):
                return row
            else:
                self.debug_print(f'{account_code}')
                # 科目コードと名称の変換
                row["Account_Code"] = self.map_account_code(account_code, errors)
                row["Account_Name"] = self.map_account_name(account_code, errors)
                return row

        # データフレーム全体に行単位で関数を適用
        beginning_balance_df = beginning_balance_df.apply(process_balance, axis=1)

        # 勘定科目の開始残高を辞書に変換
        beginning_balance_df["Account_Code"] = beginning_balance_df["Account_Code"].astype(str)
        # beginning_balance_dfに複数のAccount_Codeが存在する場合、それぞれのAccount_CodeごとにBeginning_Balanceを合計し、beginning_balancesを作成する
        beginning_balances = beginning_balance_df.groupby("Account_Code")['Beginning_Balance'].sum().to_dict()
        self.beginning_balances = beginning_balances

        # エラーログの表示
        if errors:
            self.trace_print("以下のエラーが発生しました：")
            for error in errors:
                self.trace_print(error)

    def csv2dataframe(self, param_file_path):
        # 開始、終了、経過時間ラベルを追加
        time_tracker.start()

        with open(param_file_path, "r", encoding="utf-8-sig") as param_file:
            params = json.load(param_file)

        self.params = params
        self.DEBUG = 1 == params["DEBUG"]
        self.TRACE = 1 == params["TRACE"]
        self.file_path = params["file_path"]
        self.beginning_balance_path = params["beginning_balance_path"]
        self.account_path = params["account_path"]
        self.tax_category_path = params["tax_category_path"]
        self.trading_partner_path = params["trading_partner_path"]
        self.LHM_path = params["LHM_path"]
        self.BS_path = params["HOT010_3.0_BS_10"]
        self.PL_path = params["HOT010_3.0_PL_10"]
        self.columns  = params["columns"]

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

        df = pd.read_csv(self.etax_file_path, encoding="utf-8-sig", dtype=str) # read tidy data csv
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
            self.columns["借方補助科目"],
            self.columns["貸方補助科目"],
            self.columns["借方部門"],
            self.columns["貸方部門"],
            self.columns["伝票日付"],
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
            [self.columns["伝票"], self.columns["伝票日付"], "Month"]
        ].drop_duplicates()

        # マージ前に列名を明確にするために列名を変更する
        entry_df = entry_df.rename(
            columns={
                self.columns["伝票日付"]: f"{self.columns['伝票日付']}_value",
                "Month": "Month_value",
            }
        )

        # 対象の金額の値をメインのDataFrameにマージする
        line_df = pd.merge(df, initial_rows, on=[self.columns["伝票"], self.columns["明細行"]], how="left")

        # JP04a_GL02_03（伝票日付）の値をメインのDataFrameにマージする
        line_df = pd.merge(line_df, entry_df, on=self.columns["伝票"], how="left")

        # 正しいJP04a_GL02_03（伝票日付）の値でメインのDataFrameを更新する
        line_df[self.columns["伝票日付"]] = line_df[f"{self.columns['伝票日付']}_value"].combine_first(line_df[self.columns["伝票日付"]])
        line_df["Month"] = line_df["Month_value"].combine_first(line_df["Month"])

        # マージに使用した一時的な列を削除する
        line_df.drop(columns=[f"{self.columns['伝票日付']}_value", "Month_value"], inplace=True)

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

        # 貸方科目コードが self.params["account"]["売上高"] "10D100100"の場合にのみ、貸方補助科目の条件を適用（貸方補助科目が存在する場合のみ）
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
        # codes_to_check = ["10D100101", "10D100102"]
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
        self.general_ledger()
        self.fill_account_dict()
        self.trial_balance_carried_forward()
        self.bs_pl()

        for column in self.amount_rows:
            if pd.api.types.is_numeric_dtype(self.amount_rows[column]):
                self.amount_rows[column].fillna(0, inplace=True)
            else:
                self.amount_rows[column].fillna("", inplace=True)

        time_tracker.stop()


tidy_data = TidyData()


class GUI:
    def __init__(self, root):
        self.root = root
        self.previous_selection = None
        self.processing_thread = None  # スレッドを追跡するための変数
        self.is_processing = False  # 処理中かどうかを示すフラグ
        self.progress_window = None  # 進捗ウィンドウを追跡するための変数
        self.original_data = []  # TreeViewの元のデータを保持するリスト
        self.params = None
        self.columns = None
        self.amount_df = None
        self.general_ledger_df = None
        self.summary_df = None
        self.time_label = None
        self.elapsed_time_label = None
        self.month_title = None
        self.month_combobox = None
        self.account_title = None
        self.account_combobox = None
        self.combobox = None
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
        self.result_tree1_data = None
        self.column_visible = False
        self.width_account = 80
        self.width_subaccount = 40
        self.lang = "ja"  # 初期言語を日本語に設定

    def debug_print(self, message):
        if self.DEBUG:
            print(message)

    def trace_print(self, message):
        if self.TRACE:
            print(message)

    def show_progress_window(self):
        if self.progress_window is None:
            self.progress_window = tk.Toplevel(self.root)
            self.progress_window.title("Processing")
            if self.lang == "ja":
                tk.Label(self.progress_window, text="処理中です。お待ちください...").pack(padx=20, pady=20)
            else:
                tk.Label(self.progress_window, text="Processing, please wait until the process is finished.").pack(padx=20, pady=20)
            # self.progress_window.protocol("WM_DELETE_WINDOW", self.on_close_progress_window)

    def on_close_progress_window(self):
        if not self.is_processing:
            self.progress_window.destroy()
            self.progress_window = None

    def close_progress_window(self):
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None

    def toggle_language(self):
        if self.lang == "ja":
            self.lang = "en"
            tidy_data.lang = "en"
        else:
            self.lang = "ja"
            tidy_data.lang = "ja"
        self.update_labels()

    def update_labels(self):
        # Update labels based on the selected language
        if self.lang == "ja":
            self.show_button.config(text="表示")
            self.account_title.config(text="科目:")
            self.month_title.config(text="対象月:")
            self.load_button.config(text="パラメタファイル")
            self.reset_button.config(text="選択解除")
            self.time_label.config(text="開始時刻:  終了時刻:  経過時間: ")
            self.combobox["values"] = ["仕訳帳", "総勘定元帳画面", "試算表画面", "貸借対照表", "損益計算書"]
            if self.combobox.get() == "Journal":
                self.combobox.set("仕訳帳")
            elif self.combobox.get() == "General Ledger":
                self.combobox.set("総勘定元帳画面")
            elif self.combobox.get() == "Trial Balance":
                self.combobox.set("試算表画面")
            elif self.combobox.get() == "Balance Sheet":
                self.combobox.set("貸借対照表")
            elif self.combobox.get() == "Profit and Loss":
                self.combobox.set("損益計算書")
            self.file_path_label.config(text=tidy_data.get_file_path())
            self.search_label.config(text="摘要文 検索語:")
            self.search_button.config(text="検索")
            self.reset_search_button.config(text="検索解除")
            self.view_button.config(text="データ参照")
            self.toggle_column_button.config(text="コード列の表示/非表示")
            self.save_button.config(text="CSV保存")
            self.toggle_language_button.config(text="日本語/English")
        else:
            self.show_button.config(text="Show")
            self.account_title.config(text="Account:")
            self.month_title.config(text="Month:")
            self.load_button.config(text="Load Parameters")
            self.reset_button.config(text="Reset Selection")
            self.time_label.config(text="Start Time:  End Time:  Elapsed Time: ")
            self.combobox["values"] = ["Journal", "General Ledger", "Trial Balance", "Balance Sheet", "Profit and Loss"]
            if self.combobox.get() == "仕訳帳":
                self.combobox.set("Journal")
            elif self.combobox.get() == "総勘定元帳画面":
                self.combobox.set("General Ledger")
            elif self.combobox.get() == "試算表画面":
                self.combobox.set("Trial Balance")
            elif self.combobox.get() == "貸借対照表":
                self.combobox.set("Balance Sheet")
            elif self.combobox.get() == "損益計算書":
                self.combobox.set("Profit and Loss")
            self.file_path_label.config(text=tidy_data.get_file_path())
            self.search_label.config(text="Description Search Term:")
            self.search_button.config(text="Search")
            self.reset_search_button.config(text="Reset Search")
            self.view_button.config(text="View Data")
            self.toggle_column_button.config(text="Toggle Code Columns")
            self.save_button.config(text="Save CSV")
            self.toggle_language_button.config(text="日本語/English")

        self.update_tree_headings()
        self.update_time_labels()

    def update_tree_headings(self):
        if 0 == self.frame_number:
            if self.lang == "ja":
                headings = {
                    "Journal": "伝票",
                    "DetailRow": "行",
                    "Month": "",
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
            else:
                headings = {
                    "Journal": "Journal",
                    "DetailRow": "Row",
                    "Month": "Month",
                    "TransactionDate": "Transaction Date",
                    "Description": "Description",
                    "DebitAccountCode": "Code",
                    "DebitAccountName": "Debit Account",
                    "Debit_Amount": "Debit Amount",
                    "DebitTaxCode": "Code",
                    "DebitTaxName": "Debit Tax Type",
                    "DebitTaxAmount": "Debit Tax Amount",
                    "DebitSubaccountCode": "Code",
                    "DebitSubaccountName": "Debit Subaccount",
                    "DebitDepartmentCode": "Code",
                    "DebitDepartmentName": "Debit Department",
                    "CreditAccountCode": "Code",
                    "CreditAccountName": "Credit Account",
                    "Credit_Amount": "Credit Amount",
                    "CreditTaxCode": "Code",
                    "CreditTaxName": "Credit Tax Type",
                    "CreditTaxAmount": "Credit Tax Amount",
                    "CreditSubaccountCode": "Code",
                    "CreditSubaccountName": "Credit Subaccount",
                    "CreditDepartmentCode": "Code",
                    "CreditDepartmentName": "Credit Department",
                }
            for col, text in headings.items():
                self.result_tree0.heading(col, text=text)
        elif 1 == self.frame_number:
            if self.lang == "ja":
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
            else:
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
            for col, text in headings.items():
                self.result_tree1.heading(col, text=text)
        elif 2 == self.frame_number:
            if self.lang == "ja":
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
            else:
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
            for col, text in headings.items():
                self.result_tree2.heading(col, text=text)
        elif 3 == self.frame_number:
            if self.lang == "ja":
                headings = {
                    "seq": "順序",
                    "Account_Number": "勘定科目番号",
                    "Level": "レベル",
                    "eTax_Category": "勘定科目区分",
                    "eTax_Account_Name": "勘定科目名",
                    "Beginning_Balance": "期初残高",
                    "Ending_Balance": "期末残高",
                }
            else:
                headings = {
                    "seq": "Seq",
                    "Account_Number":"Account Number",
                    "Level": "Level",
                    "eTax_Category": "Account Category",
                    "eTax_Account_Name":"Account Name",
                    "Beginning_Balance":"Starting Balance",
                    "Ending_Balance":"Ending Balance",
                }
            for col, text in headings.items():
                self.result_tree3.heading(col, text=text)
        elif 4 == self.frame_number:
            if self.lang == "ja":
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
                headings = {
                    "seq": "SEq",
                    "Account_Number":"Account Number",
                    "Level": "Level",
                    "eTax_Category": "Account Category",
                    "eTax_Account_Name":"Account Name",
                    "Debit_Amount":"Debit Amount",
                    "Credit_Amount":"Credit Amount",
                }
            for col, text in headings.items():
                self.result_tree4.heading(col, text=text)

    def update_time_labels(self):
        elapsed = time_tracker.elapsed()
        if time_tracker.start_time and time_tracker.end_time:
            if self.lang == "ja":
                self.time_label.config(text=f"開始時刻: {time_tracker.start_time.strftime('%H:%M:%S')} 終了時刻: {time_tracker.end_time.strftime('%H:%M:%S')} 経過時間: {elapsed}")
            else:
                self.time_label.config(text=f"Start Time: {time_tracker.start_time.strftime('%H:%M:%S')} End Time: {time_tracker.end_time.strftime('%H:%M:%S')} Elapsed Time: {elapsed}")

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

    def map_tax_category_name(self, code, errors):
        if not code:
            return code
        tax_category_mapping_dict = [
            details
            for details in tidy_data.tax_category_mapping_dict.values()
            if details.get('Tax_Category_Code') == code
        ]
        if len(tax_category_mapping_dict) == 0:
            return code
        if "en" == self.lang:
            return tax_category_mapping_dict[0]["Tax_Category_Name_en"]
        else:
            return tax_category_mapping_dict[0]["Tax_Category_Name_ja"]

    def format_row(self, row, frame_number):
        bs_dict = tidy_data.bs_template_df.set_index('Ledger_Account_Number').to_dict(orient="index")
        pl_dict = tidy_data.pl_template_df.set_index('Ledger_Account_Number').to_dict(orient="index")
        debit_account_name = None
        debit_account_number = row[self.columns["借方科目コード"]]
        if debit_account_number in bs_dict:
            if "ja" == self.lang:
                debit_account_name = bs_dict[debit_account_number]["Account_Name"]
            elif "en" == self.lang:
                debit_account_name = bs_dict[debit_account_number]["English_Label"]
        elif debit_account_number in pl_dict:
            if "ja" == self.lang:
                debit_account_name = pl_dict[debit_account_number]["Account_Name"]
            elif "en" == self.lang:
                debit_account_name = pl_dict[debit_account_number]["English_Label"]
        if debit_account_name:
            row[self.columns["借方科目名"]] = debit_account_name
        debit_account_name = None
        credit_account_number = row[self.columns["貸方科目コード"]]
        if credit_account_number in bs_dict:            
            if "ja" == self.lang:
                debit_account_name = bs_dict[credit_account_number]["Account_Name"]
            elif "en" == self.lang:
                debit_account_name = bs_dict[credit_account_number]["English_Label"]
        elif credit_account_number in pl_dict:
            if "ja" == self.lang:
                debit_account_name = pl_dict[credit_account_number]["Account_Name"]
            elif "en" == self.lang:
                debit_account_name = pl_dict[credit_account_number]["English_Label"]
        if debit_account_name:
            row[self.columns["貸方科目名"]] = debit_account_name
        errors = []
        debit_tax_name = credit_tax_name = None
        debit_tax_code = row[self.columns["借方税区分コード"]]
        if debit_tax_code:
            debit_tax_name = self.map_tax_category_name(debit_tax_code, errors)
        credit_tax_code = row[self.columns["貸方税区分コード"]]
        if credit_tax_code:
            credit_tax_name = self.map_tax_category_name(credit_tax_code, errors)
        if debit_tax_name:
            row[self.columns["借方税区分名"]] = debit_tax_name
        if credit_tax_name:
            row[self.columns["貸方税区分名"]] = credit_tax_name

        if 0 == frame_number: # Journal
            formatted_row = (
                row[self.columns["伝票"]],
                row[self.columns["明細行"]],
                row["Month"],
                row[self.columns["伝票日付"]],
                row[self.columns["摘要文"]],
                # 借方
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
                row[self.columns["借方補助科目コード"]],
                row[self.columns["借方補助科目名"]],
                row[self.columns["借方部門コード"]],
                row[self.columns["借方部門名"]],
                # 貸方
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
                row[self.columns["貸方補助科目コード"]],
                row[self.columns["貸方補助科目名"]],
                row[self.columns["貸方部門コード"]],
                row[self.columns["貸方部門名"]],
            )
        elif 1 == frame_number: # General Ledger
            formatted_row = (
                row["Transaction_Date"],  # オリジナルの日付列を使用
                row["Description"],
                row["Ledger_Account_Number"],
                row["Ledger_Account_Name"],
                row["Subaccount_Code"],
                row["Subaccount_Name"],
                row["Department_Code"],
                row["Department_Name"],
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
                row["Counterpart_Account_Number"],
                row["Counterpart_Account_Name"],
                row["Counterpart_Subaccount_Code"],
                row["Counterpart_Subaccount_Name"],
                row["Counterpart_Department_Code"],
            )
        elif 2 == frame_number: # Trial Balance
            formatted_row = (
                row["Month"],
                row["Ledger_Account_Number"],
                row["eTax_Category"],
                row["Ledger_Account_Name"],
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
                row["Ledger_Account_Number"],
                row["Level"],
                row["eTax_Category"],
                row["eTax_Account_Name"],
                f"{row['Beginning_Balance']:,.0f}" if row["Beginning_Balance"] else "",
                f"{row['Ending_Balance']:,.0f}" if row["Ending_Balance"] else "",
            )
        elif 4 == frame_number:  # Profit and Loss
            formatted_row = (
                row["seq"],
                row["Ledger_Account_Number"],
                row["Level"],
                row["eTax_Category"],
                row["eTax_Account_Name"],
                f"{row['Total_Debit']:,.0f}" if row["Total_Debit"] else "",
                f"{row['Total_Credit']:,.0f}" if row["Total_Credit"] else "",
            )
        return formatted_row

    def insert_data(self, filtered_df, result_tree, frame_number):
        self.original_data = filtered_df.values.tolist()  # 元のデータを保存
        try:
            # DataFrameのデータをTreeviewに挿入
            for index, row in filtered_df.iterrows():
                result_tree.insert("", "end", values=self.format_row(row, frame_number))
            if index % 100 == 0:
                result_tree.update_idletasks()  # Update the GUI to keep it responsive
        finally:
            self.is_processing = False  # 処理が終わったらフラグをリセット
            self.progress_window.destroy()  # 処理終了時に進捗ウィンドウを閉じる

    def show_results(self, frame_number, event=None):
        if self.is_processing:  # 処理中であれば新しいスレッドを開始しない
            if self.lang == "ja":
                messagebox.showwarning("警告", "処理が終了するまでお待ちください。")
            else:
                messagebox.showwarning("Warning", "Please wait until the process is finished.")
            return
        self.is_processing = True  # 処理を開始する前にフラグをセット
        # 進捗メッセージウィンドウを作成
        self.show_progress_window()
        # self.progress_window = tk.Toplevel()
        # if self.lang == "ja":
        #     tk.Label(self.progress_window, text="処理中です。お待ちください...").pack(padx=20, pady=20)
        # else:
        #     tk.Label(self.progress_window, text="Processing, please wait until the process is finished.").pack(padx=20, pady=20)
        self.columns = tidy_data.get_columns()
        if 0 == frame_number:
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
                if self.lang == "ja":
                    messagebox.showwarning("警告", "データが見つかりません。")
                else:
                    messagebox.showwarning("Warning", "No data found.")
                return
        elif 1 == frame_number:
            selected_account = self.account_combobox.get()
            selected_month = self.month_combobox.get()
            account_dict = self.account_dict = tidy_data.get_account_dict()
            self.general_ledger_df = tidy_data.get_general_ledger_df().copy()
            # Transaction_Date列をdatetime型に変換して別の列に保存
            self.general_ledger_df['Transaction_Date_dt'] = pd.to_datetime(self.general_ledger_df['Transaction_Date'])
            # Transaction_Date列をYYYY-MM形式に変換して別の列に保存
            self.general_ledger_df['Transaction_Month'] = self.general_ledger_df['Transaction_Date_dt'].dt.to_period('M').astype(str)
            result_tree = self.result_tree1
            if selected_month:
                filtered_df = self.general_ledger_df[self.general_ledger_df['Transaction_Month'] == selected_month].copy()
            else:
                filtered_df = self.general_ledger_df.copy()
            if selected_account:
                account_number = account_dict.get(selected_account)
                if account_number:
                    filtered_df = filtered_df[filtered_df["Ledger_Account_Number"] == account_number]
            else:
                if self.lang == "ja":
                    messagebox.showwarning("警告", "科目名を選択してください。")
                else:
                    messagebox.showwarning("Warning", "Please select an account name.")
                return
            if filtered_df.empty:
                if self.lang == "ja":
                    messagebox.showwarning("警告", "データが見つかりません。")
                else:
                    messagebox.showwarning("Warning", "No data found.")
                return
        elif 2 == frame_number:
            selected_month = self.month_combobox.get()
            if not selected_month:
                if self.lang == "ja":
                    messagebox.showwarning("警告", "対象月を選択してください。")
                else:
                    messagebox.showwarning("Warning", "Please select a target month.")
                return
            target_month = pd.Period(selected_month)
            self.summary_df = tidy_data.get_summary_df().copy()
            filtered_df = self.summary_df[self.summary_df['Month'] == str(target_month)]
            result_tree = self.result_tree2
        elif frame_number == 3:  # Balance Sheet (BS)
            result_tree = self.result_tree3
            # Convert dictionary to DataFrame
            filtered_df = pd.DataFrame.from_dict(tidy_data.bs_parent_dict, orient='index').reset_index()
            # Rename the index column to `Ledger_Account_Number`
            filtered_df.rename(columns={'index': "Ledger_Account_Number"}, inplace=True)
        elif frame_number == 4:  # Profit and Loss (PL)
            result_tree = self.result_tree4
            # Convert dictionary to DataFrame
            filtered_df = pd.DataFrame.from_dict(tidy_data.pl_parent_dict, orient='index').reset_index()
            # Rename the index column to `Ledger_Account_Number`
            filtered_df.rename(columns={'index': "Ledger_Account_Number"}, inplace=True)
        # Treeviewの行削除
        for i in result_tree.get_children():
            result_tree.delete(i)
        
        self.insert_data(filtered_df, result_tree, frame_number)
        # # スレッドを開始してデータを挿入 注：これは遅い
        # self.processing_thread = threading.Thread(target=self.insert_data, args=(filtered_df, result_tree, frame_number))
        # self.processing_thread.start()
        self.is_processing = False
        self.close_progress_window()

    def reset_filters(self, event=None):
        self.account_combobox.set('')
        self.month_combobox.set('')

    def show_frame(self, frame, frame_number):
        self.frame_number = frame_number
        self.is_processing = False
        frame.tkraise()
        if 0 == frame_number: # Journal
            self.hide_account()
            self.show_month()
        elif 1 == frame_number: # General Ledger
            self.show_account()
            self.show_month()
        elif 2 == frame_number: # Trial Balance
            self.hide_account()
            self.show_month()
        elif 3 == frame_number: # Balance Sheet
            self.hide_account()
            self.hide_month()
        elif 4 == frame_number: # Profit and Loss
            self.hide_account()
            self.hide_month()

    def show_account(self):
        self.account_title.grid(row=0, column=2, sticky=tk.E, padx=(5, 5), pady=5)
        self.account_combobox.grid(row=0, column=3, sticky=tk.W, padx=(5, 5), pady=5)

    def hide_account(self):
        self.account_title.grid_forget()
        self.account_combobox.grid_forget()

    def show_month(self):
        self.month_title.grid(row=1, column=2, sticky=tk.E, padx=(5, 5), pady=5)
        self.month_combobox.grid(row=1, column=3, sticky=tk.W, padx=(5, 5), pady=5)

    def hide_month(self):
        self.month_title.grid_forget()
        self.month_combobox.grid_forget()

    def format_searched_row(self, row, frame_number):
        if 0 == frame_number:
            formatted_row = (
                row[0], # 伝票
                row[1], # 明細行
                row[2], # Month
                row[3], # 伝票日付
                row[4], # 摘要文
                # 借方
                row[5], # 借方科目コード
                row[6], # 借方科目名
                (#'Debit_Amount'
                    f"{row[7]:,.0f}" if pd.notna(row[5]) and pd.notna(row[7]) and row[7] != 0 and isinstance(row[7], (int, float)) else ""
                ),
                row[8], # 借方税区分コード
                row[9], # 借方税区分名
                row[10], # 借方消費税額
                row[11], # 借方補助科目コード
                row[12], # 借方補助科目名
                row[13], # 借方部門コード
                row[14], # 借方部門名
                # 貸方
                row[15], # 貸方科目コード
                row[16], # 貸方科目名
                (# 'Credit_Amount'
                    f"{row[17]:,.0f}" if pd.notna(row[15]) and pd.notna(row[17]) and row[17] != 0 and isinstance(row[17], (int, float)) else ""
                ),
                row[18], # 貸方税区分コード
                row[19], # 貸方税区分名
                row[20], # 貸方消費税額
                row[21], # 貸方補助科目コード
                row[22], # 貸方補助科目名
                row[23], # 貸方部門コード
                row[24], # 貸方部門名
            )
        elif 1 == frame_number:
            formatted_row = (
                row[0], # Transaction_Date  # オリジナルの日付列を使用
                row[1], # Description
                row[2], # Ledger_Account_Number
                row[3], # Ledger_Account_Name
                row[4], # Subaccount_Code
                row[5], # Subaccount_Name
                row[6], # Department_Code
                row[7], # Department_Name
                ( # 'Debit_Amount'
                    f"{row[8]:,.0f}" if pd.notna(row[8]) and row[8] != 0 and isinstance(row[8], (int, float)) else ""
                ),
                ( # 'Credit_Amount'
                    f"{row[9]:,.0f}" if pd.notna(row[9]) and row[9] != 0 and isinstance(row[9], (int, float)) else ""
                ),
                ( # 'Balance'
                    f"{row[10]:,.0f}" if pd.notna(row[10]) and row[10] != 0 and isinstance(row[10], (int, float)) else ""
                ),
                row[11], # Counterpart_Account_Number
                row[12], # Counterpart_Account_Name
                row[13], # Counterpart_Subaccount_Code
                row[14], # Counterpart_Subaccount_Name
                row[15], # Counterpart_Department_Code
            )
        elif 2 == frame_number:
            formatted_row = (
                row[0], # Month
                row[1], # Ledger_Account_Number
                row[2], # Ledger_Account_Name
                ( # 'Debit_Amount'
                    f"{row[3]:,.0f}" if pd.notna(row[3]) and row[3] != 0 and isinstance(row[3], (int, float)) else ""
                ),
                ( # 'Credit_Amount'
                    f"{row[4]:,.0f}" if pd.notna(row[4]) and row[4] != 0 and isinstance(row[4], (int, float)) else ""
                ),
                ( # 'Beginning_Balance'
                    f"{row[5]:,.0f}" if pd.notna(row[5]) and row[5] != 0 and isinstance(row[5], (int, float)) else ""
                ),
                ( # 'Ending_Balance'
                    f"{float(row[10]):,.0f}" if pd.notna(row[10]) and row[10] != 0 and isinstance(row[10], (int, float)) else ""
                )
            )
        return formatted_row

    def search_keyword(self):
        self.is_processing = True
        # self.show_progress_window()
        columns = self.columns
        search_term = self.search_entry.get().lower()
        frame_number = self.frame_number
        if 0 == frame_number:
            result_tree = self.result_tree0
            # 4 '制服代' 摘要文
            # 6 '福利厚生費' 借方科目
            # 14 '札幌営業所' 借方部門
            # 16 '未払金' 貸方科目
            # 24 '共通部門' 貸方部門
            filtered_data = []
            for row in self.original_data:
                if (
                    (
                        pd.notna(row[4]) and search_term in row[4].lower()
                    )
                    or (
                        pd.notna(row[6]) and search_term in row[6].lower()
                    )
                    or (
                        pd.notna(row[14]) and search_term in row[14].lower()
                    )
                    or (
                        pd.notna(row[16]) and search_term in row[16].lower()
                    )
                    or (
                        pd.notna(row[24]) and search_term in row[24].lower()
                    )

                ):
                    filtered_data.append(row)
        elif 1 == frame_number:
            result_tree = self.result_tree1
            # 1 '制服代' 摘要文
            # 3 '未払金' 科目
            # 7 '共通部門' 部門
            # 11 '福利厚生費' 相手科目
            # 15 '札幌営業所' 相手部門
            filtered_data = []
            for row in self.original_data:
                if (
                    (
                        pd.notna(row[1]) and search_term in row[1].lower()
                    )
                    or (
                        pd.notna(row[3]) and search_term in row[3].lower()
                    )
                    or (
                        pd.notna(row[7]) and search_term in row[7].lower()
                    )
                    or (
                        pd.notna(row[11]) and not isinstance(row[11],int) and search_term in row[11].lower()
                    )
                    or (
                        pd.notna(row[15]) and not isinstance(row[15],int) and search_term in row[15].lower()
                    )
                ):
                    filtered_data.append(row)
        else:
            return

        for i in result_tree.get_children():
            result_tree.delete(i)

        for row in filtered_data:
            result_tree.insert("", "end", values=self.format_searched_row(row, frame_number))

        self.is_processing = False
        # self.close_progress_window()

    def reset_search(self):
        frame_number = self.frame_number
        self.is_processing = False
        if 0 == frame_number:
            result_tree = self.result_tree0
        elif 1 == frame_number:
            result_tree = self.result_tree1
        else:
            return
        for i in result_tree.get_children():
            result_tree.delete(i)
        for row in self.original_data:
            result_tree.insert("", "end", values=row)

    def view_data(self, event=None):
        frame_number = self.frame_number
        self.debug_print(f"frame number: {frame_number}")
        # Get the selected item
        if 0 == frame_number:
            item = self.result_tree0.selection()[0]
            row_data = self.result_tree0.item(item, "values")
            description = row_data[4]  # Assuming "Description" is the 5th column
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
            if self.lang == "ja":
                messagebox.showwarning("警告", "該当するPDFが見つかりませんでした。")
            else:
                messagebox.showwarning("Warning", "No corresponding PDF found.")

    def toggle_column(self):
        frame_number = self.frame_number
        # コード列の表示/非表示を切り替える
        self.column_visible = not self.column_visible
        if self.lang == "ja":
            label = 'コード'
        else:
            label = 'Code'
        if self.column_visible:
            if 0 == frame_number:
                self.result_tree0.column("DebitAccountCode", width=self.width_account, anchor="center", stretch=tk.NO)
                self.result_tree0.column("DebitTaxCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                self.result_tree0.column("DebitSubaccountCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                self.result_tree0.column("DebitDepartmentCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                self.result_tree0.column("CreditAccountCode", width=self.width_account, anchor="center", stretch=tk.NO)
                self.result_tree0.column("CreditTaxCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                self.result_tree0.column("CreditSubaccountCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                self.result_tree0.column("CreditDepartmentCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
            elif 1 == frame_number:
                self.result_tree1.column("Ledger_Account_Number", width=self.width_account, anchor="center", stretch=tk.NO)
                self.result_tree1.column("Subaccount_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                self.result_tree1.column("Department_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                self.result_tree1.column("Counterpart_Account_Number", width=self.width_account, anchor="center", stretch=tk.NO)
                self.result_tree1.column("Counterpart_Subaccount_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
                self.result_tree1.column("Counterpart_Department_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
            elif 2 == frame_number:
                self.result_tree1.column("Account_Number", width=self.width_account, stretch=tk.NO)
        else:
            if 0 == frame_number:
                self.result_tree0.column("DebitAccountCode", width=0, stretch=tk.NO)
                self.result_tree0.column("DebitTaxCode", width=0, stretch=tk.NO)
                self.result_tree0.column("DebitSubaccountCode", width=0, stretch=tk.NO)
                self.result_tree0.column("DebitDepartmentCode", width=0, stretch=tk.NO)
                self.result_tree0.column("CreditAccountCode", width=0, stretch=tk.NO)
                self.result_tree0.column("CreditTaxCode", width=0, stretch=tk.NO)
                self.result_tree0.column("CreditSubaccountCode", width=0, stretch=tk.NO)
                self.result_tree0.column("CreditDepartmentCode", width=0, stretch=tk.NO)
            elif 1 == frame_number:
                self.result_tree1.column("Ledger_Account_Number", width=0, stretch=tk.NO)
                self.result_tree1.column("Subaccount_Code", width=0, stretch=tk.NO)
                self.result_tree1.column("Department_Code", width=0, stretch=tk.NO)
                self.result_tree1.column("Counterpart_Account_Number", width=0, stretch=tk.NO)
                self.result_tree1.column("Counterpart_Subaccount_Code", width=0, stretch=tk.NO)
                self.result_tree1.column("Counterpart_Department_Code", width=0, stretch=tk.NO)
            elif 2 == frame_number:
                self.result_tree1.column("Account_Number", width=0, stretch=tk.NO)

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
                self.save_dict2csv(output_BS_path, tidy_data.bs_parent_dict)
                input_PL_path = tidy_data.PL_path[1+tidy_data.PL_path.index('/'):]  # PL Template CSV
                output_PL_path = os.path.join(directory, input_PL_path)
                self.save_dict2csv(output_PL_path, tidy_data.pl_parent_dict)
                if self.lang == "ja":
                    messagebox.showinfo("成功", f"DataFrameをCSVファイルとして {amount_path}, {general_ledger_path}, {summary_path}, {output_BS_path}, {output_PL_path} に保存しました。")
                else:
                    messagebox.showinfo("Success", f"DataFrames have been saved as CSV files to {amount_path}, {general_ledger_path}, {summary_path}, {output_BS_path}, {output_PL_path}.")
            except Exception as e:
                if self.lang == "ja":
                    messagebox.showerror("エラー", f"保存に失敗しました: {str(e)}")
                else:
                    messagebox.showerror("Error", f"Failed to save: {str(e)}")

    def on_combobox_select(self, event=None):
        self.is_processing = False
        selected_option = self.combobox.get()
        if self.lang == "ja":
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
        else:
            if selected_option == "Journal":
                self.show_frame(self.frame0, 0)
            elif selected_option == "General Ledger":
                self.show_frame(self.frame1, 1)
            elif selected_option == "Trial Balance":
                self.show_frame(self.frame2, 2)
            elif selected_option == "Balance Sheet":
                self.show_frame(self.frame3, 3)
            elif selected_option == "Profit and Loss":
                self.show_frame(self.frame4, 4)

    def create_gui(self):
        root = self.root
        self.previous_selection = None
        if self.lang == "ja":
            root.title("会計帳簿表示")
        else:
            root.title("Accounting Book Display")

        base_frame = tk.Frame(root)
        base_frame.pack(side="top", fill="x")

        # Comboboxの作成
        if self.lang == "ja":
            self.combobox = ttk.Combobox(base_frame, values=["仕訳帳", "総勘定元帳画面", "試算表画面", "貸借対照表", "損益計算書"])
            self.combobox.set("仕訳帳")
            self.show_button_text = "表示"
            self.account_title_text = "科目:"
            self.month_title_text = "対象月:"
            self.load_button_text = "パラメタファイル"
            self.reset_button_text = "選択解除"
            self.time_label_text = "開始時刻:  終了時刻:  経過時間: "
        else:
            self.combobox = ttk.Combobox(base_frame, values=["Journal", "General Ledger", "Trial Balance", "Balance Sheet", "Profit and Loss"])
            self.combobox.set("Journal")
            self.show_button_text = "Show"
            self.account_title_text = "Account:"
            self.month_title_text = "Month:"
            self.load_button_text = "Load Parameters"
            self.reset_button_text = "Reset Selection"
            self.time_label_text = "Start Time:  End Time:  Elapsed Time: "

        self.combobox.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="ew")
        # Comboboxの選択イベントをバインド
        self.combobox.bind("<<ComboboxSelected>>", self.on_combobox_select)

        self.show_button = tk.Button(base_frame, text=self.show_button_text, command=lambda: self.show_results(self.frame_number))
        self.show_button.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="ew")

        self.account_title = tk.Label(base_frame, text=self.account_title_text)
        self.account_title.grid(row=0, column=1, padx=(5, 5), pady=5, sticky="w")
        self.account_combobox = ttk.Combobox(base_frame)
        self.account_combobox.grid(row=0, column=2, padx=(5, 5), pady=5, sticky="ew")

        self.month_title = tk.Label(base_frame, text=self.month_title_text)
        self.month_title.grid(row=1, column=1, padx=(5, 5), pady=5, sticky="w")
        self.month_combobox = ttk.Combobox(base_frame)
        self.month_combobox.grid(row=1, column=2, padx=(5, 5), pady=5, sticky="ew")

        self.load_button = tk.Button(base_frame, text=self.load_button_text, command=lambda: self.load_json()) #, relief="raised", borderwidth=3)
        self.load_button.grid(row=0, column=4, padx=(5, 5), pady=5, sticky="ew")

        self.reset_button = tk.Button(base_frame, text=self.reset_button_text, command=lambda: self.reset_filters())
        self.reset_button.grid(row=1, column=4, padx=(5, 5), pady=5, sticky="ew")

        self.time_label = tk.Label(base_frame, text=self.time_label_text)
        self.time_label.grid(row=0, column=5, padx=(5, 15), pady=5, sticky="e")

        self.file_path_label = tk.Label(base_frame, text=tidy_data.get_file_path())
        self.file_path_label.grid(row=1, column=5, padx=(5, 15), pady=5, sticky="e")

        # カラム幅の設定
        base_frame.grid_columnconfigure(5, weight=1, minsize=30)

        self.frame0 = tk.Frame(base_frame)
        self.frame1 = tk.Frame(base_frame)
        self.frame2 = tk.Frame(base_frame)
        self.frame3 = tk.Frame(base_frame)
        self.frame4 = tk.Frame(base_frame)
        # Configure the frame to center the Treeview
        for fr in [self.frame0, self.frame1, self.frame2, self.frame3, self.frame4]:
            fr.grid_rowconfigure(0, weight=1)  # Add space above/below
            fr.grid_columnconfigure(0, weight=1)  # Add space left/right

        # Frame 0: 仕訳帳表示
        self.result_tree0 = ttk.Treeview(
            self.frame0,
            columns=(
                "Journal",
                "DetailRow",
                "Month",
                "TransactionDate",
                "Description",
                "DebitAccountCode",
                "DebitAccountName",
                "Debit_Amount",
                "DebitTaxCode",
                "DebitTaxName",
                "DebitTaxAmount",
                "DebitSubaccountCode",
                "DebitSubaccountName",
                "DebitDepartmentCode",
                "DebitDepartmentName",
                "CreditAccountCode",
                "CreditAccountName",
                "Credit_Amount",
                "CreditTaxCode",
                "CreditTaxName",
                "CreditTaxAmount",
                "CreditSubaccountCode",
                "CreditSubaccountName",
                "CreditDepartmentCode",
                "CreditDepartmentName",
            ),
            show="headings",
            height=40,
        )
        self.update_tree_headings()
        self.result_tree0.grid(row=2, column=0, columnspan=6, sticky="nsew")

        self.result_tree0.column("Journal", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        self.result_tree0.column("DetailRow", width=30, anchor="center", stretch=tk.NO)
        self.result_tree0.column("Month", width=80, anchor="center", stretch=tk.NO)
        self.result_tree0.column("TransactionDate", width=80, anchor="center", stretch=tk.NO)
        self.result_tree0.column("Description", width=250, anchor="w")
        self.result_tree0.column("DebitAccountCode", width=self.width_account, anchor="center", stretch=tk.NO)
        self.result_tree0.column("DebitAccountName", width=120, anchor="w")
        self.result_tree0.column("Debit_Amount", width=80, anchor="e")
        self.result_tree0.column("DebitTaxCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        self.result_tree0.column("DebitTaxName", width=80, anchor="w")
        self.result_tree0.column("DebitTaxAmount", width=80, anchor="e")
        self.result_tree0.column("DebitSubaccountCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        self.result_tree0.column("DebitSubaccountName", width=100, anchor="w")
        self.result_tree0.column("DebitDepartmentCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        self.result_tree0.column("DebitDepartmentName", width=80, anchor="w")
        self.result_tree0.column("CreditAccountCode", width=self.width_account, anchor="center", stretch=tk.NO)
        self.result_tree0.column("CreditAccountName", width=120, anchor="w")
        self.result_tree0.column("Credit_Amount", width=80, anchor="e")
        self.result_tree0.column("CreditTaxCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        self.result_tree0.column("CreditTaxName", width=80, anchor="w")
        self.result_tree0.column("CreditTaxAmount", width=80, anchor="e")
        self.result_tree0.column("CreditSubaccountCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        self.result_tree0.column("CreditSubaccountName", width=100, anchor="w")
        self.result_tree0.column("CreditDepartmentCode", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        self.result_tree0.column("CreditDepartmentName", width=80, anchor="w")

        self.result_tree0.heading("Journal", text="仕訳" if self.lang=="ja" else "Journal")
        self.result_tree0.heading("DetailRow", text="明細行" if self.lang=="ja" else "Detail Row")
        self.result_tree0.heading("Month", text="月" if self.lang=="ja" else "Month")
        self.result_tree0.heading("TransactionDate", text="日付" if self.lang=="ja" else "Date")
        self.result_tree0.heading("Description", text="摘要" if self.lang=="ja" else "Description")
        self.result_tree0.heading("DebitAccountCode", text="借方科目コード" if self.lang=="ja" else "Debit Account Code")
        self.result_tree0.heading("DebitAccountName", text="借方科目名" if self.lang=="ja" else "Debit Account Name")
        self.result_tree0.heading("Debit_Amount", text="借方金額" if self.lang=="ja" else "Debit Amount")
        self.result_tree0.heading("DebitTaxCode", text="借方税コード" if self.lang=="ja" else "Debit Tax Code")
        self.result_tree0.heading("DebitTaxName", text="借方税" if self.lang=="ja" else "Debit Tax Name")
        self.result_tree0.heading("DebitTaxAmount", text="借方税額" if self.lang=="ja" else "Debit Tax Amount")
        self.result_tree0.heading("DebitSubaccountCode", text="借方補助科目コード" if self.lang=="ja" else "Debit Subaccount Code")
        self.result_tree0.heading("DebitSubaccountName", text="借方補助科目名" if self.lang=="ja" else "Debit Subaccount Name")
        self.result_tree0.heading("DebitDepartmentCode", text="借方部門コード" if self.lang=="ja" else "Debit Department Code")
        self.result_tree0.heading("DebitDepartmentName", text="借方部門名" if self.lang=="ja" else "Debit epartment Name")
        self.result_tree0.heading("CreditAccountCode", text="貸方科目コード" if self.lang=="ja" else "Credit Account")
        self.result_tree0.heading("CreditAccountName", text="貸方科目名" if self.lang=="ja" else "")
        self.result_tree0.heading("Credit_Amount", text="貸方金額" if self.lang=="ja" else "Credit Amount")
        self.result_tree0.heading("CreditTaxCode", text="貸方税コード" if self.lang=="ja" else "Credit Tax Code")
        self.result_tree0.heading("CreditTaxName", text="貸方税" if self.lang=="ja" else "Credit Tax Name")
        self.result_tree0.heading("CreditTaxAmount", text="貸方税額" if self.lang=="ja" else "Credit Tax Amount")
        self.result_tree0.heading("CreditSubaccountCode", text="貸方補助科目コード" if self.lang=="ja" else "Credit Subaccount Code")
        self.result_tree0.heading("CreditSubaccountName", text="貸方補助科目名" if self.lang=="ja" else "Credit Subaccount Name")
        self.result_tree0.heading("CreditDepartmentCode", text="貸方部門コード" if self.lang=="ja" else "Credit Department Code")
        self.result_tree0.heading("CreditDepartmentName", text="貸方部門名" if self.lang=="ja" else "Credit Department Name")

        scrollbar0 = ttk.Scrollbar(self.frame0, orient=tk.VERTICAL, command=self.result_tree0.yview)
        self.result_tree0.configure(yscroll=scrollbar0.set)
        scrollbar0.grid(row=2, column=6, sticky="ns")

        self.result_tree0.bind("<Double-1>", self.view_data)
        # 注： Threadにしないとダブルクリックが検出できないが、Threadだと応答が遅くなるので、データ参照ボタンを追加した。

        # Frame 1: 総勘定元帳表示
        self.result_tree1 = ttk.Treeview(
            self.frame1,
            columns=(
                "Transaction_Date",
                "Description",
                "Ledger_Account_Number",
                "Ledger_Account_Name",
                "Subaccount_Code",
                "Subaccount_Name",
                "Department_Code",
                "Department_Name",
                "Debit_Amount",
                "Credit_Amount",
                "Balance",
                "Counterpart_Account_Number",
                "Counterpart_Account_Name",
                "Counterpart_Subaccount_Code",
                "Counterpart_Subaccount_Name",
                "Counterpart_Department_Code",
                "Counterpart_Department_Name",
            ),
            show="headings",
            height=self.width_subaccount,
        )
        self.update_tree_headings()
        self.result_tree1.grid(row=2, column=0, columnspan=6, sticky="nsew")

        self.result_tree1.column("Transaction_Date", width=80, anchor="center", stretch=tk.NO)
        self.result_tree1.column("Ledger_Account_Number", width=self.width_account, anchor="center", stretch=tk.NO)
        self.result_tree1.column("Ledger_Account_Name", width=120, anchor="w")
        self.result_tree1.column("Subaccount_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        self.result_tree1.column("Subaccount_Name", width=100, anchor="w")
        self.result_tree1.column("Department_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        self.result_tree1.column("Department_Name", width=100, anchor="w")
        self.result_tree1.column("Debit_Amount", width=80, anchor="e")
        self.result_tree1.column("Credit_Amount", width=80, anchor="e")
        self.result_tree1.column("Balance", width=80, anchor="e")
        self.result_tree1.column("Counterpart_Account_Number", width=self.width_account, anchor="center", stretch=tk.NO)
        self.result_tree1.column("Counterpart_Account_Name", width=120, anchor="w")
        self.result_tree1.column("Counterpart_Subaccount_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        self.result_tree1.column("Counterpart_Subaccount_Name", width=100, anchor="w")
        self.result_tree1.column("Counterpart_Department_Code", width=self.width_subaccount, anchor="center", stretch=tk.NO)
        self.result_tree1.column("Counterpart_Department_Name", width=100, anchor="w")
        self.result_tree1.column("Description", width=300, anchor="w")

        self.result_tree1.heading("Transaction_Date", text="日付" if self.lang=="ja" else "Date")
        self.result_tree1.heading("Ledger_Account_Number", text="勘定科目コード" if self.lang=="ja" else "Ledger Account Number")
        self.result_tree1.heading("Ledger_Account_Name", text="勘定科目名" if self.lang=="ja" else "Ledger Account Name")
        self.result_tree1.heading("Subaccount_Code", text="補助科目コード" if self.lang=="ja" else "Subaccount Code")
        self.result_tree1.heading("Subaccount_Name", text="補助科目名" if self.lang=="ja" else "Subaccount Name")
        self.result_tree1.heading("Department_Code", text="部門コード" if self.lang=="ja" else "Department Code")
        self.result_tree1.heading("Department_Name", text="部門名" if self.lang=="ja" else "Department name")
        self.result_tree1.heading("Debit_Amount", text="借方金額" if self.lang=="ja" else "Debit Amount")
        self.result_tree1.heading("Credit_Amount", text="貸方金額" if self.lang=="ja" else "Credit Amount")
        self.result_tree1.heading("Balance", text="残高" if self.lang=="ja" else "Balance")
        self.result_tree1.heading("Counterpart_Account_Number", text="相手科目コード" if self.lang=="ja" else "Counterpart Account Number")
        self.result_tree1.heading("Counterpart_Account_Name", text="相手科目名" if self.lang=="ja" else "Counter Account")
        self.result_tree1.heading("Counterpart_Subaccount_Code", text="相手補助科目コード" if self.lang=="ja" else "Counterpart Subaccount Code")
        self.result_tree1.heading("Counterpart_Subaccount_Name", text="相手補助科目名" if self.lang=="ja" else "Counterpart Subaccount Name")
        self.result_tree1.heading("Counterpart_Department_Code", text="相手部門コード" if self.lang=="ja" else "Counterpart Department Code")
        self.result_tree1.heading("Counterpart_Department_Name", text="相手部門名" if self.lang=="ja" else "CCounterpart Department Name")
        self.result_tree1.heading("Description", text="摘要" if self.lang=="ja" else "Description")

        self.frame1.grid_columnconfigure(1, weight=1)
        self.frame1.grid_rowconfigure(1, weight=1)

        scrollbar1 = ttk.Scrollbar(self.frame1, orient=tk.VERTICAL, command=self.result_tree1.yview)
        self.result_tree1.configure(yscroll=scrollbar1.set)
        scrollbar1.grid(row=2, column=6, sticky="ns")

        self.result_tree1.bind("<Double-1>", self.view_data)

        # Frame 2: 残高試算表表示
        self.result_tree2 = ttk.Treeview(
            self.frame2,
            columns=(
                "Month",
                "Account_Number",
                "eTax_Category",
                "Account_Name",
                "Beginning_Balance",
                "Debit_Amount",
                "Credit_Amount",
                "Ending_Balance",
            ),
            show="headings",
            height=40,
        )
        self.update_tree_headings()
        self.result_tree2.grid(row=2, column=0, columnspan=6, sticky="nsew")

        self.result_tree2.column("Month", width=80, anchor="center")
        self.result_tree2.column("Account_Number", width=self.width_account, anchor="center")
        self.result_tree2.column("eTax_Category", width=100, anchor="w")
        self.result_tree2.column("Account_Name", width=120, anchor="w")
        self.result_tree2.column("Beginning_Balance", width=80, anchor="e")
        self.result_tree2.column("Debit_Amount", width=80, anchor="e")
        self.result_tree2.column("Credit_Amount", width=80, anchor="e")
        self.result_tree2.column("Ending_Balance", width=80, anchor="e")

        self.result_tree2.heading("Month", text="日付" if self.lang=="ja" else "Month")
        self.result_tree2.heading("Account_Number", text="勘定科目" if self.lang=="ja" else "Account Num.")
        self.result_tree2.heading("eTax_Category", text="勘定科目区分" if self.lang=="ja" else "Account Category")
        self.result_tree2.heading("Account_Name", text="科目名" if self.lang=="ja" else "Account Name")
        self.result_tree2.heading("Beginning_Balance", text="開始残高" if self.lang=="ja" else "Starting Balance")
        self.result_tree2.heading("Debit_Amount", text="借方金額" if self.lang=="ja" else "Debit Amount")
        self.result_tree2.heading("Credit_Amount", text="貸方金額" if self.lang=="ja" else "Credit Amount")
        self.result_tree2.heading("Ending_Balance", text="終了残高" if self.lang=="ja" else "Ending Balance")

        self.frame2.grid_columnconfigure(1, weight=1)
        self.frame2.grid_rowconfigure(1, weight=1)

        scrollbar2 = ttk.Scrollbar(self.frame2, orient=tk.VERTICAL, command=self.result_tree2.yview)
        self.result_tree2.configure(yscroll=scrollbar2.set)
        scrollbar2.grid(row=2, column=6, sticky="ns")

        # Frame 3: Balance Sheet (BS) Display
        self.result_tree3 = ttk.Treeview(
            self.frame3,
            columns=("seq", "Ledger_Account_Number", "Level", "eTax_Category", "eTax_Account_Name", "Beginning_Balance", "Ending_Balance"),
            show="headings",
            height=40,
        )
        self.update_tree_headings()
        self.result_tree3.grid(row=2, column=0, columnspan=6, sticky="nsew")

        self.result_tree3.column("seq", width=20, anchor="w")
        self.result_tree3.column("Ledger_Account_Number", width=100, anchor="w")
        self.result_tree3.column("Level", width=self.width_subaccount, anchor="center")
        self.result_tree3.column("eTax_Category", width=200, anchor="w")
        self.result_tree3.column("eTax_Account_Name", width=700, anchor="w")
        self.result_tree3.column("Beginning_Balance", width=100, anchor="e")
        self.result_tree3.column("Ending_Balance", width=100, anchor="e")

        self.result_tree3.heading("seq", text="順序" if self.lang=="ja" else "Seq")
        self.result_tree3.heading("Ledger_Account_Number", text="勘定科目番号" if self.lang=="ja" else "Account Number")
        self.result_tree3.heading("Level", text="レベル" if self.lang=="ja" else "Level")
        self.result_tree3.heading("eTax_Category", text="勘定科目区分" if self.lang=="ja" else "Account Category")
        self.result_tree3.heading("eTax_Account_Name", text="勘定科目名" if self.lang=="ja" else "Account Name")
        self.result_tree3.heading("Beginning_Balance", text="期首残高" if self.lang=="ja" else "Starting Balance")
        self.result_tree3.heading("Ending_Balance", text="期末残高" if self.lang=="ja" else "Ending Balance")

        scrollbar3 = ttk.Scrollbar(self.frame3, orient=tk.VERTICAL, command=self.result_tree3.yview)
        self.result_tree3.configure(yscroll=scrollbar3.set)
        scrollbar3.grid(row=2, column=6, sticky="ns")

        # Frame 4: Profit and Loss (PL) Display
        self.result_tree4 = ttk.Treeview(
            self.frame4,
            columns=("seq", "Ledger_Account_Number", "Level", "eTax_Category", "eTax_Account_Name", "Total_Debit", "Total_Credit"),
            show="headings",
            height=40,
        )
        self.update_tree_headings()
        self.result_tree4.grid(row=2, column=0, columnspan=6, sticky="nsew")

        self.result_tree4.column("seq", width=20, anchor="w")
        self.result_tree4.column("Ledger_Account_Number", width=100, anchor="w")
        self.result_tree4.column("Level", width=50, anchor="center")
        self.result_tree4.column("eTax_Category", width=200, anchor="w")
        self.result_tree4.column("eTax_Account_Name", width=700, anchor="w")
        self.result_tree4.column("Total_Debit", width=100, anchor="e")
        self.result_tree4.column("Total_Credit", width=100, anchor="e")

        self.result_tree4.heading("seq", text="順序" if self.lang=="ja" else "Seq")
        self.result_tree4.heading("Ledger_Account_Number", text="勘定科目番号" if self.lang=="ja" else "Account Number")
        self.result_tree4.heading("Level", text="レベル" if self.lang=="ja" else "Level")
        self.result_tree4.heading("eTax_Category", text="勘定科目区分" if self.lang=="ja" else "Account Category")
        self.result_tree4.heading("eTax_Account_Name", text= "勘定科目名" if self.lang=="ja" else "Account Name")
        self.result_tree4.heading("Total_Debit", text="借方金額" if self.lang=="ja" else "Debit Amount")
        self.result_tree4.heading("Total_Credit", text="貸方金額" if self.lang=="ja" else "Credit Amount")

        scrollbar4 = ttk.Scrollbar(self.frame4, orient=tk.VERTICAL, command=self.result_tree4.yview)
        self.result_tree4.configure(yscroll=scrollbar4.set)
        scrollbar4.grid(row=2, column=6, sticky="ns")

        # Add frames to base_frame
        for frame in (self.frame0, self.frame1, self.frame2, self.frame3, self.frame4):
            frame.grid(row=2, column=0, columnspan=6, padx=(10, 10), pady=(10, 10), sticky="nsew")

        # Add search functionality
        search_frame = tk.Frame(root)
        search_frame.pack(side="top", fill="x", padx=10, pady=10)

        self.search_label = tk.Label(search_frame, text="摘要文 検索語:")
        self.search_label.pack(side="left")

        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side="left", padx=5)

        self.search_button = tk.Button(search_frame, text="検索", command=self.search_keyword)
        self.search_button.pack(side="left", padx=5)

        self.reset_search_button = tk.Button(search_frame, text="検索解除", command=self.reset_search)
        self.reset_search_button.pack(side="left", padx=5)

        self.view_button = tk.Button(search_frame, text="データ参照", command=self.view_data)
        self.view_button.pack(side="left", padx=5)

        # 列の表示/非表示を切り替えるボタンを追加
        self.toggle_column_button = tk.Button(search_frame, text="コード列の表示/非表示", command=self.toggle_column)
        self.toggle_column_button.pack(side="left", padx=5)

        self.save_button = tk.Button(search_frame, text="CSV保存", command=self.save_csv)
        self.save_button.pack(side="left", padx=5)

        self.toggle_language_button = tk.Button(search_frame, text="日本語/English", command=self.toggle_language)
        self.toggle_language_button.pack(side="left", padx=5)

        account_dict = tidy_data.get_account_dict()
        accounts = list(account_dict.keys())
        self.account_combobox["values"] = accounts

        self.summary_df = tidy_data.get_summary_df()
        months = sorted(self.summary_df["Month"].unique())
        self.month_combobox["values"] = months

        self.show_frame(self.frame0, 0)  # 最初に表示する frame を指定
        self.update_time_labels()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python script.py <parameters.jsonのパス>")
        sys.exit(1)
    param_file_path = sys.argv[1]

    # Then process the CSV
    tidy_data.csv2dataframe(param_file_path)

    # Initialize the GUI
    root = tk.Tk()
    gui = GUI(root)
    gui.create_gui()

    root.mainloop()
