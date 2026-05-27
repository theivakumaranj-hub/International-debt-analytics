import pandas as pd
from sqlalchemy import create_engine, text

# --- POSTGRESQL CONFIGURATION ---
DB_USER = "postgres"          # Your default PostgreSQL user
DB_PASSWORD = "kumaranias7"  # Replace with your actual password
DB_HOST = "localhost"
DB_PORT = "5432"               # Default port for PostgreSQL
DB_NAME = "international_debt_db"

# 1. Connect to default 'postgres' database first to create our target database
engine_default = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres")

# Create database if it doesn't exist
with engine_default.connect() as conn:
    # PostgreSQL doesn't allow 'CREATE DATABASE' inside a transaction block, so we set isolation level
    conn.execute(text("COMMIT;"))
    
    # Check if database exists
    result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}';")).fetchone()
    if not result:
        conn.execute(text(f"CREATE DATABASE {DB_NAME};"))
        print(f"Database '{DB_NAME}' created successfully.")
    else:
        print(f"Database '{DB_NAME}' already exists.")

# 2. Connect directly to the newly created international_debt_db
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

print("\n--- Processing and Uploading Datasets to PostgreSQL ---")

# Helper function to clean text columns to avoid syntax issues
def clean_dataframe(df):
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip()
    return df

# 3. Upload Country Metadata [cite: 49]
try:
    df_country = pd.read_csv("IDS_CountryMetaData.csv")
    df_country = clean_dataframe(df_country).dropna(subset=['Country Code']).drop_duplicates()
    df_country.to_sql('countries_metadata', con=engine, if_exists='replace', index=False)
    print("✓ 'countries_metadata' table uploaded.")
except Exception as e:
    print(f"Error processing Country Metadata: {e}")

# 4. Upload Series Metadata [cite: 49]
try:
    df_series = pd.read_csv("IDS_SeriesMetaData.csv")
    df_series = clean_dataframe(df_series).dropna(subset=['Series Code']).drop_duplicates()
    df_series.to_sql('indicators_metadata', con=engine, if_exists='replace', index=False)
    print("✓ 'indicators_metadata' table uploaded.")
except Exception as e:
    print(f"Error processing Series Metadata: {e}")

# 5. Upload Main Debt Data [cite: 49]
try:
    df_main = pd.read_csv("IDS_ALLCountries_Data.csv")
    df_main = clean_dataframe(df_main)
    df_main = df_main.dropna(subset=['Country Code', 'Counterpart Area Code', 'Series Code']).drop_duplicates()
    
    # Ensure value column is numeric [cite: 35]
    if 'Value' in df_main.columns:
        df_main['Value'] = pd.to_numeric(df_main['Value'], errors='coerce')
        
    df_main.to_sql('debt_data', con=engine, if_exists='replace', index=False)
    print("✓ 'debt_data' main table uploaded.")
except Exception as e:
    print(f"Error processing Main Debt Data: {e}")

# 6. Apply Constraints (Primary and Foreign Keys) [cite: 53]
print("\n--- Applying Keys and Relationships ---")
with engine.connect() as conn:
    try:
        conn.execute(text("COMMIT;"))
        # Primary Keys [cite: 53]
        conn.execute(text('ALTER TABLE countries_metadata ADD PRIMARY KEY ("Country Code");'))
        conn.execute(text('ALTER TABLE indicators_metadata ADD PRIMARY KEY ("Series Code");'))
        
        # Foreign Keys [cite: 53]
        conn.execute(text('''
            ALTER TABLE debt_data 
            ADD CONSTRAINT fk_country 
            FOREIGN KEY ("Country Code") REFERENCES countries_metadata("Country Code");
        '''))
        conn.execute(text('''
            ALTER TABLE debt_data 
            ADD CONSTRAINT fk_indicator 
            FOREIGN KEY ("Series Code") REFERENCES indicators_metadata("Series Code");
        '''))
        conn.execute(text("COMMIT;"))
        print("✓ Primary and Foreign Keys applied successfully!")
    except Exception as e:
        print(f"Constraints note: {e}")

print("\nPipeline complete. Your data is waiting for you in PostgreSQL!")