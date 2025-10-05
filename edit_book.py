import sqlite3


def edit_book(book_id, title, author, category):
    conn = sqlite3.connect("books.db")
    cur = conn.cursor()

    # update status
    cur.execute("""
        UPDATE books
        SET title = ?,
            author = ?,
            category = ?
        WHERE id = ?
    """, (title, author, category, book_id))

    conn.commit()
    conn.close()
    print(f"✅ Book ID {book_id} has been updated!")

# test interaktywny
if __name__ == "__main__":
    book_id = int(input("Enter book ID to update: "))
    title = input("Enter book title: ")
    author = input("Enter book author: ")
    category = input("Enter book category: ")
    edit_book(book_id, title, author, category)
