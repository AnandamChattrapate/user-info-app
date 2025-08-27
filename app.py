import os
import psycopg
from flask import Flask, request, render_template

app = Flask(__name__)

# Connect to PostgreSQL using environment variables
conn = psycopg.connect(
    host=os.environ.get("PGHOST"),
    port=os.environ.get("PGPORT"),
    user=os.environ.get("PGUSER"),
    password=os.environ.get("PGPASSWORD"),
    dbname=os.environ.get("PGDATABASE"),
    row_factory=psycopg.rows.dict_row  # returns results as dictionaries
)

cursor = conn.cursor()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/add', methods=['POST'])
def add_user():
    user_id = request.form['id']
    name = request.form['name']
    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id TEXT PRIMARY KEY,
            name TEXT
        )
    """)
    # Insert user
    cursor.execute("INSERT INTO users (id, name) VALUES (%s, %s)", (user_id, name))
    conn.commit()
    return f"User {name} with ID {user_id} saved successfully!"

@app.route('/user', methods=['GET'])
def get_user():
    user_id = request.args.get('id')
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    if user:
        return f"User found: {user['name']}"
    else:
        return "User not found!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
