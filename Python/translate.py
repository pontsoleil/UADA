import re
import csv
import time
from googletrans import Translator

# Initialize the translator
translator = Translator()

# Translation dictionary for cell values
translation_dict = {
    # 科目
    "資産": "Assets",
    "負債": "Liabilities",
    "収益": "Revenue",
    "費用": "Expenses",
    "現金": "Cash",
    "当座預金": "Current Account",
    "普通預金": "Regular Savings Account",
    "定期積金": "Installment Savings Account",
    "定期積金": "Regular Deposit",
    "受取手形": "Bills Receivable",
    "電子記録債権": "Electronically Recorded Receivables",
    "売掛金": "Accounts Receivable",
    "商品": "Merchandise",
    "短期貸付金": "Short-Term Loans Receivable",
    "構築物": "Structures",
    "工具器具備品": "Tools, Furniture, and Fixtures",
    "保険積立金": "Insurance Reserve Fund",
    "支払手形": "Bills Payable",
    "買掛金": "Accounts Payable",
    "短期借入金": "Short-Term Loans Payable",
    "未払金": "Accrued Expenses",
    "預り金": "Deposits Received",
    "未払事業税等": "Accrued Business Taxes",
    "未払法人税等": "Accrued Corporate Taxes",
    "未払消費税等": "Accrued Consumption Taxes",
    "長期借入金": "Long-Term Loans Payable",
    "売上高": "Sales",
    "売上値引戻り高": "Sales Returns",
    "売上割戻し高": "Sales Discounts",
    "期首商品棚卸高": "Beginning Merchandise Inventory",
    "商品仕入高": "Merchandise Purchases",
    "仕入値引戻し高": "Purchase Returns",
    "期末商品棚卸高": "Ending Merchandise Inventory",
    "役員報酬": "Executive Compensation",
    "給与手当": "Salaries and Wages",
    "賞与": "Bonuses",
    "雑給": "Miscellaneous Wages",
    "法定福利費": "Statutory Welfare Expenses",
    "福利厚生費": "Employee Welfare Expenses",
    "旅費交通費": "Travel and Transportation Expenses",
    "通信費": "Communication Expenses",
    "販売手数料": "Sales Commissions",
    "運賃": "Freight",
    "広告宣伝費": "Advertising Expenses",
    "交際接待費": "Entertainment Expenses",
    "会議費": "Conference Expenses",
    "水道光熱費": "Utilities",
    "消耗品費": "Supplies Expenses",
    "租税公課": "Taxes and Dues",
    "新聞図書費": "Books and Subscriptions",
    "車両費": "Vehicle Expenses",
    "支払手数料": "Payment Fees",
    "諸会費": "Membership Fees",
    "リース料": "Lease Payments",
    "支払報酬": "Professional Fees",
    "地代家賃": "Rent",
    "保険料": "Insurance Premiums",
    "修繕維持費": "Repairs and Maintenance",
    "事務用消耗品費": "Office Supplies",
    "減価償却費": "Depreciation Expense",
    "雑費": "Miscellaneous Expenses",
    "支払利息": "Interest Expense",
    # 部門
    "名古屋支店": "Nagoya Branch",
    "東京支店": "Tokyo Branch",
    "大阪支店": "Osaka Branch",
    "共通部門": "Common Department",
    "札幌営業所": "Sapporo Sales Office",
    "九州営業所": "Kyushu Sales Office",
    "0001役員": "0001 Executives",
    "0020営業部": "0020 Sales Department",
    "0060パート･アルバイト": "0060 Part-time and Temporary Workers",
    "1000札幌営業所": "1000 Sapporo Office",
    "3000名古屋営業所": "3000 Nagoya Office",
    "4000大阪支店": "4000 Osaka Branch",
    "5000九州営業所": "5000 Kyushu Office",
    # 税区分
    "対象外": "Out of Scope",
    "非仕入": "Non-purchase",
    "仕入8%軽": "Purchase 8% Reduced Tax Rate",
    "仕入10%": "Purchase 10%",
    "仕返10%": "Purchase Return 10%",
    "売上10%": "Sales 10%",
    "売返10%": "Sales Return 10%",
    "仕入８%軽": "Purchase ８% Reduced Tax Rate",
    "仕入１０%": "Purchase 10%",
    "売上１０%": "Sales 10%",
    "売返１０%": "Sales Return 10%",
    # 摘要文
    "旅費": "Travel Expenses",
    "その他": "Others",
    "住民税": "Resident Tax",
    "保険料": "Insurance Premium",
    "源泉税": "Withholding Tax",
    "貯蓄・保険": "Savings & Insurance",
    "JR代": "JR Fare",
    "JR回数券": "JR Commuter Pass",
    "ウォッシャー液": "Washer Fluid",
    "ウォッシャー液代": "Washer Fluid Cost",
    "お茶代": "Tea Cost",
    "お茶代他": "Tea Cost and Others",
    "お見舞い": "Get-well Gift",
    "カウンター料金": "Counter Fee",
    "ガス代": "Gas Cost",
    "ガソリン代": "Gasoline Cost",
    "コーヒー代": "Coffee Cost",
    "コーヒー代喫茶まどい": "Coffee Cost at Madoui Cafe",
    "コピー代": "Copy Cost",
    "コピー機修繕": "Copier Repair",
    "ゴルフプレー代": "Golf Play Fee",
    "スノーブレード代": "Snow Blade Cost",
    "タクシー代": "Taxi Fare",
    "ダスキン代": "Duskin Service Fee",
    "ティッシュペーパー他": "Tissue Paper and Others",
    "ティッシュ代": "Tissue Cost",
    "ティッシュ代他": "Tissue Cost and Others",
    "トイレットペーパー他": "Toilet Paper and Others",
    "トイレットペーパー代": "Toilet Paper Cost",
    "ファイル等": "Files and Others",
    "事務用品": "Office Supplies",
    "事務用品費": "Office Supplies Expense",
    "会議食事代": "Meeting Meal Cost",
    "会費": "Membership Fee",
    "会費支払い": "Membership Fee Payment",
    "住民税支払": "Resident Tax Payment",
    "保険料事業主負担分": "Employer's Share of Insurance Premiums",
    "保険料支払": "Insurance Premium Payment",
    "保険料支払い": "Insurance Premium Payment",
    "保険料預かり分": "Insurance Premium Advance",
    "修理代": "Repair Cost",
    "修繕費": "Maintenance Cost",
    "借入金返済": "Loan Repayment",
    "児童拠出金事業主負担分": "Employer's Share of Child Contribution",
    "出張旅費": "Business Trip Expense",
    "切手代": "Postage Cost",
    "利息": "Interest",
    "制服代": "Uniform Cost",
    "収入印紙": "Revenue Stamp",
    "収入印紙代": "Revenue Stamp Cost",
    "台所用品": "Kitchen Supplies",
    "名刺代": "Business Card Cost",
    "商品券": "Gift Certificate",
    "定例ミーティング会費": "Regular Meeting Membership Fee",
    "定期積立金": "Regular Savings Deposit",
    "家賃支払": "Rent Payment",
    "家賃支払い": "Rent Payment",
    "宿泊代": "Accommodation Cost",
    "宿泊費": "Accommodation Expense",
    "広告掲載": "Advertisement",
    "広告料": "Advertisement Fee",
    "広告費": "Advertising Expense",
    "引き出し": "Withdrawal",
    "忘年会会費": "Year-end Party Membership Fee",
    "手形割引料": "Bill Discount Fee",
    "手形期日落日チェック": "Bill Due Date Check",
    "携帯代": "Mobile Phone Cost",
    "携帯電話代": "Mobile Phone Bill",
    "新聞代": "Newspaper Cost",
    "景品代": "Prize Cost",
    "有線": "Wired (Cable)",
    "業務委託費": "Subcontracting Cost",
    "業務委託費支払い": "Subcontracting Fee Payment",
    "残業夜食軽減税率": "Overtime Night Meal Reduced Tax Rate",
    "水道代": "Water Cost",
    "水道料": "Water Bill",
    "洗剤他": "Detergent and Others",
    "洗剤代": "Detergent Cost",
    "消耗品費部門配賦": "Consumables Cost Department Allocation",
    "清掃料": "Cleaning Fee",
    "源泉税支払": "Withholding Tax Payment",
    "点検作業料": "Inspection Fee",
    "点検整備": "Inspection Maintenance",
    "用紙": "Paper",
    "社員夜食代": "Employee Night Meal Cost",
    "税理士報酬": "Tax Accountant Fee",
    "結婚祝い金": "Wedding Celebration Money",
    "航空券": "Airline Ticket",
    "航空券代": "Airline Ticket Cost",
    "警備料": "Security Fee",
    "貸付金": "Loan",
    "貸付金返済": "Loan Repayment",
    "資金移動": "Fund Transfer",
    "車両管理費": "Vehicle Management Cost",
    "電気代": "Electricity Cost",
    "電気料": "Electricity Bill",
    "電池代": "Battery Cost",
    "電話代": "Telephone Cost",
    "飲料水": "Drinking Water",
    "香典代": "Condolence Money",
    "駐車代": "Parking Fee",
    "高速代": "Highway Toll",
    "高速料": "Highway Toll",
    "昼食代": "Lunch Cost",
    "食事代": "Meal Cost",
    "飲食代": "Food and Beverage Cost",
    # 会社名
    "タワー株式会社": "Tower Co., Ltd.",
    "株式会社ＡＢＣ": "ABC Co., Ltd.",
    "株式会社Ｙ２": "Y2 Co., Ltd.",
    "株式会社小林マーケット": "Kobayashi Market Co., Ltd.",
    "合同会社たかだ": "Takada LLC",
    "合同会社ウェスト": "West LLC",
    "小藤丸株式会社": "Kofujimaru Co., Ltd.",
    "株式会社畠山商事": "Hatakeyama Trading Co., Ltd.",
    "斉藤産業株式会社": "Saito Industries Co., Ltd.",
    "合同会社エイム商事": "Aim Trading LLC",
    "五越株式会社": "Goketsu Co., Ltd.",
    "株式会社鎌田商店": "Kamata Shoten Co., Ltd.",
    "株式会社藤田東京本社": "Fujita Tokyo Headquarters Co., Ltd.",
    "株式会社チェック": "Check Co., Ltd.",
    "株式会社山下": "Yamashita Co., Ltd.",
    "株式会社総合経営": "Comprehensive Management Co., Ltd.",
    "阿部商事株式会社": "Abe Trading Co., Ltd.",
    "株式会社ミナミ": "Minami Co., Ltd.",
    "株式会社サンセット": "Sunset Co., Ltd.",
    "ナカムラ産業株式会社": "Nakamura Industries Co., Ltd.",
    "かめだデパート": "Kameda Department Store",
    "株式会社ＹＡＧ": "YAG Co., Ltd.",
    "鈴木販売株式会社": "Suzuki Sales Co., Ltd.",
    "株式会社アタッチ": "Attach Co., Ltd.",
    "もみじデパート": "Momiji Department Store",
    "岩下物産株式会社": "Iwashita Trading Co., Ltd.",
    "マークマーケット": "Mark Market",
    "佐々木販売株式会社": "Sasaki Sales Co., Ltd.",
    "株式会社Ｐｏｌｅ": "Pole Co., Ltd.",
    "株式会社エントリー": "Entry Co., Ltd.",
    "高橋物産株式会社": "Takahashi Trading Co., Ltd.",
    "株式会社久城商事": "Kujou Trading Co., Ltd.",
    "株式会社ハナダ": "Hanada Co., Ltd.",
    "今井百貨店": "Imai Department Store",
    "株式会社まつむら": "Matsumura Co., Ltd.",
    "株式会社有江": "Arie Co., Ltd.",
    "株式会社斉藤": "Saito Co., Ltd.",
    "株式会社渡辺産業": "Watanabe Industries Co., Ltd.",
    "株式会社はなまる商事": "Hanamaru Trading Co., Ltd.",
    "株式会社千代サービス": "Chiyo Service Co., Ltd.",
    "みずほ本店": "Mizuho Main Branch",
    "みずほ銀行": "Mizuho Bank",
    "三井名古屋": "Mitsui Nagoya",
    "三菱東京梅田": "Mitsubishi Tokyo Umeda",
    "北海道駅前": "Hokkaido Station Front",
    "株式会社Ｙ2": "Y2 Co., Ltd.",
    "株式会社藤田": "Fujita Co., Ltd.",
    "福岡北九州": "Fukuoka Kitakyushu",
    "イタリアンレストランペンネ": "Italian Restaurant Penne",
    "いろは": "Iroha",
    "うどん亭": "Udon Tei",
    "お好み焼きやきやき": "Okonomiyaki Yaki Yaki",
    "カナッシュ": "Kanashu",
    "カフェバー": "Cafe Bar",
    "カフェバーラウル": "Cafe Bar Raul",
    "スナックいちい": "Snack Ichii",
    "スナックさらら": "Snack Sarara",
    "スナックみわ": "Snack Miwa",
    "スナックライラ": "Snack Lyra",
    "スナックランディ": "Snack Randy",
    "スナックりりあん": "Snack Lillian",
    "スナックわたなべ": "Snack Watanabe",
    "スナック今日子": "Snack Kyoko",
    "スナック北新地": "Snack Kitashinchi",
    "スナック新世界": "Snack Shinsekai",
    "スナック箱船": "Snack Hakobune",
    "ダイニング彩": "Dining Sai",
    "ダイニング旬": "Dining Shun",
    "トルテーヤ": "Tortilla",
    "トン吉": "Tonkichi",
    "ハブバージョイ": "Hub Bar Joy",
    "パブランディー": "Pub Randy",
    "ホテルエンペラー": "Hotel Emperor",
    "ホテルグランディ": "Hotel Grandi",
    "ホテルクリーク": "Hotel Creek",
    "ホテルジャーマニー": "Hotel Germany",
    "ホテルラフォーネ": "Hotel Raffone",
    "ホテルララダ": "Hotel Lalada",
    "ホテルランチ": "Hotel Lunch",
    "ホテル大分": "Hotel Oita",
    "やまびこ": "Yamabiko",
    "ラーメンめん吉": "Ramen Menkichi",
    "レストランフード": "Restaurant Food",
    "レストランフレンド": "Restaurant Friend",
    "レストランライラック": "Restaurant Lilac",
    "レストランラルー": "Restaurant Lalu",
    "レストラン桜花": "Restaurant Ouka",
    "レストラン梅田": "Restaurant Umeda",
    "串揚げ一心": "Kushikatsu Isshin",
    "串揚げ千本": "Kushikatsu Senbon",
    "他": "Others",
    "会費制": "Membership System",
    "博多ラーメン": "Hakata Ramen",
    "博多亭": "Hakata Tei",
    "和風ダイニング法善寺": "Japanese Dining Hozenji",
    "和食ダイニング小笹": "Japanese Dining Ozasa",
    "和食ダイニング彩": "Japanese Dining Sai",
    "和食処川よし": "Japanese Restaurant Kawayoshi",
    "喫茶エンゼル": "Cafe Angel",
    "喫茶コーヒー代": "Cafe Coffee Cost",
    "居酒屋くるみ": "Izakaya Kurumi",
    "居酒屋チキンズ": "Izakaya Chickens",
    "居酒屋太助": "Izakaya Tasuke",
    "居酒屋富士": "Izakaya Fuji",
    "居酒屋栗の木": "Izakaya Kurinoki",
    "居酒屋田舎": "Izakaya Inaka",
    "居酒屋花道": "Izakaya Hanamichi",
    "打合せ昼食": "Meeting Lunch",
    "昼食": "Lunch",
    "梅田小路": "Umeda Alley",
    "華": "Hana",
    "長崎港屋": "Nagasaki Minato-ya",
    "鳥仙人": "Torisenjin",
    "そば屋三品": "Soba Shop Sanpin",
    "居酒屋佐助": "Izakaya Sasuke",
    "居酒屋華ゆう": "Izakaya Kayu",
    "バー薩摩": "Bar Satsuma",
    "かりん": "Karin",
    "スナック帰り道": "Snack Kaerimichi",
    "レストランファミリー": "Restaurant Family",
    "居酒屋旬": "Izakaya Shun",
    "居酒屋いろは": "Izakaya Iroha",
    "バー湯の瀬": "Bar Yunose",
    "居酒屋ラッキー": "Izakaya Lucky",
}

