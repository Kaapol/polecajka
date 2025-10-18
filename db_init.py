import sqlite3
import os

DB_NAME = "books.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_database():
    """creates db if doesn't exist"""
    if os.path.exists(DB_NAME):
        return False #exists

    conn = sqlite3.connect("books.db")
    cur = conn.cursor()

    #books table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            category TEXT,
            status TEXT DEFAULT 'To Read',
            date_added TEXT,
            thumbnail TEXT
        )
    """)

    #review table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            rating INTEGER,
            review TEXT,
            date_finished TEXT,
            FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    created = initialize_database()
    print("DB ready:", DB_NAME, "(created)" if created else "(already exists)")
