from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
# Importowanie niezbędnych modułów z Flask do obsługi aplikacji webowej.
# - Flask: Główna klasa aplikacji.
# - render_template: Funkcja do renderowania plików HTML (szablonów Jinja).
# - request: Obiekt przechowujący dane żądania HTTP (np. z formularzy).
# - redirect, url_for: Funkcje do przekierowywania użytkownika między stronami.
# - session: Obiekt do zarządzania sesjami użytkowników (np. do logowania).
# - flash: Funkcja do wyświetlania jednorazowych komunikatów (np. "Książka dodana!").
# - jsonify: Funkcja do zwracania odpowiedzi w formacie JSON (dla API).
import os
# Importowanie modułu 'os' do interakcji z systemem operacyjnym (np. do sprawdzania plików baz danych).
import bcrypt
# Importowanie modułu 'bcrypt' do bezpiecznego hashowania i weryfikacji haseł (dla logowania).
import sqlite3
# Importowanie modułu 'sqlite3' do pracy z bazą danych SQLite.
from add_book import add_book
# Importowanie funkcji 'add_book' z oddzielnego pliku, która dodaje książkę do DB.
from remove_book import remove_book
# Importowanie funkcji 'remove_book' z oddzielnego pliku, która usuwa książkę z DB.
from edit_book import edit_book
# Importowanie funkcji 'edit_book' z oddzielnego pliku, która edytuje szczegóły książki.
from complete_book import complete_book
# Importowanie funkcji 'complete_book' z oddzielnego pliku, która oznacza książkę jako ukończoną i dodaje recenzję.
from db_init import get_connection, initialize_database
# Importowanie funkcji do łączenia się z bazą danych i jej inicjalizacji.
from urllib.parse import urlparse, urljoin, quote
# Importowanie narzędzi do parsowania i manipulacji adresami URL (szczególnie dla bezpieczeństwa i API Google Books).
# - urlparse, urljoin: Do sprawdzania bezpieczeństwa przekierowań.
# - quote: Do bezpiecznego kodowania ciągów znaków w URL (np. tytułów książek w zapytaniu do Google).
from dotenv import load_dotenv
# Importowanie modułu 'dotenv' do ładowania zmiennych środowiskowych z pliku .env.
import requests
# Importowanie modułu 'requests' do wykonywania żądań HTTP (do komunikacji z Google Books API).


load_dotenv()
# Ładowanie wszystkich zmiennych środowiskowych z pliku .env (np. klucza API).
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
# PRZECHOWUJE: Klucz API do Google Books. Klucz jest pobierany z systemu operacyjnego lub pliku .env.

app = Flask(__name__)
# Inicjalizacja głównej aplikacji Flask. __name__ to nazwa bieżącego modułu.

app.secret_key = "9e6663d956531a9dbdad7a8e5196119e6d6b8cf8a6154be26834db2789038a8d"
# PRZECHOWUJE: Sekretny klucz używany przez Flask do bezpiecznego podpisywania ciasteczek sesji.
# To zapewnia, że dane sesji (jak stan zalogowania) nie mogą być zmienione przez użytkownika.


# FUNKCJE POMOCNICZE
# ==============================================================================

def is_safe_url(target):
# FUNKCJA: Sprawdza, czy docelowy adres URL jest bezpieczny do przekierowania, zapobiegając atakom typu "Open Redirect".
    ref_url = urlparse(request.host_url)
    # Parsowanie bazowego URL hosta aplikacji (np. 'http://localhost:5000').
    test_url = urlparse(urljoin(request.host_url, target))
    # Łączenie i parsowanie docelowego URL. Użycie urljoin sprawia, że ścieżki względne są traktowane poprawnie.
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
    # Sprawdzenie, czy schemat to 'http' lub 'https' ORAZ czy nazwa hosta jest taka sama jak nazwa hosta aplikacji.


