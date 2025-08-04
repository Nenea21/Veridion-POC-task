import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.types import String, Float
import urllib
import os

# Database connection
params = urllib.parse.quote_plus(
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost\\SQLEXPRESS;"  # Adjust if needed
    "Database=Veridion;"
    "Trusted_Connection=yes;"
)

engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

# Table definitions with correct data types (updated to include match_reason)
table_definitions = {
    "veridion_analysis_best_matches": {
        "input_row_key": String(255),
        "veridion_id": String(255),
        "candidate_name": String(255),
        "name_similarity": Float,
        "geographic_match": Float,
        "business_context": Float,
        "overall_confidence": Float,
        "recommendation": String(255),
        "match_reason": String(500)  # Added this column
    },
    "veridion_analysis_entity_resolution": {
        "input_row_key": String(255),
        "veridion_id": String(255),
        "candidate_name": String(255),
        "name_similarity": Float,
        "geographic_match": Float,
        "business_context": Float,
        "overall_confidence": Float,
        "recommendation": String(255),
        "match_reason": String(500)  # Added this column
    },
    "veridion_analysis_quality_issues": {
        "veridion_id": String(255),
        "company_name": String(255),
        "issues": String(1000)
    }
}

# Load and insert CSVs
successful_imports = 0
failed_imports = 0

for table_name, dtype_map in table_definitions.items():
    csv_file = f"{table_name}.csv"
    print(f"Processing {csv_file}...")
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"⚠️  Warning: {csv_file} not found. Skipping...")
        failed_imports += 1
        continue
    
    try:
        # Load CSV
        df = pd.read_csv(csv_file)
        
        # Check if DataFrame is empty
        if df.empty:
            print(f"⚠️  Warning: {csv_file} is empty. Skipping...")
            failed_imports += 1
            continue
        
        # Show info about what we're importing
        print(f"   📊 Found {len(df)} rows with columns: {list(df.columns)}")
        
        # Handle missing match_reason column for quality_issues table
        if table_name == "veridion_analysis_quality_issues" and "match_reason" in dtype_map:
            del dtype_map["match_reason"]
        
        # Import to SQL Server (this will DROP and RECREATE the table)
        df.to_sql(table_name, con=engine, if_exists='replace', index=False, dtype=dtype_map)
        
        print(f"✅ Table '{table_name}' replaced and {len(df)} rows inserted.")
        successful_imports += 1
        
    except Exception as e:
        print(f"❌ Error processing {csv_file}: {str(e)}")
        failed_imports += 1

# Summary
print(f"\n📊 Import Summary:")
print(f"✅ Successful imports: {successful_imports}")
print(f"❌ Failed imports: {failed_imports}")

if successful_imports > 0:
    print("🎉 Data import completed.")
else:
    print("⚠️  No data was imported. Please check that CSV files exist and claudiu.py ran successfully.")