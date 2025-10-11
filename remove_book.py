import sqlite3

def remove_book(id):
    conn = sqlite3.connect("books.db")
    conn.execute("PRAGMA foreign_keys = ON")  # <--- to musi być tu
    cur = conn.cursor()

    cur.execute("DELETE FROM books WHERE id = ?", (id,))

    if cur.rowcount == 0:
        print(f"\n❌ No book found with id {id}")
    else:
        print(f"\n✅ A book with ID: {id} has been removed (and its reviews cascaded).")

    conn.commit()
    conn.close()


# testowo usun jedną książkę
if __name__ == "__main__":
    remove_book(1)
