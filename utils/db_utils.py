import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/tags.db')

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def load_tags():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tags')
    tags = {row[0]: {'label': row[1], 'type': row[2], 'notes': row[3]} for row in cursor.fetchall()}
    conn.close()
    return tags

def add_or_update_tag(address, label, tag_type, notes=''):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO tags (address, label, type, notes) VALUES (?, ?, ?, ?)', (address, label, tag_type, notes))
    conn.commit()
    conn.close() 