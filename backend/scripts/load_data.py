"""
ETL Script to load historical BVMT data into PostgreSQL.

This script loads CSV and TXT files from the data directory into the database.
"""
import os
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_settings
from core.database import init_db
from core.models import Stock, HistoricalPrice

settings = get_settings()


def parse_date(date_str):
    """Parse date string in various formats."""
    try:
        return pd.to_datetime(date_str, format='%d/%m/%Y')
    except:
        try:
            return pd.to_datetime(date_str, format='%Y-%m-%d')
        except:
            return pd.to_datetime(date_str)


def load_csv_file(filepath):
    """Load CSV file and parse columns."""
    print(f"Loading {filepath}...")
    
    df = pd.read_csv(filepath, delimiter=';', encoding='latin-1')
    
    # Rename columns to standard names
    df = df.rename(columns={
        'SEANCE': 'date',
        'GROUPE': 'groupe',
        'CODE': 'code',
        'VALEUR': 'name',
        'OUVERTURE': 'open',
        'CLOTURE': 'close',
        'PLUS_BAS': 'low',
        'PLUS_HAUT': 'high',
        'QUANTITE_NEGOCIEE': 'volume',
        'NB_TRANSACTION': 'nb_transactions',
        'CAPITAUX': 'capital'
    })
    
    # Parse date
    df['date'] = df['date'].apply(parse_date)
    
    # Convert numeric columns
    numeric_cols = ['open', 'close', 'low', 'high', 'capital']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
    
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(int)
    df['nb_transactions'] = pd.to_numeric(df['nb_transactions'], errors='coerce').fillna(0).astype(int)
    
    return df


def load_txt_file(filepath):
    """Load TXT file (same format as CSV but different extension)."""
    # TXT files are just CSV with semicolon delimiter
    return load_csv_file(filepath)


def map_sector(groupe):
    """Map group code to sector name."""
    sector_mapping = {
        '11': 'Banques et Institutions Financières',
        '12': 'Assurances',
        '13': 'Services aux Consommateurs',
        '14': 'Biens duConsommateur',
        '15': 'Industrie',
        '16': 'Matériaux de Base',
        '17': 'Services aux Collectivités',
        '18': 'Technologies',
    }
    return sector_mapping.get(str(groupe), 'Autre')


def load_all_data(data_dir='../data'):
    """Load all historical data files into database."""
    print("Initializing database...")
    init_db()
    
    db_url = settings.database_url.replace('postgresql://', 'postgresql+psycopg://')
    engine = create_engine(db_url)
    
    # Get list of data files
    data_files = []
    for file in os.listdir(data_dir):
        if file.startswith('histo_cotation') and (file.endswith('.csv') or file.endswith('.txt')):
            data_files.append(os.path.join(data_dir, file))
    
    data_files.sort()
    
    print(f"Found {len(data_files)} data files")
    
    # Load all files and concatenate
    all_data = []
    for filepath in data_files:
        if filepath.endswith('.csv'):
            df = load_csv_file(filepath)
        else:
            df = load_txt_file(filepath)
        all_data.append(df)
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    
    print(f"Total records loaded: {len(combined_df)}")
    
    # Extract unique stocks
    unique_stocks = combined_df[['code', 'name', 'groupe']].drop_duplicates()
    
    print(f"Unique stocks: {len(unique_stocks)}")
    
    # Insert or update stocks
    stock_map = {}
    for _, row in unique_stocks.iterrows():
        # Generate ticker from first few letters of name
        ticker = ''.join(filter(str.isalnum, row['name']))[:6].upper()
        
        # Check if stock exists
        with engine.connect() as conn:
            result = conn.execute(
                f"SELECT id FROM stocks WHERE code = '{row['code']}' OR ticker = '{ticker}'"
            )
            existing = result.fetchone()
            
            if existing:
                stock_id = existing[0]
            else:
                # Insert new stock
                result = conn.execute(
                    f"""INSERT INTO stocks (ticker, name, code, groupe, sector) 
                        VALUES ('{ticker}', '{row['name'].replace("'", "''")}', '{row['code']}', 
                                '{row['groupe']}', '{map_sector(row['groupe'])}') 
                        RETURNING id"""
                )
                stock_id = result.fetchone()[0]
                conn.commit()
                print(f"Added stock: {ticker} - {row['name']}")
        
        stock_map[row['code']] = stock_id
    
    # Prepare historical prices data
    print("Preparing price data...")
    combined_df['stock_id'] = combined_df['code'].map(stock_map)
    
    # Select only required columns
    price_df = combined_df[[
        'stock_id', 'date', 'open', 'high', 'low', 'close', 
        'volume', 'nb_transactions', 'capital'
    ]].dropna(subset=['stock_id', 'date', 'close'])
    
    print(f"Inserting {len(price_df)} price records...")
    
    # Insert in batches
    batch_size = 10000
    for i in range(0, len(price_df), batch_size):
        batch = price_df.iloc[i:i+batch_size]
        batch.to_sql('historical_prices', engine, if_exists='append', index=False)
        print(f"Inserted batch {i//batch_size + 1}/{(len(price_df)-1)//batch_size + 1}")
    
    print("✅ Data loading complete!")
    print(f"Total stocks: {len(unique_stocks)}")
    print(f"Total price records: {len(price_df)}")
    
    # Create TimescaleDB hypertable if not exists
    with engine.connect() as conn:
        try:
            conn.execute(
                "SELECT create_hypertable('historical_prices', 'date', if_not_exists => TRUE);"
            )
            conn.commit()
            print("✅ TimescaleDB hypertable created")
        except Exception as e:
            print(f"Note: TimescaleDB hypertable creation skipped: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Load BVMT historical data')
    parser.add_argument('--data-dir', default='../data', help='Path to data directory')
    args = parser.parse_args()
    
    load_all_data(args.data_dir)
