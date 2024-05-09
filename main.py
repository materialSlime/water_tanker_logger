from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime
from sqlalchemy import create_engine, text
import pandas as pd
from mysql_queries import *
from env_vars import *

current_year = datetime.now().year

engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')

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
            "amount": f"-{customer_details['unit_charge'].item()}",
            "unit": f'+1'
        }
        conn.execute(text(insert_tanker_record), parameters=params)
        conn.execute(text(update_balance_and_unit), parameters=customer_params)
        conn.commit()


def delete_by_index(row_id):
    with engine.connect() as conn:
        tanker_details = pd.read_sql(f'SELECT * FROM tanker_records '
                                     f'WHERE id = "{row_id}"', engine)

        customer_details = pd.read_sql(f'SELECT * FROM customers '
                                       f'WHERE customer_id = "{tanker_details["customer_id"].item()}"', engine)

        customer_params = {
            "id": customer_details['customer_id'].item(),
            "amount": f"+{customer_details['unit_charge'].item()}",
            'unit': '-1'
        }

        conn.execute(text(update_balance_and_unit), parameters=customer_params)
        conn.execute(text(f"DELETE FROM `{database}`.`tanker_records` WHERE id = {row_id};"))
        conn.commit()
        print(f"Deleted row with id = {row_id} from database.")


def get_last_entry():
    tanker_logs = pd.read_sql(text(customer_tanker), engine)
    latest_entry = tanker_logs.head(1)

    try:
        last_date = datetime.strptime(latest_entry["Date"].item(), "%d-%m-%Y").strftime('%Y-%m-%d')
        last_time = datetime.strptime(latest_entry["Time "].item(), "%I:%M %p").strftime('%H:%M:%S')
    except:
        last_date = None
        last_time = None

    return last_date, last_time, latest_entry


@app.route("/", methods=["GET", "POST"])
def home():
    df_home = pd.read_sql(text(customer_tanker), engine)

    if request.method == "POST":
        tanker_id = request.form.get('tanker_id')
        delete_by_index(tanker_id)
        return redirect(url_for('home'))

    return render_template("index.html", footer_cpr_year=current_year,
                           visibility=['table', 'delete_column'], data_table=df_home)


@app.route("/entry", methods=["POST", "GET"])
def entry_page():
    last_date, last_time, latest_entry = get_last_entry()

    entry_status = False

    if request.method == "POST":

        if request.form.get('delete_btn') == "delete_btn":
            delete_by_index(latest_entry['id'].item())
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
    is_balance = None
    if request.method == "POST":
        in_range = None
        c_balance = 0
        name = None

        if request.form.get('logs_by_date') == "Retrieve by Date":
            date = request.form.get('specified-date')
            in_range = pd.read_sql(text(tanker_by_date_range.format(s_date=date, e_date=date)), engine)

        if request.form.get('logs_today') == "Retrieve Today's Log":
            today = datetime.now().strftime("%Y-%m-%d")
            in_range = pd.read_sql(text(tanker_by_date_range.format(s_date=today, e_date=today)), engine)

        elif request.form.get('submit') == "Submit":
            name = request.form['name']
            start_date = request.form['startDate']
            end_date = request.form['endDate']

            in_range = pd.read_sql(text(tanker_by_date_range.format(s_date=start_date, e_date=end_date)), engine)
            in_range = in_range[in_range['Name'] == name]
            is_balance = 'balance'

            c_balance = pd.read_sql(f"SELECT balance FROM customers "
                                    f"WHERE name = '{name}'", engine)['balance'].item()

        return render_template("retrieve.html", footer_cpr_year=current_year,
                               data_table=in_range,
                               c_balance=c_balance, visibility=['table', 'delete_column', 'footer', is_balance])
    return render_template("retrieve.html", footer_cpr_year=current_year, data_table=None,
                           visibility=[])


@app.route("/manage-accounts", methods=["GET", "POST"])
def manage_accounts():
    if request.method == 'POST':
        if request.form.get('update') == 'Update':
            cs_id = pd.read_sql(f"SELECT customer_id FROM customers "
                                f"WHERE name = '{request.form.get('name')}'", engine)['customer_id'].item()
            payment_params = {
                "customer_id": cs_id,
                "date": datetime.now().date(),
                "paid_amount": request.form.get('paid_amount')
            }

            customer_params = {
                "id": cs_id,
                "amount": request.form.get('paid_amount')
            }

            with engine.connect() as conn:
                conn.execute(text(insert_payment), parameters=payment_params)
                conn.execute(text(update_balance_only), parameters=customer_params)
                conn.commit()

            balance_df = pd.read_sql(text(customers), engine)

        elif request.form.get('retrieve') == 'By Name':
            name = request.form.get('name')
            payments_df = pd.read_sql(text(get_payments), engine)
            return render_template('./manage_accounts.html', data_table=payments_df[payments_df['Name'] == name],
                                   footer_cpr_year=current_year, visibility=['table'])

        elif request.form.get('retrieve') == 'All':
            payments_df = pd.read_sql(text(get_payments), engine)
            return render_template('./manage_accounts.html', data_table=payments_df,
                                   footer_cpr_year=current_year, visibility=['table'])

        elif request.form.get('add-account') == 'Add':
            charge = request.form.get('charge')
            username = request.form.get('account-name')
            account_params = {
                "name": username,
                "total_units": 0,
                "unit_charge": charge,
                "balance": 0
            }
            with engine.connect() as conn:
                conn.execute(text(insert_customer), parameters=account_params)
                conn.commit()

    balance_df = pd.read_sql(text(customers), engine)
    return render_template('./manage_accounts.html', data_table=balance_df,
                           footer_cpr_year=current_year, visibility=['table'])


@app.route('/download-logs')
def download_logs():
    df_sql = pd.read_sql(text(customer_tanker), engine)
    df_sql.to_csv("./records.csv", index=False)
    response = send_file("./records.csv", as_attachment=True)

    return response


if __name__ == "__main__":
    app.run(debug=debug, host="0.0.0.0", port=80)
