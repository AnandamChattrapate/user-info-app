import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
import psycopg

app = Flask(__name__)

def get_db_connection():
    """Get database connection"""
    try:
        # Try DATABASE_URL first (easiest for Render)
        database_url = os.environ.get('DATABASE_URL')
        
        # If not set, try individual variables
        if not database_url:
            db_host = os.environ.get('PGHOST')
            db_port = os.environ.get('PGPORT', '5432')
            db_name = os.environ.get('PGDATABASE')
            db_user = os.environ.get('PGUSER')
            db_password = os.environ.get('PGPASSWORD')
            
            if all([db_host, db_name, db_user, db_password]):
                database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            else:
                print("ERROR: No database connection configured!")
                print("Set either DATABASE_URL or PGHOST/PGDATABASE/PGUSER/PGPASSWORD")
                return None
        
        print(f"Connecting to database...")
        conn = psycopg.connect(database_url)
        print("Database connection successful!")
        return conn
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def initialize_database():
    """Initialize database with simple schema"""
    conn = get_db_connection()
    if conn is None:
        return False
        
    try:
        with conn:
            with conn.cursor() as cursor:
                # Simple table without created_at
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users(
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(100) NOT NULL
                    )
                """)
                print("Users table ready!")
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
                    cursor.execute("SELECT id, name FROM users ORDER BY id")
                    users_data = cursor.fetchall()
                    users = [{'id': user[0], 'name': user[1]} for user in users_data]
                    print(f"Found {len(users)} users")
        except Exception as e:
            print(f"Error fetching users: {e}")
        finally:
            conn.close()
    else:
        print("No database connection for home page")
    
    return render_template('index.html', users=users)

@app.route('/add', methods=['GET', 'POST'])
def add_user():
    """Add a new user"""
    if request.method == 'GET':
        return render_template('add_user.html')
    
    try:
        user_id = request.form.get('id')
        name = request.form.get('name')
        
        if not user_id or not name:
            return render_template('add_user.html', error='Missing id or name')
        
        try:
            user_id = int(user_id)
        except ValueError:
            return render_template('add_user.html', error='ID must be a number')
        
        name = name.strip()
        if not name:
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
                        name VARCHAR(100) NOT NULL
                    )
                """)
                
                # Check if user exists
                cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
                existing = cursor.fetchone()
                
                if existing:
                    return render_template('add_user.html', 
                                         error=f'User with ID {user_id} already exists: {existing[0]}')
                
                # Insert new user
                cursor.execute("INSERT INTO users (id, name) VALUES (%s, %s)", (user_id, name))
                print(f"Added user: ID={user_id}, Name={name}")
                
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
                cursor.execute("SELECT id, name FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                
                if user:
                    user_data = {'id': user[0], 'name': user[1]}
                    print(f"Found user: {user_data}")
                    return render_template('index.html', found_user=user_data)
                else:
                    print(f"User with ID {user_id} not found")
                    return render_template('index.html', error=f'User with ID {user_id} not found')
                    
    except Exception as e:
        print(f"Error in get_user: {e}")
        return render_template('index.html', error='Internal server error')
    finally:
        if conn:
            conn.close()

@app.route('/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """Delete a user"""
    conn = get_db_connection()
    if conn is None:
        return redirect(url_for('home'))
    
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                print(f"Deleted user with ID: {user_id}")
        return redirect(url_for('home'))
    except Exception as e:
        print(f"Error deleting user: {e}")
        return redirect(url_for('home'))
    finally:
        if conn:
            conn.close()

@app.route('/health')
def health_check():
    """Health check endpoint"""
    conn = get_db_connection()
    status = "connected" if conn else "disconnected"
    if conn:
        conn.close()
    
    return jsonify({
        'status': 'healthy',
        'database': status,
        'service': 'user-info-app'
    })

# Initialize database when app starts
if __name__ == '__main__':
    print("🚀 Starting User Info App...")
    print("Initializing database...")
    if initialize_database():
        print("✅ Database initialized successfully!")
    else:
        print("❌ Database initialization failed")
    
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
