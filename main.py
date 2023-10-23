from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import pandas as pd
from mysql_queries import *
import configparser

config = configparser.ConfigParser()
config.read('./config.ini')

host = config.get('Database', 'host')
port = config.get('Database', 'port')
user = config.get('Database', 'user')
password = config.get('Database', 'password')
database = config.get('Database', 'database')
current_year = datetime.now().year

engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')

df = pd.read_sql(text(customer_tanker), engine)
app = Flask(__name__)


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


def delete_by_index(row):
    with engine.connect() as conn:
        customer_details = pd.read_sql(f'SELECT * FROM customers '
                                       f'WHERE name = "{row["Name"].item()}"', engine)
        customer_params = {
            "id": customer_details['customer_id'].item(),
            "amount": f"+{customer_details['unit_charge'].item()}"
        }

        conn.execute(text(update_balance), parameters=customer_params)
        conn.execute(text(f"DELETE FROM `sql12654547`.`tanker_records` WHERE (id = {row['id'].item()});"))
        conn.commit()
        print(f"Deleted row with id = {row['id'].item()} from database.")


def data_in_range_date(data, start, end):
    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    date_range = []
    while start_date <= end_date:
        date_range.append(start_date.date().strftime("%d-%m-%Y"))
        start_date += timedelta(days=1)
    refined = data[data['Date'].isin(date_range)]

    return refined


def get_last_entry():
    tanker_logs = pd.read_sql(text(customer_tanker), engine)
    latest_entry = tanker_logs.tail(1)

    try:
        last_date = datetime.strptime(latest_entry["Date"].item(), "%d-%m-%Y").strftime('%Y-%m-%d')
        last_time = datetime.strptime(latest_entry["Time"].item(), "%I:%M %p").strftime('%H:%M:%S')
    except:
        last_date = None
        last_time = None

    return last_date, last_time, latest_entry


@app.route("/", methods=["GET", "POST"])
def home():
    df_home = pd.read_sql(text(customer_tanker), engine)

    if request.method == "POST":
        tanker_id = request.form.get('tanker_id')
        row_to_delete = df_home[df_home['id'] == int(tanker_id)]
        delete_by_index(row_to_delete)
        return redirect(url_for('home'))

    return render_template("index.html", footer_cpr_year=current_year,
                           data_table_bool=True, data_table=df_home.iloc[::-1])


@app.route("/entry", methods=["POST", "GET"])
def entry_page():
    last_date, last_time, latest_entry = get_last_entry()

    entry_status = False

    if request.method == "POST":

        if request.form.get('delete_btn') == "delete_btn":
            delete_by_index(latest_entry)

            return redirect(url_for('entry_page'))

        elif request.form.get('submit') == "Submit":

            form_data = {
                'Name': request.form['name'],
                'Date': request.form['date'],
                'Time': request.form['time']
            }
            insert_tanker_record_to_sql(form_data)

            entry_status = True

            last_date, last_time, latest_entry = get_last_entry()

    return render_template("entry.html", footer_cpr_year=current_year,
                           entry_status_content=entry_status, default_date=last_date,
                           default_time=last_time, last_log=latest_entry)


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
    df_sql.to_csv("./records.csv", index=False)
    response = send_file("./records.csv", as_attachment=True)

    return response


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
