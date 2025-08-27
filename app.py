import os
from flask import Flask, request, jsonify
import psycopg

app = Flask(__name__)

def get_db_connection():
    """Get database connection using individual environment variables"""
    try:
        # Get individual PostgreSQL connection variables
        db_host = os.environ.get('PGHOST')
        db_port = os.environ.get('PGPORT')
        db_name = os.environ.get('PGDATABASE')
        db_user = os.environ.get('PGUSER')
        db_password = os.environ.get('PGPASSWORD')
        
        # Check if all required variables are set
        if not all([db_host, db_port, db_name, db_user, db_password]):
            missing = []
            if not db_host: missing.append('PGHOST')
            if not db_port: missing.append('PGPORT')
            if not db_name: missing.append('PGDATABASE')
            if not db_user: missing.append('PGUSER')
            if not db_password: missing.append('PGPASSWORD')
            
            print(f"Missing database environment variables: {', '.join(missing)}")
            return None
        
        # Construct connection string
        connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        print(f"Connecting to database: {db_host}:{db_port}/{db_name}")
        conn = psycopg.connect(connection_string)
        print("Database connection successful")
        return conn
        
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def initialize_database():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    if conn is None:
        return False
        
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users(
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("Database table initialized successfully")
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False
    finally:
        if conn:
            conn.close()

@app.route('/')
def home():
    """Home endpoint with service information"""
    external_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://user-info-app-4lxh.onrender.com')
    
    return jsonify({
        'message': 'User Info API is running! 🚀',
        'external_url': external_url,
        'database_connected': get_db_connection() is not None,
        'endpoints': {
            'add_user': 'POST /add - Add a new user',
            'get_user': 'GET /user?id=<id> - Get user by ID',
            'get_all_users': 'GET /users - Get all users',
            'health': 'GET /health - Service health check',
            'debug': 'GET /debug - Connection debug info'
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    db_conn = get_db_connection()
    db_status = "connected" if db_conn else "disconnected"
    if db_conn:
        db_conn.close()
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'service': 'user-info-app'
    })

@app.route('/debug')
def debug_info():
    """Debug connection information"""
    db_connected = get_db_connection() is not None
    
    return jsonify({
        'database_connected': db_connected,
        'environment_variables': {
            'PGHOST_set': bool(os.environ.get('PGHOST')),
            'PGPORT_set': bool(os.environ.get('PGPORT')),
            'PGDATABASE_set': bool(os.environ.get('PGDATABASE')),
            'PGUSER_set': bool(os.environ.get('PGUSER')),
            'PGPASSWORD_set': bool(os.environ.get('PGPASSWORD')),
            'RENDER_EXTERNAL_URL_set': bool(os.environ.get('RENDER_EXTERNAL_URL'))
        }
    })

@app.route('/add', methods=['POST'])
def add_user():
    """Add a new user"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        
        if not data or 'id' not in data or 'name' not in data:
            return jsonify({'error': 'Missing id or name'}), 400
        
        user_id = data['id']
        name = data['name']
        
        if not isinstance(user_id, int):
            return jsonify({'error': 'id must be an integer'}), 400
            
        if not isinstance(name, str) or not name.strip():
            return jsonify({'error': 'name must be a non-empty string'}), 400
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500
            
        with conn:
            with conn.cursor() as cursor:
                # Create table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users(
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Check if user exists
                cursor.execute("SELECT id, name FROM users WHERE id = %s", (user_id,))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    return jsonify({
                        'error': f'User with id {user_id} already exists',
                        'existing_user': {'id': existing_user[0], 'name': existing_user[1]}
                    }), 409
                
                # Insert new user
                cursor.execute(
                    "INSERT INTO users (id, name) VALUES (%s, %s)", 
                    (user_id, name.strip())
                )
                
        return jsonify({
            'message': 'User added successfully', 
            'user': {'id': user_id, 'name': name.strip()}
        }), 201
        
    except Exception as e:
        print(f"Error in add_user: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/user', methods=['GET'])
def get_user():
    """Get user by ID"""
    try:
        user_id = request.args.get('id')
        if not user_id:
            return jsonify({'error': 'Missing user id parameter'}), 400
        
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({'error': 'id must be an integer'}), 400
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500
            
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name, created_at FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                
                if user:
                    return jsonify({
                        'user': {
                            'id': user[0],
                            'name': user[1],
                            'created_at': user[2].isoformat() if user[2] else None
                        }
                    }), 200
                else:
                    return jsonify({'error': 'User not found'}), 404
                    
    except Exception as e:
        print(f"Error in get_user: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/users', methods=['GET'])
def get_all_users():
    """Get all users"""
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500
            
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name, created_at FROM users ORDER BY id")
                users = cursor.fetchall()
                
                users_list = [
                    {
                        'id': user[0],
                        'name': user[1],
                        'created_at': user[2].isoformat() if user[2] else None
                    } for user in users
                ]
                
                return jsonify({
                    'count': len(users_list),
                    'users': users_list
                }), 200
                
    except Exception as e:
        print(f"Error in get_all_users: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Initialize database when app starts
if __name__ == '__main__':
    print("Initializing database...")
    if initialize_database():
        print("Database initialized successfully!")
    else:
        print("Database initialization failed. Check your connection settings.")
    
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
