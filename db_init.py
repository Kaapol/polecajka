import libsql_client
import os
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe (dla lokalnego developmentu)
load_dotenv()

# --- CENTRALNE POŁĄCZENIE ---
# To jest JEDYNE miejsce, gdzie łączymy się z bazą.
# Vercel automatycznie wstrzyknie te zmienne, które ustawiłeś w panelu.
db_url = os.environ.get("TURSO_DATABASE_URL")
db_token = os.environ.get("TURSO_AUTH_TOKEN")

if not db_url or not db_token:
    print("BŁĄD KRYTYCZNY: Nie znaleziono TURSO_DATABASE_URL lub TURSO_AUTH_TOKEN")
    # Lokalnie: upewnij się, że masz plik .env
    # Na Vercelu: upewnij się, że ustawiłeś zmienne w panelu
    # Na razie ustawiamy na None, żeby apka się nie wywaliła przy imporcie
    client = None
else:
    client = libsql_client.create_client(url=db_url, auth_token=db_token)
    print("✅ Połączono z Turso DB.")

# --- NOWE FUNKCJE POMOCNICZE ---
# Klient Turso zwraca dane inaczej niż sqlite3.
# sqlite3.Row dawało ci dicty (np. book['title']). Klient Turso daje tuple.
# Te funkcje konwertują tuple z powrotem na dicty, żeby reszta kodu działała.

def rows_to_dicts(rs: libsql_client.ResultSet) -> list[dict]:
    """Konwertuje wynik Turso (ResultSet) na listę słowników."""
    dicts = []
    for row in rs.rows:
        # Łączy nazwy kolumn (rs.columns) z wartościami w rzędzie (row)
        dicts.append(dict(zip(rs.columns, row)))
    return dicts

def row_to_dict(rs: libsql_client.ResultSet) -> dict | None:
    """Konwertuje i zwraca tylko pierwszy rząd jako słownik, lub None."""
    if not rs.rows:
        return None
    return dict(zip(rs.columns, rs.rows[0]))

# --- ZAKTUALIZOWANA FUNKCJA INICJALIZACJI ---
def initialize_database():
    """Tworzy tabele w bazie Turso, jeśli nie istnieją."""
    if not client:
        print("Błąd: Klient bazy danych nie jest skonfigurowany.")
        return False

    try:
        # Używamy BATCH do wykonania wielu poleceń naraz
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
        print("✅ Tabele bazy danych (books, reviews) zweryfikowane/stworzone na Turso.")
        return True
    except Exception as e:
        print(f"Błąd podczas inicjalizacji bazy Turso: {e}")
        return False

if __name__ == "__main__":
    if client:
        created = initialize_database()
        print("DB ready na Turso." if created else "DB na Turso już istniała.")
    else:
        print("Nie można zainicjować bazy, brak zmiennych środowiskowych.")