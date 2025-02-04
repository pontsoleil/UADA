from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import csv
import os
from collections import defaultdict

def create_pdf(file_path, slip_name):
    # Create a canvas object with the specified file path and page size
    c = canvas.Canvas(file_path, pagesize=A4)
    # Register the Japanese font
    pdfmetrics.registerFont(TTFont('NotoSansCJK', 'data/Font/NotoSansCJK-VF.ttf.ttc'))
    # Set the title and draw it on the PDF
    c.setFont("NotoSansCJK", 12)
    c.drawString(100, 800, "これはテスト用のPDFファイルです。")
    # Add some more text
    c.drawString(100, 780, "Pythonとreportlabライブラリを使って作成しました。")
    c.drawString(100, 760, "以下はサンプルテキストです：")
    # Add a block of text
    text = c.beginText(100, 740)
    text.setFont("NotoSansCJK", 20)
    # sample_text = """
    # ReportLabを使用すると、Pythonで簡単にPDFを作成できます。
    # このライブラリは、柔軟で強力なPDF生成機能を提供し、
    # 様々なカスタマイズが可能です。
    # """
    # text.textLines(sample_text)
    text.textLines(slip_name)
    c.drawText(text)
    # Save the PDF file
    c.save()

# Read CSV file
def read_csv_file(file_path):
    with open(file_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        grouped_records = defaultdict(list)
        for row in reader:
            key = (row['伝票日付'], row['取引先'])
            grouped_records[key].append(row)
        grouped_list = [records for records in grouped_records.values()]
    return grouped_list

# Function to process grouped records and generate invoice test data
def process_grouped_records(grouped_list):
    invoice_data = []
    for record_group in grouped_list:
        invoice_date = f"{record_group[0]['伝票日付'][:4]}-{record_group[0]['伝票日付'][4:6]}-{record_group[0]['伝票日付'][-2:]}"
        invoice = {
            "InvoiceDate": invoice_date,
            "Remark": record_group[0]['摘要文'],
            "Supplier": record_group[0]['取引先'],
            "TotalDebitAmount": sum(int(record['借方金額']) for record in record_group),
            "DebitTaxAmount": sum(int(record['借方消費税額']) for record in record_group if record['借方消費税額']),
            "TotalCreditAmount": sum(int(record['貸方金額']) for record in record_group),
            "CreditTaxAmount": sum(int(record['貸方消費税額']) for record in record_group if record['貸方消費税額']),
            "Details": [
                {
                    "DebitDepartment": record['借方部門名'],
                    "DebitAccount": record['借方科目名'],
                    "DebitSubAccount": record['借方補助名'],
                    "DebitAmount": int(record['借方金額']),
                    "DebitTaxCategory": record['借方税区分名'],
                    "DebitTax": int(record['借方消費税額']) if record['借方消費税額'] else 0,
                    "CreditDepartment": record['貸方部門名'],
                    "CreditAccount": record['貸方科目名'],
                    "CreditSubAccount": record['貸方補助名'],
                    "CreditAmount": int(record['貸方金額']),
                    "CreditTaxCategory": record['貸方税区分名'],
                    "CreditTax": int(record['貸方消費税額']) if record['貸方消費税額'] else 0,
                }
                for record in record_group
            ],
        }
        invoice_data.append(invoice)
    return invoice_data

# Function to create an invoice PDF with a Table for details
def create_invoice(invoice):
    file_path = f"data/invoice/{invoice['InvoiceDate']}{invoice['Supplier']}.pdf"
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    c = canvas.Canvas(file_path, pagesize=A4)
    # Register the Japanese font
    pdfmetrics.registerFont(TTFont('NotoSansCJK', 'data/Font/NotoSansCJK-VF.ttf.ttc'))
    # Set the title and draw it on the PDF
    c.setFont("NotoSansCJK", 12)
    c.drawString(100, 740, f"{invoice['InvoiceDate']}")
    c.drawString(100, 720, f"{invoice['Supplier']}")
    c.drawString(100, 700, f"{invoice['Remark'][:-3]}")
    table_data = [["部門", "", "税区分", "税込金額", "消費税"]]
    # Create data for the table
    lines = 0
    for detail in invoice['Details']:
        if "買掛金"==detail['CreditAccount']:
            table_data.append([
                detail['DebitDepartment'],
                "商品",
                # detail['DebitAccount'][2:-1],
                detail['DebitTaxCategory'][2:],
                f"{detail['DebitAmount']:,} 円",
                f"{detail['DebitTax']:,} 円"
            ])
            lines += 1
        elif "仕入値引戻し高"==detail['CreditAccount']:
            table_data.append([
                detail['CreditDepartment'],
                detail['CreditAccount'][2:-3],
                detail['CreditTaxCategory'][2:],
                f"△ {detail['CreditAmount']:,} 円",
                f"△ {detail['CreditTax']:,} 円"
            ])
            lines += 1
    if lines > 1:
        total = 0
        tax = 0
        for detail in invoice['Details']:
            if "買掛金"==detail['CreditAccount']:
                total += int(detail['DebitAmount'])
                tax += int(detail['DebitTax'])
            elif "仕入値引戻し高"==detail['CreditAccount']:
                total -= detail['CreditAmount']
                tax -= detail['CreditTax']
        table_data.append([
            "合計",
            "",
            "",
            f"{total:,} 円",
            f"{tax:,} 円"
        ])
    # Create and style the table
    table = Table(table_data, colWidths=[100, 150, 80, 100, 80])
    """
    TableStyle における範囲指定の数値は、テーブルのセル位置を指定します。範囲は (列, 行) の形式で指定し、セルの開始位置から終了位置までを定義します。

    範囲指定のフォーマット
    python
    コードをコピーする
    (開始列, 開始行), (終了列, 終了行)
    1. 列番号 (Column Index)
    テーブルの 左端から右端 の列を数値で指定します。
    0: 左端の列
    1: 2列目
    -1: 最後の列（右端）
    2. 行番号 (Row Index)
    テーブルの 上端から下端 の行を数値で指定します。
    0: 最上部の行（通常はヘッダー行）
    1: 2行目
    -1: 最後の行（下端）
    3. 範囲の意味
    (開始列, 開始行), (終了列, 終了行) の形式で、適用するセルの範囲を指定します。
    範囲に含まれるすべてのセルにスタイルが適用されます。
    """
    table.setStyle(TableStyle([
        # フォントとサイズを全セルに適用
        ('FONT', (0, 0), (-1, -1), 'NotoSansCJK', 10),
        # テーブル全体の外枠
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        # 内部グリッド
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.gray),
        # 見出し行の背景色
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        # 見出し行を中央揃え（水平）
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # 見出し行を中央揃え（垂直）
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        # 税区分列のデータを中央揃え（水平・垂直）
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('VALIGN', (2, 1), (2, -1), 'MIDDLE'),
        # データ部分の右揃え（例：金額列など）
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        # 全体の垂直中央揃え
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    # Calculate the y-position dynamically to avoid overlap with text above
    text_top_y_position = 700  # Y position of the last line of text
    table_top_margin = 20      # Margin between text and table
    # Calculate the table height dynamically
    table_width, table_height = table.wrap(0, 0)  # Get table dimensions
    # Determine the y-position for the table's top
    table_y_position = text_top_y_position - table_top_margin - table_height
    # Draw the table
    table.wrapOn(c, 50, table_y_position)
    table.drawOn(c, 50, table_y_position)
    # Save the PDF file
    c.save()

# Create the PDF
# テキストファイルから読み込み
# target = "SLIP"
target = "INVOICE"
if "SLIP"==target:
    file_path = 'data/slip_list.txt'
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        slip_list = [line.strip() for line in f.readlines()]
    for slip_name in slip_list:
        create_pdf(f"data/slip/{slip_name}.pdf", slip_name)
elif "INVOICE"==target:
    """
伝票日付,借方部門コード,借方部門名,借方科目コード,借方科目名,借方補助コード,借方補助名,借方税区分名,借方金額,借方消費税額,貸方部門名,貸方科目コード,貸方科目名,貸方補助コード,貸方補助名,貸方税区分コード,貸方税区分名,貸方金額,貸方消費税額,摘要文,取引先
Column1,Column6,Column7,Column8,Column9,Column10,Column11,Column13,Column14,Column15,Column18,Column19,Column20,Column21,Column22,Column23,Column24,Column25,Column26,Column27,Column28
    """
    file_path = "data/invoice_list.csv"
    grouped_list = read_csv_file(file_path)
    invoice_test_data = process_grouped_records(grouped_list)
    # Output the generated invoice test data
    for invoice in invoice_test_data:
        create_invoice(invoice)