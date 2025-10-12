import sqlite3

from db_init import get_connection
from datetime import datetime

DB_NAME = "books.db"

def add_book(title, author, category):
    conn = get_connection()
    cur = conn.cursor()

    date_added = datetime.now().strftime("%d-%m-%Y")

    cur.execute("""
    INSERT INTO books (title, author, category, date_added)
    VALUES (?, ?, ?, ?)
    """, (title, author, category, date_added))

    conn.commit()
    conn.close()
    print(f"Dodano książkę: {title} ({author})")

# testowo dodaj jedną książkę
if __name__ == "__main__":
    add_book("Wiedźmin: Ostatnie życzenie", "Andrzej Sapkowski", "fantasy")
