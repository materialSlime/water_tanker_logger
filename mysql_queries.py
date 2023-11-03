create_required_tables = [
    """
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(25),
        unit_charge INT,
        total_units INT,
        balance INT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tanker_records (
        id INT AUTO_INCREMENT PRIMARY KEY,
        customer_id INT,
        date DATE,
        time TIME,
        FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS payments (
        payment_id INT AUTO_INCREMENT PRIMARY KEY,
        customer_id INT,
        date DATE,
        paid_amount INT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )
    """
]

insert_customer = """
    INSERT INTO customers (name, unit_charge, total_units, balance) 
    VALUES (:name, :unit_charge, :total_units, :balance);
"""

insert_tanker_record = """
    INSERT INTO tanker_records (customer_id, date, time) 
    VALUES (:customer_id, :date, :time);
"""

insert_payment = """
    INSERT INTO payments (customer_id, date, paid_amount) 
    VALUES (:customer_id, :date, :paid_amount);
"""

update_balance_only = """
    UPDATE customers
    SET balance = balance + :amount
    WHERE customer_id = :id;
"""

update_balance_and_unit = """
    UPDATE customers
    SET balance = balance + :amount, total_units = total_units + :unit
    WHERE customer_id = :id;
"""

customer_tanker = """
   SELECT id, name AS Name, DATE_FORMAT(date,'%d-%m-%Y') AS Date, TIME_FORMAT(time,'%h:%i %p') AS Time
    FROM tanker_records AS tf
    JOIN customers AS c
        ON tf.customer_id = c.customer_id
    ORDER BY tf.id ASC;
"""
customers = '''
    SELECT name AS Name, unit_charge AS Charge, total_units AS 'Tanker Count',balance AS Balance
    FROM customers;
'''