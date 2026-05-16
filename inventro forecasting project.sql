--  DEMAND FORECASTING & INVENTORY CONTROL SYSTEM

CREATE DATABASE InventoryDB;
GO
USE InventoryDB;
GO

CREATE TABLE Category (
    CategoryID   INT           PRIMARY KEY IDENTITY(1,1),
    CategoryName VARCHAR(100)  NOT NULL UNIQUE,
    Description  VARCHAR(255)
);

CREATE TABLE Supplier (
    SupplierID   INT           PRIMARY KEY IDENTITY(1,1),
    SupplierName VARCHAR(100)  NOT NULL,
    ContactEmail VARCHAR(100)  NOT NULL UNIQUE,
    Phone        VARCHAR(20),
    City         VARCHAR(50)
);

CREATE TABLE Product (
    ProductID    INT            PRIMARY KEY IDENTITY(1,1),
    ProductName  VARCHAR(150)   NOT NULL,
    CategoryID   INT            NOT NULL,
    SupplierID   INT            NOT NULL,
    UnitPrice    DECIMAL(10,2)  NOT NULL,
    ReorderLevel INT            NOT NULL DEFAULT 50,
    CONSTRAINT FK_Product_Category FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID),
    CONSTRAINT FK_Product_Supplier FOREIGN KEY (SupplierID) REFERENCES Supplier(SupplierID)
);

CREATE TABLE Warehouse (
    WarehouseID   INT           PRIMARY KEY IDENTITY(1,1),
    WarehouseName VARCHAR(100)  NOT NULL UNIQUE,
    Location      VARCHAR(100)  NOT NULL,
    Capacity      INT           NOT NULL
);

CREATE TABLE InventoryStock (
    StockID        INT  PRIMARY KEY IDENTITY(1,1),
    ProductID      INT  NOT NULL,
    WarehouseID    INT  NOT NULL,
    QuantityOnHand INT  NOT NULL DEFAULT 0,
    LastUpdated    DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    CONSTRAINT FK_Stock_Product   FOREIGN KEY (ProductID)   REFERENCES Product(ProductID),
    CONSTRAINT FK_Stock_Warehouse FOREIGN KEY (WarehouseID) REFERENCES Warehouse(WarehouseID),
    CONSTRAINT UQ_Stock UNIQUE (ProductID, WarehouseID)
);

CREATE TABLE SalesOrder (
    OrderID      INT           PRIMARY KEY IDENTITY(1,1),
    CustomerName VARCHAR(100)  NOT NULL,
    OrderDate    DATE          NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    Status       VARCHAR(20)   NOT NULL DEFAULT 'Pending',
    TotalAmount  DECIMAL(12,2),
    CONSTRAINT CK_Order_Status CHECK (Status IN ('Pending','Confirmed','Shipped','Cancelled'))
);

CREATE TABLE OrderDetail (
    DetailID   INT            PRIMARY KEY IDENTITY(1,1),
    OrderID    INT            NOT NULL,
    ProductID  INT            NOT NULL,
    Quantity   INT            NOT NULL,
    SalePrice  DECIMAL(10,2)  NOT NULL,
    CONSTRAINT FK_Detail_Order   FOREIGN KEY (OrderID)   REFERENCES SalesOrder(OrderID),
    CONSTRAINT FK_Detail_Product FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
);

--  SCHEMA EVOLUTION — ALTER TABLE

ALTER TABLE Product  ADD LeadTimeDays INT DEFAULT 7;
ALTER TABLE Supplier ADD Rating DECIMAL(3,1) DEFAULT 5.0;
GO

--  INDEXES — Performance Optimization
CREATE INDEX IX_Product_Name    ON Product(ProductName);
CREATE INDEX IX_Stock_ProductID ON InventoryStock(ProductID);
CREATE INDEX IX_Order_Date      ON SalesOrder(OrderDate);
CREATE INDEX IX_Detail_OrderID  ON OrderDetail(OrderID);
GO

--  VIEWS — Data Abstraction

-- VIEW 1: Stock summary with reorder status
CREATE VIEW vw_StockSummary AS
SELECT
    p.ProductID, p.ProductName, c.CategoryName,
    w.WarehouseName, w.Location,
    s.QuantityOnHand, p.ReorderLevel,
    CASE WHEN s.QuantityOnHand <= p.ReorderLevel
         THEN 'Reorder Required' ELSE 'Sufficient' END AS StockStatus,
    s.LastUpdated
FROM InventoryStock s
JOIN Product   p ON s.ProductID   = p.ProductID
JOIN Category  c ON p.CategoryID  = c.CategoryID
JOIN Warehouse w ON s.WarehouseID = w.WarehouseID;
GO

