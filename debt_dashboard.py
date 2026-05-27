import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Global Debt Analytics", page_icon="🌍", layout="wide")
st.title("🌍 International Debt Analysis Dashboard")
st.markdown("### End-to-End Data Analytics Pipeline: Python ➡️ PostgreSQL ➡️ Streamlit")

# --- DATABASE CONNECTION (CACHED FOR SPEED) ---
@st.cache_resource
def init_connection():
    connection_url = URL.create(
        drivername="postgresql+psycopg2",
        username="postgres",
        password="kumaranias7",  # <-- TYPE YOUR REAL PGADMIN PASSWORD HERE
        host="localhost",
        port=5432,
        database="international_debt_db"
    )
    return create_engine(connection_url)

engine = init_connection()

# --- LOAD DATA FROM POSTGRESQL ---
@st.cache_data
def load_data():
    query = """
    SELECT "Country Name", "Series Name", "Year", "Value" 
    FROM debt_data 
    WHERE "Value" > 0
    """
    df = pd.read_sql(query, engine)
    df['Year'] = pd.to_numeric(df['Year'])
    return df

with st.spinner("Connecting to PostgreSQL & loading data..."):
    df = load_data()

# ==========================================
# ⚙️ GLOBAL SIDEBAR FILTERS
# ==========================================
st.sidebar.header("⚙️ Filter Analytics")
st.sidebar.markdown("Adjust these parameters to update all tabs dynamically.")

all_countries = sorted(df["Country Name"].unique())
all_indicators = sorted(df["Series Name"].unique())

# --- SMART DEFAULT SELECTION LOGIC ---
smart_defaults = []
important_keywords = ["stocks, total", "Principal repayments", "Interest payments"]

for keyword in important_keywords:
    matches = [ind for ind in all_indicators if keyword.lower() in ind.lower()]
    if matches:
        smart_defaults.append(matches[0])

if not smart_defaults:
    smart_defaults = all_indicators[:3]
else:
    smart_defaults = smart_defaults[:3]

# --- UI CONTROLS ---
default_countries = ["India", "China", "Brazil", "Mexico", "South Africa"]
selected_countries = st.sidebar.multiselect("Select Countries:", options=all_countries, default=default_countries)
selected_indicators = st.sidebar.multiselect("Select Economic Indicators:", options=all_indicators, default=smart_defaults)

# Apply filters
df_filtered = df[(df["Country Name"].isin(selected_countries)) & (df["Series Name"].isin(selected_indicators))]

# ==========================================
# 🏆 EXECUTIVE INSIGHTS (KPI CARDS)
# ==========================================
if not df_filtered.empty:
    st.markdown("### 📊 Executive Summary")
    
    total_filtered_debt = df_filtered["Value"].sum()
    country_totals = df_filtered.groupby("Country Name")["Value"].sum()
    highest_country = country_totals.idxmax()
    lowest_country = country_totals.idxmin()
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Debt (Selected)", f"${total_filtered_debt:,.0f}")
    kpi2.metric("Highest Debt Country", highest_country)
    kpi3.metric("Lowest Debt Country", lowest_country)
    st.divider()

# ==========================================
# 🗂️ TABBED NAVIGATION LAYOUT (NOW 5 TABS!)
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Global Trends", 
    "📊 Indicator Breakdown", 
    "🚀 YoY Growth Velocity", 
    "🍩 Debt Composition", 
    "📋 Detailed Data"
])

# --- TAB 1: Historical Timeline ---
with tab1:
    st.subheader("Historical Debt Accumulation Over Time")
    if not df_filtered.empty:
        fig_line = px.line(
            df_filtered, x="Year", y="Value", color="Country Name", 
            line_group="Series Name", hover_name="Series Name",
            markers=True, template="plotly_white"
        )
        st.plotly_chart(fig_line, use_container_width=True)

# --- TAB 2: Bar Chart Comparisons ---
with tab2:
    st.subheader("Total Value Comparison by Country")
    if not df_filtered.empty:
        agg_df = df_filtered.groupby(["Country Name", "Series Name"])["Value"].sum().reset_index()
        fig_bar = px.bar(
            agg_df, x="Country Name", y="Value", color="Series Name",
            barmode="group", template="plotly_white"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# --- TAB 3: NEW! Year-over-Year Growth Velocity ---
with tab3:
    st.subheader("Year-over-Year (YoY) Growth Percentage")
    st.markdown("Analyzes how rapidly a country's debt is increasing or decreasing compared to the previous year.")
    if not df_filtered.empty:
        # Calculate YoY percentage change
        yoy_df = df_filtered.groupby(['Year', 'Country Name'])['Value'].sum().reset_index()
        yoy_df = yoy_df.sort_values(['Country Name', 'Year'])
        yoy_df['YoY Growth (%)'] = yoy_df.groupby('Country Name')['Value'].pct_change() * 100
        
        # Plot the growth
        fig_yoy = px.bar(
            yoy_df, x="Year", y="YoY Growth (%)", color="Country Name",
            barmode="group", template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        # Add a baseline at 0%
        fig_yoy.add_hline(y=0, line_width=2, line_color="black")
        st.plotly_chart(fig_yoy, use_container_width=True)

# --- TAB 4: NEW! Debt Composition Sunburst ---
with tab4:
    st.subheader("Debt Portfolio Composition")
    st.markdown("Interactive breakdown of how the total debt is distributed across different economic indicators.")
    if not df_filtered.empty:
        # Aggregate for composition
        comp_df = df_filtered.groupby(['Country Name', 'Series Name'])['Value'].sum().reset_index()
        
        fig_sunburst = px.sunburst(
            comp_df, 
            path=['Country Name', 'Series Name'], 
            values='Value',
            template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
       # 1. Allow text to shrink to fit all slices
        fig_sunburst.update_layout(
            height=550, 
            margin=dict(t=30, l=10, r=10, b=10),
            uniformtext=dict(minsize=8, mode=False) # <-- Changed this line!
        )
        
        # 2. Auto-orient the text and force a larger base font size
        fig_sunburst.update_traces(
            textinfo="label+percent parent",
            textfont=dict(size=18, color="black"),  # <-- Added size=18 right here!
            insidetextorientation='auto',
            hovertemplate="<b>%{label}</b><br>Debt Value: $%{value:,.0f}<br>Share of Parent: %{percentParent:.1%}<extra></extra>"
        )
        
        st.plotly_chart(fig_sunburst, use_container_width=True)

# --- TAB 5: Raw Data Grid & Export ---
with tab5:
    st.subheader("Raw Data Inspector")
    if not df_filtered.empty:
        st.dataframe(
            df_filtered.sort_values(by=["Year", "Country Name"], ascending=[False, True]), 
            use_container_width=True, hide_index=True
        )
        st.divider()
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv_data, file_name='international_debt_advanced.csv', mime='text/csv',
        )