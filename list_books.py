import sqlite3
import pandas as pd
from tabulate import tabulate

def list_books(show=True):
    conn = sqlite3.connect("books.db") #connect

    df = pd.read_sql_query("SELECT * FROM books", conn)

    conn.close()

    if df.empty:
        if show:
            print(f"❌ No books found.")
        return 0

    if show:
        print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))

    return len(df)

if __name__ == "__main__":
    list_books()
