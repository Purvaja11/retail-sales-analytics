import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# ── Setup ──────────────────────────────────────────────
conn = sqlite3.connect('retail-sales-analytics/data/superstore.db')
os.makedirs('retail-sales-analytics/charts', exist_ok=True)

COLORS = ['#2C3E50', '#2E86AB', '#A23B72', '#F18F01', '#C73E1D']

# ══════════════════════════════════════════════════════
# CHART 1 — Regional Revenue vs Profit Margin
# Insight: West leads but Central has dangerously low margins
# ══════════════════════════════════════════════════════
df1 = pd.read_sql_query("""
    SELECT Region,
           ROUND(SUM(Sales), 2)  AS total_sales,
           ROUND(SUM(Profit), 2) AS total_profit,
           ROUND(SUM(Profit)/SUM(Sales)*100, 2) AS margin_pct
    FROM orders
    GROUP BY Region
    ORDER BY total_sales DESC
""", conn)

fig1 = make_subplots(specs=[[{"secondary_y": True}]])
fig1.add_trace(go.Bar(
    x=df1['Region'], y=df1['total_sales'],
    name='Total Sales ($)', marker_color=COLORS[1],
    text=['${:,.0f}'.format(v) for v in df1['total_sales']],
    textposition='outside'
), secondary_y=False)
fig1.add_trace(go.Scatter(
    x=df1['Region'], y=df1['margin_pct'],
    name='Profit Margin (%)', mode='lines+markers',
    marker=dict(size=12, color=COLORS[4]),
    line=dict(width=3, color=COLORS[4])
), secondary_y=True)
fig1.update_layout(
    title=dict(text='<b>Regional Sales vs Profit Margin</b><br>'
               '<sup>West leads revenue; Central has critical 7.9% margin gap</sup>',
               font=dict(size=16)),
    plot_bgcolor='white', paper_bgcolor='white',
    legend=dict(orientation='h', yanchor='bottom', y=1.02),
    height=450
)
fig1.update_yaxes(title_text='Total Sales ($)', secondary_y=False,
                  tickformat='$,.0f', gridcolor='#f0f0f0')
fig1.update_yaxes(title_text='Profit Margin (%)', secondary_y=True,
                  ticksuffix='%')
fig1.write_image('retail-sales-analytics/charts/chart1_regional_analysis.png', scale=2)
fig1.show()
print("✅ Chart 1 saved")

# ══════════════════════════════════════════════════════
# CHART 2 — Top 10 Products: Sales vs Profit
# Insight: 2 top-selling products are losing money
# ══════════════════════════════════════════════════════
df2 = pd.read_sql_query("""
    SELECT 
        CASE WHEN LENGTH([Product Name]) > 35 
             THEN SUBSTR([Product Name],1,35)||'...' 
             ELSE [Product Name] END AS product,
        ROUND(SUM(Sales), 2)  AS total_sales,
        ROUND(SUM(Profit), 2) AS total_profit
    FROM orders
    GROUP BY [Product Name]
    ORDER BY total_sales DESC
    LIMIT 10
""", conn)

colors_profit = ['#C73E1D' if p < 0 else '#2E86AB' 
                 for p in df2['total_profit']]

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    y=df2['product'], x=df2['total_sales'],
    name='Sales', orientation='h',
    marker_color='#BDC3C7'
))
fig2.add_trace(go.Bar(
    y=df2['product'], x=df2['total_profit'],
    name='Profit', orientation='h',
    marker_color=['#C73E1D' if p < 0 else '#2E86AB' 
                  for p in df2['total_profit']],
    text=['  -${:,.0f}'.format(abs(v)) if v < 0 
          else '  ${:,.0f}'.format(v) 
          for v in df2['total_profit']],
    textposition='outside',
    textfont=dict(size=11)
))
fig2.add_vline(x=0, line_width=2, line_color='black')
fig2.update_layout(
    title=dict(text='<b>Top 10 Products: Sales vs Profit</b><br>'
               '<sup>Red = loss-making products hiding behind high sales volume</sup>',
               font=dict(size=16)),
    barmode='group', height=500,
    plot_bgcolor='white', paper_bgcolor='white',
    xaxis=dict(tickformat='$,.0f', gridcolor='#f0f0f0', 
               range=[-15000, 75000]),
    legend=dict(orientation='h', yanchor='bottom', y=1.02),
    margin=dict(l=280, r=80)
)
fig2.write_image('retail-sales-analytics/charts/chart2_product_profitability.png', scale=2)
fig2.show()
print("✅ Chart 2 saved")

