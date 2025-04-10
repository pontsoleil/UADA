import pandas as pd
import json

class HierarchicalDataParser:
    def __init__(self, file_path, params_path):
        """
        初期化関数: ファイル読み込みとパラメータ設定
        :param file_path: CSVファイルのパス
        :param params_path: パラメータファイルのパス (JSON形式)
        """
        self.file_path = file_path

        # パラメータファイルの読み込み
        with open(params_path, 'r') as f:
            params = json.load(f)

        # ディメンション識別プレフィックスとディメンション名
        self.dimension_prefixes = tuple(params['dimension_prefixes'])
        self.dimension_names = params['dimension_names']

        # CSVデータの読み込み
        self.data = pd.read_csv(self.file_path)

        # ディメンション列の特定
        self.dimension_cols = [col for col in self.data.columns if col.startswith(self.dimension_prefixes)]
        self.data_cols = [col for col in self.data.columns if col not in self.dimension_cols]

    def process_hierarchy(self):
        """
        階層構造を解析して表示
        """
        # 会社の情報を取得
        company = self.data[self.data_cols[0]].dropna().iloc[0]
        print(f"Company: {company}")

        # 部門ごとにフィルタリング
        for dept_key in self.data[self.dimension_cols[1]].dropna().unique():
            dept_rows = self.data[self.data[self.dimension_cols[1]] == dept_key]
            department = dept_rows[self.data_cols[1]].dropna().iloc[0]
            print(f"  Department: {department}")

            # 従業員ごとにフィルタリング
            for emp_key in dept_rows[self.dimension_cols[2]].dropna().unique():
                emp_row = dept_rows[dept_rows[self.dimension_cols[2]] == emp_key]
                employee = emp_row[self.data_cols[2]].dropna().iloc[0]
                role = emp_row['Role'].dropna().iloc[0]
                print(f"    Employee: {employee}, Role: {role}")


# クラスの使用例
if __name__ == "__main__":
    # ファイルの場所とパラメータファイルの場所を指定
    file_path = 'Python/data/company.csv'
    params_path = 'Python/data/params.json'  # パラメータファイル

    # クラスを初期化して階層データを解析
    parser = HierarchicalDataParser(file_path, params_path)
    parser.process_hierarchy()
