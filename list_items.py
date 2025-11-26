import pandas as pd
from tabulate import tabulate
from db_init import client

def list_items(show=True):
    conn = client
    if not conn:
        if show:
            print("Couldn't connect with list_items.")
        return 0

    try:
        df = pd.read_sql_query("SELECT * FROM items", conn)
    except Exception as e:
        print(f"Error in reading db via pandas: {e}")
        return 0
    finally:
        if conn:
            conn.close()

    if df.empty:
        if show:
            print(f"Couldn't find any items.")
        return 0

    if show:
        print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))

    return len(df)

if __name__ == "__main__":
    list_items()