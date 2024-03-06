#!/bin/python

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

# Set automatic commit to be true, so that each action is committed without having to call conn.commit() after each command
conn.set_session(autocommit=True)

try:
    db_params['database'] = 'dwh'
    engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}')
    sql = "SELECT * FROM nsw_property_data"

    nsw_property_data_test = pd.read_sql(sql, engine)

    print('Database Already Exists!')
except:
    # Create the 'dwh' database
    cur = conn.cursor()
    cur.execute("DROP DATABASE dwh")
    cur.execute("CREATE DATABASE dwh")
    cur.close()
    conn.close()

    print('Database Created!')

    # Connect to the 'dwh' database
    db_params['database'] = 'dwh'
    engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}')

    df = pd.read_csv('/usr/src/data/nsw_property_data.csv')

    df.astype({
        'property_id': 'float',
        'download_date': 'string',
        'council_name': 'string',
        'purchase_price': 'float',
        'address': 'string',
        'post_code': 'string',
        'property_type': 'string',
        'strata_lot_number': 'string',
        'property_name': 'string',
        'area': 'float',
        'area_type': 'string',
        'contract_date': 'string',
        'settlement_date': 'string',
        'zoning': 'string',
        'nature_of_property': 'string',
        'primary_purpose': 'string',
        'legal_description': 'string'
    })

    df['download_date'] = pd.to_datetime(df['download_date'], errors = 'coerce')
    df['contract_date'] = pd.to_datetime(df['contract_date'], errors = 'coerce')
    df['settlement_date'] = pd.to_datetime(df['settlement_date'], errors = 'coerce')

    start_date = '2000-01-01'
    end_date = '2023-12-31'

    df2 = df[df["contract_date"].isin(pd.date_range(start_date, end_date))]

    df2.to_sql('nsw_property_data', engine, if_exists='replace', index=False, chunksize=5000)

    print('Done')