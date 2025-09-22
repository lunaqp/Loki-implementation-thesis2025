import psycopg

# After having created a postgres database and connected a new user to it, establish connection with the relevant info inserted below:
conn = psycopg.connect(dbname="bb", user="bb", password="BBpass", host="localhost", port=5432)

# Open a cursor to perform database operations
cur = conn.cursor()

# Read the DDL SQL file
with open("schema.sql", "r") as f:
    sql = f.read()

cur.execute(sql)

# Insert data into the tables for testing
with open("testvalues.sql", "r") as f:
    sql = f.read()

cur.execute(sql)

# Save the state with database tables created and testdata loaded in:
conn.commit()
