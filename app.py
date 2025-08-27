from flask import Flask, request, jsonify, render_template, redirect, url_for
import psycopg
import os

app = Flask(__name__)

def get_db_connection():
    try:
        conn = psycopg.connect(os.environ['DATABASE_URL'])
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def home():
    conn = get_db_connection()
    users = []
    if conn:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM users ORDER BY id")
                    users = cursor.fetchall()
        except Exception as e:
            print(f"Error fetching users: {e}")
    
    return render_template('index.html', users=users)

@app.route('/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        try:
            user_id = request.form.get('id')
            name = request.form.get('name')
            
            if not user_id or not name:
                return "Missing id or name", 400
            
            conn = get_db_connection()
            if conn is None:
                return "Database connection failed", 500
                
            with conn:
                with conn.cursor() as cursor:
                    # Create table if not exists
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users(
                            id INTEGER PRIMARY KEY,
                            name VARCHAR(100) NOT NULL
                        )
                    """)
                    
                    # Check if user exists
                    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                    if cursor.fetchone():
                        return f"User with id {user_id} already exists", 409
                    
                    # Insert new user
                    cursor.execute(
                        "INSERT INTO users (id, name) VALUES (%s, %s)", 
                        (user_id, name)
                    )
            
            return redirect(url_for('home'))
            
        except Exception as e:
            return f"Error: {e}", 500
    
    # GET request - show add form
    return render_template('add_user.html')

@app.route('/user')
def get_user():
    user_id = request.args.get('id')
    if not user_id:
        return "Missing user id parameter", 400
    
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed", 500
        
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                
                if user:
                    return f"User found: ID={user[0]}, Name={user[1]}"
                else:
                    return "User not found", 404
                    
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
