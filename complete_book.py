import sqlite3
from datetime import datetime

def complete_book(book_id, rating, review):
    conn = sqlite3.connect("books.db")
    cur = conn.cursor()


    # update status
    cur.execute("""
        UPDATE books
        SET status = 'Completed',
            rating = ?,
            review = ?,
            date_finished = ?
        WHERE id = ?
    """, (rating, review, datetime.now().strftime("%d-%m-%Y"), book_id))

    conn.commit()
    conn.close()
    print(f"✅ Book ID {book_id} marked as completed!")

# test interaktywny
if __name__ == "__main__":
    book_id = int(input("Enter book ID to mark as completed: "))
    rating = int(input("Your rating (0-10): "))
    review = input("Your review: ")
    complete_book(book_id, rating, review)
