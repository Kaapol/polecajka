import sqlite3

DB_NAME = "books.db"

def edit_book(book_id, title, author, category):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")

    # zamiana pierwszej litery każdego słowa na dużą
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

    if not fields:  # jeśli nic nie podano
        print("⚠️ Nothing to update.")
        conn.close()
        return

    query = f"UPDATE books SET {', '.join(fields)} WHERE id = ?"
    values.append(book_id)

    cur.execute(query, values)
    conn.commit()
    conn.close()
    print(f"✅ Book ID {book_id} updated with {len(fields)} change(s).")


# test interaktywny
if __name__ == "__main__":
    book_id = int(input("Enter book ID to update: "))
    title = input("Enter new title (or leave empty): ")
    author = input("Enter new author (or leave empty): ")
    category = input("Enter new category (or leave empty): ")
    edit_book(book_id, title or None, author or None, category or None)

