import os

try:
    host = os.environ['MYSQL_SERVER']
except KeyError as e:
    raise KeyError(f"MYSQL_SERVER env variable is not set") from None

port = os.environ.get("MYSQL_PORT", "3306")

try:
    user = os.environ['MYSQL_USER']
except KeyError as e:
    raise KeyError(f"MYSQL_USER env variable is not set") from None

try:
    password = os.environ['MYSQL_PASSWORD']
except KeyError as e:
    raise KeyError(f"MYSQL_PASSWORD env variable is not set") from None

try:
    database = os.environ['MYSQL_DATABASE']
except KeyError as e:
    raise KeyError(f"MYSQL_DATABASE env variable is not set") from None

debug = bool(os.environ.get('DEBUG_ON', "False"))



