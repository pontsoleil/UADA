from tidy_data_parser import TidyDataParser
import json

params_path = "Python/data/params.json"

try:
    parser = TidyDataParser(params_path)

    # JSON出力
    if TidyDataParser.check_file_writable(parser.json_path):
        hierarchy = parser.process_hierarchy()
        with open(parser.json_path, 'w', encoding='utf-8') as f:
            json.dump(hierarchy, f, indent=4, ensure_ascii=False)
        print(f"JSON written to {parser.json_path}")

    # CSV出力
    if TidyDataParser.check_file_writable(parser.file2_path):
        tidy_data = parser.reverse_hierarchy(hierarchy)
        tidy_data.to_csv(parser.file2_path, index=False)
        print(f"Tidy data CSV written to {parser.file2_path}")

except (FileNotFoundError, ValueError, KeyError, PermissionError) as e:
    print(f"Error: {e}")
