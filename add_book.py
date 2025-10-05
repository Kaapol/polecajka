import sqlite3

def add_book(title, author, category):
    conn = sqlite3.connect("books.db")
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO books (title, author, category)
    VALUES (?, ?, ?)
    """, (title, author, category))

    conn.commit()
    conn.close()
    print(f"Dodano książkę: {title} ({author})")

# testowo dodaj jedną książkę
if __name__ == "__main__":
    add_book("Wiedźmin: Ostatnie życzenie", "Andrzej Sapkowski", "fantasy")
