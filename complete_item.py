from datetime import datetime
from db_init import client
import libsql_client


def complete_item(item_id, rating, review):
    """Oznacza item jako Completed i dodaje/aktualizuje review"""
    if not client:
        return

    today = datetime.now().strftime("%d-%m-%Y")

    # Sprawdź czy recenzja istnieje
    rs = client.execute("SELECT id FROM reviews WHERE item_id = ?", (item_id,))

    if rs.rows:
        # Update istniejący review
        client.execute("""
            UPDATE reviews SET rating = ?, review = ?, date_finished = ? WHERE item_id = ?
        """, (rating, review, today, item_id))
    else:
        # Insert nowy review
        client.execute("""
            INSERT INTO reviews (item_id, rating, review, date_finished) VALUES (?, ?, ?, ?)
        """, (item_id, rating, review, today))

    # Oznacz item jako Completed
    client.execute("UPDATE items SET status = 'Completed' WHERE id = ?", (item_id,))

    print(f"✅ Completed item {item_id}")