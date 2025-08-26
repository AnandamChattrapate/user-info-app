import os
import mysql.connector
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Connect to Railway MySQL using environment variables
mydb = mysql.connector.connect(
    host=os.environ.get("DB_HOST"),       # Railway host
    user=os.environ.get("DB_USER"),       # Railway username
    password=os.environ.get("DB_PASSWORD"),  # Railway password
    database=os.environ.get("DB_NAME")    # Railway database name
)

cursor = mydb.cursor(dictionary=True)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/add', methods=['POST'])
def add_user():
    user_id = request.form['id']
    name = request.form['name']
    sql = "INSERT INTO users (id, name) VALUES (%s, %s)"
    cursor.execute(sql, (user_id, name))
    mydb.commit()
    return f"User {name} with ID {user_id} saved successfully!"

@app.route('/user', methods=['GET'])
def get_user():
    user_id = request.args.get('id')
    sql = "SELECT * FROM users WHERE id=%s"
    cursor.execute(sql, (user_id,))
    user = cursor.fetchone()
    if user:
        return f"User found: {user['name']}"
    else:
        return "User not found!"

if __name__ == "__main__":
    app.run(debug=True)
