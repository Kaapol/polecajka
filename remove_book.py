from db_init import client


def remove_book(book_id):
    if not conn:
        print("Błąd połączenia w remove_book")
        return

    try:
        cur = conn.cursor()
        # Klucze obce są włączone w get_connection(), więc recenzje usuną się kaskadowo
        cur.execute("DELETE FROM books WHERE id = ?", (book_id,))

        conn.commit()

        if cur.rowcount == 0:
            print(f"❌ Nie znaleziono książki o ID {book_id}")
        else:
            print(f"✅ Usunięto książkę o ID {book_id} (wraz z recenzjami).")

    except Exception as e:
        conn.rollback()
        print(f"Błąd w remove_book: {e}")

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    remove_book(999)  # Przetestuj usunięcie nieistniejącej książki