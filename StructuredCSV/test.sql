-- Buyer table
CREATE TABLE Buyer (
    ID VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    taxID VARCHAR(13),
    address TEXT NOT NULL
);

-- Seller table
CREATE TABLE Seller (
    ID VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    taxID VARCHAR(13),
    address TEXT NOT NULL
);

-- Item table
CREATE TABLE Item (
    ID VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    baseQuantity DECIMAL(10,3) NOT NULL,
    uom VARCHAR(10) NOT NULL
);

-- Invoice table
CREATE TABLE Invoice (
    ID VARCHAR(20) PRIMARY KEY,
    issueDate DATE NOT NULL,
    typeCode VARCHAR(10) NOT NULL,
    dueDate DATE NOT NULL,
    buyerID VARCHAR(20) NOT NULL,
    sellerID VARCHAR(20) NOT NULL,
    sumOfLineNetAmount DECIMAL(10,2) NOT NULL,
    totalAmountWithoutTax DECIMAL(10,2) NOT NULL,
    totalTaxAmount DECIMAL(10,2) NOT NULL,
    totalAmountWithTax DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (buyerID) REFERENCES Buyer(ID),
    FOREIGN KEY (sellerID) REFERENCES Seller(ID)
);

-- InvoiceLine table
CREATE TABLE InvoiceLine (
    ID VARCHAR(20) PRIMARY KEY,
    invoiceID VARCHAR(20) NOT NULL,
    netAmount DECIMAL(10,2) NOT NULL,
    itemID VARCHAR(20) NOT NULL,
    quantity DECIMAL(10,3) NOT NULL,
    uom VARCHAR(10) NOT NULL,
    FOREIGN KEY (invoiceID) REFERENCES Invoice(ID),
    FOREIGN KEY (itemID) REFERENCES Item(ID)
);

-- TaxBreakdown table
CREATE TABLE TaxBreakdown (
    invoiceID VARCHAR(20) NOT NULL,
    taxCategoryCode VARCHAR(20) NOT NULL,
    taxCategoryRate DECIMAL(5,2) NOT NULL,
    taxCategoryTaxableAmount DECIMAL(10,2) NOT NULL,
    taxCategoryTaxAmount DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (invoiceID) REFERENCES Invoice(ID)
);

INSERT INTO Buyer (
    ID, name, taxID, address
)
VALUES
    ('B001', '山田商事株式会社', 'T012345678901', '東京都港区');

INSERT INTO Buyer (
    ID, name, address
)
VALUES
    ('B002', 'Greenwood High School', '456 School Rd, NY');

INSERT INTO Seller (
    ID, name, taxID, address
)
VALUES
    ('S001', '佐藤製作所', 'T098765432109', '大阪市中央区'),
    ('S002', 'Liberty Office Supply', 'T765432109876', '123 Main St, New York, NY');

INSERT INTO Item (
    ID, name, price, baseQuantity, uom, taxCategoryCode, taxCategoryRate
)
VALUES
    ('1001', 'オフィスチェア', 15000, 1, 'EA', 'S', 0.10),
    ('2001', 'ミネラルウォーター', 1200, 1, 'BOX', 'AA', 0.08),
    ('A001', 'Notebook', 500, 1, 'EA', 'S', 0.10),
    ('A002', 'Ballpoint Pen', 120, 1, 'EA', 'S', 0.10);

INSERT INTO Invoice (
    ID, issueDate, typeCode, dueDate,
    buyerID, sellerID,
    sumOfLineNetAmount, totalAmountWithoutTax, totalTaxAmount, totalAmountWithTax
)
VALUES
    ('INV001', '2024-06-30', '380', '2024-07-15', 'B001', 'S001', 16200, 16200, 246, 18446),
    ('INV002', '2024-07-01', '380', '2024-07-15', 'B002', 'S002', 620, 620, 62, 682);

INSERT INTO TaxBreakdown (
    invoiceID, taxCategoryCode, taxCategoryRate,
    taxCategoryTaxableAmount, taxCategoryTaxAmount
)
VALUES
    ('INV001', 'S', 0.10, 15000, 150),
    ('INV001', 'AA', 0.08, 1200, 96),
    ('INV002', 'S', 0.10, 620, 62);

INSERT INTO InvoiceLine (
    ID, invoiceID, netAmount, itemID, quantity, uom
)
VALUES
    ('L001', 'INV001', 15000, '1001', 1, 'EA'),
    ('L002', 'INV001', 1200, '2001', 1, 'BOX'),
    ('L003', 'INV002', 500, 'A001', 1, 'EA'),
    ('L004', 'INV002', 120, 'A002', 1, 'EA');

