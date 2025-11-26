from db_init import client


def remove_item(item_id):
    """Usuwa item i powiązane reviews (cascade delete)"""
    if not client:
        print("Error: couldn't connect to database")
        return

    try:
        # Wykonaj DELETE
        result = client.execute("DELETE FROM items WHERE id = ?", (item_id,))

        # Sprawdź czy coś usunięto
        rows_affected = getattr(result, 'rows_affected', 0)

        if rows_affected == 0:
            print(f"Couldn't find an item with ID {item_id}")
        else:
            print(f"Successfully deleted item with ID {item_id} (with its reviews).")

    except Exception as e:
        print(f"Error in remove_item: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    remove_item(999)  # Test