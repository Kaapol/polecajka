import libsql_client
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get("TURSO_DATABASE_URL")
DB_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

client = None
if DB_URL and DB_TOKEN:
    try:
        # Używamy klienta SYNCHRONICZNEGO. To naprawia błąd "no running event loop".
        client = libsql_client.create_client_sync(url=DB_URL, auth_token=DB_TOKEN)
        print("✅ Połączono z Turso (tryb sync)")
    except Exception as e:
        print(f"❌ Błąd połączenia z Turso: {e}")
else:
    print("⚠️  OSTRZEŻENIE: Brak zmiennych TURSO. Baza nie zadziała.")

def get_client():
    """Zwraca JEDYNEGO klienta bazy."""
    return client

# --- TO JEST FUNKCJA, KTÓREJ BRAKOWAŁO ---
def rs_to_dicts(rs):
    """Przerabia cały wynik zapytania na listę słowników."""
    if not rs or not rs.rows:
        return []
    columns = rs.columns
    return [dict(zip(columns, row)) for row in rs.rows]

def row_to_dict(rs):
    """Przerabia pierwszy wiersz na słownik."""
    if not rs or not rs.rows:
        return None
    return dict(zip(rs.columns, rs.rows[0]))
# --- KONIEC FUNKCJI POMOCNICZYCH ---

def initialize_database():
    if not client:
        print("❌ Brak klienta bazy.")
        return False
    try:
        # .batch() wykonuje wiele zapytań naraz
        client.batch([
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                category TEXT,
                status TEXT DEFAULT 'To Read',
                date_added TEXT,
                thumbnail TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                rating INTEGER,
                review TEXT,
                date_finished TEXT,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
            )
            """
        ])
        print("✅ Baza danych zainicjalizowana na Turso.")
        return True
    except Exception as e:
        print(f"❌ Błąd inicjalizacji: {e}")
        return False

if __name__ == "__main__":
    initialize_database()