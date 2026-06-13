import psycopg2
import sys

print("INFO: Starting server...")
print("INFO: Loading configurations...")
print("DEBUG: Heartbeat sent")

try:
    conn = psycopg2.connect(
        dbname="shop_db",
        user="postgres",
        password="password",
        host="localhost",
        port="5432",
        connect_timeout=1
    )
except psycopg2.OperationalError as e:
    print(f"ERROR: psycopg2.OperationalError: {e}", file=sys.stderr)
    print("INFO: Healthcheck failed")
    sys.exit(1)
