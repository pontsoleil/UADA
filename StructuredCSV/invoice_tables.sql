-- Buyer table
CREATE TABLE Buyer (
    ID VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    taxID VARCHAR(30),
    address TEXT NOT NULL
);

-- Seller table
CREATE TABLE Seller (
    ID VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    taxID VARCHAR(30),
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
