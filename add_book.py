from db_init import client
from datetime import datetime

def add_book(title, author, category, thumbnail=None):
    if not client: raise Exception("No DB client")

    # Sprawdź duplikat
    rs = client.execute("SELECT id FROM books WHERE LOWER(title) = LOWER(?)", (title,))
    if rs.rows:
        raise ValueError(f"Book '{title}' already exists!")

    date_added = datetime.now().strftime("%d-%m-%Y")
    # Klient sync robi commit automatycznie po execute, ale dla pewności
    client.execute("""
        INSERT INTO books (title, author, category, date_added, thumbnail)
        VALUES (?, ?, ?, ?, ?)
    """, (title, author, category, date_added, thumbnail))
    print(f"✅ Added: {title}")

if __name__ == "__main__":
    add_book("Test Book", "Test Author", "Test Cat")