-- 1. 請求書ヘッダ + 買い手 + 売り手
SELECT
  1 AS dInvoice,
  '' AS dTaxBreakdown,
  '' AS dInvoiceLine,
  IFNULL(i.ID, '') AS `Invoice.ID`,
  IFNULL(i.issueDate, '') AS issueDate,
  IFNULL(i.typeCode, '') AS typeCode,
  IFNULL(i.dueDate, '') AS dueDate,
  IFNULL(b.name, '') AS `Buyer.name`,
  IFNULL(s.name, '') AS `Seller.name`,
  IFNULL(s.taxID, '') AS `Seller.taxID`,
  IFNULL(i.sumOfLineNetAmount, '') AS sumOfLineNetAmount,
  IFNULL(i.totalAmountWithoutTax, '') AS totalAmountWithoutTax,
  IFNULL(i.totalTaxAmount, '') AS totalTaxAmount,
  IFNULL(i.totalAmountWithTax, '') AS totalAmountWithTax,
  '' AS `TaxBreakdown.taxCategoryCode`,
  '' AS `TaxBreakdown.taxCategoryRate`,
  '' AS `TaxBreakdown.taxCategoryTaxAmount`,
  '' AS `InvoiceLine.ID`,
  '' AS `InvoiceLine.netAmount`,
  '' AS `InvoiceLine.quantity`,
  '' AS `InvoiceLine.uom`,
  '' AS `Item.ID`,
  '' AS `Item.name`,
  '' AS `Item.price`,
  '' AS `Item.baseQuantity`,
  '' AS `Item.uom`,
  '' AS `Item.taxCategoryCode`,
  '' AS `Item.taxCategoryRate`
FROM Invoice i
JOIN Buyer b ON i.buyerID = b.ID
JOIN Seller s ON i.sellerID = s.ID
WHERE i.ID = 'INV001'
-- 2. 税区分内訳
UNION ALL
SELECT
  1 AS dInvoice,
  ROW_NUMBER() OVER () AS dTaxBreakdown,
  '' AS dInvoiceLine,
  '' AS `Invoice.ID`,
  '', '', '', '', '', '', '', '', '', '',
  IFNULL(tb.taxCategoryCode, '') AS `TaxBreakdown.taxCategoryCode`,
  IFNULL(tb.taxCategoryRate, '') AS `TaxBreakdown.taxCategoryRate`,
  IFNULL(tb.taxCategoryTaxAmount, '') AS `TaxBreakdown.taxCategoryTaxAmount`,
  '', '', '', '',
  '', '', '', '', '', '', ''
FROM TaxBreakdown tb
WHERE tb.invoiceID = 'INV001'
-- 3. 明細行 + 商品
UNION ALL
SELECT
  1 AS dInvoice,
  '' AS dTaxBreakdown,
  ROW_NUMBER() OVER () AS dInvoiceLine,
  '' AS `Invoice.ID`,
  '', '', '', '', '', '', '', '', '', '', '', '', '',
  IFNULL(il.ID, '') AS `InvoiceLine.ID`,
  IFNULL(il.netAmount, '') AS `InvoiceLine.netAmount`,
  IFNULL(il.quantity, '') AS `InvoiceLine.quantity`,
  IFNULL(il.uom, '') AS `InvoiceLine.uom`,
  IFNULL(it.ID, '') AS `Item.ID`,
  IFNULL(it.name, '') AS `Item.name`,
  IFNULL(it.price, '') AS `Item.price`,
  IFNULL(it.baseQuantity, '') AS `Item.baseQuantity`,
  IFNULL(it.uom, '') AS `Item.uom`,
  IFNULL(it.taxCategoryCode, '') AS `Item.taxCategoryCode`,
  IFNULL(it.taxCategoryRate, '') AS `Item.taxCategoryRate`
FROM InvoiceLine il
JOIN Item it ON il.itemID = it.ID
WHERE il.invoiceID = 'INV001';

-- 既に定義されていたら削除
DROP TABLE IF EXISTS InvoiceStructuredCSV;

