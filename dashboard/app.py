import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Page config ────────────────────────────────────────
st.set_page_config(
    page_title="Retail Sales Analytics",
    page_icon="🛒",
    layout="wide"
)

# ── Load data ──────────────────────────────────────────
@st.cache_data
def load_data():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Try SQLite first (local), fall back to CSV (deployed)
    db_path = os.path.join(base_dir, 'data', 'superstore.db')
    csv_path = os.path.join(base_dir, 'data', 'superstore_clean.csv')
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM orders", conn)
        conn.close()
    except:
        df = pd.read_csv(csv_path, encoding='latin-1')
    
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    df['Year'] = df['Order Date'].dt.year
    df['Month'] = df['Order Date'].dt.to_period('M').astype(str)
    return df

df = load_data()

# ── Sidebar filters ────────────────────────────────────
st.sidebar.title("🔍 Filters")
selected_region = st.sidebar.multiselect(
    "Region", options=df['Region'].unique(),
    default=df['Region'].unique()
)
selected_category = st.sidebar.multiselect(
    "Category", options=df['Category'].unique(),
    default=df['Category'].unique()
)
selected_year = st.sidebar.multiselect(
    "Year", options=sorted(df['Year'].unique()),
    default=sorted(df['Year'].unique())
)

# Filter dataframe
filtered = df[
    (df['Region'].isin(selected_region)) &
    (df['Category'].isin(selected_category)) &
    (df['Year'].isin(selected_year))
]

# ── Title ──────────────────────────────────────────────
st.title("🛒 Retail Sales & Customer Analytics")
st.caption("Superstore Dataset | 9,994 transactions | 2014–2017")
st.divider()

# ── Page tabs ──────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "📈 Sales Analysis",
    "🏷️ Product & Discount",
    "👥 Customer Insights"
])

