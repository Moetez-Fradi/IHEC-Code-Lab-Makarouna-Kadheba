import pandas as pd
from sqlalchemy import create_engine
import os
import glob
import dotenv

dotenv.load_env()

xls_dir_path = "./xls_files"
postgres_url = os.getenv("POSTGRES_URL")

engine = create_engine(postgres_url)

for xls_file_path in glob.glob(os.path.join(xls_dir_path, "*.xls*")):
    table_name = os.path.splitext(os.path.basename(xls_file_path))[0]
    
    df = pd.read_excel(xls_file_path)
    df.columns = [c.strip().replace(' ', '_').replace('.', '').replace('-', '_') for c in df.columns]
    
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    print(f"Data from {xls_file_path} saved to table '{table_name}' successfully.")