# ══════════════════════════════════════════════════════
# CHART 3 — Sub-Category Margin vs Volume Bubble Chart
# Insight: Paper & Copiers = best margin, underutilized
# ══════════════════════════════════════════════════════
df3 = pd.read_sql_query("""
    SELECT 
        Category, [Sub-Category],
        ROUND(SUM(Sales), 2)  AS total_sales,
        ROUND(SUM(Profit), 2) AS total_profit,
        ROUND(SUM(Profit)/SUM(Sales)*100, 2) AS margin_pct,
        SUM(Quantity) AS units_sold
    FROM orders
    GROUP BY Category, [Sub-Category]
""", conn)

cat_colors = {'Technology': '#2E86AB', 
              'Office Supplies': '#F18F01', 
              'Furniture': '#C73E1D'}
df3['color'] = df3['Category'].map(cat_colors)

fig3 = px.scatter(df3,
    x='total_sales', y='margin_pct',
    size='units_sold', color='Category',
    text='Sub-Category',
    color_discrete_map=cat_colors,
    title='<b>Sub-Category: Sales Volume vs Profit Margin</b><br>'
          '<sup>Bubble size = units sold | Top-right quadrant = high sales + high margin</sup>',
    labels={'total_sales': 'Total Sales ($)',
            'margin_pct': 'Profit Margin (%)'},
    height=500
)
fig3.update_traces(textposition='top center', textfont_size=10)
fig3.add_hline(y=df3['margin_pct'].mean(), line_dash='dash',
               line_color='gray',
               annotation_text=f"Avg margin: {df3['margin_pct'].mean():.1f}%")
fig3.add_vline(x=df3['total_sales'].mean(), line_dash='dash',
               line_color='gray',
               annotation_text="Avg sales")
fig3.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                   xaxis=dict(tickformat='$,.0f', gridcolor='#f0f0f0'),
                   yaxis=dict(ticksuffix='%', gridcolor='#f0f0f0'))
fig3.write_image('retail-sales-analytics/charts/chart3_subcategory_bubble.png', scale=2)
fig3.show()
print("✅ Chart 3 saved")

# ══════════════════════════════════════════════════════
# CHART 4 — Monthly Sales Trend with Profit Overlay
# Insight: Nov peak has worst margins — discount problem
# ══════════════════════════════════════════════════════
df4 = pd.read_sql_query("""
    SELECT 
        SUBSTR([Order Date], -4) || '-' || 
        PRINTF('%02d', CAST(SUBSTR([Order Date], 1, 
        INSTR([Order Date],'/')-1) AS INTEGER)) AS month,
        ROUND(SUM(Sales), 2)  AS monthly_sales,
        ROUND(SUM(Profit), 2) AS monthly_profit,
        ROUND(SUM(Profit)/SUM(Sales)*100, 2) AS margin_pct
    FROM orders
    GROUP BY month
    ORDER BY month
""", conn)

fig4 = make_subplots(specs=[[{"secondary_y": True}]])
fig4.add_trace(go.Bar(
    x=df4['month'], y=df4['monthly_sales'],
    name='Monthly Sales', marker_color='#2E86AB',
    opacity=0.8
), secondary_y=False)
fig4.add_trace(go.Scatter(
    x=df4['month'], y=df4['margin_pct'],
    name='Profit Margin %', mode='lines+markers',
    marker=dict(size=8, color='#C73E1D'),
    line=dict(width=2, color='#C73E1D')
), secondary_y=True)
fig4.update_layout(
    title=dict(text='<b>Monthly Sales Trend vs Profit Margin (2014–2017)</b><br>'
               '<sup>Peak sales months show lowest margins — heavy seasonal discounting</sup>',
               font=dict(size=16)),
    plot_bgcolor='white', paper_bgcolor='white',
    height=450,
    legend=dict(orientation='h', yanchor='bottom', y=1.02),
    xaxis=dict(tickangle=45, gridcolor='#f0f0f0')
)
fig4.update_yaxes(title_text='Monthly Sales ($)', secondary_y=False,
                  tickformat='$,.0f', gridcolor='#f0f0f0')
