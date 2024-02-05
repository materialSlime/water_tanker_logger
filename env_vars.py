import os

host = os.environ['MYSQL_SERVER']
port = os.environ.get("MYSQL_PORT","3306")
user = os.environ['MYSQL_USER']
password = os.environ['MYSQL_PASSWORD']
database = os.environ['MYSQL_DATABASE']
debug = bool(os.environ.get('DEBUG_ON', "False"))
