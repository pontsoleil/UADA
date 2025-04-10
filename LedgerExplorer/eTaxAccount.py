"""
Update entryGL.csv and write entryGLeTax.csv after 
1. Change the value of Column8, column19 value with retrieved value in account_list.csv matching Account_Code and retrieve eTax_Account_Code value.
2. If entryGL.csv 's row Column11 or  Column22 or Column27  contains string in name or alias1 or alias2  in account_list.csv, check  digital_transaction in column's value is 1 or not. 
If the value in Column8, column19 is 10D100100 then 
a)  digital_transaction is 1 and changed value change its value to 10D100101 
b)  digital_transaction is not 1 and changed value change its value to 10D100102
Else If the value in Column8, column19 is 10D100100 then 
a)  digital_transaction is 1 and changed value change its value to 10D100101 
b)  digital_transaction is not 1 and changed value change its value to 10D100102
"""
import pandas as pd

DEBUG = False

# Load the data files
base = "data/_PCA"
entryGL_path = f"{base}/entryGL.csv"
account_list_path = f"{base}/account_list.csv"
trading_partner_path = f"{base}/trading_partner.csv"

entryGL = pd.read_csv(entryGL_path, dtype=str)
account_list = pd.read_csv(account_list_path, dtype=str)
trading_partner = pd.read_csv(trading_partner_path, dtype=str)

# Ensure column names are stripped of leading/trailing spaces
entryGL.columns = entryGL.columns.str.strip()
account_list.columns = account_list.columns.str.strip()
trading_partner.columns = trading_partner.columns.str.strip()

# Step 1a: Convert Account_Code to string to avoid mismatches
account_list["Account_Code"] = account_list["Account_Code"].astype(str)
entryGL["Column8"] = entryGL["Column8"].astype(str)
entryGL["Column19"] = entryGL["Column19"].astype(str)

# Step 1b: Ensure NaN values are handled in account_list
account_list["eTax_Account_Code"] = account_list["eTax_Account_Code"].fillna("")
account_list["eTax_Account_Name"] = account_list["eTax_Account_Name"].fillna("")

# Create mapping dictionaries
account_name = account_list.set_index("Account_Code")["eTax_Account_Name"].to_dict()
account_number = account_list.set_index("Account_Code")["eTax_Account_Code"].to_dict()

if DEBUG:
    # Debugging output before applying mapping
    print("Mapping dictionaries created. Checking sample values...")
    print("First 10 Account_Code to eTax_Account_Code mappings:", list(account_number.items())[:10])
    print("First 10 Account_Code to eTax_Account_Name mappings:", list(account_name.items())[:10])

# Step 1: Convert Account_Code to string to avoid mismatches
account_list["Account_Code"] = account_list["Account_Code"].astype(str)
entryGL["Column8"] = entryGL["Column8"].astype(str)
entryGL["Column19"] = entryGL["Column19"].astype(str)

# Step 2: Ensure NaN values are handled in account_list
account_list["eTax_Account_Code"] = account_list["eTax_Account_Code"].fillna("")
account_list["eTax_Account_Name"] = account_list["eTax_Account_Name"].fillna("")

# Step 3: Create mapping dictionaries
account_number_mapping = account_list.set_index("Account_Code")["eTax_Account_Code"].to_dict()
account_name_mapping = account_list.set_index("eTax_Account_Code")["eTax_Account_Name"].to_dict()

if DEBUG:
    # Debugging output before applying mapping
    print("🔍 Checking Account_Code to eTax_Account_Code mapping (first 10 entries):")
    print(list(account_number_mapping.items())[:10])

    print("🔍 Checking eTax_Account_Code to eTax_Account_Name mapping (first 10 entries):")
    print(list(account_name_mapping.items())[:10])

# Step 4: Replace Column8 and Column19 with eTax_Account_Code
print("Applying mapping to Column8 and Column19...")
entryGL["Column8"] = entryGL["Column8"].map(lambda x: account_number_mapping.get(x, "")) 
entryGL["Column19"] = entryGL["Column19"].map(lambda x: account_number_mapping.get(x, "")) 

