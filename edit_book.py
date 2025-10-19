import sqlite3
from datetime import datetime
DB_NAME = "books.db"

def edit_book(book_id, title=None, author=None, category=None):
    """Aktualizuje książkę w tabeli books (bez daty)"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")

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
        conn.close()
        return

    query = f"UPDATE books SET {', '.join(fields)} WHERE id = ?"
    values.append(book_id)

    cur.execute(query, values)
    conn.commit()
    conn.close()
    print(f"✅ Book ID {book_id} updated with {len(fields)} change(s).")


def edit_review_date(book_id, date_finished):
    """Aktualizuje date_finished w tabeli reviews"""
    if not date_finished:
        return

    # konwersja YYYY-MM-DD → DD-MM-YYYY
    try:
        parsed_date = datetime.strptime(date_finished, "%Y-%m-%d")
        date_finished = parsed_date.strftime("%d-%m-%Y")
    except ValueError:
        print(f"⚠️ Nieprawidłowy format daty: {date_finished}")
        return

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")

    cur.execute("UPDATE reviews SET date_finished = ? WHERE book_id = ?", (date_finished, book_id))
    conn.commit()
    conn.close()
    print(f"✅ Review date for Book ID {book_id} updated to {date_finished}")


# test interaktywny
if __name__ == "__main__":
    book_id = int(input("Enter book ID to update: "))
    title = input("Enter new title (or leave empty): ")
    author = input("Enter new author (or leave empty): ")
    category = input("Enter new category (or leave empty): ")
    date_finished = input("Enter new date (YYYY-MM-DD or leave empty): ")

    edit_book(book_id, title or None, author or None, category or None)
    edit_review_date(book_id, date_finished or None)