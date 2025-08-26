import os
import mysql.connector
from flask import Flask, request, render_template

app = Flask(__name__)

# Connect to Railway MySQL using environment variables
mydb = mysql.connector.connect(
    host=os.environ.get("DB_HOST"),       # Railway MySQL host
    user=os.environ.get("DB_USER"),       # Railway MySQL username
    password=os.environ.get("DB_PASSWORD"),  # Railway MySQL password
    database=os.environ.get("DB_NAME")    # Railway MySQL database name
)

cursor = mydb.cursor(dictionary=True)

# Create 'users' table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT PRIMARY KEY,
        name VARCHAR(255) NOT NULL
    )
""")
mydb.commit()


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/add', methods=['POST'])
def add_user():
    try:
        user_id = int(request.form['id'])
        name = request.form['name']
        sql = "INSERT INTO users (id, name) VALUES (%s, %s)"
        cursor.execute(sql, (user_id, name))
        mydb.commit()
        return f"User {name} with ID {user_id} saved successfully!"
    except mysql.connector.IntegrityError:
        return f"Error: User with ID {user_id} already exists."
    except Exception as e:
        return f"Error: {e}"


@app.route('/user', methods=['GET'])
def get_user():
    try:
        user_id = int(request.args.get('id'))
        sql = "SELECT * FROM users WHERE id=%s"
        cursor.execute(sql, (user_id,))
        user = cursor.fetchone()
        if user:
            return f"User found: {user['name']}"
        else:
            return "User not found!"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    # Render sets PORT environment variable automatically
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
