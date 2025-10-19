import sqlite3

from db_init import get_connection
from datetime import datetime

DB_NAME = "books.db"

def add_book(title, author, category, thumbnail=None):
    print("DEBUG:", title, author, category, thumbnail)
    conn = get_connection()
    cur = conn.cursor()

    #check if book already exists
    cur.execute("SELECT id FROM books WHERE LOWER(title) = LOWER(?)", (title,))
    existing = cur.fetchone()

    if existing:
        conn.close()
        raise ValueError(f"Book {title} already exists!")


    date_added = datetime.now().strftime("%d-%m-%Y")

    cur.execute("""
    INSERT INTO books (title, author, category, date_added, thumbnail)
    VALUES (?, ?, ?, ?, ?)
    """, (title, author, category, date_added, thumbnail))

    conn.commit()
    conn.close()
    print(f"Dodano książkę: {title} ({author})")

# testowo dodaj jedną książkę
if __name__ == "__main__":
    add_book("Wiedźmin: Ostatnie życzenie", "Andrzej Sapkowski", "fantasy")
