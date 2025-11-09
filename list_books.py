import pandas as pd
from tabulate import tabulate
from db_init import client

def list_books(show=True):
    conn = client
    if not conn:
        if show:
            print("❌ Błąd połączenia w list_books.")
        return 0

    try:
        # pandas.read_sql_query działa idealnie z obiektem połączenia
        df = pd.read_sql_query("SELECT * FROM books", conn)
    except Exception as e:
        print(f"Błąd odczytu bazy przez pandas: {e}")
        return 0
    finally:
        if conn:
            conn.close() # Zawsze zamykaj połączenie

    if df.empty:
        if show:
            print(f"❌ Nie znaleziono żadnych książek.")
        return 0

    if show:
        print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))

    return len(df)

if __name__ == "__main__":
    list_books()