# ══════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════
with tab1:
    # KPI cards
    col1, col2, col3, col4 = st.columns(4)
    total_sales   = filtered['Sales'].sum()
    total_profit  = filtered['Profit'].sum()
    margin        = total_profit / total_sales * 100 if total_sales > 0 else 0
    total_orders  = filtered['Order ID'].nunique()

    col1.metric("Total Revenue",  f"${total_sales:,.0f}")
    col2.metric("Total Profit",   f"${total_profit:,.0f}")
    col3.metric("Profit Margin",  f"{margin:.2f}%")
    col4.metric("Total Orders",   f"{total_orders:,}")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        # Regional bar chart
        reg = filtered.groupby('Region').agg(
            total_sales=('Sales','sum'),
            total_profit=('Profit','sum')
        ).reset_index()
        reg['margin'] = reg['total_profit'] / reg['total_sales'] * 100

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(
            x=reg['Region'], y=reg['total_sales'],
            name='Revenue', marker_color='#2C3E50'
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=reg['Region'], y=reg['margin'],
            name='Margin %', mode='lines+markers',
            marker=dict(size=10, color='#C73E1D'),
            line=dict(width=3, color='#C73E1D')
        ), secondary_y=True)
        fig.update_layout(
            title='Revenue & Margin by Region',
            plot_bgcolor='white', height=350,
            legend=dict(orientation='h', y=1.1)
        )
        fig.update_yaxes(tickformat='$,.0f',
                         gridcolor='#f0f0f0', secondary_y=False)
        fig.update_yaxes(ticksuffix='%', secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        # Category donut
        cat = filtered.groupby('Category')['Sales'].sum().reset_index()
        fig2 = px.pie(cat, values='Sales', names='Category',
                      hole=0.45,
                      color_discrete_sequence=['#2C3E50','#2E86AB','#F18F01'],
                      title='Revenue by Category')
        fig2.update_layout(height=350)
        st.plotly_chart(fig2, use_container_width=True)

    # Business insights callout
    st.subheader("💡 Key Business Insights")
    i1, i2, i3 = st.columns(3)
    i1.info("**Regional Gap**\nWest: 14.94% margin\nCentral: 7.92% margin\nCause: heavy discounting")
    i2.warning("**Loss-Making Products**\n2 of top 10 products by sales are unprofitable.\nCisco EX90: -$1,811 loss")
    i3.success("**Growth Opportunity**\nHome Office has highest margin (14.03%) but fewest customers (148)")

# ══════════════════════════════════════════════════════
# TAB 2 — SALES ANALYSIS
# ══════════════════════════════════════════════════════
with tab2:
    # Monthly trend
    monthly = filtered.groupby('Month').agg(
        sales=('Sales','sum'),
        profit=('Profit','sum')
    ).reset_index()
    monthly['margin'] = monthly['profit'] / monthly['sales'] * 100

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(go.Bar(
        x=monthly['Month'], y=monthly['sales'],
        name='Monthly Sales', marker_color='#2E86AB', opacity=0.8
    ), secondary_y=False)
    fig3.add_trace(go.Scatter(
        x=monthly['Month'], y=monthly['margin'],
        name='Margin %', mode='lines+markers',
        marker=dict(size=6, color='#C73E1D'),
        line=dict(width=2, color='#C73E1D')
    ), secondary_y=True)
    fig3.update_layout(
        title='Monthly Sales Trend vs Profit Margin',
        plot_bgcolor='white', height=400,
        xaxis=dict(tickangle=45, gridcolor='#f0f0f0'),
        legend=dict(orientation='h', y=1.1)
    )
    fig3.update_yaxes(tickformat='$,.0f',
                      gridcolor='#f0f0f0', secondary_y=False)
    fig3.update_yaxes(ticksuffix='%', secondary_y=True)
    st.plotly_chart(fig3, use_container_width=True)

    st.warning("⚠️ **Peak Season Paradox:** November is the highest revenue month but has the lowest profit margin — heavy seasonal discounting destroys profit when it matters most.")

    # Sub-category bubble
    sub = filtered.groupby(['Category','Sub-Category']).agg(
        sales=('Sales','sum'),
        profit=('Profit','sum'),
        qty=('Quantity','sum')
    ).reset_index()
    sub['margin'] = sub['profit'] / sub['sales'] * 100

    fig4 = px.scatter(sub,
        x='sales', y='margin', size='qty',
        color='Category', text='Sub-Category',
        color_discrete_map={
            'Technology':'#2C3E50',
            'Office Supplies':'#F18F01',
            'Furniture':'#C73E1D'
        },
        title='Sub-Category: Sales Volume vs Profit Margin',
        labels={'sales':'Total Sales ($)', 'margin':'Profit Margin (%)'},
        height=450
    )
    fig4.update_traces(textposition='top center', textfont_size=10)
    fig4.add_hline(y=sub['margin'].mean(), line_dash='dash',
                   line_color='gray',
                   annotation_text=f"Avg: {sub['margin'].mean():.1f}%")
    fig4.update_layout(plot_bgcolor='white',
                       xaxis=dict(tickformat='$,.0f',
                                  gridcolor='#f0f0f0'),
                       yaxis=dict(ticksuffix='%',
                                  gridcolor='#f0f0f0'))
    st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════
# TAB 3 — PRODUCT & DISCOUNT ANALYSIS
# ══════════════════════════════════════════════════════
with tab3:
    st.subheader("🔥 Discount Impact Analysis")
    st.error("**Critical Finding:** Orders with 0% discount earn 29.51% margin. Above 40% discount, the business loses 77¢ on every $1 sold.")

    # Discount bracket chart
    filtered['discount_bracket'] = pd.cut(
        filtered['Discount'],
        bins=[-0.01, 0.001, 0.10, 0.20, 0.30, 0.40, 1.0],
        labels=['0% No Discount','1-10%','11-20%',
                '21-30%','31-40%','40%+']
    )
    disc = filtered.groupby('discount_bracket',
                             observed=True).agg(
        sales=('Sales','sum'),
        profit=('Profit','sum'),
        orders=('Order ID','count')
    ).reset_index()
    disc['margin'] = disc['profit'] / disc['sales'] * 100

    bar_colors = ['#2E86AB' if m >= 0 else '#C73E1D'
                  for m in disc['margin']]
    fig5 = go.Figure(go.Bar(
        x=disc['discount_bracket'], y=disc['margin'],
        marker_color=bar_colors,
        text=[f"{m:.1f}%" for m in disc['margin']],
        textposition='outside'
    ))
    fig5.add_hline(y=0, line_width=2, line_color='black')
    fig5.add_hline(y=12.47, line_dash='dash', line_color='gray',
                   annotation_text="Overall avg: 12.47%")
    fig5.update_layout(
        title='Discount Rate vs Profit Margin',
        yaxis=dict(ticksuffix='%', gridcolor='#f0f0f0',
                   range=[-90, 45]),
        plot_bgcolor='white', height=400
    )
    st.plotly_chart(fig5, use_container_width=True)

    col_l2, col_r2 = st.columns(2)
    with col_l2:
        # Top 10 products
        top10 = filtered.groupby('Product Name').agg(
            sales=('Sales','sum'),
            profit=('Profit','sum')
        ).nlargest(10, 'sales').reset_index()

        fig6 = go.Figure()
        fig6.add_trace(go.Bar(
            y=top10['Product Name'].str[:35],
            x=top10['sales'], name='Sales',
            orientation='h', marker_color='#BDC3C7'
        ))
        fig6.add_trace(go.Bar(
            y=top10['Product Name'].str[:35],
            x=top10['profit'], name='Profit',
            orientation='h',
            marker_color=['#C73E1D' if p < 0 else '#2E86AB'
                          for p in top10['profit']]
        ))
        fig6.add_vline(x=0, line_width=2, line_color='black')
        fig6.update_layout(
            title='Top 10 Products: Sales vs Profit',
            barmode='group', height=420,
            plot_bgcolor='white',
            xaxis=dict(tickformat='$,.0f',
                       gridcolor='#f0f0f0'),
            margin=dict(l=250)
        )
        st.plotly_chart(fig6, use_container_width=True)

    with col_r2:
        # Loss orders by region
        loss = filtered.groupby('Region').apply(
            lambda x: pd.Series({
                'loss_pct': (x['Profit'] < 0).mean() * 100,
                'total_loss': abs(x.loc[x['Profit']<0,'Profit'].sum())
            })
        ).reset_index()

        fig7 = make_subplots(rows=2, cols=1,
            subplot_titles=('Loss Order %', 'Total Loss Amount ($)'))
        colors_r = ['#C73E1D','#E8845A','#F0A87A','#2E86AB']
        fig7.add_trace(go.Bar(
            x=loss['Region'], y=loss['loss_pct'],
            marker_color=colors_r, showlegend=False,
            text=[f"{v:.1f}%" for v in loss['loss_pct']],
            textposition='outside'
        ), row=1, col=1)
        fig7.add_trace(go.Bar(
            x=loss['Region'], y=loss['total_loss'],
            marker_color=colors_r, showlegend=False,
            text=[f"${v:,.0f}" for v in loss['total_loss']],
            textposition='outside'
        ), row=2, col=1)
        fig7.update_layout(
            title='Loss Orders by Region',
            plot_bgcolor='white', height=420
        )
        fig7.update_yaxes(gridcolor='#f0f0f0')
        st.plotly_chart(fig7, use_container_width=True)

# ══════════════════════════════════════════════════════
# TAB 4 — CUSTOMER INSIGHTS
# ══════════════════════════════════════════════════════
with tab4:
    col1, col2 = st.columns(2)

    with col1:
        # Segment comparison
        seg = filtered.groupby('Segment').agg(
            revenue=('Sales','sum'),
            profit=('Profit','sum'),
            orders=('Order ID','nunique'),
            customers=('Customer ID','nunique')
        ).reset_index()
        seg['margin'] = seg['profit'] / seg['revenue'] * 100
        seg['aov'] = seg['revenue'] / seg['orders']

        fig8 = make_subplots(rows=1, cols=3,
            subplot_titles=('Revenue','Avg Order Value','Margin %'))
        sc = ['#2C3E50','#2E86AB','#F18F01']
        fig8.add_trace(go.Bar(
            x=seg['Segment'], y=seg['revenue'],
            marker_color=sc, showlegend=False,
            text=[f"${v/1e6:.2f}M" for v in seg['revenue']],
            textposition='outside'
        ), row=1, col=1)
        fig8.add_trace(go.Bar(
            x=seg['Segment'], y=seg['aov'],
            marker_color=sc, showlegend=False,
            text=[f"${v:.0f}" for v in seg['aov']],
            textposition='outside'
        ), row=1, col=2)
        fig8.add_trace(go.Bar(
            x=seg['Segment'], y=seg['margin'],
            marker_color=sc, showlegend=False,
            text=[f"{v:.1f}%" for v in seg['margin']],
            textposition='outside'
        ), row=1, col=3)
        fig8.update_layout(
            title='Customer Segment Analysis',
            plot_bgcolor='white', height=380
        )
        fig8.update_yaxes(gridcolor='#f0f0f0')
        st.plotly_chart(fig8, use_container_width=True)

    with col2:
        # Customer LTV
        ltv = filtered.groupby('Customer ID').agg(
            orders=('Order ID','nunique'),
            spent=('Sales','sum'),
            aov=('Sales','mean')
        ).reset_index()
        ltv['type'] = ltv['orders'].apply(
            lambda x: 'Loyal (4+ orders)' if x >= 4
            else ('Occasional (2-3)' if x >= 2
                  else 'One-time')
        )
        ltv_sum = ltv.groupby('type').agg(
            customers=('Customer ID','count'),
            avg_ltv=('spent','mean'),
            avg_aov=('aov','mean')
        ).reset_index()

        fig9 = px.bar(ltv_sum, x='type', y='avg_ltv',
                      color='type',
                      color_discrete_sequence=[
                          '#2C3E50','#2E86AB','#BDC3C7'],
                      title='Avg Lifetime Value by Customer Type',
                      text=[f"${v:,.0f}" for v in ltv_sum['avg_ltv']],
                      labels={'avg_ltv':'Avg Lifetime Value ($)',
                              'type':'Customer Type'},
                      height=380)
        fig9.update_traces(textposition='outside')
        fig9.update_layout(
            plot_bgcolor='white',
            showlegend=False,
            yaxis=dict(gridcolor='#f0f0f0')
        )
        st.plotly_chart(fig9, use_container_width=True)

    st.success("**Retention Insight:** Loyal customers have 7x higher lifetime value than one-time buyers ($3,160 vs $430). Investing in retention programmes delivers more ROI than new customer acquisition.")

    # Data explorer
    st.divider()
    st.subheader("🔎 Raw Data Explorer")
    st.dataframe(
        filtered[['Order Date','Region','Category',
                  'Sub-Category','Product Name',
                  'Sales','Profit','Discount']
                 ].sort_values('Sales', ascending=False),
        use_container_width=True, height=300
    )