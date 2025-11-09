# usunięto import sqlite3
from datetime import datetime
from db_init import client  # Importujemy klienta Turso


# usunięto DB_NAME = "books.db"

def edit_book(book_id, title=None, author=None, category=None):
    """Aktualizuje książkę w tabeli books (bez daty)"""
    if not client:
        return

    # usunięto conn = sqlite3.connect...
    # usunięto cur = conn.cursor()
    # usunięto conn.row_factory...
    # usunięto cur.execute("PRAGMA...")

    title = title.title() if title else None
    author = author.title() if author else None
    category = category.title() if category else None

    fields = []
    values = []

    if title:
        fields.append("title = ?")
        values.append(title)
    if author:
        fields.append("author = ?")
        values.append(author)
    if category:
        fields.append("category = ?")
        values.append(category)

    if not fields:
        print("⚠️ Nothing to update.")
        return  # usunięto conn.close()

    query = f"UPDATE books SET {', '.join(fields)} WHERE id = ?"
    values.append(book_id)

    client.execute(query, values)
    # usunięto conn.commit()
    # usunięto conn.close()
    print(f"✅ Book ID {book_id} updated with {len(fields)} change(s).")


def edit_review_date(book_id, date_finished):
    """Aktualizuje date_finished w tabeli reviews"""
    if not date_finished or not client:
        return

    # konwersja YYYY-MM-DD > DD-MM-YYYY
    try:
        parsed_date = datetime.strptime(date_finished, "%Y-%m-%d")
        date_finished = parsed_date.strftime("%d-%m-%Y")
    except ValueError:
        print(f"⚠️ Nieprawidłowy format daty: {date_finished}")
        return

    # usunięto conn = sqlite3.connect... i resztę

    client.execute("UPDATE reviews SET date_finished = ? WHERE book_id = ?", (date_finished, book_id))
    # usunięto conn.commit()
    # usunięto conn.close()
    print(f"✅ Review date for Book ID {book_id} updated to {date_finished}")


# test interaktywny
if __name__ == "__main__":
    if not client:
        print("Brak połączenia z bazą, zatrzymuję.")
    else:
        book_id = int(input("Enter book ID to update: "))
        title = input("Enter new title (or leave empty): ")
        author = input("Enter new author (or leave empty): ")
        category = input("Enter new category (or leave empty): ")
        date_finished = input("Enter new date (YYYY-MM-DD or leave empty): ")

        edit_book(book_id, title or None, author or None, category or None)
        edit_review_date(book_id, date_finished or None)