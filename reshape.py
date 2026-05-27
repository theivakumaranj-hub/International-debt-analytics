import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# --- 1. SAFE DATABASE CONFIGURATION ---
DB_USER = "postgres"
DB_PASSWORD = "kumaranias7"  # <-- Type your password here!
DB_HOST = "localhost"
DB_PORT = 5432  # Keep this as a raw number, no quotes
DB_NAME = "international_debt_db"  # Must match pgAdmin exactly

print("🔌 Connecting to PostgreSQL securely...")

# The URL.create function guarantees that slashes, colons, and passwords never get mixed up.
connection_url = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME
)

engine = create_engine(connection_url)

print("🚀 Step 1: Reading raw World Bank data...")
df = pd.read_csv("IDS_ALLCountries_Data.csv", encoding='latin-1')
df.columns = df.columns.str.strip()

year_columns = [col for col in df.columns if col.isdigit()]
identifier_columns = [col for col in df.columns if not col.isdigit()]

print("🔄 Step 2: Reshaping data from Wide to Long format (Pandas Melt)...")
df_long = df.melt(id_vars=identifier_columns, value_vars=year_columns, var_name='Year', value_name='Value')

print("🧹 Step 3: Cleaning nulls and bad data...")
df_long['Value'] = pd.to_numeric(df_long['Value'], errors='coerce')
df_long = df_long.dropna(subset=['Value', 'Country Code', 'Series Code'])

print(f"📤 Step 4: Uploading {len(df_long)} perfectly structured rows to PostgreSQL...")
df_long.to_sql('debt_data', con=engine, if_exists='replace', index=False)

print("🔗 Step 5: Re-applying Foreign Key Links...")
with engine.connect() as conn:
    try:
        conn.execute(text("COMMIT;"))
        conn.execute(text('''
            ALTER TABLE debt_data 
            ADD CONSTRAINT fk_country FOREIGN KEY ("Country Code") REFERENCES countries_metadata("Country Code") ON DELETE CASCADE;
        '''))
        conn.execute(text('''
            ALTER TABLE debt_data 
            ADD CONSTRAINT fk_indicator FOREIGN KEY ("Series Code") REFERENCES indicators_metadata("Series Code") ON DELETE CASCADE;
        '''))
        conn.execute(text("COMMIT;"))
        print("✓ Success! Data is now perfectly formatted for SQL analytics.")
    except Exception as e:
        print(f"Constraints Warning: {e}")