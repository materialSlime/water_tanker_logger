from datetime import datetime, timedelta
import pandas as pd


def update_dataframe(name, amt):

    df = pd.read_csv('./logs.csv')
    filtered = df[(df['Name'] == name) & (df["Payment Status"] == "Pending")]

    print(df[(df['Name'] == name) & (df["Payment Status"] == "Pending")])
    for index, row in filtered.iterrows():

        if amt >= row['Amount (Rs.)']:
            df.at[index, 'Payment Status'] = 'Paid'
            amt -= row['Amount (Rs.)']

    print(df[(df['Name'] == name) & (df["Payment Status"] == "Pending")])
    df.to_csv('./logs2.csv')


update_dataframe("Imrat", 60*5)