# Define a dictionary for Japanese month names
jp_months = {
    "1月": "January",
    "2月": "February",
    "3月": "March",
    "4月": "April",
    "5月": "May",
    "6月": "June",
    "7月": "July",
    "8月": "August",
    "9月": "September",
    "10月": "October",
    "11月": "November",
    "12月": "December"
}

company_names = set()
trading_partner_names = set()
cost_center_names = set()
description_pattern = set()

def translate_date(jp_date):
    # Match the Japanese date format using regular expression
    match = re.match(r'(\d{1,2})月(\d{1,2})日', jp_date)
    if not match:
        return jp_date  # Return original string if format doesn't match
    month_num, day = match.groups()
    month_str = f"{int(month_num)}月"
    # Get the English month name
    if month_str in jp_months:
        month = jp_months[month_str]
    else:
        return jp_date  # Return original string if month is not found
    if 1 == day[-1]:
        day = f"{day[:-1]}1st"
    elif 2 == day[-1]:
        day = f"{day[:-1]}2nd"
    elif 3 == day[-1]:
        day = f"{day[:-1]}3rd"
    else:
        day = f"{day}th"
    # Return the formatted date
    return f"{month} {day}"

def translate_month(month_str):
    if month_str in jp_months:
        month = jp_months[month_str]
        return month
    return month_str  # Return original string if month is not found