-- VIEW 2: Product revenue summary
CREATE VIEW vw_ProductRevenue AS
SELECT
    p.ProductID, p.ProductName, c.CategoryName,
    COUNT(od.DetailID)              AS TotalOrderLines,
    SUM(od.Quantity)                AS TotalUnitsSold,
    SUM(od.Quantity * od.SalePrice) AS TotalRevenue,
    AVG(od.SalePrice)               AS AvgSellingPrice
FROM OrderDetail od
JOIN Product  p ON od.ProductID = p.ProductID
JOIN Category c ON p.CategoryID = c.CategoryID
GROUP BY p.ProductID, p.ProductName, c.CategoryName;
GO

--  DML — SAMPLE DATA

INSERT INTO Category (CategoryName, Description) VALUES
('Electronics',    'Electronic gadgets and components'),
('Grocery',        'Food and daily use items'),
('Apparel',        'Clothing and fashion items'),
('Furniture',      'Home and office furniture'),
('Pharmaceuticals','Medicines and health products');

INSERT INTO Supplier (SupplierName, ContactEmail, Phone, City, Rating) VALUES
('TechMart Pvt Ltd',   'techmart@gmail.com',   '0300-1234567', 'Lahore',     4.5),
('GreenGrocer Co.',    'green@grocery.pk',     '0301-2345678', 'Karachi',    4.2),
('FashionHub',         'info@fashionhub.pk',   '0302-3456789', 'Faisalabad', 4.8),
('Comfort Furniture',  'comfort@furniture.pk', '0303-4567890', 'Islamabad',  3.9),
('MedSupply Pakistan', 'med@supply.pk',        '0304-5678901', 'Lahore',     4.6);

