import sqlite3
from datetime import datetime

DB_NAME = "books.db"

def complete_book(book_id, rating, review):
    # połączenie z DB
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")  # włącz klucze obce

    # 1️⃣ zaktualizuj status w books
    cur.execute("""
        UPDATE books
        SET status = 'Completed'
        WHERE id = ?
    """, (book_id,))

    # 2️⃣ Sprawdź, czy książka już ma recenzję
    cur.execute("SELECT id FROM reviews WHERE book_id = ?", (book_id,))
    existing = cur.fetchone()

    if existing:
        # 3️⃣ Jeśli istnieje — aktualizuj
        cur.execute("""
                    UPDATE reviews
                    SET rating        = ?,
                        review        = ?,
                        date_finished = ?
                    WHERE book_id = ?
                    """, (rating, review, datetime.now().strftime("%d-%m-%Y"), book_id))
        print(f"🔁 Updated review for book ID {book_id}")
    else:
        # 4️⃣ Jeśli nie ma — dodaj nowy wpis
        cur.execute("""
                    INSERT INTO reviews (book_id, rating, review, date_finished)
                    VALUES (?, ?, ?, ?)
                    """, (book_id, rating, review, datetime.now().strftime("%d-%m-%Y")))
        print(f"✅ Added new review for book ID {book_id}")

    conn.commit()
    conn.close()
    print(f"✅ Book ID {book_id} marked as completed with review!")

# test interaktywny
if __name__ == "__main__":
    book_id = int(input("Enter book ID to mark as completed: "))
    rating = int(input("Your rating (0-10): "))
    review = input("Your review: ")
    complete_book(book_id, rating, review)
