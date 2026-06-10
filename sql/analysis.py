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

# ══════════════════════════════════════════════════════
# UPGRADE: Discount Impact Analysis
# The real reason Central region has 7.9% margin
# ══════════════════════════════════════════════════════

print("\n" + "="*60)
print("UPGRADE ANALYSIS: Discount Impact on Profitability")
print("="*60)

# Query 6 — Discount brackets vs profit margin
q6 = pd.read_sql_query("""
    SELECT 
        CASE 
            WHEN Discount = 0 THEN '0% - No Discount'
            WHEN Discount <= 0.10 THEN '1-10% Discount'
            WHEN Discount <= 0.20 THEN '11-20% Discount'
            WHEN Discount <= 0.30 THEN '21-30% Discount'
            WHEN Discount <= 0.40 THEN '31-40% Discount'
            ELSE '40%+ Discount'
        END AS discount_bracket,
        COUNT(*) AS order_count,
        ROUND(AVG(Discount)*100, 1) AS avg_discount_pct,
        ROUND(SUM(Sales), 2) AS total_sales,
        ROUND(SUM(Profit), 2) AS total_profit,
        ROUND(SUM(Profit)/SUM(Sales)*100, 2) AS profit_margin_pct
    FROM orders
    GROUP BY discount_bracket
    ORDER BY avg_discount_pct
""", conn)
print("\n📊 Q6 — Discount Brackets vs Profit Margin:")
print(q6.to_string(index=False))

# Query 7 — Loss orders analysis
q7 = pd.read_sql_query("""
    SELECT 
        Region,
        COUNT(*) AS total_orders,
        SUM(CASE WHEN Profit < 0 THEN 1 ELSE 0 END) AS loss_orders,
        ROUND(SUM(CASE WHEN Profit < 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS loss_order_pct,
        ROUND(SUM(CASE WHEN Profit < 0 THEN Profit ELSE 0 END), 2) AS total_loss_amount,
        ROUND(SUM(CASE WHEN Profit < 0 THEN Discount ELSE 0 END) / 
              SUM(CASE WHEN Profit < 0 THEN 1 ELSE 0 END) * 100, 1) AS avg_discount_on_loss_orders
    FROM orders
    GROUP BY Region
    ORDER BY loss_order_pct DESC
""", conn)
print("\n📊 Q7 — Loss Orders by Region:")
print(q7.to_string(index=False))

# Query 8 — Repeat customer analysis
q8 = pd.read_sql_query("""
    SELECT 
        purchase_type,
        COUNT(*) AS customer_count,
        ROUND(AVG(total_orders), 1) AS avg_orders,
        ROUND(AVG(total_spent), 2) AS avg_lifetime_value,
        ROUND(AVG(avg_order_value), 2) AS avg_order_value
    FROM (
        SELECT 
            [Customer ID],
            COUNT(DISTINCT [Order ID]) AS total_orders,
            ROUND(SUM(Sales), 2) AS total_spent,
            ROUND(AVG(Sales), 2) AS avg_order_value,
            CASE 
                WHEN COUNT(DISTINCT [Order ID]) = 1 THEN 'One-time Buyer'
                WHEN COUNT(DISTINCT [Order ID]) <= 3 THEN 'Occasional Buyer'
                ELSE 'Loyal Customer'
            END AS purchase_type
        FROM orders
        GROUP BY [Customer ID]
    )
    GROUP BY purchase_type
    ORDER BY avg_lifetime_value DESC
""", conn)
print("\n📊 Q8 — Repeat Customer Analysis:")
print(q8.to_string(index=False))

conn.close()
print("\n✅ Upgrade analysis complete")
