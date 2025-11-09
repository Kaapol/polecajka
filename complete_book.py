from datetime import datetime
from db_init import client
import libsql_client


def complete_book(book_id, rating, review):
    if not client: return

    today = datetime.now().strftime("%d-%m-%Y")

    # Używamy transakcji batch dla bezpieczeństwa
    stmts = [
        libsql_client.Statement("UPDATE books SET status = 'Completed' WHERE id = ?", (book_id,))
    ]

    # Sprawdź czy recenzja istnieje
    rs = client.execute("SELECT id FROM reviews WHERE book_id = ?", (book_id,))
    if rs.rows:
        stmts.append(libsql_client.Statement("""
            UPDATE reviews SET rating = ?, review = ?, date_finished = ? WHERE book_id = ?
        """, (rating, review, today, book_id)))
    else:
        stmts.append(libsql_client.Statement("""
            INSERT INTO reviews (book_id, rating, review, date_finished) VALUES (?, ?, ?, ?)
        """, (book_id, rating, review, today)))

    # Potrzebny import Statement na górze jeśli używamy batch w ten sposób,
    # ale prościej zrobić dwa execute jeśli nie importujemy Statement:
    client.execute("UPDATE books SET status = 'Completed' WHERE id = ?", (book_id,))
    if rs.rows:
        client.execute("UPDATE reviews SET rating = ?, review = ?, date_finished = ? WHERE book_id = ?",
                       (rating, review, today, book_id))
    else:
        client.execute("INSERT INTO reviews (book_id, rating, review, date_finished) VALUES (?, ?, ?, ?)",
                       (book_id, rating, review, today))

    print(f"✅ Completed book {book_id}")