INSERT INTO Product (ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES
('Samsung 4K TV 55"',      1, 1, 85000, 10, 14),
('Wireless Keyboard',      1, 1,  2500, 30,  7),
('USB-C Hub 7-Port',       1, 1,  1800, 40,  5),
('Basmati Rice 25kg',      2, 2,  3200,100,  3),
('Cooking Oil 5L',         2, 2,   850,150,  3),
('Mineral Water 1L x24',   2, 2,   480,200,  2),
('Men Shalwar Kameez',     3, 3,  1200, 60,  7),
('Women Kurti',            3, 3,   950, 80,  7),
('Kids School Uniform',    3, 3,   700, 50,  5),
('Office Chair Executive', 4, 4, 12000, 15, 21),
('Study Table 4ft',        4, 4,  8500, 10, 21),
('Panadol CF 10s',         5, 5,   120,300,  3),
('ORS Sachets x10',        5, 5,    85,250,  3),
('Vitamin C 500mg x30',    5, 5,   350,200,  5);

INSERT INTO Warehouse (WarehouseName, Location, Capacity) VALUES
('Central Warehouse', 'Lahore Industrial Zone',  50000),
('North Hub',         'Islamabad Logistic Park', 30000),
('South Depot',       'Karachi Port Area',        40000);

INSERT INTO InventoryStock (ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES
(1,1,25,'2025-04-01'),(2,1,120,'2025-04-01'),(3,1,200,'2025-04-01'),
(4,1,500,'2025-04-01'),(5,1,600,'2025-04-01'),(6,1,800,'2025-04-01'),
(7,1,300,'2025-04-01'),(8,1,250,'2025-04-01'),(9,1,180,'2025-04-01'),
(10,1,20,'2025-04-01'),(11,1,15,'2025-04-01'),(12,1,1200,'2025-04-01'),
(13,1,900,'2025-04-01'),(14,1,700,'2025-04-01'),
(1,2,8,'2025-04-01'),(4,2,300,'2025-04-01'),(7,2,150,'2025-04-01'),
(10,2,12,'2025-04-01'),(12,2,600,'2025-04-01'),
(2,3,80,'2025-04-01'),(5,3,400,'2025-04-01'),(8,3,200,'2025-04-01'),
(11,3,8,'2025-04-01'),(13,3,500,'2025-04-01');

INSERT INTO SalesOrder (CustomerName, OrderDate, Status, TotalAmount) VALUES
('Ahmed Traders',       '2025-01-10', 'Shipped',    96800),
('Bilal Enterprises',   '2025-01-18', 'Shipped',    18500),
('Chaudhry Store',      '2025-02-05', 'Shipped',    42000),
('Dawood Retail',       '2025-02-20', 'Confirmed',  12750),
('Ehsan Medical',       '2025-03-01', 'Shipped',     8400),
('Farhan Grocers',      '2025-03-15', 'Shipped',    25600),
('Gulzar Fashion',      '2025-03-22', 'Pending',    14250),
('Hamid Electronics',   '2025-04-02', 'Confirmed',  17300),
('Imran Office Needs',  '2025-04-10', 'Shipped',    20500),
('Javed General Store', '2025-04-18', 'Pending',     5400);

INSERT INTO OrderDetail (OrderID, ProductID, Quantity, SalePrice) VALUES
(1,1,1,85000),(1,2,3,2500),(1,3,2,1800),
(2,7,5,1200),(2,8,8,950),(2,9,5,700),
(3,4,10,3200),(3,5,12,850),
(4,12,50,120),(4,13,30,85),(4,14,15,350),
(5,12,40,120),(5,13,50,85),
(6,4,5,3200),(6,5,10,850),(6,6,20,480),
(7,7,8,1200),(7,8,5,950),
(8,2,4,2500),(8,3,6,1800),
(9,10,1,12000),(9,11,1,8500),
(10,12,20,120),(10,14,10,350);
GO

--  ADVANCED QUERIES — Analytics

-- Q1: MULTI-TABLE JOIN (4 tables) — Stock overview with reorder alert
SELECT
    p.ProductName, c.CategoryName, s.SupplierName, s.City AS SupplierCity,
    SUM(i.QuantityOnHand) AS TotalStock, p.ReorderLevel,
    CASE WHEN SUM(i.QuantityOnHand) <= p.ReorderLevel
         THEN 'REORDER NOW' ELSE 'OK' END AS Alert
FROM Product p
JOIN Category       c ON p.CategoryID  = c.CategoryID
JOIN Supplier       s ON p.SupplierID  = s.SupplierID
JOIN InventoryStock i ON p.ProductID   = i.ProductID
GROUP BY p.ProductName, c.CategoryName, s.SupplierName, s.City, p.ReorderLevel
ORDER BY TotalStock ASC;

-- Q2: GROUP BY + HAVING — Categories with revenue > 10,000
SELECT
    c.CategoryName,
    COUNT(DISTINCT p.ProductID)         AS TotalProducts,
    SUM(od.Quantity)                    AS TotalUnitsSold,
    SUM(od.Quantity * od.SalePrice)     AS TotalRevenue,
    AVG(od.SalePrice)                   AS AvgPrice
FROM OrderDetail od
JOIN Product  p ON od.ProductID  = p.ProductID
JOIN Category c ON p.CategoryID  = c.CategoryID
GROUP BY c.CategoryName
HAVING SUM(od.Quantity * od.SalePrice) > 10000
ORDER BY TotalRevenue DESC;

-- Q3: SUBQUERY IN WHERE — Products below average stock level
SELECT p.ProductName, SUM(i.QuantityOnHand) AS TotalStock, p.ReorderLevel
FROM InventoryStock i
JOIN Product p ON i.ProductID = p.ProductID
GROUP BY p.ProductName, p.ReorderLevel
HAVING SUM(i.QuantityOnHand) < (
    SELECT AVG(TotalQty) FROM (
        SELECT SUM(QuantityOnHand) AS TotalQty
        FROM InventoryStock
        GROUP BY ProductID
    ) AS StockAvg
)
ORDER BY TotalStock ASC;

-- Q4: SUBQUERY IN FROM — Monthly demand summary
SELECT MonthYear, TotalOrders, TotalUnitsSold, TotalRevenue,
    CAST(TotalRevenue / TotalOrders AS DECIMAL(10,2)) AS AvgOrderValue
FROM (
    SELECT
        FORMAT(o.OrderDate, 'yyyy-MM')      AS MonthYear,
        COUNT(DISTINCT o.OrderID)           AS TotalOrders,
        SUM(od.Quantity)                    AS TotalUnitsSold,
        SUM(od.Quantity * od.SalePrice)     AS TotalRevenue
    FROM SalesOrder o
    JOIN OrderDetail od ON o.OrderID = od.OrderID
    WHERE o.Status != 'Cancelled'
    GROUP BY FORMAT(o.OrderDate, 'yyyy-MM')
) AS MonthlySummary
ORDER BY MonthYear;

-- Q5: LIKE + BETWEEN — Product search with filters
SELECT p.ProductName, c.CategoryName, p.UnitPrice, s.SupplierName
FROM Product p
JOIN Category c ON p.CategoryID = c.CategoryID
JOIN Supplier s ON p.SupplierID = s.SupplierID
WHERE p.ProductName LIKE '%a%'
  AND p.UnitPrice BETWEEN 500 AND 5000
ORDER BY p.UnitPrice;

-- Q6: DISTINCT + ORDER BY — Unique supplier cities
SELECT DISTINCT City FROM Supplier ORDER BY City ASC;

-- Q7: VIEW USAGE — Top 5 fastest-moving products
SELECT TOP 5 ProductName, CategoryName, TotalUnitsSold, TotalRevenue
FROM vw_ProductRevenue
ORDER BY TotalUnitsSold DESC;

-- Q8: VIEW USAGE — Reorder alerts
SELECT * FROM vw_StockSummary
WHERE StockStatus = 'Reorder Required'
ORDER BY QuantityOnHand ASC;

GO
PRINT 'All done — Database ready!';