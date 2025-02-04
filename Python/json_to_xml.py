from lxml import etree
import json

def json_to_xml(json_data, root_tag="Root"):
    """
    Convert JSON data to XML without unnecessary wrapping for repeated elements.
    :param json_data: The JSON object to convert.
    :param root_tag: The name of the root element in the XML.
    :return: XML string.
    """
    root = etree.Element(root_tag)

    def build_xml_tree(parent, data, key_prefix="d"):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    # Handle lists directly without a wrapper
                    for item in value:
                        # Create child without prefix for repeated elements
                        child = etree.SubElement(parent, key[len(key_prefix):] if key.startswith(key_prefix) else key)
                        build_xml_tree(child, item)
                else:
                    child = etree.SubElement(parent, key)
                    build_xml_tree(child, value)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    child = etree.SubElement(parent, parent.tag[len(key_prefix):] if parent.tag.startswith(key_prefix) else parent.tag)
                    build_xml_tree(child, item)
                else:
                    # Handle non-dict items in a list
                    child = etree.SubElement(parent, parent.tag[len(key_prefix):] if parent.tag.startswith(key_prefix) else parent.tag)
                    child.text = str(item)
        else:
            parent.text = str(data)

    build_xml_tree(root, json_data)
    return etree.tostring(root, pretty_print=True, encoding="unicode")

# Read JSON from a file and write XML to a file
HOME = "Python/data"
input_file = f"{HOME}/company.json"
output_file = f"{HOME}/company.xml"

try:
    with open(input_file, "r", encoding="utf-8") as json_file:
        json_data = json.load(json_file)

    xml_output = json_to_xml(json_data, root_tag="Companies")

    with open(output_file, "w", encoding="utf-8") as xml_file:
        xml_file.write(xml_output)

    print(f"XML successfully written to {output_file}")

except FileNotFoundError:
    print(f"File {input_file} not found.")
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
