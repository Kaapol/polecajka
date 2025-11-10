from db_init import client


def remove_book(book_id):
    if not client:
        print("❌ Błąd: brak połączenia z bazą")
        return

    try:
        # Wykonaj DELETE
        result = client.execute("DELETE FROM books WHERE id = ?", (book_id,))

        # Sprawdź czy coś usunięto
        rows_affected = getattr(result, 'rows_affected', 0)

        if rows_affected == 0:
            print(f"❌ Nie znaleziono książki o ID {book_id}")
        else:
            print(f"✅ Usunięto książkę o ID {book_id} (wraz z recenzjami).")

    except Exception as e:
        print(f"❌ Błąd w remove_book: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    remove_book(999)  # Test