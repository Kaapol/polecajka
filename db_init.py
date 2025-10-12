import sqlite3

DB_NAME = "books.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # 🔥 włącza klucze obce
    return conn

conn1 = sqlite3.connect("books.db")
cur = conn1.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS books (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  author TEXT,
  category TEXT,
  status TEXT DEFAULT 'To Read',
  date_added TEXT
)""")

conn1.commit()
conn1.close()
print("DB ready: books.db")
