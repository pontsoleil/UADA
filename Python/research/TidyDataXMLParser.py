import pandas as pd
import xmlschema
from lxml import etree
import os
import json

class TidyDataXMLParser:
    def __init__(self, params_path):
        """
        Initialize the parser with the file paths.
        :param xml_path: Path to the XML file
        :param params_path: Path to the JSON file containing parameters
        """
        if not os.path.isfile(params_path):
            raise FileNotFoundError(f"Parameters file not found: {params_path}")
        # Load parameters
                # Load parameters from the JSON file
        try:
            with open(params_path, 'r') as f:
                params = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON file: {params_path}\n{e}")
        # Validate required keys in params
        required_keys = ["dimension_prefixes", "dimension", "dimension_names", "file_path", "json_path", "file2_path"]
        for key in required_keys:
            if key not in params:
                raise ValueError(f"Missing required key '{key}' in parameters file.")

        self.xml_path = params["xml_path"]
        self.json_path = params["json_path"]
        self.file2_path = params["file2_path"]
        if not os.path.isfile(self.xml_path):
            raise FileNotFoundError(f"Input XML file not found: {self.xml_path}")
        self.dimension_names = params["dimension_names"]
        self.dimension = params["dimension"]
        self.dimension_id = {}
        # Generate the children dictionary from the dimension dictionary
        self.children = self._generate_children()
        # Generate the descendants dictionary from the dimension dictionary
        self.descendants = self._generate_descendants()
        # Generate the ancestor dictionary from the dimension dictionary
        self.ancestor = self._generate_ancestor()

    def _generate_children(self):
        """
        Generate the children dictionary from the dimension dictionary.
        :return: Children dictionary
        """
        dimension = self.dimension # Dictionary mapping each dimension to its lower-level dimensions
        children = {key: [] for key in dimension.keys()}
        for parent, lower_dimensions in dimension.items():
            for lower in lower_dimensions:
                if lower not in children:
                    raise KeyError(f"Dimension {lower} referenced in {parent} is not defined.")
                children[parent].append(lower)
        return children
    
    def _generate_descendants(self):
        """
        Generate the descendants dictionary from the dimension dictionary.
        Each key maps to all its direct and indirect descendants.
        :return: A dictionary where each key maps to its descendants (direct and indirect).
        """
        dimension = self.dimension # Dictionary mapping each dimension to its lower-level dimensions.
        descendants = {key: set() for key in dimension.keys()}
        def traverse_descendants(current):
            for child in dimension.get(current, []):
                descendants[current].add(child)
                descendants[current].update(traverse_descendants(child))
            return descendants[current]
        for root in dimension.keys():
            traverse_descendants(root)
        # Convert sets to sorted lists for consistency
        return {key: sorted(value) for key, value in descendants.items()}

    def _generate_ancestor(self):
        """
        Generate the ancestors dictionary from the dimension dictionary.
        :param dimension: Dictionary mapping each dimension to its lower-level dimensions
        :return: Ancestors dictionary with no duplicates
        """
        dimension = self.dimension
        ancestors = {key: [] for key in dimension.keys()}
        # Helper function to traverse dimensions recursively
        def traverse_ancestors(current, current_ancestors):
            for child in dimension.get(current, []):
                if child not in ancestors:
                    raise KeyError(f"Dimension {child} referenced in {current} is not defined.")
                # Extend ancestors while maintaining order and removing duplicates
                ancestors[child] = list(dict.fromkeys(ancestors[child] + current_ancestors + [current]))
                traverse_ancestors(child, ancestors[child])
        # Start traversing from the root dimensions
        for root in dimension.keys():
            traverse_ancestors(root, [])
        return ancestors
    
    def _is_leaf(self, name):
        """
        Determines if a dimension is a leaf node by checking its corresponding list in the dimension dictionary.
        A leaf node is defined as a dimension with no child dimensions (an empty list in the dimension dictionary).
        :param name: The dimension name to check (e.g., "Skill", "Color").
        :return: True if the dimension is a leaf node (no children), False otherwise.
        :raises ValueError: If the provided name does not match any dimension.
        """
        dimension_names = self.dimension_names  # Mapping of dimension keys to their names
        dimension = self.dimension  # Dictionary defining the hierarchy of dimensions
        # Find the dimension key corresponding to the provided name
        key = next((k for k, v in dimension_names.items() if v == name), None)
        if not key:
            raise ValueError(f"Dimension '{name}' not found in the dimension names.")
        # Check if the key exists in the dimension dictionary and has an empty list (no children)
        return key in dimension and len(dimension[key]) == 0

    def parse_xml_to_tidy_data(self):
        """
        Process the hierarchy and build the structured JSON with IDs.
        Parse XML and convert it into a tidy DataFrame.
        """
        # Load the XML file
        with open(self.xml_path, "rb") as file:
            tree = etree.parse(file)
        root = tree.getroot()
        rows = []

        def traverse_hierarchy(current_dimension, element, row=None):
            if current_dimension not in self.children:
                return []
            child_dimensions = self.children[current_dimension]
            unique_keys = filtered_data[current_dimension].dropna().unique()
            hierarchy = []
            for key in unique_keys:
                # Filter rows at the current level strictly
                filter_conditions = filtered_data[current_dimension] == key
                rows_at_level = filtered_data[filter_conditions].copy()
                row = rows_at_level.iloc[0]  # Take the first row for static data
                # Build the current node
                node = {} # {"id": int(key) if pd.api.types.is_numeric_dtype(type(key)) else key}
                if current_dimension in self.dimension_names:
                    node[self.dimension_names[current_dimension]] = str(row[self.dimension_names[current_dimension]])
                # Add data columns
                for col in self.data_cols:
                    if pd.notna(row[col]):
                        if col in self.dimension_cols:
                            node[self.dimension_names[col]] = (
                                rows_at_level[col]
                                .dropna()
                                .apply(lambda x: {self.dimension_names[col]: str(x)})
                                .tolist()
                            )
                        else:
                            node[col] = str(row[col])
                # Recursively process child dimensions
                for child_dimension in child_dimensions:
                    child_hierarchy = traverse_hierarchy(child_dimension, rows_at_level)
                    if child_hierarchy:
                        node[child_dimension] = child_hierarchy
                hierarchy.append(node)
            return hierarchy
        # Start traversal from the root dimension
        root_dimension = next(iter(self.dimension))  # The first key in the hierarchy
        return {root_dimension: traverse_hierarchy(root_dimension, self.data)}

    # def parse_xml_to_tidy_data(self):
    #     """
    #     Parse XML and convert it into a tidy DataFrame.
    #     """
    #     # Load the XML file
    #     with open(self.xml_path, "rb") as file:
    #         tree = etree.parse(file)
    #     root = tree.getroot()
    #     rows = []

    #     def traverse(element, row=None):
    #         """
    #         Recursively traverse the XML tree and build tidy rows.
    #         """
    #         if row is None:
    #             row = {dim: "" for dim in self.dimension_cols}  # Initialize row with dimensions
    #         current_row = row.copy()

    #         # Extract tag name without namespace
    #         tag_name = element.tag.split('}')[-1]

    #         # Add element text if it's meaningful
    #         if tag_name in self.dimension_names.values():
    #             element_text = element.text.strip() if element.text and element.text.strip() else None
    #             if element_text:
    #                 current_row[tag_name] = element_text

    #         # Recursively process child elements
    #         has_children = False
    #         for child in element:
    #             has_children = True
    #             traverse(child, current_row)

    #         # Append the row if the element is a leaf node
    #         if not has_children and current_row:
    #             rows.append(current_row)

    #     # Start traversal from the root element
    #     traverse(root)

    #     # Convert collected rows to a DataFrame
    #     tidy_data = pd.DataFrame(rows)

    #     # Fill missing values with empty strings or NaN as needed
    #     tidy_data = tidy_data.fillna("")

    #     return tidy_data


    def json_to_xml(self, json_data, root_tag):
        """
        Convert JSON data into an XML Element.
        """
        root = etree.Element(root_tag)

        def add_elements(parent, data):
            for key, values in data.items():
                for value in values:
                    element = etree.SubElement(parent, key)
                    for k, v in value.items():
                        sub_element = etree.SubElement(element, k)
                        sub_element.text = v

        add_elements(root, json_data)
        return etree.ElementTree(root)

    def process(self):
        """
        Process the XML file into JSON and regenerate XML.
        """
        # Step 1: Parse XML and generate tidy data
        df = self.parse_xml_to_tidy_data()
        print("Tidy Data:\n", df)

        # Step 2: Convert tidy data to JSON
        json_data = self.tidy_data_to_json(df)
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        print(f"JSON written to: {self.json_path}")

        # Step 3: Convert JSON back to XML
        xml_tree = self.json_to_xml(json_data, "store")
        xml_tree.write(self.file2_path, encoding="utf-8", xml_declaration=True)
        print(f"XML written to: {self.file2_path}")

if __name__ == "__main__":
    params_path = "Python/data/paramsXML.json"
    try:
        parser = TidyDataXMLParser(params_path)
        parser.process()
    except (FileNotFoundError, ValueError, KeyError, PermissionError) as e:
        print(f"Error: {e}")
