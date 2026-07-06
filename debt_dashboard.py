import sys  
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
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
        password="kumaranias7",  
        host="localhost",
        port=5432,
        database="international_debt_db"
    )
    return create_engine(connection_url)

engine = init_connection()

# --- LOAD DATA FROM POSTGRESQL ---
@st.cache_data
def load_data():
    # Fetch data directly from the main fact table (eliminates multi-table dependencies)
    query = """
    SELECT "Country Name", "Country Code", "Series Name", "Year", "Value" 
    FROM debt_data 
    WHERE "Value" > 0
    """
    df = pd.read_sql(query, engine)
    
    # Standardize and clean types
    df['Year'] = pd.to_numeric(df['Year'])
    df["Country Code"] = df["Country Code"].astype(str).str.upper().str.strip()
    df["Country Name"] = df["Country Name"].astype(str).str.strip()
    df["Series Name"] = df["Series Name"].astype(str).str.strip()
    
    return df

with st.spinner("Connecting to PostgreSQL & loading data..."):
    df = load_data()

# ==========================================
# ⚙️ GLOBAL SIDEBAR FILTERS
# ==========================================
st.sidebar.header("⚙️ Filter Analytics")
st.sidebar.markdown("Adjust these parameters to update all tabs dynamically.")

# 1. Country Filter Setup
all_countries = sorted(df["Country Name"].unique())
valid_defaults = all_countries[:5] if len(all_countries) >= 5 else all_countries

selected_countries = st.sidebar.multiselect(
    "Select Countries:", 
    options=all_countries, 
    default=valid_defaults,
    key="countries_sidebar"
)

# 2. Indicator Filter (Smart Defaults search)
all_indicators = sorted(df["Series Name"].unique())
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

selected_indicators = st.sidebar.multiselect(
    "Select Economic Indicators:", 
    options=all_indicators, 
    default=smart_defaults,
    key="indicators_sidebar"
)

# 3. Year Range Slider
min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
selected_years = st.sidebar.slider(
    "Select Year Range:", 
    min_value=min_year, 
    max_value=max_year, 
    value=(min_year, max_year),
    key="years_sidebar"
)