def get_books():
# FUNKCJA: Pobiera listę wszystkich książek z bazy danych wraz z powiązanymi recenzjami.
    if not os.path.exists("books.db"):
    # Warunek: Sprawdza, czy plik bazy danych w ogóle istnieje.
        return []
    # Zwraca pustą listę, jeśli bazy danych nie ma.

    conn = get_connection()
    # Nawiązuje połączenie z bazą danych (funkcja z db_init).
    cur = conn.cursor()
    # Tworzy kursor do wykonywania zapytań SQL.
    cur.execute("""
        SELECT b.id, b.title, b.author, b.category, b.status,
               r.rating, r.review, b.thumbnail
        FROM books b
        LEFT JOIN reviews r ON b.id = r.book_id
        ORDER BY b.date_added DESC
    """)
    # Wykonanie zapytania: Pobiera wszystkie szczegóły książki (b.*) i łączy je z recenzjami (r.*),
    # używając LEFT JOIN, aby pokazać książki, nawet jeśli nie mają recenzji. Wyniki są sortowane malejąco po dacie dodania.
    books = cur.fetchall()
    # Pobiera wszystkie wiersze z wyników zapytania.
    conn.close()
    # Zamyka połączenie z bazą danych.
    return books
    # Zwraca listę słowników lub tupli (w zależności od konfiguracji cur.fetchone).


# ROUTING APLIKACJI
# ==============================================================================

@app.route("/")
# DEFINICJA ROUTE: Określa funkcję 'home' jako obsługującą żądanie GET dla głównego URL ('/').
def home():
# FUNKCJA: Renderuje stronę powitalną (główny landing page).
    return render_template("home.html")
    # Zwraca wyrenderowany plik 'home.html'.


@app.route("/books")
# DEFINICJA ROUTE: Obsługuje żądanie GET dla strony z listą wszystkich książek.
def index():
# FUNKCJA: Renderuje główną stronę z listą książek.
    db_exists = os.path.exists("books.db")
    # PRZECHOWUJE: Wartość logiczną, czy baza danych istnieje.
    books = get_books()
    # Pobiera listę książek z DB (patrz wyżej).
    return render_template("index.html", books=books, db_exists=db_exists)
    # Renderuje 'index.html', przekazując do szablonu listę książek i status bazy danych.


@app.route("/add", methods=["POST"])
# DEFINICJA ROUTE: Obsługuje żądanie POST (wysłanie formularza) w celu dodania nowej książki.
def add():
# FUNKCJA: Dodaje nową książkę do bazy danych, w tym wyszukuje jej miniaturkę.
    title = request.form["title"].title()
    # Pobiera tytuł z formularza POST i formatuje go z wielkiej litery.
    author = request.form["author"].title()
    # Pobiera autora z formularza POST i formatuje go z wielkiej litery.
    category = request.form["category"].title()
    # Pobiera kategorię z formularza POST i formatuje ją z wielkiej litery.

    thumbnail = None
    # PRZECHOWUJE: Zmienna inicjalizowana na None, w której zostanie zapisany URL miniaturki.

    # Wyszukiwanie miniaturki za pomocą Google Books API
    query = f'intitle:{quote(title)}+inauthor:{quote(author)}'
    # Tworzenie zapytania do API: kodowanie tytułu i autora, aby były bezpieczne w URL (quote).
    url = "https://www.googleapis.com/books/v1/volumes"
    # Adres endpointu API Google Books.
    params = {
        "q": query,
        "maxResults": 5,
        "printType": "books",
        "key": GOOGLE_BOOKS_API_KEY
    }
    # Parametry zapytania: zapytanie, max. 5 wyników, tylko książki, użycie klucza API.
    resp = requests.get(url, params=params)
    # Wysyłanie żądania GET do Google Books API.
    if resp.status_code == 200:
    # Warunek: Sprawdza, czy zapytanie zakończyło się sukcesem (kod HTTP 200).
        data = resp.json()
        # Deserializacja odpowiedzi JSON.
        items = data.get("items", [])
        # Pobieranie listy wyników książek.
        if items:
        # Warunek: Sprawdza, czy lista wyników nie jest pusta.
            # pętla przez wyniki aż znajdziemy pierwszą miniaturkę
            for volume in items:
            # Iteracja przez każdy wynik książki.
                image_links = volume.get("volumeInfo", {}).get("imageLinks", {})
                # Pobieranie obiektu 'imageLinks' zawierającego URL miniaturki.
                thumbnail = image_links.get("thumbnail") or image_links.get("smallThumbnail")
                # Przypisanie URL: preferuje dużą miniaturkę ('thumbnail'), a jeśli jej nie ma, używa małej ('smallThumbnail').
                if thumbnail:
                # Warunek: Sprawdza, czy miniaturka została znaleziona.
                    thumbnail = thumbnail.replace("http://", "https://")
                    # Wymusza użycie bezpiecznego protokołu HTTPS, jeśli API zwróciło HTTP.
                    break
                    # Przerywa pętlę po znalezieniu pierwszej miniaturki.

    print("DEBUG add book:", title, author, category, thumbnail)
    # Wypisuje do konsoli serwera szczegóły dodawanej książki (do debugowania).
    add_book(title, author, category, thumbnail)
    # Wywołuje funkcję z add_book.py, zapisując wszystkie dane do bazy.
    return redirect(url_for("index"))
    # Przekierowuje użytkownika z powrotem na listę książek.


