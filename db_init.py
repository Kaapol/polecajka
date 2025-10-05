import sqlite3

conn = sqlite3.connect("books.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS books (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  author TEXT,
  category TEXT,
  status TEXT DEFAULT 'To Read',
  rating INTEGER,
  review TEXT,
  date_added TEXT DEFAULT (datetime('now')),
  date_finished TEXT
)""")

conn.commit()
conn.close()
print("DB ready: books.db")