# --- FINAL COMBINED DATA SLICE ---
df_filtered = df[
    (df["Country Name"].isin(selected_countries)) & 
    (df["Series Name"].isin(selected_indicators)) &
    (df["Year"] >= selected_years[0]) & (df["Year"] <= selected_years[1])
]

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
# 🗺️ IN-MEMORY DATA STORES FOR THE 30 SQL QUERIES
# ==========================================
sql_categories = {
    "Basic Queries (1-10)": {
        "1. Distinct Country Names": 'SELECT DISTINCT "Country Name" FROM debt_data;',
        "2. Total Countries Count": 'SELECT COUNT(DISTINCT "Country Code") AS total_countries FROM debt_data;',
        "3. Total Indicators Count": 'SELECT COUNT(DISTINCT "Series Code") AS total_indicators FROM debt_data;',
        "4. First 10 Records Sample": 'SELECT * FROM debt_data LIMIT 10;',
        "5. Total Global Debt Volume": 'SELECT SUM("Value") AS total_global_debt FROM debt_data;',
        "6. Unique Indicator Names": 'SELECT DISTINCT "Series Name" FROM debt_data;',
        "7. Record Counts per Country": 'SELECT "Country Name", COUNT(*) AS record_count FROM debt_data GROUP BY "Country Name";',
        "8. High-Value Debt Rows (> 1 Billion)": 'SELECT * FROM debt_data WHERE "Value" > 1000000000;',
        "9. Descriptive Statistics Summary": 'SELECT MIN("Value") AS min_debt, MAX("Value") AS max_debt, AVG("Value") AS avg_debt FROM debt_data;',
        "10. Total Dataset Rows Check": 'SELECT COUNT(*) AS total_records FROM debt_data;'
    },
    "Intermediate Queries (11-20)": {
        "11. Total Debt Volume per Country": 'SELECT "Country Name", SUM("Value") AS total_debt FROM debt_data GROUP BY "Country Name";',
        "12. Top 10 Highest National Debts": 'SELECT "Country Name", SUM("Value") AS total_debt FROM debt_data GROUP BY "Country Name" ORDER BY total_debt DESC LIMIT 10;',
        "13. Average Debt Value per Country": 'SELECT "Country Name", AVG("Value") AS average_debt FROM debt_data GROUP BY "Country Name";',
        "14. Total Debt Volume per Indicator": 'SELECT "Series Code", "Series Name", SUM("Value") AS total_debt FROM debt_data GROUP BY "Series Code", "Series Name";',
        "15. Highest Contributing Global Indicator": 'SELECT "Series Code", "Series Name", SUM("Value") AS total_debt FROM debt_data GROUP BY "Series Code", "Series Name" ORDER BY total_debt DESC LIMIT 1;',
        "16. Country with Lowest Total Debt": 'SELECT "Country Name", SUM("Value") AS total_debt FROM debt_data GROUP BY "Country Name" ORDER BY total_debt ASC LIMIT 1;',
        "17. Combined Country-Indicator Aggregates": 'SELECT "Country Name", "Series Name", SUM("Value") AS combined_debt FROM debt_data GROUP BY "Country Name", "Series Name";',
        "18. Distinct Indicator Counts per Nation": 'SELECT "Country Name", COUNT(DISTINCT "Series Code") AS indicator_count FROM debt_data GROUP BY "Country Name";',
        "19. Countries Exceeding Global Average": 'SELECT "Country Name", SUM("Value") AS total_debt FROM debt_data GROUP BY "Country Name" HAVING SUM("Value") > (SELECT AVG(country_debt) FROM (SELECT SUM("Value") AS country_debt FROM debt_data GROUP BY "Country Code") AS subquery);',
        "20. Dense Rank Country Standings": 'SELECT "Country Name", SUM("Value") AS total_debt, DENSE_RANK() OVER (ORDER BY SUM("Value") DESC) AS debt_rank FROM debt_data GROUP BY "Country Name";'
    },
    "Advanced Queries (21-30)": {
        "21. Top 5 Global Mass Indicators": 'SELECT "Series Name", SUM("Value") AS total_contribution FROM debt_data GROUP BY "Series Name" ORDER BY total_contribution DESC LIMIT 5;',
        "22. Percentage Share Contribution": 'SELECT "Country Name", SUM("Value") AS country_debt, (SUM("Value") / (SELECT SUM("Value") FROM debt_data) * 100) AS percentage_contribution FROM debt_data GROUP BY "Country Name" ORDER BY percentage_contribution DESC;',
        "23. Top 3 Highest Debt Countries per Series": 'WITH RankedDebt AS (SELECT "Series Name", "Country Name", "Value", ROW_NUMBER() OVER (PARTITION BY "Series Name" ORDER BY "Value" DESC) AS rn FROM debt_data) SELECT "Series Name", "Country Name", "Value" FROM RankedDebt WHERE rn <= 3;',
        "24. High-Low Asset Variance per Country": 'SELECT "Country Name", (MAX("Value") - MIN("Value")) AS debt_variance FROM debt_data GROUP BY "Country Name";',
        "25. Database View Instantiation Script": 'CREATE OR REPLACE VIEW view_top_10_highest_debt_countries AS SELECT "Country Name", SUM("Value") AS total_debt FROM debt_data GROUP BY "Country Name" ORDER BY total_debt DESC LIMIT 10;',
        "26. High/Medium/Low Debt Case Logic": "SELECT \"Country Name\", SUM(\"Value\") AS total_debt, CASE WHEN SUM(\"Value\") > 500000000000 THEN 'High Debt' WHEN SUM(\"Value\") BETWEEN 100000000000 AND 500000000000 THEN 'Medium Debt' ELSE 'Low Debt' END AS debt_category FROM debt_data GROUP BY \"Country Name\";",
        "27. Cumulative Running Total Window Framework": 'SELECT \"Country Name\", \"Series Code\", \"Value\", SUM(\"Value\") OVER (PARTITION BY \"Country Name\" ORDER BY \"Value\" ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_debt FROM debt_data;',
        "28. Series Exceeding Comprehensive Mean": 'SELECT "Series Name", AVG("Value") AS avg_indicator_debt FROM debt_data GROUP BY "Series Name" HAVING AVG("Value") > (SELECT AVG("Value") FROM debt_data);',
        "29. Nations Controlling > 5% Global Debt": 'SELECT "Country Name", SUM("Value") AS total_debt FROM debt_data GROUP BY "Country Name" HAVING (SUM("Value") / (SELECT SUM("Value") FROM debt_data) * 100) > 5.0;',
        "30. Most Dominant Indicator per Nation": 'WITH CountryIndicatorMax AS (SELECT "Country Name", "Series Name", SUM("Value") AS indicator_total, ROW_NUMBER() OVER(PARTITION BY "Country Name" ORDER BY SUM("Value") DESC) as rn FROM debt_data GROUP BY "Country Name", "Series Name") SELECT "Country Name", "Series Name", indicator_total AS dominant_debt_value FROM CountryIndicatorMax WHERE rn = 1;'
    }
}

# ==========================================
# 🗂️ TABBED NAVIGATION LAYOUT
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Global Trends", "📊 Indicator Breakdown", "🚀 YoY Growth Velocity", 
    "🍩 Debt Composition", "📋 SQL Query Sandbox"
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