# 半角カナから全角カナへの変換用の関数
def convert_halfwidth_to_fullwidth(text):
    # Complete mapping for half-width to full-width katakana, including voiced and semi-voiced sounds
    kana_conversion_table = {
        'ｶﾞ': 'ガ', 'ｷﾞ': 'ギ', 'ｸﾞ': 'グ', 'ｹﾞ': 'ゲ', 'ｺﾞ': 'ゴ',
        'ｻﾞ': 'ザ', 'ｼﾞ': 'ジ', 'ｽﾞ': 'ズ', 'ｾﾞ': 'ゼ', 'ｿﾞ': 'ゾ',
        'ﾀﾞ': 'ダ', 'ﾁﾞ': 'ヂ', 'ﾂﾞ': 'ヅ', 'ﾃﾞ': 'デ', 'ﾄﾞ': 'ド',
        'ﾊﾞ': 'バ', 'ﾋﾞ': 'ビ', 'ﾌﾞ': 'ブ', 'ﾍﾞ': 'ベ', 'ﾎﾞ': 'ボ',
        'ﾊﾟ': 'パ', 'ﾋﾟ': 'ピ', 'ﾌﾟ': 'プ', 'ﾍﾟ': 'ペ', 'ﾎﾟ': 'ポ',
        'ｧ': 'ァ', 'ｨ': 'ィ', 'ｩ': 'ゥ', 'ｪ': 'ェ', 'ｫ': 'ォ',
        'ｬ': 'ャ', 'ｭ': 'ュ', 'ｮ': 'ョ', 'ｯ': 'ッ',
        'ｳﾞ': 'ヴ', 'ﾜﾞ': 'ヷ', 'ｦﾞ': 'ヺ',
        'ｰ': 'ー'
    }
    # Convert voiced and semi-voiced characters first
    for hw, fw in kana_conversion_table.items():
        text = text.replace(hw, fw)
    # Convert other half-width katakana to full-width katakana
    half_width = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜｦﾝ"
    full_width = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
    hw_to_fw = str.maketrans(half_width, full_width)
    text = text.translate(hw_to_fw)
    return text

