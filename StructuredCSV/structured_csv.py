#!/usr/bin/env python3
# coding: utf-8
"""
UADA (Universal Audit Data Adapter): structured_csv.py

This script reads multiple CSV files exported from a relational database (RDB)
— including invoice headers, buyers, sellers, tax breakdowns, and line items —
and converts them into a single hierarchically structured CSV file.

構造化された1枚または複数の請求書を tidy data フォーマットで出力します。
日本の中小企業共通EDIやXBRL GL対応にも応用可能です。

designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)

Creation Date: 2025-05-30
Last Modified: 2025-06-02

MIT License

(c) 2025 SAMBUICHI Nobuyuki (Sambuichi Professional Engineers Office)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import pandas as pd
import os
import argparse

def main(base_dir, invoice_id=None, single_csv_path=None, all_csv_path=None):
    # 出力ファイル名のデフォルト設定（指定がなければ標準のファイル名を使用）
    if single_csv_path is None:
        single_csv_path = os.path.join(base_dir, "structured_invoice_export0.csv")
    if all_csv_path is None:
        all_csv_path = os.path.join(base_dir, "structured_invoice_export1.csv")

    # --- CSV 読み込み ---
    # 各種マスタファイルと取引データを読み込む
    invoice_df = pd.read_csv(os.path.join(base_dir, "Invoice.csv"), dtype=str)
    buyer_df = pd.read_csv(os.path.join(base_dir, "Buyer.csv"), dtype=str)
    seller_df = pd.read_csv(os.path.join(base_dir, "Seller.csv"), dtype=str)
    tax_df = pd.read_csv(os.path.join(base_dir, "TaxBreakdown.csv"), dtype=str)
    line_df = pd.read_csv(os.path.join(base_dir, "InvoiceLine.csv"), dtype=str)
    item_df = pd.read_csv(os.path.join(base_dir, "Item.csv"), dtype=str)

    # --- カラム定義 ---
    # 出力CSVの列順と構造を定義する
    columns = [
        "dInvoice", "dTaxBreakdown", "dInvoiceLine",
        "Invoice.ID", "issueDate", "typeCode", "dueDate",
        "Buyer.name", "Seller.name", "Seller.taxID",
        "sumOfLineNetAmount", "totalAmountWithoutTax", "totalTaxAmount", "totalAmountWithTax",
        "TaxBreakdown.taxCategoryCode", "TaxBreakdown.taxCategoryRate", "TaxBreakdown.taxCategoryTaxAmount",
        "InvoiceLine.ID", "InvoiceLine.netAmount", "InvoiceLine.quantity", "InvoiceLine.uom",
        "Item.ID", "Item.name", "Item.price", "Item.baseQuantity", "Item.uom",
        "Item.taxCategoryCode", "Item.taxCategoryRate"
    ]

    # --- 単一請求書の出力処理 ---
    def export_single_invoice(inv_id):
        rows = []
        # 対象の請求書レコードを抽出
        i = invoice_df[invoice_df["ID"] == inv_id]
        if i.empty:
            raise ValueError(f"Invoice {inv_id} not found.")
        i = i.iloc[0]
        # BuyerおよびSeller情報を取得
        b = buyer_df[buyer_df["ID"] == i["buyerID"]].iloc[0]
        s = seller_df[seller_df["ID"] == i["sellerID"]].iloc[0]

        # 請求書ヘッダ行を追加
        rows.append({
            "dInvoice": 1, "dTaxBreakdown": pd.NA, "dInvoiceLine": pd.NA,
            "Invoice.ID": i["ID"], "issueDate": i.get("issueDate", ""), "typeCode": i.get("typeCode", ""),
            "dueDate": i.get("dueDate", ""), "Buyer.name": b.get("name", ""), "Seller.name": s.get("name", ""),
            "Seller.taxID": s.get("taxID", ""), "sumOfLineNetAmount": i.get("sumOfLineNetAmount", ""),
            "totalAmountWithoutTax": i.get("totalAmountWithoutTax", ""), "totalTaxAmount": i.get("totalTaxAmount", ""),
            "totalAmountWithTax": i.get("totalAmountWithTax", ""),
            **{k: "" for k in columns[14:]}
        })

        # 税情報の出力（ユニークなカテゴリごとに並べ替えて順番を振る）
        tb = tax_df[tax_df["invoiceID"] == inv_id].copy()
        tb["key"] = tb["taxCategoryCode"].fillna('') + "|" + tb["taxCategoryRate"].fillna('')
        tb["dTaxBreakdown"] = tb["key"].factorize()[0] + 1

        for _, t in tb.iterrows():
            row = {k: "" for k in columns}
            row.update({
                "dInvoice": 1,
                "dTaxBreakdown": t["dTaxBreakdown"],
                "TaxBreakdown.taxCategoryCode": t.get("taxCategoryCode", ""),
                "TaxBreakdown.taxCategoryRate": t.get("taxCategoryRate", ""),
                "TaxBreakdown.taxCategoryTaxAmount": t.get("taxCategoryTaxAmount", "")
            })
            rows.append(row)

        # 明細行情報の出力
        il = line_df[line_df["invoiceID"] == inv_id].copy()
        il["dInvoiceLine"] = il["ID"].factorize()[0] + 1

        for _, l in il.iterrows():
            item = item_df[item_df["ID"] == l["itemID"]].iloc[0]
            row = {k: "" for k in columns}
            row.update({
                "dInvoice": 1,
                "dInvoiceLine": l["dInvoiceLine"],
                "InvoiceLine.ID": l.get("ID", ""),
                "InvoiceLine.netAmount": l.get("netAmount", ""),
                "InvoiceLine.quantity": l.get("quantity", ""),
                "InvoiceLine.uom": l.get("uom", ""),
                "Item.ID": item.get("ID", ""), "Item.name": item.get("name", ""),
                "Item.price": item.get("price", ""), "Item.baseQuantity": item.get("baseQuantity", ""),
                "Item.uom": item.get("uom", ""), "Item.taxCategoryCode": item.get("taxCategoryCode", ""),
                "Item.taxCategoryRate": item.get("taxCategoryRate", "")
            })
            rows.append(row)

        return pd.DataFrame(rows, columns=columns)

    # --- 全請求書の出力処理 ---
    def export_all_invoices():
        rows = []
        invoice_df_sorted = invoice_df.sort_values("ID").copy()
        invoice_df_sorted["dInvoice"] = range(1, len(invoice_df_sorted) + 1)

        for _, i in invoice_df_sorted.iterrows():
            d_inv = i["dInvoice"]
            b = buyer_df[buyer_df["ID"] == i["buyerID"]].iloc[0]
            s = seller_df[seller_df["ID"] == i["sellerID"]].iloc[0]

            # 請求書ヘッダ行
            rows.append({
                "dInvoice": d_inv, "dTaxBreakdown": pd.NA, "dInvoiceLine": pd.NA,
                "Invoice.ID": i["ID"], "issueDate": i.get("issueDate", ""), "typeCode": i.get("typeCode", ""),
                "dueDate": i.get("dueDate", ""), "Buyer.name": b.get("name", ""), "Seller.name": s.get("name", ""),
                "Seller.taxID": s.get("taxID", ""), "sumOfLineNetAmount": i.get("sumOfLineNetAmount", ""),
                "totalAmountWithoutTax": i.get("totalAmountWithoutTax", ""), "totalTaxAmount": i.get("totalTaxAmount", ""),
                "totalAmountWithTax": i.get("totalAmountWithTax", ""),
                **{k: "" for k in columns[14:]}
            })

            # 税ブレークダウン行
            tb = tax_df[tax_df["invoiceID"] == i["ID"]].copy()
            tb["key"] = tb["taxCategoryCode"].fillna('') + "|" + tb["taxCategoryRate"].fillna('')
            tb["dTaxBreakdown"] = tb["key"].factorize()[0] + 1

            for _, t in tb.iterrows():
                row = {k: "" for k in columns}
                row.update({
                    "dInvoice": d_inv,
                    "dTaxBreakdown": t["dTaxBreakdown"],
                    "TaxBreakdown.taxCategoryCode": t.get("taxCategoryCode", ""),
                    "TaxBreakdown.taxCategoryRate": t.get("taxCategoryRate", ""),
                    "TaxBreakdown.taxCategoryTaxAmount": t.get("taxCategoryTaxAmount", "")
                })
                rows.append(row)

            # 明細行
            il = line_df[line_df["invoiceID"] == i["ID"]].copy()
            il["dInvoiceLine"] = il["ID"].factorize()[0] + 1

            for _, l in il.iterrows():
                item = item_df[item_df["ID"] == l["itemID"]].iloc[0]
                row = {k: "" for k in columns}
                row.update({
                    "dInvoice": d_inv,
                    "dInvoiceLine": l["dInvoiceLine"],
                    "InvoiceLine.ID": l.get("ID", ""),
                    "InvoiceLine.netAmount": l.get("netAmount", ""),
                    "InvoiceLine.quantity": l.get("quantity", ""),
                    "InvoiceLine.uom": l.get("uom", ""),
                    "Item.ID": item.get("ID", ""), "Item.name": item.get("name", ""),
                    "Item.price": item.get("price", ""), "Item.baseQuantity": item.get("baseQuantity", ""),
                    "Item.uom": item.get("uom", ""), "Item.taxCategoryCode": item.get("taxCategoryCode", ""),
                    "Item.taxCategoryRate": item.get("taxCategoryRate", "")
                })
                rows.append(row)

        return pd.DataFrame(rows, columns=columns)

    # --- 処理分岐 ---
    if invoice_id:
        # 単一請求書出力
        if single_csv_path:
            df0 = export_single_invoice(invoice_id)
            for col in ["dInvoice", "dTaxBreakdown", "dInvoiceLine"]:
                df0[col] = df0[col].apply(lambda x: pd.NA if not str(x).strip().isdigit() else int(x)).astype("Int64")
            df0.to_csv(single_csv_path, index=False, encoding="utf-8-sig")
            print(f"✅ Exported: {single_csv_path}")
        # 全請求書も出力
        if all_csv_path:
            df1 = export_all_invoices()
            for col in ["dInvoice", "dTaxBreakdown", "dInvoiceLine"]:
                df1[col] = df1[col].apply(lambda x: pd.NA if not str(x).strip().isdigit() else int(x)).astype("Int64")
            df1.to_csv(all_csv_path, index=False, encoding="utf-8-sig")
            print(f"✅ Exported: {all_csv_path}")
    else:
        # 全請求書出力（単体請求書ID未指定時）
        df1 = export_all_invoices()
        for col in ["dInvoice", "dTaxBreakdown", "dInvoiceLine"]:
            df1[col] = df1[col].apply(lambda x: pd.NA if not str(x).strip().isdigit() else int(x)).astype("Int64")
        df1.to_csv(all_csv_path, index=False, encoding="utf-8-sig")
        print(f"✅ Exported: {all_csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="構造化インボイスCSVエクスポート")
    parser.add_argument("--base_dir", required=True, help="CSVファイル格納ディレクトリ")
    parser.add_argument("--invoice_id", help="単一請求書ID（指定時はその請求書を出力）")
    parser.add_argument("--single_csv_path", help="単一請求書の出力先ファイルパス")
    parser.add_argument("--all_csv_path", help="全請求書の出力先ファイルパス")
    args = parser.parse_args()
    main(
        args.base_dir,
        invoice_id=args.invoice_id,
        single_csv_path=args.single_csv_path,
        all_csv_path=args.all_csv_path
    )
