import pandas as pd
import json
import os

class TidyDataParser:
    def __init__(self, params_path):
        """
        Initialize the parser with the file paths.
        :param file_path: Path to the CSV file
        :param params_path: Path to the JSON file containing parameters
        """
        if not os.path.isfile(params_path):
            raise FileNotFoundError(f"Parameters file not found: {params_path}")
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
        self.file_path = params["file_path"]
        # Check if files exist
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")
        self.json_path = params["json_path"]
        self.file2_path = params["file2_path"] 
        # Extract dimension prefixes, dimension relationships, and dimension names
        self.dimension_prefixes = tuple(params['dimension_prefixes'])
        self.dimension = params['dimension']
        self.dimension_names = params['dimension_names']
        self.dimension_id = {}
        # Generate the children dictionary from the dimension dictionary
        self.children = self._generate_children()
        # Generate the descendants dictionary from the dimension dictionary
        self.descendants = self._generate_descendants()
        # Generate the ancestor dictionary from the dimension dictionary
        self.ancestor = self._generate_ancestor()
        # Load the CSV data
        try:
            self.data = pd.read_csv(self.file_path)
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {self.file_path}\n{e}")
        # Drop unnamed or irrelevant columns
        self.data = self.data.loc[:, ~self.data.columns.str.contains('^Unnamed')]
        # Identify dimension columns and data columns
        self.dimension_cols = [col for col in self.data.columns if col.startswith(self.dimension_prefixes)]
        self.data_cols = [col for col in self.data.columns if col not in self.dimension_cols]

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

    def process_hierarchy(self):
        """
        Process the hierarchy and build the structured JSON with IDs.
        """
        def traverse_hierarchy(current_dimension, filtered_data):
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

    def reverse_hierarchy(self, hierarchy):
        """
        Reverse the hierarchy to generate hierarchical tidy data CSV.
        """
        def traverse_reverse(current_hierarchy, rows, current_dimension):
            """
            Recursively traverse the JSON hierarchy and reconstruct tidy data rows.
            :param current_hierarchy: Current level of the JSON hierarchy
            :param rows: List of rows to populate
            :param current_dimension: Current dimension being processed
            :param parent_row: Parent row with values for higher dimensions
            """
            for node in current_hierarchy:
                # Start with an empty row, only filling fields related to the current dimension
                row = {col: "" for col in self.dimension_cols + self.data_cols}
                # Populate the current dimension ID and its associated fields
                if current_dimension not in self.dimension_id:
                    self.dimension_id[current_dimension] = 1
                else:
                    self.dimension_id[current_dimension] += 1
                # Initialize all descendant dimension values to 0
                for descendant in self.descendants.get(current_dimension, []):
                    self.dimension_id[descendant] = 0
                # Property is is given from dictionary
                id = self.dimension_id[current_dimension]
                row[current_dimension] = id
                # Copy all properties associated with the current dimension
                for key, value in node.items():
                    if key in self.dimension_names.values() and not isinstance(value, list) and key != "id":
                        row[key] = value  
                # Copy ancestor's id.
                for ancestor in self.ancestor[current_dimension]:
                    row[ancestor] = self.dimension_id.get(ancestor, "")
                # Append non-hierarchical child lists (e.g., Skill, Color) as separate rows
                for key, value in node.items():
                    if isinstance(value, list) and key in self.dimension_names.values():
                        for item in value:
                            # print(f"{key}: {value}")
                            child_row = row.copy()
                            child_row.update({k: v for k, v in item.items() if k != "id"})
                            rows.append(child_row)
                    elif not isinstance(value, list) and key != "id":
                        row[key] = value
                # Add the current row (only if not a list row)
                rows.append(row)
                # Recursively process child dimensions
                for child_dimension in self.children.get(current_dimension, []):
                    if child_dimension in node:
                        traverse_reverse(node[child_dimension], rows, child_dimension)
        # Start from the root dimension
        root_key = next(iter(hierarchy.keys()))
        rows = []
        traverse_reverse(hierarchy[root_key], rows, root_key)
        # Create a DataFrame and reorder columns to match the original tidy data structure
        tidy_data = pd.DataFrame(rows)
        ordered_columns = self.dimension_cols + self.data_cols
        tidy_data = tidy_data.reindex(columns=ordered_columns, fill_value="")
        return tidy_data

    @staticmethod
    def check_file_writable(file_path):
        """ ファイルが書き込み可能かどうかを事前に確認 """
        if os.path.exists(file_path):
            try:
                with open(file_path, 'a+'):  # Appendモードで開く（既存ファイル確認）
                    pass
            except OSError:
                return False
        return True

if __name__ == "__main__":
    # Specify file paths
    params_path = "Python/data/params.json"
    try:
        # Initialize
        parser = TidyDataParser(params_path)
        json_path = parser.json_path
        file2_path = parser.file2_path
        # Pre-check if the JSON file is writable
        if not TidyDataParser.check_file_writable(json_path):
            raise PermissionError(f"Output JSON file is in use or not writable: {json_path}")
        # Pre-check if the CSV file is writable
        if not TidyDataParser.check_file_writable(file2_path):
            raise PermissionError(f"Output CSV file is in use or not writable: {file2_path}")
        # Write JSON file
        hierarchy = parser.process_hierarchy()
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(hierarchy, json_file, indent=4, ensure_ascii=False)
        print(f"JSON written to {json_path}")
        # Write CSV file
        tidy_data = parser.reverse_hierarchy(hierarchy)
        tidy_data.to_csv(file2_path, index=False)
        print(f"Tidy data CSV written to {file2_path}")
    except (FileNotFoundError, ValueError, KeyError, PermissionError) as e:
        print(f"Error: {e}")
