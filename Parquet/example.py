import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# 請求書データの作成
data = [
    {
        "invoice_id": 1,
        "date": "2025-02-14",
        "customer": "株式会社A",
        "items": [
            {"item_id": 101, "description": "商品X", "quantity": 2, "price": 1000},
            {"item_id": 102, "description": "商品Y", "quantity": 1, "price": 2000},
        ],
    },
    {
        "invoice_id": 2,
        "date": "2025-02-15",
        "customer": "株式会社B",
        "items": [
            {"item_id": 103, "description": "商品Z", "quantity": 5, "price": 500},
        ],
    },
]

# Arrowのテーブルに変換
table = pa.Table.from_pandas(
    pd.json_normalize(data, "items", ["invoice_id", "date", "customer"])
)

# Parquetファイルに保存
pq.write_table(table, 'Parquet/invoices.parquet')

import pandas as pd

# Load Parquet file
df = pd.read_parquet("Parquet/invoices.parquet", engine="pyarrow")

# Display first few rows
print(df.head())

