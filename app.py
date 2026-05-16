import streamlit as st
import pymysql
import pymysql.cursors
import pandas as pd
import plotly.express as px

autocommit=True
def get_connection():
    conn = pymysql.connect(
        host='turntable.proxy.rlwy.net',
        user='root',
        password='cvxLLyijdJFTcOyXoZFyRwsjOjuOjQbT',
        port=40417,
        database='railway',
        autocommit=True
    )
    return conn

def run_query(sql, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()
    cursor.close()
    return pd.DataFrame(data, columns=columns)

def run_write(sql, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    conn.commit()
    cursor.close()

st.set_page_config(page_title="Inventory Control", page_icon="📦", layout="wide")

st.sidebar.title("📦 Inventory System")
page = st.sidebar.radio("Navigate", [
    "🏠 Dashboard",
    "📋 Products",
    "📦 Stock Management",
    "🛒 Sales Orders",
    "📊 BI Analytics",
    "⚠️ Reorder Alerts",
    "➕ Add Records"
])

# ── DASHBOARD ──────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.title("📦 Demand Forecasting & Inventory Control")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Products",
        run_query("SELECT COUNT(*) AS n FROM Product").iloc[0,0])
    col2.metric("Total Orders",
        run_query("SELECT COUNT(*) AS n FROM SalesOrder").iloc[0,0])
    col3.metric("Total Revenue", "PKR " +
        f"{run_query('SELECT COALESCE(SUM(Quantity*SalePrice),0) AS n FROM OrderDetail').iloc[0,0]:,.0f}")
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
            SELECT DATE_FORMAT(o.OrderDate,'%Y-%m') AS Month,
                   SUM(od.Quantity*od.SalePrice) AS Revenue
            FROM SalesOrder o
            JOIN OrderDetail od ON o.OrderID=od.OrderID
            WHERE o.Status != 'Cancelled'
            GROUP BY DATE_FORMAT(o.OrderDate,'%Y-%m')
            ORDER BY Month
        """)
        st.plotly_chart(px.bar(df2, x="Month", y="Revenue"), use_container_width=True)

# ── PRODUCTS ──────────────────────────────────────────────
elif page == "📋 Products":
    st.title("📋 Product Catalogue")
    st.markdown("---")

    search = st.text_input("Search product")
    min_p, max_p = st.slider("Price Range (PKR)", 0, 100000, (0, 100000), step=500)

    df = run_query("""
        SELECT p.ProductID, p.ProductName, c.CategoryName, s.SupplierName,
               p.UnitPrice, p.ReorderLevel, p.LeadTimeDays
        FROM Product p
        JOIN Category c ON p.CategoryID=c.CategoryID
        JOIN Supplier s ON p.SupplierID=s.SupplierID
        WHERE p.ProductName LIKE %s AND p.UnitPrice BETWEEN %s AND %s
        ORDER BY p.ProductName
    """, params=(f"%{search}%", min_p, max_p))
    st.dataframe(df, use_container_width=True)
    st.caption(f"{len(df)} products found")

    st.markdown("---")
    t1, t2 = st.tabs(["✏️ Edit Product", "🗑️ Delete Product"])

    with t1:
        st.subheader("Edit Product")
        all_products = run_query("SELECT ProductID, ProductName FROM Product ORDER BY ProductName")
        prod_map = dict(zip(all_products.ProductName, all_products.ProductID))
        sel = st.selectbox("Select Product", list(prod_map.keys()), key="edit_sel")

        if sel:
            pid = prod_map[sel]
            current = run_query("SELECT * FROM Product WHERE ProductID=%s", params=(pid,))
            cats = run_query("SELECT CategoryID, CategoryName FROM Category")
            sups = run_query("SELECT SupplierID, SupplierName FROM Supplier")
            cat_map = dict(zip(cats.CategoryName, cats.CategoryID))
            sup_map = dict(zip(sups.SupplierName, sups.SupplierID))
            cat_names = list(cat_map.keys())
            sup_names = list(sup_map.keys())

            current_cat = cats[cats.CategoryID == current.iloc[0]['CategoryID']]['CategoryName'].values[0]
            current_sup = sups[sups.SupplierID == current.iloc[0]['SupplierID']]['SupplierName'].values[0]

            new_name = st.text_input("Product Name", value=current.iloc[0]['ProductName'])
            new_cat  = st.selectbox("Category", cat_names, index=cat_names.index(current_cat))
            new_sup  = st.selectbox("Supplier",  sup_names, index=sup_names.index(current_sup))
            new_price = st.number_input("Price (PKR)", value=float(current.iloc[0]['UnitPrice']), min_value=1.0, step=50.0)
            new_rl   = st.number_input("Reorder Level", value=int(current.iloc[0]['ReorderLevel']), min_value=1)
            new_lt   = st.number_input("Lead Time (days)", value=int(current.iloc[0]['LeadTimeDays']), min_value=1)

            if st.button("Update Product", type="primary"):
                run_write("""
                    UPDATE Product SET
                    ProductName=%s, CategoryID=%s, SupplierID=%s,
                    UnitPrice=%s, ReorderLevel=%s, LeadTimeDays=%s
                    WHERE ProductID=%s
                """, params=(new_name, cat_map[new_cat], sup_map[new_sup], new_price, new_rl, new_lt, pid))
                st.success(f"'{new_name}' updated!")
                st.rerun()

    with t2:
        st.subheader("Delete Product")
        all_products2 = run_query("SELECT ProductID, ProductName FROM Product ORDER BY ProductName")
        prod_map2 = dict(zip(all_products2.ProductName, all_products2.ProductID))
        sel2 = st.selectbox("Select Product", list(prod_map2.keys()), key="del_sel")

        if sel2:
            st.warning(f"⚠️ '{sel2}' will be deleted!")
            if st.button("Delete Product", type="primary"):
                pid2 = prod_map2[sel2]
                run_write("DELETE FROM OrderDetail WHERE ProductID=%s", params=(pid2,))
                run_write("DELETE FROM InventoryStock WHERE ProductID=%s", params=(pid2,))
                run_write("DELETE FROM Product WHERE ProductID=%s", params=(pid2,))
                st.success(f"'{sel2}' deleted!")
                st.rerun()

# ── STOCK MANAGEMENT ──────────────────────────────────────
elif page == "📦 Stock Management":
    st.title("📦 Inventory Stock")
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
            SET QuantityOnHand=%s, LastUpdated=CURDATE()
            WHERE ProductID=%s AND WarehouseID=%s
        """, params=(qty, prod_map[sel_p], wh_map[sel_w]))
        st.success("Stock updated!")
        st.rerun()