fig4.update_yaxes(title_text='Profit Margin (%)', secondary_y=True,
                  ticksuffix='%')
fig4.write_image('retail-sales-analytics/charts/chart4_monthly_trend.png', scale=2)
fig4.show()
print("✅ Chart 4 saved")

# ══════════════════════════════════════════════════════
# CHART 5 — Customer Segment Analysis
# Insight: Home Office = highest value, most underserved
# ══════════════════════════════════════════════════════
df5 = pd.read_sql_query("""
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

fig5 = make_subplots(
    rows=1, cols=3,
    subplot_titles=('Total Sales by Segment',
                    'Avg Order Value',
                    'Profit Margin %')
)
seg_colors = ['#2C3E50', '#2E86AB', '#F18F01']

fig5.add_trace(go.Bar(
    x=df5['Segment'], y=df5['total_sales'],
    marker_color=seg_colors, showlegend=False,
    text=['${:,.0f}'.format(v) for v in df5['total_sales']],
    textposition='outside'
), row=1, col=1)

fig5.add_trace(go.Bar(
    x=df5['Segment'], y=df5['avg_order_value'],
    marker_color=seg_colors, showlegend=False,
    text=['${:.0f}'.format(v) for v in df5['avg_order_value']],
    textposition='outside'
), row=1, col=2)

fig5.add_trace(go.Bar(
    x=df5['Segment'], y=df5['profit_margin_pct'],
    marker_color=seg_colors, showlegend=False,
    text=['{:.1f}%'.format(v) for v in df5['profit_margin_pct']],
    textposition='outside'
), row=1, col=3)

fig5.update_layout(
    title=dict(text='<b>Customer Segment Analysis</b><br>'
               '<sup>Home Office: smallest segment, highest margin & AOV — biggest growth opportunity</sup>',
               font=dict(size=16)),
    plot_bgcolor='white', paper_bgcolor='white',
    height=420
)
fig5.update_yaxes(gridcolor='#f0f0f0')
fig5.write_image('retail-sales-analytics/charts/chart5_customer_segments.png', scale=2)
fig5.show()
print("✅ Chart 5 saved")

# ══════════════════════════════════════════════════════
# CHART 6 — Discount Impact on Profit Margin
# ══════════════════════════════════════════════════════
df6 = pd.read_sql_query("""
    SELECT 
        CASE 
            WHEN Discount = 0 THEN '0% No Discount'
            WHEN Discount <= 0.10 THEN '1-10%'
            WHEN Discount <= 0.20 THEN '11-20%'
            WHEN Discount <= 0.30 THEN '21-30%'
            WHEN Discount <= 0.40 THEN '31-40%'
            ELSE '40%+'
        END AS discount_bracket,
        ROUND(AVG(Discount)*100, 1) AS avg_discount_pct,
        ROUND(SUM(Profit)/SUM(Sales)*100, 2) AS profit_margin_pct,
        COUNT(*) AS order_count
    FROM orders
    GROUP BY discount_bracket
    ORDER BY avg_discount_pct
""", conn)

colors_margin = ['#C73E1D' if m < 0 else '#2E86AB' 
                 for m in df6['profit_margin_pct']]

fig6 = go.Figure()
fig6.add_trace(go.Bar(
    x=df6['discount_bracket'],
    y=df6['profit_margin_pct'],
    marker_color=colors_margin,
    text=[f"{m:.1f}%" for m in df6['profit_margin_pct']],
    textposition='outside',
    textfont=dict(size=12, color='black')
))
fig6.add_hline(y=0, line_width=2, line_color='black')
fig6.add_hline(y=12.47, line_dash='dash', line_color='gray',
               annotation_text="Overall avg margin: 12.47%",
               annotation_position="top right")
fig6.update_layout(
    title=dict(
        text='<b>Discount Rate vs Profit Margin</b><br>'
             '<sup>Discounts above 20% destroy profitability — 40%+ loses 77¢ per dollar sold</sup>',
        font=dict(size=16)
    ),
    xaxis_title='Discount Bracket',
    yaxis_title='Profit Margin (%)',
    yaxis=dict(ticksuffix='%', gridcolor='#f0f0f0',
               range=[-90, 45]),
    plot_bgcolor='white', paper_bgcolor='white',
    height=450
)
fig6.write_image('retail-sales-analytics/charts/chart6_discount_impact.png', scale=2)
fig6.show()
print("✅ Chart 6 saved")

# ══════════════════════════════════════════════════════
# CHART 7 — Loss Orders by Region
# ══════════════════════════════════════════════════════
df7 = pd.read_sql_query("""
    SELECT 
        Region,
        ROUND(SUM(CASE WHEN Profit < 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS loss_order_pct,
        ROUND(ABS(SUM(CASE WHEN Profit < 0 THEN Profit ELSE 0 END)), 2) AS total_loss,
        ROUND(SUM(CASE WHEN Profit < 0 THEN Discount ELSE 0 END) /
              SUM(CASE WHEN Profit < 0 THEN 1 ELSE 0 END) * 100, 1) AS avg_discount_on_losses
    FROM orders
    GROUP BY Region
    ORDER BY loss_order_pct DESC
""", conn)

fig7 = make_subplots(rows=1, cols=2,
                     subplot_titles=('Loss Order % by Region',
                                     'Total Loss Amount by Region ($)'))
bar_colors = ['#C73E1D', '#E8845A', '#F0A87A', '#2E86AB']

fig7.add_trace(go.Bar(
    x=df7['Region'], y=df7['loss_order_pct'],
    marker_color=bar_colors,
    text=[f"{v}%" for v in df7['loss_order_pct']],
    textposition='outside', showlegend=False
), row=1, col=1)

fig7.add_trace(go.Bar(
    x=df7['Region'], y=df7['total_loss'],
    marker_color=bar_colors,
    text=[f"${v:,.0f}" for v in df7['total_loss']],
    textposition='outside', showlegend=False
), row=1, col=2)

fig7.update_layout(
    title=dict(
        text='<b>Loss Orders by Region</b><br>'
             '<sup>Central: 31.9% of orders lose money — avg 54.9% discount on loss orders</sup>',
        font=dict(size=16)
    ),
    plot_bgcolor='white', paper_bgcolor='white',
    height=420
)
fig7.update_yaxes(gridcolor='#f0f0f0')
fig7.write_image('retail-sales-analytics/charts/chart7_loss_by_region.png', scale=2)
fig7.show()
print("✅ Chart 7 saved")

# ══════════════════════════════════════════════════════
# CHART 8 — Customer Lifetime Value by Type
# ══════════════════════════════════════════════════════
df8 = pd.read_sql_query("""
    SELECT 
        purchase_type,
        COUNT(*) AS customer_count,
        ROUND(AVG(total_spent), 2) AS avg_lifetime_value,
        ROUND(AVG(avg_order_value), 2) AS avg_order_value,
        ROUND(AVG(total_orders), 1) AS avg_orders
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

fig8 = make_subplots(
    rows=1, cols=3,
    subplot_titles=('Avg Lifetime Value ($)',
                    'Avg Order Value ($)',
                    'Avg Number of Orders')
)
seg_colors = ['#2C3E50', '#2E86AB', '#BDC3C7']

fig8.add_trace(go.Bar(
    x=df8['purchase_type'], y=df8['avg_lifetime_value'],
    marker_color=seg_colors, showlegend=False,
    text=[f"${v:,.0f}" for v in df8['avg_lifetime_value']],
    textposition='outside'
), row=1, col=1)

fig8.add_trace(go.Bar(
    x=df8['purchase_type'], y=df8['avg_order_value'],
    marker_color=seg_colors, showlegend=False,
    text=[f"${v:,.0f}" for v in df8['avg_order_value']],
    textposition='outside'
), row=1, col=2)

fig8.add_trace(go.Bar(
    x=df8['purchase_type'], y=df8['avg_orders'],
    marker_color=seg_colors, showlegend=False,
    text=[f"{v:.1f}" for v in df8['avg_orders']],
    textposition='outside'
), row=1, col=3)

fig8.update_layout(
    title=dict(
        text='<b>Customer Lifetime Value Analysis</b><br>'
             '<sup>Loyal customers worth 7x more than one-time buyers — retention beats acquisition</sup>',
        font=dict(size=16)
    ),
    plot_bgcolor='white', paper_bgcolor='white',
    height=420
)
fig8.update_yaxes(gridcolor='#f0f0f0')
fig8.write_image('retail-sales-analytics/charts/chart8_customer_ltv.png', scale=2)
fig8.show()
print("✅ Chart 8 saved")

conn.close()
print("\n✅ All upgrade charts saved")