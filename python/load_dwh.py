# Library
import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text

# Define the database connection parameters
db_params = {
    'host': '10.5.0.5',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'postgres'
}

# Create a connection to the PostgreSQL server
conn = psycopg2.connect(
    host=db_params['host'],
    database=db_params['database'],
    user=db_params['user'],
    password=db_params['password']
)

# Create a cursor object
cur = conn.cursor()

# Set automatic commit to be true, so that each action is committed without having to call conn.committ() after each command
conn.set_session(autocommit=True)

# Create the 'dwh' database
cur.execute("CREATE DATABASE dwh")

# Commit the changes and close the connection to the default database
conn.commit()
cur.close()
conn.close()

# Connect to the 'dwh' database
db_params['database'] = 'dwh'
engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}')

# Define the file paths for your CSV files
csv_files = {
    'nsw_property_data': '/usr/src/data/nsw_property_data.csv',
    'nsw_property_archived_data': '/usr/src/data/nsw_property_archived_data.csv'
}

# Load and display the contents of each CSV file to check
for table_name, file_path in csv_files.items():
    print(f"Contents of '{table_name}' CSV file:")
    df = pd.read_csv(file_path)
    print(df.head(2))  # Display the first few rows of the DataFrame
    print("\n")

# Loop through the CSV files and import them into PostgreSQL
for table_name, file_path in csv_files.items():
    df = pd.read_csv(file_path)
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    print(f'{table_name} load complete!')