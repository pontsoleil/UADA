import xmlschema
from lxml import etree
import os

def validate_xml_local(xml_file, xsd_file):
    """
    Validate an XML file against the given XSD schema file.
    :param xml_file: Path to the XML file
    :param xsd_file: Path to the XSD schema file
    """
    try:
        # Load the XSD schema
        schema = xmlschema.XMLSchema(xsd_file)
        # Validate the XML file
        schema.validate(xml_file)
        print("XML validation successful.")
    except xmlschema.XMLSchemaValidationError as e:
        print(f"Validation failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def execute_xpath(xml_file, xpath_query, namespaces):
    """
    Execute an XPath query on the XML file.
    :param xml_file: Path to the XML file
    :param xpath_query: XPath query string
    :param namespaces: Dictionary of namespaces used in the XML document
    """
    try:
        # Load the XML file
        with open(xml_file, "rb") as file:
            tree = etree.parse(file)
        # Execute the XPath query with namespace support
        results = tree.xpath(xpath_query, namespaces=namespaces)
        print(f"Results for XPath '{xpath_query}':{results}")
        for result in results:
            if isinstance(result, etree._Element):
                print(etree.tostring(result, pretty_print=True).decode())
                # Extract and print the text value of the element
                print(f'RESULT: {result.text.strip() if result.text else "None"}')
            else:
                print(result)
    except Exception as e:
        print(f"Error executing XPath: {e}")

if __name__ == "__main__":
    # File paths
    DATA_DIR = "Python/data"
    XML_FILE = os.path.join(DATA_DIR, "SalInvoiceGen.xml")
    XSD_FILE = os.path.join(DATA_DIR, "AdcSalInvoicesGenerated-v1.0.xsd")

    # Namespace definitions
    namespaces = {"ns": "http://schemas.iso.org/AdcsML/Messages/AdcSalInvoicesGenerated-v1"}

    # Validate the XML
    print("Validating XML...")
    validate_xml_local(XML_FILE, XSD_FILE)

    # Execute XPath queries
    queries = [
        '/ns:AdcSalInvoicesGenerated/ns:SalInvoiGen[ns:Tax/ns:TaxTypCd="VAT-SS"]/ns:InvoiId',
        '/ns:AdcSalInvoicesGenerated/ns:SalInvoiGen/ns:InvoiId',
        '/ns:AdcSalInvoicesGenerated/ns:SalInvoiGen/ns:Tax/ns:TaxTrAmt',
    ]

    print("\nExecuting XPath queries...")
    for query in queries:
        execute_xpath(XML_FILE, query, namespaces)
