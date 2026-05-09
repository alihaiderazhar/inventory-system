import streamlit as st
import pyodbc
import pandas as pd
import plotly.express as px

@st.cache_resource
def get_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=ALI-HAIDER\\SQLEXPRESS;"
        "DATABASE=InventoryDB;"
        "Trusted_Connection=yes;"
    )
    return conn

def run_query(sql, params=None):
    conn = get_connection()
    if params:
        return pd.read_sql(sql, conn, params=params)
    return pd.read_sql(sql, conn)

def run_write(sql, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params) if params else cursor.execute(sql)
    conn.commit()

st.set_page_config(page_title="Inventory Control", page_icon="📦", layout="wide")

st.sidebar.title("📦 Inventory System")
page = st.sidebar.radio("Navigate", [
    "🏠 Dashboard",
    "📋 Products",
    "🏭 Stock Management",
    "🛒 Sales Orders",
    "📊 BI Analytics",
    "⚠️ Reorder Alerts",
    "➕ Add Records"
])

# ── DASHBOARD ──────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.title("📦 Demand Forecasting & Inventory Control")
    st.markdown("**FAST-NUCES | Intro to DB Lab Project**")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Products",
        run_query("SELECT COUNT(*) AS n FROM Product").iloc[0,0])
    col2.metric("Total Orders",
        run_query("SELECT COUNT(*) AS n FROM SalesOrder").iloc[0,0])
    col3.metric("Total Revenue", "PKR " +
        f"{run_query('SELECT ISNULL(SUM(Quantity*SalePrice),0) AS n FROM OrderDetail').iloc[0,0]:,.0f}")
    col4.metric("Reorder Alerts",
        run_query("SELECT COUNT(*) AS n FROM vw_StockSummary WHERE StockStatus='Reorder Required'").iloc[0,0])

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Revenue by Category")
        df = run_query("""
            SELECT c.CategoryName, SUM(od.Quantity*od.SalePrice) AS Revenue
            FROM OrderDetail od
            JOIN Product p ON od.ProductID=p.ProductID
            JOIN Category c ON p.CategoryID=c.CategoryID
            GROUP BY c.CategoryName
        """)
        st.plotly_chart(px.pie(df, values="Revenue", names="CategoryName"), use_container_width=True)

    with col_b:
        st.subheader("Monthly Sales Trend")
        df2 = run_query("""
            SELECT FORMAT(o.OrderDate,'yyyy-MM') AS Month,
                   SUM(od.Quantity*od.SalePrice) AS Revenue
            FROM SalesOrder o
            JOIN OrderDetail od ON o.OrderID=od.OrderID
            WHERE o.Status != 'Cancelled'
            GROUP BY FORMAT(o.OrderDate,'yyyy-MM')
            ORDER BY Month
        """)
        st.plotly_chart(px.bar(df2, x="Month", y="Revenue"), use_container_width=True)

# ── PRODUCTS ───────────────────────────────────────────────
elif page == "📋 Products":
    st.title("📋 Product Catalogue")
    st.markdown("---")

    search = st.text_input("Search product")
    min_p, max_p = st.slider("Price Range (PKR)", 0, 100000, (0, 100000), step=500)

    df = run_query("""
        SELECT p.ProductName, c.CategoryName, s.SupplierName,
               p.UnitPrice, p.ReorderLevel, p.LeadTimeDays
        FROM Product p
        JOIN Category c ON p.CategoryID=c.CategoryID
        JOIN Supplier s ON p.SupplierID=s.SupplierID
        WHERE p.ProductName LIKE ? AND p.UnitPrice BETWEEN ? AND ?
        ORDER BY p.ProductName
    """, params=(f"%{search}%", min_p, max_p))
    st.dataframe(df, use_container_width=True)
    st.caption(f"{len(df)} products found")