#get book ID
def get_book_by_id(book_id):
# FUNKCJA: Pobiera szczegóły pojedynczej książki na podstawie jej ID.
    conn = get_connection()
    # Nawiązuje połączenie z bazą.
    cur = conn.cursor()
    # Tworzy kursor.
    cur.execute("""
        SELECT b.id, b.title, b.author, b.category, b.status, b.date_added, b.thumbnail,
               r.date_finished, r.rating, r.review
        FROM books b
        LEFT JOIN reviews r ON b.id = r.book_id
        WHERE b.id = ?
    """, (book_id,))
    # Wykonanie zapytania: Pobiera wszystkie szczegóły (w tym miniaturkę i recenzję) dla książki o podanym ID (?).
    book = cur.fetchone()
    # Pobiera tylko jeden wiersz (ponieważ ID jest unikatowe).
    conn.close()
    # Zamyka połączenie.
    return book
    # Zwraca dane książki.


@app.route("/book/<int:book_id>")
# DEFINICJA ROUTE: Obsługuje żądanie GET dla strony szczegółów książki. <int:book_id> przechwytuje ID z URL.
def book_detail(book_id):
# FUNKCJA: Renderuje stronę ze szczegółami jednej książki.
    book = get_book_by_id(book_id)
    # Pobiera dane książki za pomocą ID.
    return render_template("book.html", book=book)
    # Renderuje 'book.html', przekazując do szablonu dane książki.

@app.route("/delete/<int:book_id>", methods=["POST"])
# DEFINICJA ROUTE: Obsługuje żądanie POST (np. z formularza) do usunięcia książki.
def delete(book_id):
# FUNKCJA: Usuwa książkę z bazy danych.
    remove_book(book_id)
    # Wywołuje funkcję z remove_book.py, która usuwa książkę i powiązaną recenzję.
    return redirect(url_for("index"))
    # Przekierowuje na listę książek.


@app.route("/complete/<int:book_id>", methods=["POST"])
# DEFINICJA ROUTE: Obsługuje żądanie POST do oznaczenia książki jako ukończonej i dodania recenzji/oceny.
def complete(book_id):
# FUNKCJA: Aktualizuje status książki.
    rating = int(request.form["rating"])
    # Pobiera ocenę z formularza i konwertuje na liczbę całkowitą.
    review = request.form["review"]
    # Pobiera treść recenzji z formularza.
    complete_book(book_id, rating, review)
    # Wywołuje funkcję z complete_book.py, która aktualizuje DB.
    return redirect(url_for("book_detail", book_id=book_id))
    # Przekierowuje z powrotem na stronę szczegółów tej samej książki.

@app.route("/edit/<int:book_id>", methods=["POST"])
# DEFINICJA ROUTE: Obsługuje żądanie POST do edycji podstawowych szczegółów książki (Tytuł, Autor, Kategoria).
def edit(book_id):
# FUNKCJA: Edytuje dane książki.
    title = request.form["title"].strip()
    # Pobiera tytuł, usuwając białe znaki na początku i końcu.
    author = request.form["author"].strip()
    # Pobiera autora, usuwając białe znaki.
    category = request.form["category"].strip()
    # Pobiera kategorię, usuwając białe znaki.

    # Puste stringi zamień na None, żeby edit_book je pominął
    title = title if title else None
    # Jeśli tytuł jest pusty, ustawia go na None.
    author = author if author else None
    # Jeśli autor jest pusty, ustawia go na None.
    category = category if category else None
    # Jeśli kategoria jest pusta, ustawia ją na None.

    edit_book(book_id, title, author, category)
    # Wywołuje funkcję z edit_book.py do aktualizacji danych.
    return redirect(url_for("index"))
    # Przekierowuje na listę książek (możesz zmienić na 'book_detail').


