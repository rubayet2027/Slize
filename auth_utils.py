import sqlite3
import os

DB_FILE = 'slize_data.db'

def init_db():
    """Initialize the SQLite database for user clip history."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # History table (Using email as the identifier from Google Auth)
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            clip_name TEXT NOT NULL,
            original_video TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_history(email, clip_name, original_video=""):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO history (email, clip_name, original_video) VALUES (?,?,?)', 
              (email, clip_name, original_video))
    conn.commit()
    conn.close()

def get_user_history(email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT clip_name, timestamp FROM history WHERE email = ? ORDER BY timestamp DESC', (email,))
    data = c.fetchall()
    conn.close()
    return data
