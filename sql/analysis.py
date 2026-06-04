import sqlite3
import pandas as pd

# ── Load data ──────────────────────────────────────────
df = pd.read_csv('retail-sales-analytics/data/superstore.csv', encoding='latin-1')
print("Shape:", df.shape)
print("\nColumns:", df.columns.tolist())
print("\nSample:\n", df.head(3))

# ── Create SQLite DB ───────────────────────────────────
conn = sqlite3.connect('retail-sales-analytics/data/superstore.db')
df.to_sql('orders', conn, if_exists='replace', index=False)
print("\n✅ Database created — orders table loaded")

# ── Business Question 1 ────────────────────────────────
# Which region generates the most revenue and profit?
q1 = pd.read_sql_query("""
    SELECT 
        Region,
        ROUND(SUM(Sales), 2)  AS total_sales,
        ROUND(SUM(Profit), 2) AS total_profit,
        ROUND(SUM(Profit)/SUM(Sales)*100, 2) AS profit_margin_pct
    FROM orders
    GROUP BY Region
    ORDER BY total_sales DESC
""", conn)
print("\n📊 Q1 — Revenue & Profit by Region:\n", q1.to_string(index=False))

# ── Business Question 2 ────────────────────────────────
# What are the top 10 products by sales?
q2 = pd.read_sql_query("""
    SELECT 
        [Product Name],
        ROUND(SUM(Sales), 2)    AS total_sales,
        ROUND(SUM(Profit), 2)   AS total_profit,
        SUM(Quantity)           AS units_sold
    FROM orders
    GROUP BY [Product Name]
    ORDER BY total_sales DESC
    LIMIT 10
""", conn)
print("\n📊 Q2 — Top 10 Products by Sales:\n", q2.to_string(index=False))

# ── Business Question 3 ────────────────────────────────
# Which category and sub-category is most profitable?
q3 = pd.read_sql_query("""
    SELECT 
        Category,
        [Sub-Category],
        ROUND(SUM(Sales), 2)  AS total_sales,
        ROUND(SUM(Profit), 2) AS total_profit,
        ROUND(SUM(Profit)/SUM(Sales)*100, 2) AS margin_pct
    FROM orders
    GROUP BY Category, [Sub-Category]
    ORDER BY total_profit DESC
    LIMIT 10
""", conn)
print("\n📊 Q3 — Most Profitable Sub-Categories:\n", q3.to_string(index=False))

# ── Business Question 4 ────────────────────────────────
# Monthly sales trend — is business growing?
# ── Business Question 4 (FIXED) ────────────────────────
q4 = pd.read_sql_query("""
    SELECT 
        SUBSTR([Order Date], -4) || '-' || 
        PRINTF('%02d', CAST(SUBSTR([Order Date], 1, INSTR([Order Date],'/')-1) AS INTEGER)) AS month,
        ROUND(SUM(Sales), 2)       AS monthly_sales,
        ROUND(SUM(Profit), 2)      AS monthly_profit,
        COUNT(DISTINCT [Order ID]) AS order_count
    FROM orders
    GROUP BY month
    ORDER BY month
""", conn)
print("\n📊 Q4 — Monthly Sales Trend (last 12 months):\n", q4.tail(12).to_string(index=False))

# ── Business Question 5 ────────────────────────────────
# Which customer segment is most valuable?
q5 = pd.read_sql_query("""
    SELECT 
        Segment,
        COUNT(DISTINCT [Customer ID])       AS customer_count,
        ROUND(SUM(Sales), 2)                AS total_sales,
        ROUND(AVG(Sales), 2)                AS avg_order_value,
        ROUND(SUM(Profit)/SUM(Sales)*100,2) AS profit_margin_pct
    FROM orders
    GROUP BY Segment
    ORDER BY total_sales DESC
""", conn)
print("\n📊 Q5 — Customer Segment Analysis:\n", q5.to_string(index=False))

conn.close()
print("\n✅ Day 1 complete — 5 business questions answered with SQL")