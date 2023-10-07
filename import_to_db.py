from datetime import datetime
from sqlalchemy import create_engine, text
import pandas as pd
from mysql_queries import *

host = '127.0.0.1'
user = 'root'
password = 'bharti'
port = 3306
database = "water_tanker_records"

engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/')
df = pd.read_csv('./logs.csv')

# Getting DB ready (DB and tables creation)
with engine.connect() as conn:
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {database};"))
    conn.execute(text(f"USE {database};"))
    for statement in create_required_tables:
        conn.execute(text(statement))

# Importing csv to tables in DB
# -- customers --
# for name in df['Name'].unique().tolist():
#     count = int(df["Name"][df["Name"] == name].count())
#
#     params = {
#         'name': name,
#         'unit_charge': 70,
#         'total_units': count,
#         'balance': 70 * count
#     }
#     with engine.connect() as conn:
#         conn.execute(text(insert_customer), parameters=params)
#         conn.commit()
#
# # # -- records --
# for index, row in df.iterrows():
#
#     params = {
#         'customer_id': pd.read_sql(f"SELECT customer_id FROM customers "
#                                    f"WHERE name ='{row['Name']}'", engine)['customer_id'].item(),
#         'date': row['Date'],
#         'time': row['Time']
#     }
#     with engine.connect() as conn:
#         conn.execute(text(insert_tanker_record), parameters=params)
#         conn.commit()

# -- payments --
for index, row in df.iterrows():

    params = {
        'customer_id': pd.read_sql(f"SELECT customer_id FROM customers "
                                   f"WHERE name ='{row['Name']}';", engine)['customer_id'].item(),
        'date': row,
        'paid_amount': int(df[df['Payment Status'] == "Paid"]['Payment Status'].count()) * 70
    }
    with engine.connect() as conn:
        conn.execute(text(insert_payment), parameters=params)
        conn.commit()

df_sql = pd.read_sql("SELECT * FROM payments  ", engine)
print(df_sql)
