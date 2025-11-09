# usunięto import sqlite3
from datetime import datetime
from db_init import client, row_to_dict  # Importujemy klienta i pomocnika


# usunięto DB_NAME = "books.db"

def complete_book(book_id, rating, review):
    if not client:
        return

    # usunięto połączenie sqlite3

    # check if there is review
    rs = client.execute("""
        SELECT date_finished
        FROM reviews
        WHERE id = ?
    """, (book_id,))

    existing = row_to_dict(rs)  # Używamy nowej funkcji pomocniczej

    # Używamy BATCH do wykonania wielu operacji w jednej transakcji
    batch_queries = []

    if existing and existing["date_finished"]:
        # Jeśli istnieje — aktualizuj
        batch_queries.append(libsql_client.Statement(
            """
            UPDATE reviews
            SET rating = ?, review = ?
            WHERE book_id = ?
            """,
            (rating, review, book_id)
        ))
        print(f"🔁 Updated review for book ID {book_id}")
    else:
        # Jeśli nie ma — dodaj nowy wpis
        date_finished = datetime.now().strftime("%d-%m-%Y")

        batch_queries.append(libsql_client.Statement(
            """
            UPDATE books
            SET status = 'Completed'
            WHERE id = ?
            """,
            (book_id,)
        ))
        print(f"✅ Marked book ID {book_id} as 'Completed'")

        if existing:
            # exists but with no date
            batch_queries.append(libsql_client.Statement(
                """
                UPDATE reviews
                SET rating = ?, review = ?, date_finished = ?
                WHERE book_id = ?
                """,
                (rating, review, date_finished, book_id)
            ))
            print(f"✅ Updated existing review record for book ID {book_id}")
        else:
            batch_queries.append(libsql_client.Statement(
                """
                    INSERT INTO reviews (book_id, rating, review, date_finished)
                        VALUES (?, ?, ?, ?)
                """,
                (book_id, rating, review, date_finished)
            ))
            print(f"✅ Added new review for book ID {book_id}")

    # Wykonaj wszystkie zapytania
    if batch_queries:
        client.batch(batch_queries)

    # usunięto conn.commit() i conn.close()
    print(f"✅ Book ID {book_id} processing complete!")


# test interaktywny
if __name__ == "__main__":
    if not client:
        print("Brak połączenia z bazą.")
    else:
        book_id = int(input("Enter book ID to mark as completed: "))
        rating = int(input("Your rating (0-10): "))
        review = input("Your review: ")
        complete_book(book_id, rating, review)