# 文字列をクリーンアップする関数
def clean_text(text):
    if text is None or text == '':
        return text
    text = str(text)
    # 許可された符号
    allowed_symbols = {'＆', '’', '，', '‐', '．', '・', '&', "'", ',', '-', '.', '･'}
    # Step 1: Replace (株) with 株式会社
    text = convert_halfwidth_to_fullwidth(text)
    text = text.replace('㈱', '株式会社')
    text = text.replace('(同)', '合同会社')
    # Step 2: Extract contiguous alphabet, symbol, and numeric segments (including full-width characters)
    pattern = re.compile(r'[Ａ-Ｚａ-ｚA-Za-z０-９0-9’，‐．・&\',\-\.･\s]+|[^Ａ-Ｚａ-ｚA-Za-z０-９0-9＆’，‐．・&\',\-\.･\s]+')
    segments = pattern.findall(text)
    # Step 3: Validate segments and check for disallowed characters
    validated_segments = []
    for segment in segments:
        segment = segment.strip(" 　")
        if re.match(r'[\-+0-9]+', segment):
            validated_segments.append(segment)
        elif re.match(r'[Ａ-Ｚａ-ｚA-Za-z＆’，‐．・&\',\-\.･\s]+', segment):
            if not all(
                char in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
                "0123456789"
                "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
                "０１２３４５６７８９"
                or char in allowed_symbols
                or char in " 　"
                for char in segment
            ) or (
                len(segment) > 1
                and (
                    segment[0] in allowed_symbols
                    or (
                        segment[-1] not in ["．", "."]
                        and segment[-1] in allowed_symbols
                    )
                )
            ):
                raise ValueError(f"使用できない符号が含まれています: {segment}")
            validated_segments.append(segment)
        else:
            validated_segments.append(segment)
    # Step 4: Clean segments
    cleaned_segments = []
    for segment in validated_segments:
        if re.match(r'[Ａ-Ｚａ-ｚA-Za-z＆’，‐．・&\',\-\.･\s]+', segment):
            # Replace multiple spaces in segments with a single full-width space
            segment = re.sub(r'[\s]+', ' ', segment)
            # Convert half-width Kana to full-width Kana
            segment = convert_halfwidth_to_fullwidth(segment)
            # Half-width to full-width conversion table
            half_width = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            full_width = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ" \
                         "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
            hw_to_fw = str.maketrans(half_width, full_width)
            segment = segment.translate(hw_to_fw)
            # Replace multiple spaces in segments with a single full-width space again after conversion
            segment = re.sub(r'[\s]+', '　', segment)
        else:
            segment = segment.replace('　', '').replace(' ', '')  # Remove spaces from non-segment parts
        cleaned_segments.append(segment)
    # Combine cleaned segments
    cleaned_text = ''.join(cleaned_segments)
    return cleaned_text

