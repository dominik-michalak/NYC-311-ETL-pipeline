import pandas as pd
from sqlalchemy import create_engine, text
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'mojabaza')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

print("=" * 60)
print("ETL PIPELINE: public.nyc_311_raw → etl.* (Star Schema)")
print("=" * 60)

print("\n[1/4] EXTRACT - Reading from public.nyc_311_raw...")
df = pd.read_sql("SELECT * FROM public.nyc_311_raw", engine)
print(f"      Extracted: {len(df):,} rows, {len(df.columns)} columns")

print("\n[2/4] TRANSFORM - Cleaning data...")

df.columns = df.columns.str.lower().str.strip()

df = df.dropna(subset=['unique_key', 'created_date', 'complaint_type'])

df['created_date'] = pd.to_datetime(df['created_date'], errors='coerce')
df['closed_date'] = pd.to_datetime(df['closed_date'], errors='coerce')

df['complaint_type'] = df['complaint_type'].astype(str).str.strip().str.title()
df['descriptor'] = df['descriptor'].fillna('Unknown').astype(str).str.strip().str.title()
df['borough'] = df['borough'].fillna('Unspecified').astype(str).str.strip().str.upper()

borough_map = {
    'MANHATTAN': 'Manhattan',
    'BROOKLYN': 'Brooklyn',
    'QUEENS': 'Queens',
    'BRONX': 'Bronx',
    'STATEN ISLAND': 'Staten Island',
    'STATEN_ISLAND': 'Staten Island',
    'UNSPECIFIED': 'Unknown'
}
df['borough'] = df['borough'].replace(borough_map)

def map_category(ct):
    ct_lower = str(ct).lower()
    if 'noise' in ct_lower:
        return 'Noise'
    elif 'parking' in ct_lower or 'blocked driveway' in ct_lower:
        return 'Parking'
    elif 'sanitation' in ct_lower or 'dirty' in ct_lower or 'rodent' in ct_lower:
        return 'Sanitation'
    elif 'water' in ct_lower or 'plumbing' in ct_lower or 'heating' in ct_lower:
        return 'Infrastructure'
    elif 'street' in ct_lower or 'sidewalk' in ct_lower or 'traffic' in ct_lower:
        return 'Transportation'
    elif 'vehicle' in ct_lower or 'taxi' in ct_lower:
        return 'Vehicle'
    else:
        return 'Other'

df['category'] = df['complaint_type'].apply(map_category)

df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

df['incident_zip'] = df['incident_zip'].astype(str).str.extract(r'(\d{5})')[0]
df['incident_zip'] = df['incident_zip'].fillna('Unknown')

df['status'] = df['status'].astype(str).str.strip().str.title()

print(f"      After cleaning: {len(df):,} rows")

print("\n[3/4] Creating dimension tables...")

dim_complaint = df[['complaint_type', 'category']].drop_duplicates().reset_index(drop=True)
dim_complaint['complaint_type_id'] = range(1, len(dim_complaint) + 1)

dim_borough = df[['borough']].drop_duplicates().reset_index(drop=True)
borough_codes = {'Manhattan': 'MN', 'Brooklyn': 'BK', 'Queens': 'QN', 'Bronx': 'BX', 'Staten Island': 'SI', 'Unknown': 'UN'}
dim_borough['borough_code'] = dim_borough['borough'].map(borough_codes).fillna('UN')
dim_borough['borough_id'] = range(1, len(dim_borough) + 1)
dim_borough.rename(columns={'borough': 'borough_name'}, inplace=True)

dates = pd.to_datetime(df['created_date']).dt.date.unique()
dim_date = pd.DataFrame({'full_date': dates})
dim_date['date_id'] = range(1, len(dim_date) + 1)
dim_date['year'] = pd.to_datetime(dim_date['full_date']).dt.year
dim_date['month'] = pd.to_datetime(dim_date['full_date']).dt.month
dim_date['day_of_week'] = pd.to_datetime(dim_date['full_date']).dt.day_name()
dim_date['is_weekend'] = pd.to_datetime(dim_date['full_date']).dt.dayofweek >= 5

print(f"      Complaint types: {len(dim_complaint)}")
print(f"      Boroughs: {len(dim_borough)}")
print(f"      Dates: {len(dim_date)}")

print("\n[4/4] Creating fact table...")

