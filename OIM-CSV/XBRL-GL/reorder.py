# import pandas as pd

# # Define file paths
base = "OIM-CSV/XBRL-GL/SA/"
# sa_file_path = f"{base}/SA/sa.csv"
# sa_new_file_path = f"{base}/SA/sa_PALK.csv"
# sa_sorted_file_path = f"{base}/SA/sa_PALK_sorted.csv"

# # Load the original sa.csv to get the column order
# sa_df = pd.read_csv(sa_file_path, dtype=str)
# column_order = sa_df.columns.tolist()

# # Load the new sa_2025-01-29.csv
# sa_new_df = pd.read_csv(sa_new_file_path, dtype=str)

# # Reorder columns to match sa.csv
# sa_sorted_df = sa_new_df[column_order]

# # Save the sorted dataframe
# sa_sorted_df.to_csv(sa_sorted_file_path, index=False)

# # Provide the sorted file to the user
# sa_sorted_file_path
import csv

# Define file paths
sa_skeleton_file_path = f"{base}/sa.csv"
sa_palk_file_path = f"{base}/SA_PALK.csv"
sa_sorted_file_path = f"{base}/SA_PALK_sorted.csv"

# Read column order from sa_skeleton.csv
with open(sa_skeleton_file_path, newline='', encoding='utf-8') as skeleton_file:
    reader = csv.reader(skeleton_file)
    skeleton_columns = next(reader)  # Read header

# Read data from SA_PALK.csv
with open(sa_palk_file_path, newline='', encoding='utf-8') as palk_file:
    reader = csv.reader(palk_file)
    palk_columns = next(reader)  # Read header from SA_PALK.csv
    palk_data = [row for row in reader]  # Read all rows

# Determine final column order: skeleton columns first, then extra columns from SA_PALK
extra_columns = [col for col in palk_columns if col not in skeleton_columns]
final_columns = skeleton_columns + extra_columns

# Write sorted data to SA_PALK_sorted.csv
with open(sa_sorted_file_path, 'w', newline='', encoding='utf-8') as sorted_file:
    writer = csv.writer(sorted_file)

    # Write header in the correct order
    writer.writerow(final_columns)

    # Write rows with correct column mapping
    for row in palk_data:
        row_dict = dict(zip(palk_columns, row))  # Map original columns to values
        sorted_row = [row_dict.get(col, "NA") for col in final_columns]  # Fill missing columns with "NA"
        writer.writerow(sorted_row)

# Provide the sorted file path
sa_sorted_file_path
