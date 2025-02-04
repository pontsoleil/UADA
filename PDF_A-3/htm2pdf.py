import pdfkit
from lxml import etree

# wkhtmltopdf.exeのパスを指定
path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

# # XML と XSLT のファイルパス
# xml_file = 'PDF_A-3/Japan_PINT_Invoice_UBL_Example.xml'
# xslt_file = 'PDF_A-3/stylesheet-ubl.xsl'
# html_output = 'PDF_A-3/output.html'

# # XML を XSLT で変換
# xml = etree.parse(xml_file)
# xslt = etree.parse(xslt_file)
# transform = etree.XSLT(xslt)
# html_tree = transform(xml)

# # HTML ファイルとして保存
# with open(html_output, "wb") as f:
#     f.write(etree.tostring(html_tree, pretty_print=True, method="html"))

html_output = 'PDF_A-3/Japan_PINT_Invoice_UBL_Example.htm'

# HTML を PDF に変換
pdf_output = 'PDF_A-3/output.pdf'
pdfkit.from_file(html_output, pdf_output, configuration=config)
