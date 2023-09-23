from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime, timedelta
import pandas as pd
import csv

app = Flask(__name__)

current_year = datetime.now().year


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


handle_no_file_found()


def write_entry_to_file(data):
    with open("./logs.csv", 'a', newline='') as tanker_logs:
        fieldnames = ['Name', 'Date', 'Time', 'Payment Mode', 'Payment Status', 'Amount (Rs.)', 'Note']
        writer = csv.DictWriter(tanker_logs, fieldnames=fieldnames)

        if tanker_logs.tell() == 0:
            writer.writeheader()
            writer.writerow(data)
        else:
            writer.writerow(data)


def delete_last_entry():
    logs = pd.read_csv('./logs.csv')
    if not logs.empty:
        logs = logs.iloc[:-1]
        logs.to_csv("./logs.csv", index=False)
        print("Last line deleted from the CSV file.")
    else:
        print("CSV file is empty.")


def data_in_range_date(data, start, end):
    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    date_range = []
    while start_date <= end_date:
        date_range.append(start_date.strftime("%Y-%m-%d"))
        start_date += timedelta(days=1)

    refined = data[data['Date'].isin(date_range)]

    return refined


def get_amount_sum(data):
    all_pending_payments = data[data["Payment Status"] == "Pending"]
    return all_pending_payments["Amount (Rs.)"].sum()


def update_dataframe(name, amt):
    df = pd.read_csv('./logs.csv')
    filtered = df[(df['Name'] == name) & (df["Payment Status"] == "Pending")]

    for index, row in filtered.iterrows():

        if amt >= row['Amount (Rs.)']:
            df.at[index, 'Payment Status'] = 'Paid'
            amt -= row['Amount (Rs.)']
        print("Updating")

    df.to_csv('./logs.csv', index=False)


@app.route("/")
def home():
    data = pd.read_csv('./logs.csv')[::-1]
    return render_template("index.html", footer_cpr_year=current_year, data_table_bool=True, data_table=data)


@app.route("/entry", methods=["POST", "GET"])
def entry_page():
    tanker_logs = pd.read_csv('./logs.csv')
    try:
        default_date = tanker_logs.tail(1)['Date'].item()
        last_time = tanker_logs.tail(1)["Time"].item()
    except:
        default_date = None
        last_time = None

    entry_status = False

    if request.method == "POST":

        if request.form.get('delete_btn') == "delete_btn":
            delete_last_entry()

        elif request.form.get('submit') == "Submit":
            form_data = {
                'Name': request.form['name'],
                'Date': request.form['date'],
                'Time': request.form['time'],
                'Payment Mode': request.form['payment_mode'],
                'Payment Status': request.form['payment_status'],
                'Amount (Rs.)': request.form['amount'],
                'Note': request.form['note']
            }
            entry_status = True
            write_entry_to_file(form_data)

    tanker_logs = pd.read_csv('./logs.csv')
    last_row = tanker_logs.tail(1)
    return render_template("entry.html", footer_cpr_year=current_year,
                           entry_status_content=entry_status, default_date=default_date,
                           last_time=last_time, last_log=last_row)


@app.route("/retrieve", methods=["GET", "POST"])
def retrieve_page():
    if request.method == "POST":
        if request.form.get('logs_by_date') == "Retrieve by Date":
            data = pd.read_csv('./logs.csv')
            date = request.form.get('specified-date')
            in_range = data_in_range_date(data, date, date)
            return render_template("retrieve.html", footer_cpr_year=current_year,
                                   data_table=in_range, data_table_bool=True, amount_sum=get_amount_sum(in_range))

        if request.form.get('logs_today') == "Retrieve Today's Log":
            data = pd.read_csv('./logs.csv')
            today = datetime.now().strftime("%Y-%m-%d")
            in_range = data_in_range_date(data, today, today)
            return render_template("retrieve.html", footer_cpr_year=current_year,
                                   data_table=in_range, data_table_bool=True, amount_sum=get_amount_sum(in_range))

        elif request.form.get('submit') == "Submit":
            name = request.form['name']
            start_date = request.form['startDate']
            end_date = request.form['endDate']
            tanker_logs = pd.read_csv('./logs.csv')
            all_matching_names = tanker_logs[tanker_logs['Name'] == name]
            in_range = data_in_range_date(all_matching_names, start_date, end_date)
            return render_template("retrieve.html", footer_cpr_year=current_year,
                                   data_table=in_range, data_table_bool=True, amount_sum=get_amount_sum(in_range))
    return render_template("retrieve.html", footer_cpr_year=current_year,
                           data_table=None, data_table_bool=False)


@app.route("/update-pay-info", methods=["GET", "POST"])
def update_pay_info_page():
    if request.method == 'POST':
        if request.form.get('update') == 'Update':
            name = request.form.get('name')
            paid_amt = request.form.get('paid_amount')
            mode = request.form.get('payment_mode')
            update_dataframe(name, int(paid_amt))
            return render_template('./update_payment.html', update_succeed=True)
    else:
        return render_template('./update_payment.html')


@app.route('/download-logs')
def download_logs():
    response = send_file("./logs.csv", as_attachment=True)
    return response


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