# Function to process and translate the description
def process_description(description):
    pattern1 = r'([0-9０-９]{1,2}月[0-9０-９]{1,2}日)伝票[NoＮｏ]+([0-9０-９]+)(.+)'
    pattern2 = r'([0-9０-９]{1,2}月[0-9０-９]{1,2}日)～([0-9０-９]{1,2}月[0-9０-９]{1,2}日)分仕入' # Purchases for the period from October 1 to October 31
    pattern3 = r'([0-9０-９]{1,2}月[0-9０-９]{1,2}日)～([0-9０-９]{1,2}月[0-9０-９]{1,2}日)分売上' # Sales for the period from October 1 to October 31
    pattern4 = r'([0-9０-９]{1,2}月)分支払' # Payment for October
    pattern5 = r'([0-9０-９]{1,2}月)給与その他(.+)' # October Salary Others 0001 Executives'
    pattern6 = r'(.*代)[ 　]*([^0-9]+)[ 　]*([0-9]+)名' # Food and Beverage Cost Snack Kitashinchi 4 People
    match1 = re.match(pattern1, description)
    match2 = re.match(pattern2, description)
    match3 = re.match(pattern3, description)
    match4 = re.match(pattern4, description)
    match5 = re.match(pattern5, description)
    match6 = re.match(pattern6, description)
    translated_description = None
    if match1:
        date = match1.group(1)
        slip_number = match1.group(2)
        company = match1.group(3).strip(" 　")  # Strip any leading/trailing whitespace
        company = clean_text(company)
        hw_to_fw = str.maketrans("1234567890", "１２３４５６７８９０")
        company = company.translate(hw_to_fw)
        company_names.add(company)
        # Translate each part
        date_translated = translate_date(date)
        slip_number_translated = f"Slip No. {slip_number}"  # Simplify slip number translation
        company_translated = translate_text(company)
        # Recombine the translated parts
        translated_description = f"{date_translated} {slip_number_translated} {company_translated}"
        translated_description_pattern = f"Month date Slip No. xxx {company_translated}"
        # Add to translation dictionary
        if translated_description_pattern not in description_pattern:
            description_pattern.add(translated_description_pattern)
    elif match2:
        start_date = match2.group(1)
        end_date = match2.group(2)
        start_date = translate_date(start_date)
        end_date = translate_date(end_date)
        translated_description = f"Purchases for the period from {start_date} to {end_date}"
    elif match3:
        start_date = match3.group(1)
        end_date = match3.group(2)
        start_date = translate_date(start_date)
        end_date = translate_date(end_date)
        translated_description = f"Sales for the period from {start_date} to {end_date}"
    elif match4:
        month_str = match4.group(1)
        month = translate_month(month_str)
        translated_description = f"Payment for {month}"
    elif match5:
        month_str = match5.group(1)
        month = translate_month(month_str)
        cost_center_str = match5.group(2)
        if cost_center_str in translation_dict:
            cost_center = translation_dict[cost_center_str]
        else:
            cost_center = cost_center_str
        translated_description = f"{month} Salary Others {cost_center}"
    elif match6:
        account_str = match6.group(1).strip(" 　")  # Strip any leading/trailing whitespace
        if account_str in translation_dict:
            account = translation_dict[account_str]
        else:
            account = account_str
        entity_str = match6.group(2).strip(" 　")  # Strip any leading/trailing whitespace
        if entity_str in translation_dict:
            entity = translation_dict[entity_str]
        else:
            entity = entity_str
            print(f"- process_description {entity_str} is not defined in translation_dict.")
        if '他' in description:
            other = ' Other'
        else:
            other = ''
        people_number = match6.group(3)
        translated_description = f"{account} {other}{entity} {people_number} People"
    if translated_description:
        return translated_description
    text = description
    try:
        if None is text or '' == text:
            return ''
        time.sleep(0.2)
        if text in translation_dict:
            return translation_dict[text]
        text = clean_text(text)
        # Use Google Translate to translate text
        translated = translator.translate(text, src='ja', dest='en').text
        return translated
    except Exception as e:
        print(f"- Translation error in process_description for '{text}': {e}")
        return text

