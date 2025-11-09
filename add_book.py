# usunięto import sqlite3
from db_init import client  # Importujemy klienta Turso
from datetime import datetime


# usunięto DB_NAME = "books.db"
# usunięto 'from db_init import get_connection'

def add_book(title, author, category, thumbnail=None):
    if not client:
        raise ValueError("Database client not configured!")

    print("DEBUG:", title, author, category, thumbnail)

    # Zmieniona logika
    rs = client.execute("SELECT id FROM books WHERE LOWER(title) = LOWER(?)", (title,))
    existing = rs.rows[0] if rs.rows else None  # Sprawdzamy, czy są jakieś rzędy

    if existing:
        raise ValueError(f"Book {title} already exists!")

    date_added = datetime.now().strftime("%d-%m-%Y")

    client.execute("""
    INSERT INTO books (title, author, category, date_added, thumbnail)
    VALUES (?, ?, ?, ?, ?)
    """, (title, author, category, date_added, thumbnail))
    # Nie ma conn.commit() ani conn.close() - klient Turso robi to auto

    print(f"Dodano książkę: {title} ({author})")


# test interaktywny
if __name__ == "__main__":
    if client:
        add_book("Wiedźmin: Ostatnie życzenie", "Andrzej Sapkowski", "fantasy")
    else:
        print("Nie można dodać książki, brak połączenia z bazą (sprawdź .env)")