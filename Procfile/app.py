from flask import Flask, request, render_template
import mysql.connector

app = Flask(__name__)

# Connect to MySQL
mydb = mysql.connector.connect(
    host="localhost",
    user="root",       # change if your MySQL username is different
    password="h6@CRwCw4E4qX@X",   # put your MySQL root password here
    database="userdb"
)
cursor = mydb.cursor()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/add', methods=['POST'])
def add_user():
    user_id = request.form['id']
    name = request.form['name']

    # Insert into MySQL
    sql = "INSERT INTO users (id, name) VALUES (%s, %s)"
    val = (user_id, name)
    cursor.execute(sql, val)
    mydb.commit()

    return f"User {name} with ID {user_id} saved successfully!"

@app.route('/user', methods=['GET'])
def get_user():
    user_id = request.args.get('id')
    
    # Fetch from MySQL
    sql = "SELECT name FROM users WHERE id = %s"
    cursor.execute(sql, (user_id,))
    result = cursor.fetchone()

    if result:
        return f"User found: {result[0]}"
    else:
        return "User not found!"

if __name__ == "__main__":
    app.run(debug=True)
