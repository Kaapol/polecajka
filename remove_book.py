# usunięto import sqlite3
from db_init import client  # Importujemy klienta Turso


def remove_book(id):
    if not client:
        return

    # usunięto conn = sqlite3.connect...
    # usunięto conn.execute("PRAGMA...")
    # usunięto cur = conn.cursor()

    rs = client.execute("DELETE FROM books WHERE id = ?", (id,))

    # Zmieniamy 'cur.rowcount' na 'rs.rows_affected'
    if rs.rows_affected == 0:
        print(f"\n❌ No book found with id {id}")
    else:
        print(f"\n✅ A book with ID: {id} has been removed (and its reviews cascaded).")

    # usunięto conn.commit()
    # usunięto conn.close()


# testowo usun jedną książkę
if __name__ == "__main__":
    if client:
        remove_book(1)
    else:
        print("Brak połączenia z bazą.")