CREATE table InvoiceStructuredCSV AS
-- (1) WITH句で請求書ごとにその順序番号をdInvoiceに割り当てる
WITH InvoiceIndex AS (
  SELECT
    ID AS invoiceID,
    ROW_NUMBER() OVER (ORDER BY ID) AS dInvoice
  FROM Invoice
)
-- (2) ヘッダ行を抽出（dInvoice のみ設定）
SELECT
  ii.dInvoice,
  '' AS dTaxBreakdown,
  '' AS dInvoiceLine,
  IFNULL(i.ID, '') AS `Invoice.ID`,
  IFNULL(i.issueDate, '') AS issueDate,
  IFNULL(i.typeCode, '') AS typeCode,
  IFNULL(i.dueDate, '') AS dueDate,
  IFNULL(b.name, '') AS `Buyer.name`,
  IFNULL(s.name, '') AS `Seller.name`,
  IFNULL(s.taxID, '') AS `Seller.taxID`,
  IFNULL(i.sumOfLineNetAmount, '') AS sumOfLineNetAmount,
  IFNULL(i.totalAmountWithoutTax, '') AS totalAmountWithoutTax,
  IFNULL(i.totalTaxAmount, '') AS totalTaxAmount,
  IFNULL(i.totalAmountWithTax, '') AS totalAmountWithTax,
  '' AS `TaxBreakdown.taxCategoryCode`,
  '' AS `TaxBreakdown.taxCategoryRate`,
  '' AS `TaxBreakdown.taxCategoryTaxAmount`,
  '' AS `InvoiceLine.ID`,
  '' AS `InvoiceLine.netAmount`,
  '' AS `InvoiceLine.quantity`,
  '' AS `InvoiceLine.uom`,
  '' AS `Item.ID`,
  '' AS `Item.name`,
  '' AS `Item.price`,
  '' AS `Item.baseQuantity`,
  '' AS `Item.uom`,
  '' AS `Item.taxCategoryCode`,
  '' AS `Item.taxCategoryRate`
FROM Invoice i
JOIN InvoiceIndex ii ON i.ID = ii.invoiceID
JOIN Buyer b ON i.buyerID = b.ID
JOIN Seller s ON i.sellerID = s.ID
-- (3) 税内訳を抽出（dTaxBreakdown のみ設定）
UNION ALL
SELECT
  ii.dInvoice,
  ROW_NUMBER() OVER (PARTITION BY tb.invoiceID ORDER BY tb.taxCategoryCode) AS dTaxBreakdown,
  '' AS dInvoiceLine,
  '', '', '', '', '', '', '', '', '', '', '',
  IFNULL(tb.taxCategoryCode, '') AS `TaxBreakdown.taxCategoryCode`,
  IFNULL(tb.taxCategoryRate, '') AS `TaxBreakdown.taxCategoryRate`,
  IFNULL(tb.taxCategoryTaxAmount, '') AS `TaxBreakdown.taxCategoryTaxAmount`,
  '', '', '', '',
  '', '', '', '', '', '', ''
FROM TaxBreakdown tb
JOIN InvoiceIndex ii ON tb.invoiceID = ii.invoiceID
-- (4) 明細＋商品情報を抽出（dInvoiceLine のみ設定）
UNION ALL
SELECT
  ii.dInvoice,
  '' AS dTaxBreakdown,
  ROW_NUMBER() OVER (PARTITION BY il.invoiceID ORDER BY il.ID) AS dInvoiceLine,
  '', '', '', '', '', '', '', '', '', '', '', '', '', '',
  IFNULL(il.ID, '') AS `InvoiceLine.ID`,
  IFNULL(il.netAmount, '') AS `InvoiceLine.netAmount`,
  IFNULL(il.quantity, '') AS `InvoiceLine.quantity`,
  IFNULL(il.uom, '') AS `InvoiceLine.uom`,
  IFNULL(it.ID, '') AS `Item.ID`,
  IFNULL(it.name, '') AS `Item.name`,
  IFNULL(it.price, '') AS `Item.price`,
  IFNULL(it.baseQuantity, '') AS `Item.baseQuantity`,
  IFNULL(it.uom, '') AS `Item.uom`,
  IFNULL(it.taxCategoryCode, '') AS `Item.taxCategoryCode`,
  IFNULL(it.taxCategoryRate, '') AS `Item.taxCategoryRate`
FROM InvoiceLine il
JOIN InvoiceIndex ii ON il.invoiceID = ii.invoiceID
JOIN Item it ON il.itemID = it.ID
-- (5) ソート：ヘッダ→税内訳→明細
ORDER BY
  dInvoice,
  CASE
    WHEN dTaxBreakdown IS NULL AND dInvoiceLine IS NULL THEN 0
    WHEN dTaxBreakdown IS NOT NULL THEN 1
    WHEN dInvoiceLine IS NOT NULL THEN 2
    ELSE 3
  END,
  dTaxBreakdown,
  dInvoiceLine;

