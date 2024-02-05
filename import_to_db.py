from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
from mysql_queries import *
from env_vars import *

print(host, type(host))
print(port, user, password, database)

current_year = datetime.now().year

engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/')
df = pd.read_csv('./logs.csv')

# Getting DB ready (DB and tables creation)
with engine.connect() as conn:
    conn.execute(text(f"DROP DATABASE {database};"))
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {database};"))
    conn.execute(text(f"USE {database};"))
    for statement in create_required_tables:
        conn.execute(text(statement))

# Importing csv to tables in DB
# -- customers --
for name in df['Name'].unique().tolist():

    count = int(df["Name"][df["Name"] == name].count())

    unit_charge = 100
    if name in ("Brijpal", "Parvat", "Jain"):
        unit_charge = 70
    elif name == "Imrat":
        unit_charge = 60

    params = {
        'name': name,
        'unit_charge': unit_charge,
        'total_units': count,
        'balance': 70 * count
    }
    with engine.connect() as conn:
        conn.execute(text(insert_customer), parameters=params)
        conn.commit()

# # -- records --
for index, row in df.iterrows():
    params = {
        'customer_id': pd.read_sql(f"SELECT customer_id FROM customers "
                                   f"WHERE name ='{row['Name']}'", engine)['customer_id'].item(),
        'date': row['Date'],
        'time': row['Time']
    }
    with engine.connect() as conn:
        conn.execute(text(insert_tanker_record), parameters=params)
        conn.commit()

# -- payments --
for index, row in pd.read_sql("SELECT * FROM customers;", engine).iterrows():
    params = {
        'customer_id': row['customer_id'],
        'date': "2023-09-30",
        'paid_amount': int(df[(df['Name'] == row['name']) & (df['Payment Status'] == "Paid")]['Name'].count()) * 70
    }

    # print(params)
    with engine.connect() as conn:
        conn.execute(text(insert_payment), parameters=params)
        conn.commit()

# -- adjust balance --
with engine.connect() as conn:
    conn.execute(text("""
        UPDATE customers AS c
            SET balance =
                (SELECT paid_amount
                 FROM payments AS p
                 WHERE p.customer_id = c.customer_id) - balance;
         """))
    conn.commit()

with engine.connect() as conn:
    conn.execute(text("""
        UPDATE customers AS c
            SET unit_charge = 70
            WHERE name = "Imrat";
         """))
    conn.commit()

df_sql = pd.read_sql("SELECT * FROM customers  ", engine)
print(df_sql)
