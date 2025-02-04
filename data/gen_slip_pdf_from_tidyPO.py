import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import A4

# Load the CSV data
csv_file = 'data/_PCA/try/generated_invoice_from_PO.csv'  # Replace with the correct file path
df = pd.read_csv(csv_file, encoding='utf-8-sig')

# Function to create PDFs per slip
def create_pdf(file_path, slip_data):
    # Create a canvas object with the specified file path and page size
    c = canvas.Canvas(file_path, pagesize=A4)

    # Register the Japanese font
    pdfmetrics.registerFont(TTFont('NotoSansCJK', 'data/Font/NotoSansCJK-VF.ttf.ttc'))

    # Set the title and draw it on the PDF
    c.setFont("NotoSansCJK", 12)
    c.drawString(100, 800, f"伝票番号: {slip_data['伝票'].iloc[0]}")
    c.drawString(100, 780, f"発注先名: {slip_data['発注先名'].iloc[0]}")
    c.drawString(100, 760, f"発注日: {slip_data['発注日'].iloc[0]}")

    # List the details of the items in the slip
    text = c.beginText(100, 740)
    text.setFont("NotoSansCJK", 10)

    # Add the item details
    for index, row in slip_data.iterrows():
        item_line = f"{row['商品名']} - 数量: {row['数量']} {row['単位']} - 金額: {row['発注金額']}円"
        text.textLine(item_line)

    c.drawText(text)

    # Save the PDF file
    c.save()

# Group the data by '伝票' and generate separate PDFs
for slip_number, slip_data in df.groupby('伝票'):
    file_path = f"slip_{slip_number}.pdf"
    create_pdf(file_path, slip_data)

print("PDF generation completed.")