SELECT DISTINCT
  `Invoice.ID` AS ID,
  issueDate,
  typeCode,
  dueDate,
  sumOfLineNetAmount,
  totalAmountWithoutTax,
  totalTaxAmount,
  totalAmountWithTax,
  `Buyer.name`,
  `Seller.name`,
  `Seller.taxID`
FROM InvoiceStructuredCSV
WHERE `Invoice.ID` = 'INV001'
AND dInvoice IS NOT NULL;

SELECT
  d.dInvoice AS invoiceRef,
  d.`TaxBreakdown.taxCategoryCode`,
  d.`TaxBreakdown.taxCategoryRate`,
  d.`TaxBreakdown.taxCategoryTaxAmount`
FROM InvoiceStructuredCSV d
WHERE d.dInvoice = (
  SELECT dInvoice
  FROM InvoiceStructuredCSV
  WHERE `Invoice.ID` = 'INV001'
  AND dInvoice IS NOT NULL
)
AND d.dTaxBreakdown IS NOT NULL;

SELECT
  d.dInvoice AS invoiceRef,
  d.`InvoiceLine.ID`,
  d.`InvoiceLine.netAmount`,
  d.`InvoiceLine.quantity`,
  d.`InvoiceLine.uom`,
  d.`Item.ID`,
  d.`Item.name`,
  d.`Item.price`,
  d.`Item.baseQuantity`,
  d.`Item.uom`,
  d.`Item.taxCategoryCode`,
  d.`Item.taxCategoryRate`
FROM InvoiceStructuredCSV d
WHERE d.dInvoice = (
  SELECT dInvoice
  FROM InvoiceStructuredCSV
  WHERE `Invoice.ID` = 'INV001'
  AND dInvoice IS NOT NULL
)
AND d.dInvoiceLine IS NOT NULL;

SELECT
  IFNULL(dInvoice, '') AS dInvoice,
  IFNULL(dTaxBreakdown, '') AS dTaxBreakdown,
  IFNULL(dInvoiceLine, '') AS dInvoiceLine,
  IFNULL(`Invoice.ID`, '') AS `Invoice.ID`,
  IFNULL(issueDate, '') AS issueDate,
  IFNULL(typeCode, '') AS typeCode,
  IFNULL(dueDate, '') AS dueDate,
  IFNULL(`Buyer.name`, '') AS `Buyer.name`,
  IFNULL(`Seller.name`, '') AS `Seller.name`,
  IFNULL(`Seller.taxID`, '') AS `Seller.taxID`,
  IFNULL(sumOfLineNetAmount, '') AS sumOfLineNetAmount,
  IFNULL(totalAmountWithoutTax, '') AS totalAmountWithoutTax,
  IFNULL(totalTaxAmount, '') AS totalTaxAmount,
  IFNULL(totalAmountWithTax, '') AS totalAmountWithTax,
  IFNULL(`TaxBreakdown.taxCategoryCode`, '') AS `TaxBreakdown.taxCategoryCode`,
  IFNULL(`TaxBreakdown.taxCategoryRate`, '') AS `TaxBreakdown.taxCategoryRate`,
  IFNULL(`TaxBreakdown.taxCategoryTaxAmount`, '') AS `TaxBreakdown.taxCategoryTaxAmount`,
  IFNULL(`InvoiceLine.ID`, '') AS `InvoiceLine.ID`,
  IFNULL(`InvoiceLine.netAmount`, '') AS `InvoiceLine.netAmount`,
  IFNULL(`InvoiceLine.quantity`, '') AS `InvoiceLine.quantity`,
  IFNULL(`InvoiceLine.uom`, '') AS `InvoiceLine.uom`,
  IFNULL(`Item.ID`, '') AS `Item.ID`,
  IFNULL(`Item.name`, '') AS `Item.name`,
  IFNULL(`Item.price`, '') AS `Item.price`,
  IFNULL(`Item.baseQuantity`, '') AS `Item.baseQuantity`,
  IFNULL(`Item.uom`, '') AS `Item.uom`,
  IFNULL(`Item.taxCategoryCode`, '') AS `Item.taxCategoryCode`,
  IFNULL(`Item.taxCategoryRate`, '') AS `Item.taxCategoryRate`
FROM InvoiceStructuredCSV;
