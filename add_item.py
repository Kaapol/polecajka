from db_init import client
from datetime import datetime

def add_item(user_id, item_type, title, creator, category, thumbnail=None):
    """Dodaje item dla konkretnego użytkownika"""
    if not client:
        raise Exception("No DB client")

    if not item_type:
        raise ValueError("Item type is required")

    # Sprawdź duplikat DLA TEGO UŻYTKOWNIKA I TYPU
    rs = client.execute(
        "SELECT id FROM items WHERE LOWER(title) = LOWER(?) AND user_id = ? AND type = ?",
        (title, user_id, item_type)
    )
    if rs.rows:
        raise ValueError(f"'{title}' already exists in your {item_type}!")

    date_added = datetime.now().strftime("%d-%m-%Y")
    client.execute("""
        INSERT INTO items (user_id, type, title, creator, category, date_added, thumbnail, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'To Complete')
    """, (user_id, item_type, title, creator, category, date_added, thumbnail))
    print(f"✅ Added: {title} ({item_type}) for user {user_id}")


if __name__ == "__main__":
    # Test
    pass