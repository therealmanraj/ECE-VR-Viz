import trino

TRINO_HOST = "localhost"  # SSH tunnel: ssh -L 8080:localhost:8080 <user>@20.151.177.201
TRINO_PORT = 8080          # 8079 is Superset; Trino runs on 8080
TRINO_USER = "admin"
CATALOG = "mongo_prod"     # Trino catalog name (from mongo_prod.properties)
SCHEMA = "langara-dev-client"  # MongoDB database name

conn = trino.dbapi.connect(
    host=TRINO_HOST,
    port=TRINO_PORT,
    user=TRINO_USER,
    catalog=CATALOG,
    schema=SCHEMA,
)

cursor = conn.cursor()

# Show available tables (schema name has hyphens so must be quoted)
cursor.execute(f'SHOW TABLES FROM {CATALOG}."langara-dev-client"')
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# Query a table
cursor.execute('SELECT * FROM mongo_prod."langara-dev-client".levelflows LIMIT 5')
rows = cursor.fetchall()
col_names = [desc[0] for desc in cursor.description]
print("Columns:", col_names)
for row in rows:
    print(row)

cursor.close()
conn.close()