def clean_description(description):
    pattern1 = r'([0-9０-９]{1,2}月[0-9０-９]{1,2}日)伝票[NoＮｏ]+([0-9０-９]+)(.+)'
    match1 = re.match(pattern1, description)
    translated_description = None
    if match1:
        date = match1.group(1)
        slip_number = match1.group(2)
        company = match1.group(3).strip(" 　")  # Strip any leading/trailing whitespace
        company = clean_text(company)
        hw_to_fw = str.maketrans("1234567890", "１２３４５６７８９０")
        company = company.translate(hw_to_fw)
        translated_description = f"{date} 伝票No {slip_number} {company}"
    if translated_description:
        return translated_description
    text = description
    return text

# Function to translate text using the translation dictionary and Google Translate
def translate_text(text, column=None):
    # Convert the text to string
    text = str(text)
    text = clean_text(text)
    # Skip text that is numeric, a date, or contains only alphanumeric and printable symbols
    if re.match(r'^[a-zA-Z0-9\s\-\:\,\.\/]+$', text):
        return text
    # Check if text is in the dictionary
    elif text in translation_dict:
        return translation_dict[text]
    else:
        try:
            if None is text or '' == text:
                return ''
            time.sleep(0.2)
            if text in translation_dict:
                return translation_dict[text]
            # Use Google Translate to translate text
            translated = translator.translate(text, src='ja', dest='en').text
            return translated
        except Exception as e:
            print(f"- Translation error in translate_text {column} for '{text}': {e}")
            return text