fact = df.merge(dim_complaint[['complaint_type', 'complaint_type_id']], on='complaint_type', how='left')
fact = fact.merge(dim_borough[['borough_name', 'borough_id']], left_on='borough', right_on='borough_name', how='left')

fact_cols = ['unique_key', 'created_date', 'closed_date', 'complaint_type_id', 'borough_id',
             'descriptor', 'location_type', 'incident_zip', 'latitude', 'longitude', 'status']
fact_cols = [c for c in fact_cols if c in fact.columns]
fact_df = fact[fact_cols].copy()
fact_df.insert(0, 'request_id', range(1, len(fact_df) + 1))

print(f"      Fact table: {len(fact_df):,} rows")

print("\nLoading to PostgreSQL...")

with engine.connect() as conn:
    conn.execute(text("DROP SCHEMA IF EXISTS etl CASCADE;"))
    conn.execute(text("CREATE SCHEMA etl;"))
    
    conn.execute(text("""
        CREATE TABLE etl.dim_complaint_type (
            complaint_type_id SERIAL PRIMARY KEY,
            complaint_type VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL
        );
    """))
    
    conn.execute(text("""
        CREATE TABLE etl.dim_borough (
            borough_id SERIAL PRIMARY KEY,
            borough_name VARCHAR(50) NOT NULL,
            borough_code CHAR(2) NOT NULL
        );
    """))
    
    conn.execute(text("""
        CREATE TABLE etl.dim_date (
            date_id SERIAL PRIMARY KEY,
            full_date DATE NOT NULL UNIQUE,
            year INT NOT NULL,
            month INT NOT NULL,
            day_of_week VARCHAR(10) NOT NULL,
            is_weekend BOOLEAN NOT NULL
        );
    """))
    
    conn.execute(text("""
        CREATE TABLE etl.service_requests (
            request_id SERIAL PRIMARY KEY,
            unique_key VARCHAR(20) NOT NULL UNIQUE,
            created_date TIMESTAMP NOT NULL,
            closed_date TIMESTAMP,
            complaint_type_id INT REFERENCES etl.dim_complaint_type(complaint_type_id),
            borough_id INT REFERENCES etl.dim_borough(borough_id),
            descriptor TEXT,
            location_type VARCHAR(100),
            incident_zip VARCHAR(10),
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            status VARCHAR(20) NOT NULL
        );
    """))
    
    conn.execute(text("""
        CREATE INDEX idx_sr_created ON etl.service_requests(created_date);
        CREATE INDEX idx_sr_borough ON etl.service_requests(borough_id);
        CREATE INDEX idx_sr_complaint ON etl.service_requests(complaint_type_id);
    """))
    
    conn.commit()

dim_complaint.to_sql('dim_complaint_type', engine, schema='etl', if_exists='append', index=False)
dim_borough.to_sql('dim_borough', engine, schema='etl', if_exists='append', index=False)
dim_date.to_sql('dim_date', engine, schema='etl', if_exists='append', index=False)

fact_df.to_sql('service_requests', engine, schema='etl', if_exists='append', index=False)

print("\nPreparation of a table")

powerbi_df = fact_df.merge(dim_borough[['borough_id', 'borough_name']], on='borough_id', how='left')
powerbi_df = powerbi_df.merge(dim_complaint[['complaint_type_id', 'complaint_type', 'category']], on='complaint_type_id', how='left')
powerbi_df = powerbi_df.merge(dim_date, left_on=pd.to_datetime(fact_df['created_date']).dt.date.astype(str), right_on=dim_date['full_date'].astype(str), how='left')

powerbi_df.to_csv('powerbi_master_data.csv', index=False)
print("powerbi_master_data.csv file was generated.")

print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

with engine.connect() as conn:
    for table in ['dim_complaint_type', 'dim_borough', 'dim_date', 'service_requests']:
        result = conn.execute(text(f"SELECT COUNT(*) FROM etl.{table}"))
        count = result.scalar()
        print(f"  etl.{table}: {count:,} rows")

print("\n" + "=" * 60)
print("ETL PIPELINE COMPLETE!")
print("=" * 60)
print("\nYou can now query the star schema in pgAdmin4 / DBeaver:")
print("  - etl.service_requests (fact table)")
print("  - etl.dim_complaint_type")
print("  - etl.dim_borough")
print("  - etl.dim_date")