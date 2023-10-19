from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import pandas as pd
import csv
from mysql_queries import *

host = 'sql12.freemysqlhosting.net'
user = 'sql12654547'
password = 'Nt6PqNw1Cd'
port = 3306
database = "sql12654547"
current_year = datetime.now().year

engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')

df = pd.read_sql(text(customer_tanker), engine)
app = Flask(__name__)


def handle_no_file_found():
    try:
        data = pd.read_csv('./logs.csv')
    except FileNotFoundError:
        with open("./logs.csv", 'a', newline='') as tanker_logs:
            fieldnames = ['Name', 'Date', 'Time', 'Payment Mode', 'Payment Status', 'Amount (Rs.)', 'Note']
            writer = csv.DictWriter(tanker_logs, fieldnames=fieldnames)

            if tanker_logs.tell() == 0:
                writer.writeheader()
                print("No logs file found, but one is created with with give fieldnames")
        data = pd.read_csv('./logs.csv')


# handle_no_file_found()


def insert_tanker_record_to_sql(data):
    with engine.connect() as conn:
        customer_details = pd.read_sql(f'SELECT * FROM customers '
                                       f'WHERE name = "{data["Name"]}"', engine)

        params = {
            'customer_id': customer_details['customer_id'].item(),
            'date': data['Date'],
            'time': data['Time']
        }
        customer_params = {
            "id": customer_details['customer_id'].item(),
            "amount": f"-{customer_details['unit_charge'].item()}"
        }
        conn.execute(text(insert_tanker_record), parameters=params)
        conn.execute(text(update_balance), parameters=customer_params)
        conn.commit()


def delete_last_entry():
    params = {
        'customer_id': customer_details['customer_id'].item(),
        'date': data['Date'],
        'time': data['Time']
    }
    customer_params = {
        "id": customer_details['customer_id'].item(),
        "amount": f"-{customer_details['unit_charge'].item()}"
    }
    with engine.connect() as conn:
        conn.execute(text(insert_tanker_record), parameters=params)
        conn.execute(text(update_balance), parameters=customer_params)
        conn.commit()

    logs = pd.read_csv('./logs.csv')
    if not logs.empty:
        logs = logs.iloc[:-1]
        logs.to_csv("./logs.csv", index=False)
        print("Last line deleted from the CSV file.")
    else:
        print("CSV file is empty.")


def delete_by_index(index):
    with engine.connect() as conn:
        conn.execute()
        conn.commit()

    logs = pd.read_csv('./logs.csv')
    if not logs.empty:
        logs = logs.drop(int(index))
        logs.to_csv("./logs.csv", index=False)
        print(f"Line with index:{index} is deleted from the CSV file.")
    else:
        print("CSV file is empty.")


def data_in_range_date(data, start, end):
    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    date_range = []
    while start_date <= end_date:
        date_range.append(start_date.date())
        start_date += timedelta(days=1)
    refined = data[data['Date'].isin(date_range)]

    return refined


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if request.form.get('table-index'):
            delete_by_index(request.form.get('table-index'))
    data = pd.read_sql(text(customer_tanker), engine)
    return render_template("index.html", footer_cpr_year=current_year,
                           data_table_bool=True, data_table=data)


@app.route("/entry", methods=["POST", "GET"])
def entry_page():
    tanker_logs = pd.read_sql(text(customer_tanker), engine)
    try:
        last_date = tanker_logs.tail(1)['date'].item()
        last_time = tanker_logs.tail(1)["time"].item()
    except:
        last_date = None
        last_time = None

    entry_status = False

    if request.method == "POST":

        if request.form.get('delete_btn') == "delete_btn":
            delete_last_entry()

        elif request.form.get('submit') == "Submit":
            form_data = {
                'Name': request.form['name'],
                'Date': request.form['date'],
                'Time': request.form['time']
            }
            entry_status = True
            insert_tanker_record_to_sql(form_data)

    tanker_logs = pd.read_sql(text(customer_tanker), engine)
    latest_row = tanker_logs.head(1)

    return render_template("entry.html", footer_cpr_year=current_year,
                           entry_status_content=entry_status, default_date=last_date,
                           last_time=last_time, last_log=latest_row)


@app.route("/retrieve", methods=["GET", "POST"])
def retrieve_page():
    if request.method == "POST":
        in_range = None
        c_balance = 0
        data = pd.read_sql(text(customer_tanker), engine)
        if request.form.get('logs_by_date') == "Retrieve by Date":
            date = request.form.get('specified-date')
            in_range = data_in_range_date(data, date, date)

        if request.form.get('logs_today') == "Retrieve Today's Log":
            today = datetime.now().strftime("%Y-%m-%d")
            in_range = data_in_range_date(data, today, today)

        elif request.form.get('submit') == "Submit":
            name = request.form['name']
            start_date = request.form['startDate']
            end_date = request.form['endDate']
            tanker_logs = pd.read_sql(text(customer_tanker), engine)
            all_matching_names = tanker_logs[tanker_logs['Name'] == name]
            in_range = data_in_range_date(all_matching_names, start_date, end_date)

            c_balance = pd.read_sql(f"SELECT balance FROM customers "
                                    f"WHERE name = '{name}'", engine)['balance'].item()

        return render_template("retrieve.html", footer_cpr_year=current_year,
                               data_table=in_range, data_table_bool=True, c_balance=c_balance)
    return render_template("retrieve.html", footer_cpr_year=current_year,
                           data_table=None, data_table_bool=False)


@app.route("/update-pay-info", methods=["GET", "POST"])
def payment_entry_page():
    if request.method == 'POST':
        if request.form.get('update') == 'Update':
            cs_id = pd.read_sql(f"SELECT customer_id FROM customers "
                                f"WHERE name = '{request.form.get('name')}'", engine)['customer_id'].item()
            payment_params = {
                "customer_id": cs_id,
                "date": datetime.now().date(),
                "paid_amount": request.form.get('paid_amount')
                # "mode" : request.form.get('payment_mode')
            }

            customer_params = {
                "id": cs_id,
                "amount": request.form.get('paid_amount')
            }

            with engine.connect() as conn:
                conn.execute(text(insert_payment), parameters=payment_params)
                conn.execute(text(update_balance), parameters=customer_params)
                conn.commit()

            return render_template('./payment_entry.html', update_succeed=True)
    else:
        return render_template('./payment_entry.html')


@app.route('/download-logs')
def download_logs():
    df_sql = pd.read_sql(text(customer_tanker), engine)
    df_sql.to_csv("./records.csv")
    response = send_file("./records.csv", as_attachment=True)

    return response


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