print('# Define the base directory and file paths')
base_dir = 'data/_PCA'
input_file_path = f'{base_dir}/entryGL.csv'
output_file_path = f'{base_dir}/entryGL_translated.csv'
company_file_path = f'{base_dir}/company_names.csv'
trading_partner_file_path = f'{base_dir}/trading_partner_names.csv'
cost_center_file_path = f'{base_dir}/cost_center_names.csv'
refined_file_path = f'{base_dir}/entryGL_refined.csv'

print('# Define columns to translate')
columns_to_translate = {
    'Column9': '借方科目名',
    'Column20': '貸方科目名',
    'Column7': '借方部門名',
    'Column18': '貸方部門名',
    'Column11': '借方補助名',
    'Column22': '貸方補助名',
    'Column27': '摘要文',
    'Column58': '借方取引先名',
    'Column66': '貸方取引先名',
    'Column13': '借方税区分名',
    'Column24': '貸方税区分名'
}

print('# Read the CSV file')
with open(input_file_path, mode='r', encoding='utf-8-sig') as infile:
    reader = csv.DictReader(infile)
    rows = list(reader)
    header = rows[0]
    rows = rows[1:]

original_rows = rows.copy()

print('# Extract and save trading partner names')
for row in rows:
    trading_partner_names.add(clean_text(row['Column11']))
    trading_partner_names.add(clean_text(row['Column22']))

