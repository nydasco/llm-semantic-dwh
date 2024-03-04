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

try:
    db_params['database'] = 'dwh'
    cur.execute("SELECT * FROM nsw_property_data")

    # Close the connection to the default database
    cur.close()
    conn.close()

    print('Database Already Exists!')
except:
    # Create the 'dwh' database
    cur.execute("CREATE DATABASE dwh")

    # Close the connection to the default database
    cur.close()
    conn.close()

    print('Database Created!')

    # Connect to the 'dwh' database
    db_params['database'] = 'dwh'
    engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}')

    df = pd.read_csv('/usr/src/data/nsw_property_data.csv')
    print(df.head())

    df.to_sql('nsw_property_data', engine, if_exists='replace', index=False, chunksize=5000)

    print('Done')