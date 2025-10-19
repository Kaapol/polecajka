import sqlite3
from datetime import datetime

DB_NAME = "books.db"

def complete_book(book_id, rating, review):
    # połączenie z DB
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")  # włącz klucze obce

    # check if there is review
    cur.execute("""
        SELECT date_finished
        FROM reviews
        WHERE id = ?
    """, (book_id,))

    existing = cur.fetchone()

    if existing and existing["date_finished"]:
        # Jeśli istnieje — aktualizuj
        cur.execute("""
                    UPDATE reviews
                    SET rating        = ?,
                        review        = ?
                    WHERE book_id = ?
                    """, (rating, review, book_id))
        print(f"🔁 Updated review for book ID {book_id}")
    else:
        #Jeśli nie ma — dodaj nowy wpis
        date_finished = datetime.now().strftime("%d-%m-%Y")

        cur.execute("""
                    UPDATE book
                    SET status = 'Completed'
                    WHERE id = ?
                    """, (book_id,))
        print(f"✅ Added new review for book ID {book_id}")

        if existing:
            #exists but with no date
            cur.execute("""
            UPDATE reviews
            SET rating        = ?,
                review        = ?,
                date_finished = ?
                WHERE book_id = ?
            """, (rating, review, date_finished, book_id))
        else:
            cur.execute("""
                INSERT INTO reviews (book_id, rating, review, date_finished)
                    VALUES (?, ?, ?, ?)
            """, (book_id, rating, review, date_finished))

    conn.commit()
    conn.close()
    print(f"✅ Book ID {book_id} marked as completed with review!")

# test interaktywny
if __name__ == "__main__":
    book_id = int(input("Enter book ID to mark as completed: "))
    rating = int(input("Your rating (0-10): "))
    review = input("Your review: ")
    complete_book(book_id, rating, review)
