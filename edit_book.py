from datetime import datetime
from db_init import client

def edit_book(book_id, title=None, author=None, category=None):
    if not client: return

    fields, values = [], []
    if title:
        fields.append("title = ?")
        values.append(title.title())
    if author:
        fields.append("author = ?")
        values.append(author.title())
    if category:
        fields.append("category = ?")
        values.append(category.title())

    if not fields: return

    values.append(book_id)
    query = f"UPDATE books SET {', '.join(fields)} WHERE id = ?"
    client.execute(query, values)
    print(f"✅ Updated book {book_id}")

def edit_review_date(book_id, date_finished):
    if not date_finished: return
    if not client: return
    try:
        new_date = datetime.strptime(date_finished, "%Y-%m-%d").strftime("%d-%m-%Y")
        client.execute("UPDATE reviews SET date_finished = ? WHERE book_id = ?", (new_date, book_id))
        print(f"✅ Updated date for {book_id}")
    except ValueError:
        print("⚠️ Invalid date format")

if __name__ == "__main__":
    # Testy
    pass