# ── STOCK MANAGEMENT ───────────────────────────────────────
elif page == "🏭 Stock Management":
    st.title("🏭 Inventory Stock")
    st.markdown("---")

    st.dataframe(
        run_query("SELECT * FROM vw_StockSummary ORDER BY QuantityOnHand"),
        use_container_width=True
    )

    st.markdown("---")
    st.subheader("Update Stock Quantity")

    products   = run_query("SELECT ProductID, ProductName FROM Product ORDER BY ProductName")
    warehouses = run_query("SELECT WarehouseID, WarehouseName FROM Warehouse")
    prod_map = dict(zip(products.ProductName, products.ProductID))
    wh_map   = dict(zip(warehouses.WarehouseName, warehouses.WarehouseID))

    c1, c2, c3 = st.columns(3)
    sel_p = c1.selectbox("Product",   list(prod_map.keys()))
    sel_w = c2.selectbox("Warehouse", list(wh_map.keys()))
    qty   = c3.number_input("New Quantity", min_value=0, step=10)

    if st.button("Update", type="primary"):
        run_write("""
            UPDATE InventoryStock
            SET QuantityOnHand=?, LastUpdated=CAST(GETDATE() AS DATE)
            WHERE ProductID=? AND WarehouseID=?
        """, params=(qty, prod_map[sel_p], wh_map[sel_w]))
        st.success("Stock updated!")
        st.rerun()

# ── SALES ORDERS ───────────────────────────────────────────
elif page == "🛒 Sales Orders":
    st.title("🛒 Sales Orders")
    st.markdown("---")

    df = run_query("""
        SELECT o.OrderID, o.CustomerName, o.OrderDate, o.Status,
               COUNT(od.DetailID) AS Items,
               SUM(od.Quantity*od.SalePrice) AS OrderValue
        FROM SalesOrder o
        JOIN OrderDetail od ON o.OrderID=od.OrderID
        GROUP BY o.OrderID, o.CustomerName, o.OrderDate, o.Status
        ORDER BY o.OrderDate DESC
    """)
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("View Order Details")
    oid = st.number_input("Enter Order ID", min_value=1, step=1, value=1)
    df2 = run_query("""
        SELECT p.ProductName, od.Quantity, od.SalePrice,
               od.Quantity*od.SalePrice AS LineTotal
        FROM OrderDetail od
        JOIN Product p ON od.ProductID=p.ProductID
        WHERE od.OrderID=?
    """, params=(int(oid),))
    st.dataframe(df2, use_container_width=True)
    if not df2.empty:
        st.info(f"Order Total: PKR {df2.LineTotal.sum():,.2f}")

# ── BI ANALYTICS ───────────────────────────────────────────
elif page == "📊 BI Analytics":
    st.title("📊 Business Intelligence Dashboard")
    st.markdown("---")

    t1, t2, t3 = st.tabs(["Category Revenue", "Top Products", "Monthly Demand"])

    with t1:
        st.subheader("Category Revenue (GROUP BY + HAVING)")
        df = run_query("""
            SELECT c.CategoryName,
                   COUNT(DISTINCT p.ProductID)       AS Products,
                   SUM(od.Quantity)                  AS UnitsSold,
                   SUM(od.Quantity*od.SalePrice)     AS Revenue
            FROM OrderDetail od
            JOIN Product p ON od.ProductID=p.ProductID
            JOIN Category c ON p.CategoryID=c.CategoryID
            GROUP BY c.CategoryName
            HAVING SUM(od.Quantity*od.SalePrice) > 0
            ORDER BY Revenue DESC
        """)
        st.dataframe(df, use_container_width=True)
        st.plotly_chart(
            px.bar(df, x="CategoryName", y="Revenue", color="CategoryName"),
            use_container_width=True
        )

    with t2:
        st.subheader("Top 5 Fastest-Moving Products")
        df = run_query("""
            SELECT TOP 5 ProductName, CategoryName, TotalUnitsSold, TotalRevenue
            FROM vw_ProductRevenue
            ORDER BY TotalUnitsSold DESC
        """)
        st.dataframe(df, use_container_width=True)
        st.plotly_chart(
            px.bar(df, x="ProductName", y="TotalUnitsSold",
                   color_discrete_sequence=["#16A34A"]),
            use_container_width=True
        )

    with t3:
        st.subheader("Monthly Demand Trend (Subquery in FROM)")
        df = run_query("""
            SELECT MonthYear, TotalOrders, TotalUnitsSold, TotalRevenue,
                   CAST(TotalRevenue/TotalOrders AS DECIMAL(10,2)) AS AvgOrderValue
            FROM (
                SELECT FORMAT(o.OrderDate,'yyyy-MM')    AS MonthYear,
                       COUNT(DISTINCT o.OrderID)        AS TotalOrders,
                       SUM(od.Quantity)                 AS TotalUnitsSold,
                       SUM(od.Quantity*od.SalePrice)    AS TotalRevenue
                FROM SalesOrder o
                JOIN OrderDetail od ON o.OrderID=od.OrderID
                WHERE o.Status != 'Cancelled'
                GROUP BY FORMAT(o.OrderDate,'yyyy-MM')
            ) AS Monthly
            ORDER BY MonthYear
        """)
        st.dataframe(df, use_container_width=True)
        st.plotly_chart(
            px.line(df, x="MonthYear", y="TotalRevenue", markers=True,
                    color_discrete_sequence=["#DC2626"]),
            use_container_width=True
        )

