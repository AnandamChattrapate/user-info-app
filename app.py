import os
from flask import Flask, request, jsonify
import psycopg
from psycopg import sql

app = Flask(__name__)

# Database connection function with better error handling
def get_db_connection():
    try:
        conn = psycopg.connect(os.environ['DATABASE_URL'])
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def home():
    return "User Info App is running!"

@app.route('/add', methods=['POST'])
def add_user():
    try:
        data = request.get_json()
        if not data or 'id' not in data or 'name' not in data:
            return jsonify({'error': 'Missing id or name'}), 400
        
        user_id = data['id']
        name = data['name']
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500
            
        with conn:
            with conn.cursor() as cursor:
                # Create table if not exists (with proper error handling)
                try:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users(
                            id INTEGER PRIMARY KEY,
                            name VARCHAR(100) NOT NULL
                        )
                    """)
                except Exception as e:
                    print(f"Table creation error (may already exist): {e}")
                    # Continue execution - table might already exist
                
                # Check if user already exists
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    return jsonify({'error': f'User with id {user_id} already exists'}), 409
                
                # Insert new user
                cursor.execute(
                    "INSERT INTO users (id, name) VALUES (%s, %s)", 
                    (user_id, name)
                )
                
        return jsonify({'message': 'User added successfully', 'id': user_id, 'name': name}), 201
        
    except psycopg.errors.UniqueViolation:
        return jsonify({'error': f'User with id {user_id} already exists'}), 409
    except Exception as e:
        print(f"Error in add_user: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/user', methods=['GET'])
def get_user():
    try:
        user_id = request.args.get('id')
        if not user_id:
            return jsonify({'error': 'Missing user id parameter'}), 400
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500
            
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                
                if user:
                    return jsonify({
                        'id': user[0],
                        'name': user[1]
                    }), 200
                else:
                    return jsonify({'error': 'User not found'}), 404
                    
    except Exception as e:
        print(f"Error in get_user: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/users', methods=['GET'])
def get_all_users():
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500
            
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users ORDER BY id")
                users = cursor.fetchall()
                
                users_list = [{'id': user[0], 'name': user[1]} for user in users]
                return jsonify({'users': users_list}), 200
                
    except Exception as e:
        print(f"Error in get_all_users: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
