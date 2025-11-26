from datetime import datetime
from db_init import client


def edit_item(item_id, title=None, creator=None, category=None):
    """Edytuje item - title, creator lub category"""
    if not client:
        return

    fields, values = [], []

    if title:
        fields.append("title = ?")
        values.append(title.title())
    if creator:
        fields.append("creator = ?")
        values.append(creator.title())
    if category:
        fields.append("category = ?")
        values.append(category.title())

    if not fields:
        return

    values.append(item_id)
    query = f"UPDATE items SET {', '.join(fields)} WHERE id = ?"
    client.execute(query, values)
    print(f"✅ Updated item {item_id}")


def edit_review_date(item_id, date_finished):
    """Edytuje datę ukończenia w reviews"""
    if not date_finished:
        return
    if not client:
        return
    try:
        new_date = datetime.strptime(date_finished, "%Y-%m-%d").strftime("%d-%m-%Y")
        client.execute("UPDATE reviews SET date_finished = ? WHERE item_id = ?", (new_date, item_id))
        print(f"✅ Updated date for item {item_id}")
    except ValueError:
        print("⚠️ Invalid date format")


if __name__ == "__main__":
    pass