# ── REORDER ALERTS ─────────────────────────────────────────
elif page == "⚠️ Reorder Alerts":
    st.title("⚠️ Reorder Alerts")
    st.markdown("---")

    df = run_query("""
        SELECT * FROM vw_StockSummary
        WHERE StockStatus = 'Reorder Required'
        ORDER BY QuantityOnHand ASC
    """)

    if df.empty:
        st.success("All products sufficiently stocked!")
    else:
        st.warning(f"{len(df)} items need reordering!")
        st.dataframe(df, use_container_width=True)
        st.plotly_chart(
            px.bar(df, x="ProductName", y="QuantityOnHand", color="WarehouseName"),
            use_container_width=True
        )

# ── ADD RECORDS ────────────────────────────────────────────
elif page == "➕ Add Records":
    st.title("➕ Add New Records")
    st.markdown("---")

    t1, t2, t3 = st.tabs(["Add Product", "Add Order", "Delete Order"])

    with t1:
        st.subheader("Add New Product")
        cats = run_query("SELECT CategoryID, CategoryName FROM Category")
        sups = run_query("SELECT SupplierID, SupplierName FROM Supplier")
        cat_map = dict(zip(cats.CategoryName, cats.CategoryID))
        sup_map = dict(zip(sups.SupplierName,  sups.SupplierID))

        nm = st.text_input("Product Name")
        ct = st.selectbox("Category", list(cat_map.keys()))
        sp = st.selectbox("Supplier",  list(sup_map.keys()))
        pr = st.number_input("Price (PKR)", min_value=1.0, step=50.0)
        rl = st.number_input("Reorder Level", min_value=1, value=50)
        lt = st.number_input("Lead Time (days)", min_value=1, value=7)
        if st.button("Add Product", type="primary"):
            if nm.strip():
                run_write("""
                    INSERT INTO Product
                    (ProductName,CategoryID,SupplierID,UnitPrice,ReorderLevel,LeadTimeDays)
                    VALUES (?,?,?,?,?,?)
                """, params=(nm, cat_map[ct], sup_map[sp], pr, rl, lt))
                st.success(f"'{nm}' added!")
            else:
                st.error("Product name daalo!")

    with t2:
        st.subheader("Add New Sales Order")
        cn   = st.text_input("Customer Name")
        od   = st.date_input("Order Date")
        st_s = st.selectbox("Status", ["Pending","Confirmed","Shipped","Cancelled"])

        if st.button("Create Order", type="primary"):
            if cn.strip():
                run_write("""
                    INSERT INTO SalesOrder (CustomerName, OrderDate, Status)
                    VALUES (?,?,?)
                """, params=(cn, str(od), st_s))
                st.success(f"Order for '{cn}' created!")
            else:
                st.error("Customer name daalo!")

    with t3:
        st.subheader("Delete Order")
        did = st.number_input("Order ID to Delete", min_value=1, step=1)
        if st.button("Delete", type="primary"):
            run_write("DELETE FROM OrderDetail WHERE OrderID=?", params=(int(did),))
            run_write("DELETE FROM SalesOrder  WHERE OrderID=?", params=(int(did),))
            st.success(f"Order {did} deleted.")