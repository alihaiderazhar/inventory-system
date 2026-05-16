import pymysql

conn = pymysql.connect(
    host='turntable.proxy.rlwy.net',
    user='root',
    password='cvxLLyijdJFTcOyXoZFyRwsjOjuOjQbT',
    port=40417,
    database='railway'
)
cursor = conn.cursor()

statements = [
    # Tables
    """CREATE TABLE IF NOT EXISTS Category (
        CategoryID INT AUTO_INCREMENT PRIMARY KEY,
        CategoryName VARCHAR(100) NOT NULL UNIQUE,
        Description VARCHAR(255)
    )""",

    """CREATE TABLE IF NOT EXISTS Supplier (
        SupplierID INT AUTO_INCREMENT PRIMARY KEY,
        SupplierName VARCHAR(100) NOT NULL,
        ContactEmail VARCHAR(100) NOT NULL UNIQUE,
        Phone VARCHAR(20),
        City VARCHAR(50),
        Rating DECIMAL(3,1) DEFAULT 5.0
    )""",

    """CREATE TABLE IF NOT EXISTS Warehouse (
        WarehouseID INT AUTO_INCREMENT PRIMARY KEY,
        WarehouseName VARCHAR(100) NOT NULL UNIQUE,
        Location VARCHAR(100) NOT NULL,
        Capacity INT NOT NULL
    )""",

    """CREATE TABLE IF NOT EXISTS Product (
        ProductID INT AUTO_INCREMENT PRIMARY KEY,
        ProductName VARCHAR(150) NOT NULL,
        CategoryID INT NOT NULL,
        SupplierID INT NOT NULL,
        UnitPrice DECIMAL(10,2) NOT NULL,
        ReorderLevel INT NOT NULL DEFAULT 50,
        LeadTimeDays INT DEFAULT 7,
        FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID),
        FOREIGN KEY (SupplierID) REFERENCES Supplier(SupplierID)
    )""",

    """CREATE TABLE IF NOT EXISTS InventoryStock (
        StockID INT AUTO_INCREMENT PRIMARY KEY,
        ProductID INT NOT NULL,
        WarehouseID INT NOT NULL,
        QuantityOnHand INT NOT NULL DEFAULT 0,
        LastUpdated DATE NOT NULL DEFAULT (CURRENT_DATE),
        UNIQUE KEY UQ_Stock (ProductID, WarehouseID),
        FOREIGN KEY (ProductID) REFERENCES Product(ProductID),
        FOREIGN KEY (WarehouseID) REFERENCES Warehouse(WarehouseID)
    )""",

    """CREATE TABLE IF NOT EXISTS SalesOrder (
        OrderID INT AUTO_INCREMENT PRIMARY KEY,
        CustomerName VARCHAR(100) NOT NULL,
        OrderDate DATE NOT NULL DEFAULT (CURRENT_DATE),
        Status VARCHAR(20) NOT NULL DEFAULT 'Pending',
        TotalAmount DECIMAL(12,2),
        CONSTRAINT CK_Order_Status CHECK (Status IN ('Pending','Confirmed','Shipped','Cancelled'))
    )""",

    """CREATE TABLE IF NOT EXISTS OrderDetail (
        DetailID INT AUTO_INCREMENT PRIMARY KEY,
        OrderID INT NOT NULL,
        ProductID INT NOT NULL,
        Quantity INT NOT NULL,
        SalePrice DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (OrderID) REFERENCES SalesOrder(OrderID),
        FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
    )""",

    # Views
    """CREATE OR REPLACE VIEW vw_StockSummary AS
    SELECT p.ProductID, p.ProductName, c.CategoryName,
           w.WarehouseName, w.Location,
           s.QuantityOnHand, p.ReorderLevel,
           CASE WHEN s.QuantityOnHand <= p.ReorderLevel
                THEN 'Reorder Required' ELSE 'Sufficient' END AS StockStatus,
           s.LastUpdated
    FROM InventoryStock s
    JOIN Product p ON s.ProductID = p.ProductID
    JOIN Category c ON p.CategoryID = c.CategoryID
    JOIN Warehouse w ON s.WarehouseID = w.WarehouseID""",

    """CREATE OR REPLACE VIEW vw_ProductRevenue AS
    SELECT p.ProductID, p.ProductName, c.CategoryName,
           COUNT(od.DetailID) AS TotalOrderLines,
           SUM(od.Quantity) AS TotalUnitsSold,
           SUM(od.Quantity * od.SalePrice) AS TotalRevenue,
           AVG(od.SalePrice) AS AvgSellingPrice
    FROM OrderDetail od
    JOIN Product p ON od.ProductID = p.ProductID
    JOIN Category c ON p.CategoryID = c.CategoryID
    GROUP BY p.ProductID, p.ProductName, c.CategoryName""",

    # Data - Category
    "INSERT IGNORE INTO Category (CategoryID, CategoryName, Description) VALUES (1, 'Electronics', 'Electronic gadgets and components')",
    "INSERT IGNORE INTO Category (CategoryID, CategoryName, Description) VALUES (2, 'Grocery', 'Food and daily use items')",
    "INSERT IGNORE INTO Category (CategoryID, CategoryName, Description) VALUES (3, 'Apparel', 'Clothing and fashion items')",
    "INSERT IGNORE INTO Category (CategoryID, CategoryName, Description) VALUES (4, 'Furniture', 'Home and office furniture')",
    "INSERT IGNORE INTO Category (CategoryID, CategoryName, Description) VALUES (5, 'Pharmaceuticals', 'Medicines and health products')",

    # Data - Supplier
    "INSERT IGNORE INTO Supplier (SupplierID, SupplierName, ContactEmail, Phone, City, Rating) VALUES (1, 'TechMart Pvt Ltd', 'techmart@gmail.com', '0300-1234567', 'Lahore', 4.5)",
    "INSERT IGNORE INTO Supplier (SupplierID, SupplierName, ContactEmail, Phone, City, Rating) VALUES (2, 'GreenGrocer Co.', 'green@grocery.pk', '0301-2345678', 'Karachi', 4.2)",
    "INSERT IGNORE INTO Supplier (SupplierID, SupplierName, ContactEmail, Phone, City, Rating) VALUES (3, 'FashionHub', 'info@fashionhub.pk', '0302-3456789', 'Faisalabad', 4.8)",
    "INSERT IGNORE INTO Supplier (SupplierID, SupplierName, ContactEmail, Phone, City, Rating) VALUES (4, 'Comfort Furniture', 'comfort@furniture.pk', '0303-4567890', 'Islamabad', 3.9)",
    "INSERT IGNORE INTO Supplier (SupplierID, SupplierName, ContactEmail, Phone, City, Rating) VALUES (5, 'MedSupply Pakistan', 'med@supply.pk', '0304-5678901', 'Lahore', 4.6)",

    # Data - Warehouse
    "INSERT IGNORE INTO Warehouse (WarehouseID, WarehouseName, Location, Capacity) VALUES (1, 'Central Warehouse', 'Lahore Industrial Zone', 50000)",
    "INSERT IGNORE INTO Warehouse (WarehouseID, WarehouseName, Location, Capacity) VALUES (2, 'North Hub', 'Islamabad Logistic Park', 30000)",
    "INSERT IGNORE INTO Warehouse (WarehouseID, WarehouseName, Location, Capacity) VALUES (3, 'South Depot', 'Karachi Port Area', 40000)",

    # Data - Product
    "INSERT IGNORE INTO Product (ProductID, ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES (1, 'Samsung 4K TV 55\"', 1, 1, 85000.00, 10, 14)",
    "INSERT IGNORE INTO Product (ProductID, ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES (2, 'Wireless Keyboard', 1, 1, 2500.00, 30, 7)",
    "INSERT IGNORE INTO Product (ProductID, ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES (3, 'USB-C Hub 7-Port', 1, 1, 1800.00, 40, 5)",
    "INSERT IGNORE INTO Product (ProductID, ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES (4, 'Basmati Rice 25kg', 2, 2, 3200.00, 100, 3)",
    "INSERT IGNORE INTO Product (ProductID, ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES (5, 'Cooking Oil 5L', 2, 2, 850.00, 150, 3)",
    "INSERT IGNORE INTO Product (ProductID, ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES (6, 'Mineral Water 1L x24', 2, 2, 480.00, 200, 2)",
    "INSERT IGNORE INTO Product (ProductID, ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES (7, 'Men Shalwar Kameez', 3, 3, 1200.00, 60, 7)",
    "INSERT IGNORE INTO Product (ProductID, ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES (8, 'Women Kurti', 3, 3, 950.00, 80, 7)",
    "INSERT IGNORE INTO Product (ProductID, ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES (9, 'Kids School Uniform', 3, 3, 700.00, 50, 5)",
    "INSERT IGNORE INTO Product (ProductID, ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES (10, 'Office Chair Executive', 4, 4, 12000.00, 15, 21)",
    "INSERT IGNORE INTO Product (ProductID, ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES (11, 'Study Table 4ft', 4, 4, 8500.00, 10, 21)",
    "INSERT IGNORE INTO Product (ProductID, ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES (12, 'Panadol CF 10s', 5, 5, 120.00, 300, 3)",
    "INSERT IGNORE INTO Product (ProductID, ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES (13, 'ORS Sachets x10', 5, 5, 85.00, 250, 3)",
    "INSERT IGNORE INTO Product (ProductID, ProductName, CategoryID, SupplierID, UnitPrice, ReorderLevel, LeadTimeDays) VALUES (14, 'Vitamin C 500mg x30', 5, 5, 350.00, 200, 5)",

    # Data - SalesOrder
    "INSERT IGNORE INTO SalesOrder (OrderID, CustomerName, OrderDate, Status, TotalAmount) VALUES (1, 'Ahmed Traders', '2025-01-10', 'Shipped', 96800.00)",
    "INSERT IGNORE INTO SalesOrder (OrderID, CustomerName, OrderDate, Status, TotalAmount) VALUES (2, 'Bilal Enterprises', '2025-01-18', 'Shipped', 18500.00)",
    "INSERT IGNORE INTO SalesOrder (OrderID, CustomerName, OrderDate, Status, TotalAmount) VALUES (3, 'Chaudhry Store', '2025-02-05', 'Shipped', 42000.00)",
    "INSERT IGNORE INTO SalesOrder (OrderID, CustomerName, OrderDate, Status, TotalAmount) VALUES (4, 'Dawood Retail', '2025-02-20', 'Confirmed', 12750.00)",
    "INSERT IGNORE INTO SalesOrder (OrderID, CustomerName, OrderDate, Status, TotalAmount) VALUES (5, 'Ehsan Medical', '2025-03-01', 'Shipped', 8400.00)",
    "INSERT IGNORE INTO SalesOrder (OrderID, CustomerName, OrderDate, Status, TotalAmount) VALUES (6, 'Farhan Grocers', '2025-03-15', 'Shipped', 25600.00)",
    "INSERT IGNORE INTO SalesOrder (OrderID, CustomerName, OrderDate, Status, TotalAmount) VALUES (7, 'Gulzar Fashion', '2025-03-22', 'Pending', 14250.00)",
    "INSERT IGNORE INTO SalesOrder (OrderID, CustomerName, OrderDate, Status, TotalAmount) VALUES (8, 'Hamid Electronics', '2025-04-02', 'Confirmed', 17300.00)",
    "INSERT IGNORE INTO SalesOrder (OrderID, CustomerName, OrderDate, Status, TotalAmount) VALUES (9, 'Imran Office Needs', '2025-04-10', 'Shipped', 20500.00)",
    "INSERT IGNORE INTO SalesOrder (OrderID, CustomerName, OrderDate, Status, TotalAmount) VALUES (10, 'Javed General Store', '2025-04-18', 'Pending', 5400.00)",

    # Data - OrderDetail
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (1, 1, 1, 1, 85000.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (2, 1, 2, 3, 2500.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (3, 1, 3, 2, 1800.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (4, 2, 7, 5, 1200.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (5, 2, 8, 8, 950.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (6, 2, 9, 5, 700.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (7, 3, 4, 10, 3200.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (8, 3, 5, 12, 850.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (9, 4, 12, 50, 120.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (10, 4, 13, 30, 85.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (11, 4, 14, 15, 350.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (12, 5, 12, 40, 120.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (13, 5, 13, 50, 85.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (14, 6, 4, 5, 3200.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (15, 6, 5, 10, 850.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (16, 6, 6, 20, 480.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (17, 7, 7, 8, 1200.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (18, 7, 8, 5, 950.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (19, 8, 2, 4, 2500.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (20, 8, 3, 6, 1800.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (21, 9, 10, 1, 12000.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (22, 9, 11, 1, 8500.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (23, 10, 12, 20, 120.00)",
    "INSERT IGNORE INTO OrderDetail (DetailID, OrderID, ProductID, Quantity, SalePrice) VALUES (24, 10, 14, 10, 350.00)",

    # InventoryStock
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (1, 1, 1, 25, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (2, 2, 1, 120, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (3, 3, 1, 200, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (4, 4, 1, 500, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (5, 5, 1, 600, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (6, 6, 1, 800, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (7, 7, 1, 300, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (8, 8, 1, 250, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (9, 9, 1, 180, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (10, 10, 1, 20, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (11, 11, 1, 15, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (12, 12, 1, 1200, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (13, 13, 1, 900, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (14, 14, 1, 700, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (15, 1, 2, 8, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (16, 4, 2, 300, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (17, 7, 2, 150, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (18, 10, 2, 12, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (19, 12, 2, 600, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (20, 2, 3, 80, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (21, 5, 3, 400, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (22, 8, 3, 200, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (23, 11, 3, 8, '2025-04-01')",
    "INSERT IGNORE INTO InventoryStock (StockID, ProductID, WarehouseID, QuantityOnHand, LastUpdated) VALUES (24, 13, 3, 500, '2025-04-01')",
]

for stmt in statements:
    try:
        cursor.execute(stmt)
    except Exception as e:
        print(f"Error: {e}")

conn.commit()
print("✅ Database import complete!")
conn.close()