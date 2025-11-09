# usunięto import sqlite3
import pandas as pd
from tabulate import tabulate
from db_init import client  # Importujemy klienta Turso


def list_books(show=True):
    if not client:
        if show:
            print("❌ Baza danych nie jest połączona.")
        return 0

    # Zmieniona logika pobierania danych dla Pandas
    rs = client.execute("SELECT * FROM books")

    if not rs.rows:
        if show:
            print(f"❌ No books found.")
        return 0

    # Tworzymy DataFrame ręcznie z wyników Turso
    df = pd.DataFrame(rs.rows, columns=rs.columns)

    # reszta bez zmian
    if show:
        print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))

    return len(df)


if __name__ == "__main__":
    list_books()