with open(trading_partner_file_path, mode='w', newline='', encoding='utf-8-sig') as tpfile:
    tp_writer = csv.writer(tpfile)
    tp_writer.writerow(['取引先名'])
    for name in trading_partner_names:
        name = clean_text(name)
        tp_writer.writerow([name])

print('# Extract and save cost center names')
for row in rows:
    cost_center_names.add(clean_text(row['Column7']))
    cost_center_names.add(clean_text(row['Column18']))

with open(cost_center_file_path, mode='w', newline='', encoding='utf-8-sig') as csfile:
    cs_writer = csv.writer(csfile)
    cs_writer.writerow(['部門名'])
    for name in cost_center_names:
        if not name:
            continue
        name = clean_text(name)
        cs_writer.writerow([name])

print('# Translate the specified columns')
current_month = None
for row in rows:
    if row['Column1'][:6] != current_month:
        print(f"Translating {row['Column1'][:6][:4]}-{row['Column1'][:6][-2:]}")
    current_month = row['Column1'][:6]
    for column in [
        "Column9", # 借方科目名
        "Column7", # 借方部門名
        "Column11", # 借方補助名
        "Column13", # 借方税区分名
        "Column58", # 借方取引先名
        "Column20", # 貸方科目名
        "Column18", # 貸方部門名
        "Column22", # 貸方補助名
        "Column24", # 貸方税区分名
        "Column66", # 貸方取引先名
        "Column27", # 摘要文
    ]:
        if not row[column]:
            continue
        if column in [
            "Column9", # 借方科目名
            "Column7", # 借方部門名
            "Column11", # 借方補助名
            "Column13", # 借方税区分名
            "Column20", # 貸方科目名
            "Column18", # 貸方部門名
            "Column22", # 貸方補助名
            "Column24", # 貸方税区分名
        ]:
            text = clean_text(row[column])
            if text in translation_dict:
                row[column] = translation_dict[text]
            else:
                row[column] = translate_text(text, column)
        elif column == "Column27":
            text = clean_text(row[column])
            row[column] = process_description(text)
        elif column in ["Column58", "Column66"]:
            text = clean_text(row[column])
            row[column] = translate_text(text, column)

with open(company_file_path, mode='w', newline='', encoding='utf-8-sig') as cmfile:
    cm_writer = csv.writer(cmfile)
    cm_writer.writerow(['取引先名'])
    for name in company_names:
        cm_writer.writerow([name])

print('# Write the translated rows to a new CSV file')
with open(output_file_path, mode='w', newline='', encoding='utf-8-sig') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

# Define columns to translate
columns_to_translate = {
    'Column11': '借方補助名',
    'Column22': '貸方補助名',
    'Column27': '摘要文',
}

refined_rows = []
print('# Clean the specified columns')
for row in original_rows:
    refined_row = row.copy()
    for column in columns_to_translate.keys():
        if column in row:
            if column == 'Column27':
                refined_row[column] = clean_description(row[column])
            else:
                refined_row[column] = clean_text(row[column])
    refined_rows.append(refined_row)

print('# Write the cleaned and translated rows to a new CSV file')
with open(refined_file_path, mode='w', newline='', encoding='utf-8-sig') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(refined_rows)

print("Translation and cleaning completed and saved to:", output_file_path)

print("Translation completed and saved to:", output_file_path)
print("Refine completed and saved to:", refined_file_path)
print("Company names saved to:", company_file_path)
print("Trading partner names saved to:", trading_partner_file_path)
print("Cost center names saved to:", cost_center_file_path)