# --- TAB 2: Ranked Horizontal Bar Chart ---
with tab2:
    st.subheader("Total Value Comparison by Country")
    st.markdown("Ranked horizontal bar chart for clear categorical comparison.")
    if not df_filtered.empty:
        agg_df = df_filtered.groupby("Country Name")["Value"].sum().reset_index()
        
        fig_bar = px.bar(
            agg_df, x="Value", y="Country Name", color="Value",
            orientation='h', template="plotly_white", text_auto='.2s'
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

# --- TAB 3: Year-over-Year Growth Velocity (Line Chart) ---
with tab3:
    st.subheader("Year-over-Year (YoY) Growth Percentage")
    st.markdown("Analyzes how rapidly a country's debt is increasing or decreasing compared to the previous year.")
    if not df_filtered.empty:
        yoy_df = df_filtered.groupby(['Year', 'Country Name'])['Value'].sum().reset_index()
        yoy_df = yoy_df.sort_values(['Country Name', 'Year'])
        yoy_df['YoY Growth (%)'] = yoy_df.groupby('Country Name')['Value'].pct_change() * 100
        
        fig_yoy = px.line(
            yoy_df, x="Year", y="YoY Growth (%)", color="Country Name",
            template="plotly_white", markers=True,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_yoy.add_hline(y=0, line_width=2, line_color="black", line_dash="dash")
        fig_yoy.update_xaxes(type='category')
        st.plotly_chart(fig_yoy, use_container_width=True)

# --- TAB 4: Debt Portfolio Composition (Pie Chart) ---
with tab4:
    st.subheader("Debt Portfolio Composition")
    st.markdown("Proportional breakdown of debt across selected countries and indicators.")
    
    if not df_filtered.empty:
        comp_df = df_filtered.groupby(['Country Name', 'Series Name'])['Value'].sum().reset_index()
        comp_df['Detailed Category'] = comp_df['Country Name'] + " - " + comp_df['Series Name']
        
        fig_pie = px.pie(
            comp_df, 
            names='Detailed Category', 
            values='Value',
            template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_layout(
            height=650, 
            margin=dict(t=30, l=10, r=10, b=10),
            showlegend=False 
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            textfont=dict(size=12, color="black"),
            hovertemplate="<b>%{label}</b><br>Debt Value: $%{value:,.0f}<br>Share: %{percent:.1%}<extra></extra>"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# --- TAB 5: Live SQL Analytical Queries Sandbox ---
with tab5:
    st.subheader("📋 SQL Analytical Queries Sandbox")
    st.markdown("Select an analytical tier and query string to execute live operations directly against the PostgreSQL database catalog.")
    
    # 1. Primary Dropdown Menu - Category Selection
    selected_tier = st.selectbox(
        "Choose Query Analytical Tier:",
        options=list(sql_categories.keys()),
        key="dropdown_sql_tier"
    )
    
    # 2. Secondary Dropdown Menu - Dynamic Nested Query Target
    tier_queries = sql_categories[selected_tier]
    selected_query_name = st.selectbox(
        "Select Specific SQL Target Statement:",
        options=list(tier_queries.keys()),
        key="dropdown_sql_statement"
    )
    
    # Extract raw SQL script string
    raw_sql_script = tier_queries[selected_query_name]
    
    # Display script code container block
    st.markdown("##### 💻 SQL Code Command:")
    st.code(raw_sql_script, language="sql")
    
    # Live execution pipeline
    with st.spinner("Executing database script against local PostgreSQL server..."):
        try:
            # Safe branch handling for DDL View instantiation vs Data extraction
            if "CREATE OR REPLACE VIEW" in raw_sql_script.upper():
                with engine.connect() as conn:
                    conn.execute(text("COMMIT;"))
                    conn.execute(text(raw_sql_script))
                    conn.execute(text("COMMIT;"))
                st.success("✓ Database Virtual View Layer created successfully inside PostgreSQL catalog structure!")
                
                # Fetch a sample preview from the newly compiled View to prove it works live!
                view_preview = pd.read_sql("SELECT * FROM view_top_10_highest_debt_countries", engine)
                st.markdown("##### 📊 View Layer Content Preview (Fetched Live via SQL):")
                st.dataframe(view_preview, use_container_width=True, hide_index=True)
            else:
                # Standard DML Data Extraction Read
                query_output_df = pd.read_sql(raw_sql_script, engine)
                st.markdown(f"##### 📊 Query Data Results Output ({len(query_output_df)} rows returned):")
                st.dataframe(query_output_df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"PostgreSQL Execution Error: {e}")
