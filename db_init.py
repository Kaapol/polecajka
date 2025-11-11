import libsql_client
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get("TURSO_DATABASE_URL")
DB_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

client = None
if DB_URL and DB_TOKEN:
    try:
        url_https = DB_URL.replace("libsql://", "https://")

        #klucz synchroniczny z https
        client = libsql_client.create_client_sync(
            url=url_https,
            auth_token=DB_TOKEN
        )
        print(f"✅ Połączono z Turso (sync): {url_https}")
    except Exception as e:
        print(f"❌ Błąd połączenia z Turso: {e}")
        import traceback

        traceback.print_exc()
else:
    print("⚠️  OSTRZEŻENIE: Brak zmiennych TURSO. Baza nie zadziała.")


def is_database_initialized(client):
    """Sprawdzaj czy istnieje tabela 'books' (marker inicjalizacji)"""
    if not client:
        return False

    try:
        # Jeśli istnieje ta tabela, to DB jest zainicjalizowana
        rs = client.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='books'
        """)
        tables = rs_to_dicts(rs)
        db_init = len(tables) > 0
        print(f"Database initialized check: {db_init}")
        return db_init
    except Exception as e:
        print(f"Error checking database: {e}")
        return False

def get_client():
    """Zwraca JEDYNEGO klienta bazy."""
    return client


def rs_to_dicts(rs):
    """Przerabia cały wynik zapytania na listę słowników."""
    if not rs or not hasattr(rs, 'rows') or not rs.rows:
        return []

    columns = rs.columns if hasattr(rs, 'columns') else []

    # Konwertuj każdy wiersz na dict
    result = []
    for row in rs.rows:
        if isinstance(row, dict):
            result.append(row)
        elif hasattr(row, '_asdict'):
            result.append(row._asdict())
        else:
            # Jeśli to tuple/list, użyj columns jako kluczy
            result.append(dict(zip(columns, row)))

    return result


def row_to_dict(rs):
    """Przerabia pierwszy wiersz na słownik."""
    if not rs or not hasattr(rs, 'rows') or not rs.rows:
        return None

    columns = rs.columns if hasattr(rs, 'columns') else []
    row = rs.rows[0]

    if isinstance(row, dict):
        return row
    elif hasattr(row, '_asdict'):
        return row._asdict()
    else:
        return dict(zip(columns, row))


def initialize_database():
    """Inicjalizuje bazę danych - tworzy tabele."""
    if not client:
        print("❌ Brak klienta bazy.")
        return False

    try:
        client.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        client.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                author TEXT,
                category TEXT,
                status TEXT DEFAULT 'To Read',
                date_added TEXT,
                thumbnail TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        client.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                rating INTEGER,
                review TEXT,
                date_finished TEXT,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
            )
        """)

        # Włącz foreign keys
        client.execute("PRAGMA foreign_keys = ON")

        print("✅ Baza danych zainicjalizowana na Turso.")
        return True

    except Exception as e:
        print(f"❌ Błąd inicjalizacji: {e}")
        import traceback
        traceback.print_exc()
        return False



if __name__ == "__main__":
    print(f"DB_URL: {DB_URL}")
    print(f"DB_TOKEN: {'***' if DB_TOKEN else 'BRAK'}")
    initialize_database()