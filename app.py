import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
import psycopg
from datetime import datetime

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
            print("Missing some database environment variables")
            return None
        
        # Construct connection string
        connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        conn = psycopg.connect(connection_string)
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
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False
    finally:
        if conn:
            conn.close()

@app.route('/')
def home():
    """Home page with user management interface"""
    conn = get_db_connection()
    users = []
    
    if conn:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, name, created_at FROM users ORDER BY id")
                    users_data = cursor.fetchall()
                    users = [
                        {
                            'id': user[0],
                            'name': user[1],
                            'created_at': user[2].strftime('%Y-%m-%d %H:%M:%S') if user[2] else 'Unknown'
                        }
                        for user in users_data
                    ]
        except Exception as e:
            print(f"Error fetching users: {e}")
        finally:
            conn.close()
    
    return render_template('index.html', users=users)

@app.route('/add', methods=['GET', 'POST'])
def add_user():
    """Add a new user - shows form on GET, processes form on POST"""
    if request.method == 'GET':
        # Show the add user form
        return render_template('add_user.html')
    
    # POST request - process form submission
    try:
        user_id = request.form.get('id')
        name = request.form.get('name')
        
        if not user_id or not name:
            return render_template('add_user.html', error='Missing id or name')
        
        try:
            user_id = int(user_id)
        except ValueError:
            return render_template('add_user.html', error='ID must be a number')
        
        if not name.strip():
            return render_template('add_user.html', error='Name cannot be empty')
        
        conn = get_db_connection()
        if conn is None:
            return render_template('add_user.html', error='Database connection failed')
            
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
                    return render_template('add_user.html', 
                                         error=f'User with ID {user_id} already exists: {existing_user[1]}')
                
                # Insert new user
                cursor.execute(
                    "INSERT INTO users (id, name) VALUES (%s, %s)", 
                    (user_id, name.strip())
                )
                
        return redirect(url_for('home'))
        
    except Exception as e:
        print(f"Error in add_user: {e}")
        return render_template('add_user.html', error='Internal server error')

@app.route('/user', methods=['GET'])
def get_user():
    """Find user by ID"""
    user_id = request.args.get('id')
    
    if not user_id:
        return render_template('index.html', error='Please provide a user ID')
    
    try:
        user_id = int(user_id)
    except ValueError:
        return render_template('index.html', error='ID must be a number')
    
    conn = get_db_connection()
    if conn is None:
        return render_template('index.html', error='Database connection failed')
    
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name, created_at FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                
                if user:
                    user_data = {
                        'id': user[0],
                        'name': user[1],
                        'created_at': user[2].strftime('%Y-%m-%d %H:%M:%S') if user[2] else 'Unknown'
                    }
                    return render_template('index.html', found_user=user_data)
                else:
                    return render_template('index.html', error=f'User with ID {user_id} not found')
                    
    except Exception as e:
        print(f"Error in get_user: {e}")
        return render_template('index.html', error='Internal server error')
    finally:
        conn.close()

# Keep these API endpoints for programmatic access
@app.route('/api/health')
def health_check():
    """Health check endpoint (API)"""
    db_conn = get_db_connection()
    db_status = "connected" if db_conn else "disconnected"
    if db_conn:
        db_conn.close()
    
    return jsonify({'status': 'healthy', 'database': db_status})

@app.route('/api/debug')
def debug_info():
    """Debug connection information (API)"""
    db_connected = get_db_connection() is not None
    return jsonify({
        'database_connected': db_connected,
        'environment_variables_set': {
            'PGHOST': bool(os.environ.get('PGHOST')),
            'PGPORT': bool(os.environ.get('PGPORT')),
            'PGDATABASE': bool(os.environ.get('PGDATABASE')),
            'PGUSER': bool(os.environ.get('PGUSER')),
            'PGPASSWORD': bool(os.environ.get('PGPASSWORD'))
        }
    })

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