@app.route("/book/<int:book_id>/edit", methods=["POST"])
# DEFINICJA ROUTE: To jest alias lub alternatywny route do edycji (jak funkcja 'edit' powyżej, ale z inną nazwą URL).
def edit_book_route(book_id):
# FUNKCJA: Edytuje dane książki (używa tej samej logiki co 'edit').
    title = request.form.get("title")
    # Pobiera tytuł (używając .get() dla bezpieczeństwa).
    author = request.form.get("author")
    # Pobiera autora.
    category = request.form.get("category")
    # Pobiera kategorię.
    edit_book(book_id, title, author, category)
    # Wywołuje funkcję edytującą.
    return redirect(url_for("book_detail", book_id=book_id))
    # Przekierowuje na stronę szczegółów książki.

@app.errorhandler(404)
# DEKORATOR: Funkcja obsługująca błędy '404 Not Found'.
@app.errorhandler(500)
# DEKORATOR: Funkcja obsługująca błędy '500 Internal Server Error'.
def handle_error(e):
# FUNKCJA: Przekierowuje użytkownika na stronę główną w przypadku błędu.
    return redirect(url_for("home"))
    # Przekierowanie.


# ZARZĄDZANIE SESJAMI I AUTORYZACJĄ
# ==============================================================================

ADMIN_USERNAME = "admin"
# PRZECHOWUJE: Zdefiniowana nazwa użytkownika dla administratora.
ADMIN_PASSWORD_HASH = b"$2b$12$rHOwLdcakTzBDyJXm4NA1On.94bCm4bNLZaUps7sEBsj.KQxtW5xK"
# PRZECHOWUJE: Zahashowane hasło dla administratora (użyte do weryfikacji przez bcrypt).

@app.route("/login", methods=["GET", "POST"])
# DEFINICJA ROUTE: Obsługuje wyświetlanie i przetwarzanie formularza logowania.
def login():
# FUNKCJA: Logowanie użytkownika.
    # Jeżeli użytkownik jest już zalogowany, to niech nie wraca na login
    if session.get("is_admin"):
    # Warunek: Sprawdza, czy w sesji jest flaga zalogowania.
        return redirect(session.get("pre_login_url") or url_for("index"))
        # Jeśli tak, przekierowuje na stronę, z której przyszedł, lub na listę książek.

    if request.method == "GET":
    # Warunek: Jeśli żądanie jest GET (czyli użytkownik otwiera stronę logowania).
        # referrer can be none if entering directly
        session["pre_login_url"] = request.referrer or url_for("index")
        # Zapisuje w sesji URL strony, z której użytkownik przyszedł.
        # dont save if referrer is login
        if session["pre_login_url"].endswith("/login"):
        # Warunek: Jeśli użytkownik przyszedł ze strony logowania (np. odświeżył).
            session["pre_login_url"] = url_for("index")
            # Ustawia domyślny URL przekierowania na listę książek.

    if request.method == "POST":
    # Warunek: Jeśli żądanie jest POST (czyli użytkownik wysłał formularz).
        username = request.form.get("username")
        # Pobiera nazwę użytkownika.
        password = request.form.get("password")
        # Pobiera hasło.

        if username == ADMIN_USERNAME and bcrypt.checkpw(password.encode("utf-8"), ADMIN_PASSWORD_HASH):
        # WERYFIKACJA: Sprawdza nazwę użytkownika ORAZ bezpiecznie weryfikuje hasło za pomocą bcrypt.
            session.permanent = True
            # Ustawia sesję jako trwałą (nie wygasa po zamknięciu przeglądarki).
            session["is_admin"] = True
            # Ustawia flagę zalogowania w sesji.
            session["username"] = username
            # Zapisuje nazwę użytkownika w sesji.
            flash("Logged in successfully!", "success")
            # Wyświetla komunikat sukcesu.

            redirect_url = session.pop("pre_login_url", url_for("index"))
            # Pobiera i usuwa URL do przekierowania po zalogowaniu.
            return redirect(redirect_url)
            # Przekierowuje użytkownika.

        else:
            return render_template("login.html", error="Invalid username or password")
            # W przypadku niepowodzenia, ponownie renderuje stronę z błędem.

    return render_template("login.html")
    # Renderuje stronę logowania dla żądania GET.