# Step 5: Replace Column9 and Column20 with eTax_Account_Name
print("Applying mapping to Column9 and Column20...")
entryGL["Column9"] = entryGL["Column8"].map(lambda x: account_name_mapping.get(x, "")) 
entryGL["Column20"] = entryGL["Column19"].map(lambda x: account_name_mapping.get(x, "")) 

if DEBUG:
    # Debugging: Check mapped values
    print("✅ Updated entryGL sample (after mapping):")
    print(entryGL[["Column8", "Column9", "Column19", "Column20"]].head(20))

# Debugging output
print("Updated entryGL sample:")
# print(entryGL[["Column8", "Column9", "Column19", "Column20"]].head(100))
# 関係する列のみ取得
filtered_rows = entryGL[["Column8", "Column9", "Column19", "Column20"]]
# 4つのカラムのうち、どれかに値がある行を取得
filtered_rows = filtered_rows.dropna(how="all")  # 全カラムがNaNの行は削除
if DEBUG:
    # 1行ずつ丁寧に出力
    for index, row in filtered_rows.iterrows():
        print(f"Row {index}: Column8={row['Column8']}, Column9={row['Column9']}, Column19={row['Column19']}, Column20={row['Column20']}")

# Step 2: Check conditions for updating digital_transaction values
for index, row in entryGL.iterrows():
    trading_partner_value = None  # 初期値
    contains_match = False

    # Column11, Column22, Column27 のいずれかの値が trading_partner の name, alias1, alias2 に含まれるかチェック
    for col in ["Column11", "Column22", "Column27"]:
        matched_rows = trading_partner[
            (trading_partner["name"] == row[col]) |
            (trading_partner["alias1"] == row[col]) |
            (trading_partner["alias2"] == row[col])
        ]

        if not matched_rows.empty:
            contains_match = True
            value = matched_rows.iloc[0]["digital_transaction"]  # 取得
            trading_partner_value = False if pd.isna(value) else True  # NaNならFalse、それ以外ならTrue
            break  # 最初にマッチしたら処理を抜ける

    # 後続処理で trading_partner_value を使用
    # if contains_match:
    #     print(f"Index {index}: Found matching trading partner {trading_partner_value}")
    """
    10D100100	総売上高 *
    10D100101	電子取引売上高
    10D100102	電子取引以外売上高
    10D100110	売上値引及び戻り高 *
    10D100111	電子取引売上値引及び戻り高
    10D100112	電子取引以外売上値引及び戻り高
    10E100130	当期商品仕入高
    10E100131	電子取引当期商品仕入高
    10E100132	電子取引以外当期商品仕入高
    10E100120	仕入値引及び戻し高
    10E100133	電子取引仕入値引及び戻し高
    10E100134	電子取引以外仕入値引及び戻し高
    """
    # trading_partner_value を使って追加の処理を行う
    if row["Column8"] in ["10D100110", "10E100130"]:
        if trading_partner_value:
            entryGL.at[index, "Column8"] = row["Column8"][:-1] + "1"
            entryGL.at[index, "Column9"] = "電子取引" + row["Column9"]
        else:
            entryGL.at[index, "Column8"] = row["Column8"][:-1] + "2"
            entryGL.at[index, "Column9"] = "電子取引以外" + row["Column9"]

    if row["Column19"] in ["10D100100","10E100120"]:
        if trading_partner_value:
            entryGL.at[index, "Column19"] = row["Column19"][:-1] + "1"
            entryGL.at[index, "Column20"] = "電子取引" + row["Column20"]
        else:
            entryGL.at[index, "Column19"] = row["Column19"][:-1] + "2"
            entryGL.at[index, "Column20"] = "電子取引以外" + row["Column20"]
# Save the modified file as entryGLeTax.csv with UTF-8 BOM encoding
output_path = f"{base}/entryGLeTax.csv"
entryGL.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"Updated file saved as {output_path}")
