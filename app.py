import os
import psycopg2
from flask import Flask, request, render_template

app = Flask(__name__)

# Connect to PostgreSQL using environment variables
conn = psycopg2.connect(
    host=os.environ.get("PGHOST"),
    port=os.environ.get("PGPORT"),
    user=os.environ.get("PGUSER"),
    password=os.environ.get("PGPASSWORD"),
    dbname=os.environ.get("PGDATABASE")
)

cursor = conn.cursor()

# Ensure table exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id TEXT PRIMARY KEY,
    name TEXT
)
""")
conn.commit()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/add', methods=['POST'])
def add_user():
    user_id = request.form['id']
    name = request.form['name']
    sql = "INSERT INTO users (id, name) VALUES (%s, %s)"
    try:
        cursor.execute(sql, (user_id, name))
        conn.commit()
        return f"User {name} with ID {user_id} saved successfully!"
    except psycopg2.IntegrityError:
        conn.rollback()
        return f"User with ID {user_id} already exists!"

@app.route('/user', methods=['GET'])
def get_user():
    user_id = request.args.get('id')
    sql = "SELECT * FROM users WHERE id=%s"
    cursor.execute(sql, (user_id,))
    user = cursor.fetchone()
    if user:
        return f"User found: {user[1]}"  # index 1 is 'name'
    else:
        return "User not found!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