# ── SALES ORDERS ──────────────────────────────────────────
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
        WHERE od.OrderID=%s
    """, params=(int(oid),))
    st.dataframe(df2, use_container_width=True)
    if not df2.empty:
        st.info(f"Order Total: PKR {df2.LineTotal.sum():,.2f}")

# ── BI ANALYTICS ──────────────────────────────────────────
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
            SELECT ProductName, CategoryName, TotalUnitsSold, TotalRevenue
            FROM vw_ProductRevenue
            ORDER BY TotalUnitsSold DESC
            LIMIT 5
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
                SELECT DATE_FORMAT(o.OrderDate,'%Y-%m') AS MonthYear,
                       COUNT(DISTINCT o.OrderID)        AS TotalOrders,
                       SUM(od.Quantity)                 AS TotalUnitsSold,
                       SUM(od.Quantity*od.SalePrice)    AS TotalRevenue
                FROM SalesOrder o
                JOIN OrderDetail od ON o.OrderID=od.OrderID
                WHERE o.Status != 'Cancelled'
                GROUP BY DATE_FORMAT(o.OrderDate,'%Y-%m')
            ) AS Monthly
            ORDER BY MonthYear
        """)
        st.dataframe(df, use_container_width=True)
        st.plotly_chart(
            px.line(df, x="MonthYear", y="TotalRevenue", markers=True,
                    color_discrete_sequence=["#DC2626"]),
            use_container_width=True
        )

# ── REORDER ALERTS ────────────────────────────────────────
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

# ── ADD RECORDS ───────────────────────────────────────────
elif page == "➕ Add Records":
    st.title("➕ Add New Records")
    st.markdown("---")

    t1, t2, t3 = st.tabs(["Add Product", "Add Order", "Delete Order"])

    with t1:
        st.subheader("Add New Product")
        cats = run_query("SELECT CategoryID, CategoryName FROM Category")
        sups = run_query("SELECT SupplierID, SupplierName FROM Supplier")
        cat_map = dict(zip(cats.CategoryName, cats.CategoryID))
        sup_map = dict(zip(sups.SupplierName, sups.SupplierID))

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
                    VALUES (%s,%s,%s,%s,%s,%s)
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
                    VALUES (%s,%s,%s)
                """, params=(cn, str(od), st_s))
                st.success(f"Order for '{cn}' created!")
            else:
                st.error("Customer name daalo!")

    with t3:
        st.subheader("Delete Order")
        did = st.number_input("Order ID to Delete", min_value=1, step=1)
        if st.button("Delete", type="primary"):
            run_write("DELETE FROM OrderDetail WHERE OrderID=%s", params=(int(did),))
            run_write("DELETE FROM SalesOrder  WHERE OrderID=%s", params=(int(did),))
            st.success(f"Order {did} deleted.")
