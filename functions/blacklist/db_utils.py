import os 
import sqlite3 

def get_all_blacklist_db_connections(db_dir='blacklistsdatabase'):
    """
    Returns a list of sqlite3 connections for all .db files in the specified directory.
    This is used for checking a user’s blacklist status across all databases.
    """
    connections = []
    os.makedirs(db_dir, exist_ok=True)
    db_files = [f for f in os.listdir(db_dir) if f.endswith('.db')]
    for db_file in db_files:
        try:
            conn = sqlite3.connect(os.path.join(db_dir, db_file))
            connections.append(conn)
        except sqlite3.Error as e:
            print(f"Error connecting to {db_file}: {e}")
    return connections

def get_blacklist_db(user_id, db_dir='blacklistsdatabase', max_users=5000):
    """
    Finds (or creates) the appropriate blacklist database for a user.
    
    Returns:
        (conn, cursor): a tuple of the SQLite connection and cursor.
    """
    os.makedirs(db_dir, exist_ok=True)
    db_index = 1
    while True:
        db_path = os.path.join(db_dir, f"blacklists_{db_index}.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blacklists (
                user_id TEXT PRIMARY KEY,
                blacklist_status TEXT
            )
        ''')
        conn.commit()
        
        cursor.execute("SELECT * FROM blacklists WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            return conn, cursor
        
        cursor.execute("SELECT COUNT(*) FROM blacklists")
        count = cursor.fetchone()[0]
        if count < max_users:
            return conn, cursor
        conn.close()
        db_index += 1

def find_user_blacklist_db(user_id, db_dir='blacklistsdatabase'):
    """
    Finds the exact blacklist database file where the user exists.
    
    Returns:
        (conn, cursor) if the user is found; otherwise, (None, None).
    """
    db_index = 1
    while True:
        db_path = os.path.join(db_dir, f"blacklists_{db_index}.db")
        if not os.path.exists(db_path):
            return None, None
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blacklists WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            return conn, cursor
        conn.close()
        db_index += 1

def get_image_db(user_id, db_dir='imagedatabase', max_users=10000):
    """
    Finds (or creates) the appropriate image database for a user.
    
    Returns:
        (conn, cursor): a tuple of the SQLite connection and cursor.
    """
    os.makedirs(db_dir, exist_ok=True)
    db_index = 1
    while True:
        db_path = os.path.join(db_dir, f"image_{db_index}.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imagethumbnail (
                user_id TEXT PRIMARY KEY,
                image TEXT,
                thumbnail TEXT,
                DWC TEXT
            )
        ''')
        conn.commit()
        
        cursor.execute("SELECT * FROM imagethumbnail WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            return conn, cursor
        
        cursor.execute("SELECT COUNT(*) FROM imagethumbnail")
        count = cursor.fetchone()[0]
        if count < max_users:
            return conn, cursor
        conn.close()
        db_index += 1

def find_user_image_db(user_id, db_dir='imagedatabase'):
    """
    Finds the exact image database file where the user exists.
    
    Returns:
        (conn, cursor) if found; otherwise, (None, None).
    """
    db_index = 1
    while True:
        db_path = os.path.join(db_dir, f"image_{db_index}.db")
        if not os.path.exists(db_path):
            return None, None
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM imagethumbnail WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            return conn, cursor
        conn.close()
        db_index += 1