@app.route("/logout")
# DEFINICJA ROUTE: Obsługuje wylogowanie.
def logout():
# FUNKCJA: Wylogowuje użytkownika.
    session.clear()
    # Czyści wszystkie dane z sesji (usuwając flagę 'is_admin').
    flash("Logged out successfully", "info")
    # Wyświetla komunikat.

    referrer = request.referrer
    # Pobiera URL strony, z której przyszedł użytkownik.
    if referrer and is_safe_url(referrer):
    # Warunek: Sprawdza, czy URL istnieje i jest bezpieczny.
        return redirect(referrer)
        # Przekierowuje na poprzednią stronę.
    return redirect(url_for("home"))
    # Jeśli nie ma referera lub jest niebezpieczny, przekierowuje na stronę główną.


@app.route("/init_books_db", methods=["POST"])
# DEFINICJA ROUTE: Obsługuje inicjalizację bazy danych (dostępne tylko dla admina).
def init_books_db():
# FUNKCJA: Tworzy tabele w bazie danych.
    if not session.get("is_admin"):
    # Warunek: Sprawdza, czy użytkownik jest zalogowany jako admin.
        flash("Unauthorized", "danger")
        # Błąd, jeśli nie jest adminem.
        return redirect(url_for("index"))
        # Przekierowuje na listę książek.

    created = initialize_database()
    # Wywołuje funkcję z db_init, która tworzy bazę danych (zwraca True/False).
    if created:
        flash("Books database created successfully!", "success")
    else:
        flash("Database already exists!", "info")

    return redirect(url_for("index"))
    # Przekierowuje na listę książek.


# GOOGLE BOOKS API (WYSZUKIWANIE)
# ==============================================================================

@app.route("/search")
# DEFINICJA ROUTE: Obsługuje żądanie API do wyszukiwania książek (używane przez autouzupełnianie).
def search_books():
# FUNKCJA: Łączy się z Google Books API w celu znalezienia sugestii.
    query = request.args.get("q", "")
    # Pobiera frazę wyszukiwania z parametrów URL (np. ?q=wiedzmin).
    if not query:
    # Warunek: Sprawdza, czy zapytanie nie jest puste.
        return {"error": "Missing query"}, 400
        # Zwraca błąd 400 Bad Request.

    url = "https://www.googleapis.com/books/v1/volumes"
    # Adres endpointu API.
    params = {
        "q": query,
        "maxResults": 8,
        "printType": "books",
        "key": GOOGLE_BOOKS_API_KEY
    }
    # Ustawia parametry: zapytanie, max 8 wyników, tylko książki, klucz API.

    response = requests.get(url, params=params)
    # Wykonuje żądanie HTTP.
    if response.status_code != 200:
        return {"error": "Google API request failed"}, 500
        # Obsługa błędu, jeśli API Google zwróciło inny kod niż 200.

    data = response.json()
    # Deserializacja odpowiedzi JSON.

    # Poniżej znajduje się list comprehension, które buduje listę wyników w wymaganym formacie
    return jsonify({
        "results": [
            {
                "title": item["volumeInfo"].get("title", ""),
                # Pobiera tytuł.
                "authors": item["volumeInfo"].get("authors", []),
                # Pobiera listę autorów.
                "thumbnail": item["volumeInfo"].get("imageLinks", {}).get("thumbnail", ""),
                # Pobiera URL miniaturki.
                "categories": item["volumeInfo"].get("categories", [])
                # Pobiera listę kategorii.
            }
            for item in data.get("items", [])
            # Iteruje przez każdy wynik z API.
        ]
    })
    # Zwraca wynik w formacie JSON do przeglądarki.


if __name__ == "__main__":
# Blok kodu, który wykonuje się tylko wtedy, gdy plik jest uruchamiany bezpośrednio (a nie importowany).
    app.run(debug=False)
    # Uruchomienie serwera Flask. debug=False oznacza, że nie uruchomi się w trybie debugowania (produkcyjny standard).
