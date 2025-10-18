# ============================================================================
# IMPORTY - Ładowanie narzędzi potrzebnych do działania aplikacji
# ============================================================================

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
# Flask - główna klasa do tworzenia aplikacji webowej
# render_template - funkcja która bierze plik HTML i wypełnia go danymi
# request - obiekt zawierający wszystko co użytkownik wysłał (formularz, URL, itp)
# redirect - funkcja która mówi przeglądarce "idź na inną stronę"
# url_for - funkcja która generuje URL do konkretnej funkcji (np. url_for("index") = "/books")
# session - słownik który przechowuje dane o zalogowanym użytkowniku (działa jak ciasteczko)
# flash - funkcja do pokazywania jednorazowych wiadomości (np. "Książka dodana!")
# jsonify - zamienia pythonowy słownik na JSON (format zrozumiały dla JavaScript)

import os
# os - moduł do interakcji z systemem operacyjnym
# Używamy go np. żeby sprawdzić czy plik "books.db" istnieje na dysku

import bcrypt
# bcrypt - biblioteka do bezpiecznego hashowania haseł
# Zamiast przechowywać hasło "admin123", przechowujemy zaszyfrowany śmieć typu "$2b$12$rH..."
# Nawet jeśli ktoś ukradnie bazę danych, nie odczyta hasła

import sqlite3
# sqlite3 - biblioteka do pracy z bazą danych SQLite (prosty plik .db)
# SQLite to jak Excel na sterydach - przechowuje tabele z danymi

from add_book import add_book
# Importujemy funkcję add_book z pliku add_book.py
# Ta funkcja zapisuje nową książkę do bazy danych

from remove_book import remove_book
# Importujemy funkcję remove_book z pliku remove_book.py
# Ta funkcja usuwa książkę z bazy danych

from edit_book import edit_book
# Importujemy funkcję edit_book z pliku edit_book.py
# Ta funkcja zmienia dane książki w bazie

from complete_book import complete_book
# Importujemy funkcję complete_book z pliku complete_book.py
# Ta funkcja oznacza książkę jako przeczytaną i dodaje recenzję

from db_init import get_connection, initialize_database
# get_connection - funkcja która otwiera połączenie z bazą danych
# initialize_database - funkcja która tworzy tabele w bazie (books, reviews)

from urllib.parse import urlparse, urljoin, quote
# urlparse - rozbija URL na części (protokół, host, ścieżka)
# urljoin - skleja części URL w jeden
# quote - zamienia specjalne znaki w URL (np. spacje na %20)
# Przykład: quote("Harry Potter") = "Harry%20Potter"

from dotenv import load_dotenv
# dotenv - biblioteka do ładowania zmiennych z pliku .env
# Plik .env to jak sejf na hasła i klucze API - trzymamy tam sekrety

import requests

# requests - biblioteka do wysyłania zapytań HTTP
# Używamy jej do komunikacji z Google Books API


# ============================================================================
# KONFIGURACJA - Ustawienia początkowe aplikacji
# ============================================================================

load_dotenv()
# Czyta plik .env i ładuje wszystkie zmienne do pamięci
# Teraz możemy używać os.getenv("NAZWA_ZMIENNEJ")

GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
# Pobieram klucz API do Google Books z systemu
# Ten klucz to jak przepustka - bez niej Google nie odpowie na nasze zapytania
# Wartość np: "AIzaSyB3kd9fj2k3l4m5n6o7p8q9"

app = Flask(__name__)
# Tworzę aplikację Flask
# __name__ mówi Flaskowi gdzie szukać plików HTML (w folderze templates)
# Od teraz zmienna 'app' reprezentuje całą naszą aplikację webową

app.secret_key = "9e6663d956531a9dbdad7a8e5196119e6d6b8cf8a6154be26834db2789038a8d"


# Sekretny klucz do szyfrowania sesji
# Sesja to ciasteczko które przechowuje info "użytkownik jest zalogowany"
# Bez tego klucza haker mógłby fałszować sesje i udawać admina


# ============================================================================
# FUNKCJE POMOCNICZE - Narzędzia używane przez inne funkcje
# ============================================================================

def is_safe_url(target):
    """
    Sprawdza czy URL jest bezpieczny do przekierowania

    Przykład:
    - is_safe_url("/books") = True (bezpieczny, nasza domena)
    - is_safe_url("http://evil.com") = False (niebezpieczny, inna domena)
    """
    ref_url = urlparse(request.host_url)
    # Rozbijam URL naszej aplikacji na części
    # request.host_url = "http://localhost:5000"
    # Po parseowaniu: ref_url.netloc = "localhost:5000"

    test_url = urlparse(urljoin(request.host_url, target))
    # Łączę nasz host z docelowym URL i rozbijam na części
    # Jeśli target = "/books" → test_url = "http://localhost:5000/books"
    # Jeśli target = "http://evil.com" → test_url = "http://evil.com"

    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
    # Sprawdzam 2 rzeczy:
    # 1. Czy protokół to http lub https (nie ftp, nie javascript:)
    # 2. Czy host się zgadza (localhost:5000 == localhost:5000)
    # Jeśli obie prawda → return True (bezpieczny)
    # Jeśli którakolwiek fałsz → return False (niebezpieczny)


def get_books():
    """
    Pobiera wszystkie książki z bazy danych

    Zwraca listę książek, każda książka to słownik:
    {
        'id': 1,
        'title': 'Harry Potter',
        'author': 'J.K. Rowling',
        'category': 'Fantasy',
        'status': 'completed',
        'rating': 5,
        'review': 'Świetna książka!',
        'thumbnail': 'http://...'
    }
    """
    if not os.path.exists("books.db"):
        # Sprawdzam czy plik books.db istnieje na dysku
        # os.path.exists("books.db") zwraca True jeśli plik istnieje, False jeśli nie
        return []
        # Jeśli bazy nie ma, zwracam pustą listę []
        # To zapobiega błędowi "nie można otworzyć nieistniejącego pliku"

    conn = get_connection()
    # Otwieram połączenie z bazą danych
    # conn to jak kabel USB między naszym kodem a bazą danych
    # Teraz mogę wysyłać zapytania SQL przez ten kabel

    cur = conn.cursor()
    # Tworzę kursor - to jak wskaźnik/pilot do poruszania się po bazie
    # Kursor wykonuje zapytania SQL i zbiera wyniki

    cur.execute("""
                SELECT b.id,
                       b.title,
                       b.author,
                       b.category,
                       b.status,
                       r.rating,
                       r.review,
                       b.thumbnail
                FROM books b
                         LEFT JOIN reviews r ON b.id = r.book_id
                ORDER BY b.date_added DESC
                """)
    # Wysyłam zapytanie SQL do bazy:
    # SELECT - pobieram kolumny (id, title, author, itd.)
    # FROM books b - z tabeli books (skrót 'b')
    # LEFT JOIN reviews r - dołączam tabelę reviews (skrót 'r')
    # ON b.id = r.book_id - łączę po ID książki
    # LEFT JOIN znaczy: pokaż książki NAWET jeśli nie mają recenzji
    # ORDER BY b.date_added DESC - sortuj od najnowszych do najstarszych

    books = cur.fetchall()
    # Pobieram WSZYSTKIE wiersze z wyniku zapytania
    # books to teraz lista krotek, np:
    # [(1, 'Harry Potter', 'Rowling', 'Fantasy', 'completed', 5, 'Super', 'http://...'),
    #  (2, 'Witcher', 'Sapkowski', 'Fantasy', 'reading', None, None, 'http://...')]

    conn.close()
    # Zamykam połączenie z bazą (odłączam kabel USB)
    # Ważne! Zawsze zamykaj połączenie, inaczej wyciekną zasoby

    return books
    # Zwracam listę książek do funkcji która mnie wywołała


# ============================================================================
# ROUTING - Definicje stron (URL → Funkcja → HTML)
# ============================================================================

@app.route("/")
# DEKORATOR - mówi Flaskowi: "gdy ktoś wejdzie na URL '/', wywołaj funkcję home()"
# "/" to strona główna (jak wejdziesz na localhost:5000)
def home():
    """Strona powitalna"""
    return render_template("home.html")
    # Znajduje plik templates/home.html
    # Renderuje go (zamienia {{ zmienne }} na prawdziwe wartości)
    # Wysyła gotowy HTML do przeglądarki
    # Przeglądarka użytkownika widzi stronę powitalną


@app.route("/books")
# Gdy ktoś wejdzie na URL '/books', wywołaj funkcję index()
def index():
    """Strona z listą wszystkich książek"""

    db_exists = os.path.exists("books.db")
    # Sprawdzam czy baza istnieje
    # db_exists = True jeśli plik jest na dysku
    # db_exists = False jeśli nie ma pliku

    books = get_books()
    # Wywołuję funkcję get_books() (zdefiniowaną wyżej)
    # books to teraz lista wszystkich książek z bazy

    return render_template("index.html", books=books, db_exists=db_exists)
    # Renderuję szablon index.html
    # Przekazuję mu 2 zmienne:
    # - books (lista książek) - w HTML mogę użyć {{ books }}
    # - db_exists (True/False) - w HTML mogę użyć {% if db_exists %}
    # Flask zamienia szablon na gotowy HTML i wysyła do przeglądarki


@app.route("/add", methods=["POST"])
# Gdy ktoś wyśle formularz POST na URL '/add', wywołaj funkcję add()
# methods=["POST"] oznacza że akceptuję tylko POST (nie GET)
# POST to wysyłanie danych (formularz), GET to pobieranie strony
def add():
    """Dodaje nową książkę do bazy danych"""

    title = request.form["title"].title()
    # request.form to słownik z danymi z formularza
    # request.form["title"] pobieram wartość pola <input name="title">
    # Przykład: użytkownik wpisał "harry potter"
    # .title() zamienia pierwszą literę każdego słowa na wielką
    # Wynik: title = "Harry Potter"

    author = request.form["author"].title()
    # Podobnie jak wyżej, pobieram autora z formularza
    # Przykład: użytkownik wpisał "j.k. rowling"
    # Wynik: author = "J.K. Rowling"

    category = request.form["category"].title()
    # Pobieram kategorię z formularza
    # Przykład: użytkownik wpisał "fantasy"
    # Wynik: category = "Fantasy"

    thumbnail = None

    # Inicjalizuję zmienną thumbnail na None (pusty)
    # Tutaj będzie URL do obrazka okładki
    # Przykład końcowej wartości: "https://books.google.com/books/content?id=abc123..."

    # ------------------------------------------------------------------------
    # FUNKCJE POMOCNICZE DO WYSZUKIWANIA OBRAZKA
    # ------------------------------------------------------------------------

    def normalize_text(text):
        """
        Normalizuje tekst do porównań

        Przykład:
        normalize_text("Harry Potter & The Stone!") = "harry potter the stone"
        """
        import re
        # Importuję moduł re (regular expressions) do operacji na tekście

        if not text:
            # Jeśli text jest None lub pusty string
            return ""
            # Zwróć pusty string (bezpieczne)

        text = text.lower()
        # Zamieniam wszystkie litery na małe
        # "Harry Potter" → "harry potter"

        text = re.sub(r'[^\w\s]', ' ', text)
        # re.sub to "znajdź i zamień"
        # r'[^\w\s]' to regex oznaczający "wszystko co NIE jest literą lub spacją"
        # Zamieniam to na spację
        # "harry potter & the stone!" → "harry potter   the stone "

        text = ' '.join(text.split())
        # text.split() rozbija tekst na słowa (dzieli po spacjach)
        # "harry potter   the stone " → ["harry", "potter", "the", "stone"]
        # ' '.join(...) skleja słowa z powrotem, dodając tylko jedną spację między nimi
        # Wynik: "harry potter the stone"

        return text
        # Zwracam oczyszczony tekst

    def get_key_words(text):
        """
        Wyciąga ważne słowa (usuwa "śmieciowe" słowa typu "the", "and")

        Przykład:
        get_key_words("Harry Potter and the Stone") = ["harry", "potter", "stone"]
        """
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'by'}
        # Zbiór (set) śmieciowych słów które nie wnoszą znaczenia
        # Używam set zamiast list bo sprawdzanie "czy słowo jest w set" jest szybsze

        words = normalize_text(text).split()
        # Normalizeję tekst i rozbiajam na listę słów
        # "Harry Potter and the Stone" → ["harry", "potter", "and", "the", "stone"]

        return [w for w in words if w not in stop_words and len(w) > 2]
        # LIST COMPREHENSION - to jak pętla for w jednej linii
        # Przechodźę przez każde słowo 'w' w liście 'words'
        # Zostawiam tylko te słowa które:
        # - NIE są w stop_words (nie są śmieciowe)
        # - mają więcej niż 2 litery (usuwam "in", "at", itp)
        # Wynik: ["harry", "potter", "stone"]

    def check_match(book_title, book_authors, search_title, search_author):
        """
        Sprawdza jak dobrze książka z API pasuje do tego czego szukamy

        Parametry:
        - book_title: tytuł książki znalezionej w Google Books
        - book_authors: lista autorów znalezionej książki
        - search_title: tytuł który wpisał użytkownik
        - search_author: autor którego wpisał użytkownik

        Zwraca:
        - (True/False, score) - czy pasuje + ile punktów dostała (0-100)

        Przykład:
        check_match(
            "Harry Potter and the Philosopher's Stone",
            ["J.K. Rowling"],
            "Harry Potter Stone",
            "J.K. Rowling"
        ) → (True, 95)
        """
        norm_book_title = normalize_text(book_title)
        # Normalzeję tytuł książki z API
        # "Harry Potter and the Philosopher's Stone" → "harry potter and the philosopher s stone"

        norm_search_title = normalize_text(search_title)
        # Normalzeję tytuł który wpisał użytkownik
        # "Harry Potter Stone" → "harry potter stone"

        search_title_words = set(get_key_words(search_title))
        # Wyciągam ważne słowa z tego co wpisał użytkownik i zamieniam na set
        # "harry potter stone" → {"harry", "potter", "stone"}
        # Set to jak lista, ale bez duplikatów i szybsze porównania

        book_title_words = set(get_key_words(book_title))
        # Wyciągam ważne słowa z książki znalezionej w API
        # "harry potter and the philosopher s stone" → {"harry", "potter", "philosopher", "stone"}

        # OBLICZAM DOPASOWANIE TYTUŁU
        if not search_title_words:
            # Jeśli użytkownik nie wpisał żadnych ważnych słów (bardzo rzadkie)
            title_match = 0
            # Dopasowanie = 0 (brak danych do porównania)
        else:
            common_words = search_title_words.intersection(book_title_words)
            # .intersection() znajduje wspólne elementy w dwóch setach
            # {"harry", "potter", "stone"} ∩ {"harry", "potter", "philosopher", "stone"}
            # = {"harry", "potter", "stone"} (3 wspólne słowa)

            title_match = len(common_words) / len(search_title_words)
            # Obliczam procent dopasowania
            # 3 wspólne słowa / 3 słowa użytkownika = 1.0 (100% dopasowanie)
            # Przykład gorszy: 2/3 = 0.66 (66% dopasowanie)

        # SPRAWDZAM AUTORA
        author_match = False
        # Zakładam że autor się NIE zgadza
        # Zmienię to na True jeśli znajdę dopasowanie

        if book_authors:
            # Jeśli książka w API ma jakichś autorów (czasami nie ma!)

            norm_search_author = normalize_text(search_author)
            # Normalizeję autora wpisanego przez użytkownika
            # "J.K. Rowling" → "j k rowling"

            search_author_words = set(get_key_words(search_author))
            # Wyciągam ważne słowa z nazwiska
            # "j k rowling" → {"rowling"} (j i k są za krótkie, zostają usunięte)

            for author in book_authors:
                # Przechodźę przez każdego autora książki z API
                # book_authors to lista, np: ["J.K. Rowling", "John Tiffany"]

                norm_book_author = normalize_text(author)
                # Normalizeję autora z API
                # "J.K. Rowling" → "j k rowling"

                if norm_search_author == norm_book_author:
                    # Jeśli są DOKŁADNIE takie same
                    # "j k rowling" == "j k rowling" → True
                    author_match = True
                    # Autor się zgadza!
                    break
                    # Wychodzę z pętli (nie trzeba sprawdzać kolejnych autorów)

                if search_author_words:
                    # Jeśli użytkownik wpisał jakieś ważne słowa w nazwisku

                    book_author_words = set(get_key_words(author))
                    # Wyciągam ważne słowa z autora z API
                    # "j k rowling" → {"rowling"}

                    common = search_author_words.intersection(book_author_words)
                    # Znajduję wspólne słowa
                    # {"rowling"} ∩ {"rowling"} = {"rowling"}

                    if len(common) >= 1:
                        # Jeśli przynajmniej 1 słowo się zgadza (zazwyczaj nazwisko)
                        author_match = True
                        # Autor się zgadza!
                        break
                        # Wychodzę z pętli

        # OBLICZAM KOŃCOWY WYNIK (SCORE)
        score = 0
        # Zaczynam od 0 punktów

        if title_match >= 0.5:
            # Jeśli przynajmniej 50% słów z tytułu się zgadza
            score += int(title_match * 60)
            # Dodaję punkty proporcjonalnie
            # 100% dopasowanie = 60 punktów
            # 75% dopasowanie = 45 punktów
            # 50% dopasowanie = 30 punktów

        if author_match:
            # Jeśli autor się zgadza
            score += 40
            # Dodaję 40 punktów

        # Maksymalny możliwy wynik: 60 (tytuł) + 40 (autor) = 100 punktów

        return score > 40, score
        # Zwracam krotkę (tuple) z 2 elementami:
        # 1. True/False - czy książka pasuje (czy score > 40 punktów)
        # 2. score - ile punktów dostała
        # Przykład: (True, 95) lub (False, 25)

    # ------------------------------------------------------------------------
    # GŁÓWNA LOGIKA WYSZUKIWANIA OBRAZKA
    # ------------------------------------------------------------------------

    search_queries = []
    # Pusta lista do przechowywania różnych strategii wyszukiwania
    # Na końcu będzie wyglądać np:
    # ['"Harry Potter" "Rowling"', 'Harry Potter Rowling', 'intitle:Harry...', ...]

    # STRATEGIA 1: Dokładny tytuł + autor (w cudzysłowach)
    search_queries.append(f'"{title}" "{author}"')
    # f-string: wstawiam zmienne do tekstu
    # Jeśli title="Harry Potter" i author="Rowling"
    # To dodaję do listy: '"Harry Potter" "Rowling"'
    # Cudzysłowy mówią Google: "szukaj DOKŁADNIE tej frazy"

    # STRATEGIA 2: Dokładny tytuł + autor (bez cudzysłowów)
    search_queries.append(f'{title} {author}')
    # Dodaję: 'Harry Potter Rowling'
    # Bez cudzysłowów Google szuka bardziej elastycznie

    # STRATEGIA 3: Operatory Google (intitle + inauthor)
    search_queries.append(f'intitle:{title} inauthor:{author}')
    # Dodaję: 'intitle:Harry Potter inauthor:Rowling'
    # intitle: mówi Google "szukaj w tytule"
    # inauthor: mówi Google "szukaj w autorze"

    # STRATEGIA 4: Tylko tytuł w cudzysłowach
    search_queries.append(f'"{title}"')
    # Dodaję: '"Harry Potter"'
    # Czasami autor jest niepoprawny, więc szukam tylko po tytule

    # STRATEGIA 5: Tytuł + ważne słowa z nazwiska autora
    author_words = get_key_words(author)
    # Wyciągam ważne słowa z nazwiska
    # "J.K. Rowling" → ["rowling"]

    if author_words:
        # Jeśli są jakieś ważne słowa
        search_queries.append(f'{title} {" ".join(author_words)}')
        # " ".join(["rowling"]) = "rowling"
        # Dodaję: 'Harry Potter rowling'

    # STRATEGIA 6: Pierwsze 3 ważne słowa z tytułu + autor
    title_words = get_key_words(title)
    # Wyciągam ważne słowa z tytułu
    # "Harry Potter and the Philosopher's Stone" → ["harry", "potter", "philosopher", "stone"]

    if len(title_words) >= 2:
        # Jeśli są przynajmniej 2 ważne słowa
        search_queries.append(f'{" ".join(title_words[:3])} {author}')
        # title_words[:3] bierze pierwsze 3 elementy
        # ["harry", "potter", "philosopher"]
        # " ".join(...) skleja je spacjami
        # Dodaję: 'harry potter philosopher Rowling'

    # STRATEGIA 7: Pierwsze ważne słowo z tytułu + autor (ostatnia deska ratunku)
    if title_words:
        # Jeśli są jakiekolwiek ważne słowa
        search_queries.append(f'{title_words[0]} {author}')
        # title_words[0] to pierwsze słowo
        # Dodaję: 'harry Rowling'

    # Teraz search_queries wygląda tak:
    # [
    #   '"Harry Potter" "Rowling"',
    #   'Harry Potter Rowling',
    #   'intitle:Harry Potter inauthor:Rowling',
    #   '"Harry Potter"',
    #   'Harry Potter rowling',
    #   'harry potter philosopher Rowling',
    #   'harry Rowling'
    # ]

    print(f"\n=== Searching for: {title} by {author} ===")
    # Wypisuję do konsoli (terminala) co właśnie szukam
    # To pomaga w debugowaniu - widzę co się dzieje

    best_match = None
    # Zmienna do przechowania najlepszego znalezionego URL obrazka
    # Na razie None (pusty), będzie np: "https://books.google.com/..."

    best_score = 0
    # Zmienna do przechowania najlepszego wyniku (score)
    # Na razie 0, będzie np: 95

    url = "https://www.googleapis.com/books/v1/volumes"
    # URL do Google Books API
    # To adres gdzie wysyłam zapytania

    for i, query in enumerate(search_queries):
        # Przechodźę przez każdą strategię wyszukiwania
        # enumerate() daje mi index (i) i wartość (query)
        # Iteracja 1: i=0, query='"Harry Potter" "Rowling"'
        # Iteracja 2: i=1, query='Harry Potter Rowling'
        # itd...

        print(f"\nStrategy {i + 1}: {query}")
        # Wypisuję do konsoli którą strategię teraz testuję
        # i+1 bo numerowanie od 1 jest bardziej czytelne dla człowieka

        params = {
            "q": query,
            "maxResults": 15,
            "printType": "books",
            "key": GOOGLE_BOOKS_API_KEY,
            "langRestrict": "",
        }
        # Słownik z parametrami zapytania do API
        # q - zapytanie (query), np: '"Harry Potter" "Rowling"'
        # maxResults - ile maksymalnie wyników chcę (15 książek)
        # printType - jakiego typu publikacje (tylko "books", nie magazyny)
        # key - mój klucz API (przepustka)
        # langRestrict - ograniczenie języka ("" = bez ograniczenia)

        try:
            # Blok try-except łapie błędy
            # Jeśli coś pójdzie nie tak w try, kod przeskoczy do except

            resp = requests.get(url, params=params, timeout=10)
            # Wysyłam zapytanie GET do Google Books API
            # requests.get() łączy URL z params i wysyła
            # Pełny URL wygląda: https://www.googleapis.com/books/v1/volumes?q="Harry Potter"&maxResults=15&...
            # timeout=10 oznacza "jeśli Google nie odpowie w 10 sekund, przerwij"
            # resp to odpowiedź (response) z Google

            if resp.status_code == 200:
                # Sprawdzam kod statusu HTTP
                # 200 = OK (wszystko działa)
                # 404 = Not Found (nie znaleziono)
                # 500 = Server Error (serwer Google się wysypał)

                data = resp.json()
                # Zamieniam odpowiedź JSON (tekst) na pythonowy słownik
                # JSON to format: {"items": [{"volumeInfo": {"title": "Harry Potter", ...}}]}
                # Po .json() mogę używać data["items"][0]["volumeInfo"]["title"]

                items = data.get("items", [])
                # Pobieram listę książek z odpowiedzi
                # .get("items", []) znaczy: "daj mi items, a jeśli nie ma, zwróć pustą listę []"
                # items to lista słowników, każdy słownik = jedna książka

                print(f"  Found {len(items)} results")
                # Wypisuję ile książek Google znalazł
                # np: "  Found 15 results"

                for idx, volume in enumerate(items):
                    # Przechodźę przez każdą znalezioną książkę
                    # idx to index (0, 1, 2, ...)
                    # volume to słownik z danymi książki

                    volume_info = volume.get("volumeInfo", {})
                    # Pobieram sekcję "volumeInfo" ze słownika
                    # volumeInfo zawiera tytuł, autora, obrazki, itp.
                    # .get("volumeInfo", {}) = "daj mi volumeInfo, a jeśli nie ma, zwróć pusty słownik {}"

                    book_title = volume_info.get("title", "")
                    # Pobieram tytuł książki z API
                    # Przykład: book_title = "Harry Potter and the Philosopher's Stone"
                    # Jeśli nie ma tytułu, zwróć pusty string ""

                    book_authors = volume_info.get("authors", [])
                    # Pobieram listę autorów
                    # Przykład: book_authors = ["J.K. Rowling"]
                    # Jeśli nie ma autorów, zwróć pustą listę []

                    image_links = volume_info.get("imageLinks", {})
                    # Pobieram słownik z linkami do obrazków
                    # Przykład: image_links = {"thumbnail": "http://...", "smallThumbnail": "http://..."}
                    # Jeśli nie ma obrazków, zwróć pusty słownik {}

                    current_thumbnail = (
                            image_links.get("thumbnail") or
                            image_links.get("smallThumbnail") or
                            image_links.get("small") or
                            image_links.get("medium")
                    )
                    # Pobieram URL do obrazka, preferując większe rozmiary
                    # Python wykonuje to od góry do dołu i zatrzymuje się na pierwszym True:
                    # 1. Najpierw próbuję "thumbnail" (duży obrazek)
                    # 2. Jeśli nie ma, próbuję "smallThumbnail" (mały obrazek)
                    # 3. Jeśli nie ma, próbuję "small"
                    # 4. Jeśli nie ma, próbuję "medium"
                    # 5. Jeśli nic nie ma, current_thumbnail = None
                    # "or" działa tak: "jeśli lewy jest pusty/None/False, użyj prawego"

                    if not current_thumbnail:
                        # Jeśli current_thumbnail jest None (nie znalazłem żadnego obrazka)
                        continue
                        # Pomiń tę książkę i przejdź do następnej iteracji pętli
                        # Ta książka jest bezużyteczna bo nie ma obrazka

                    is_match, score = check_match(book_title, book_authors, title, author)
                    # Wywołuję funkcję check_match (zdefiniowaną wyżej)
                    # Przekazuję jej:
                    # - book_title: tytuł z API ("Harry Potter and the Philosopher's Stone")
                    # - book_authors: autorzy z API (["J.K. Rowling"])
                    # - title: co wpisał użytkownik ("Harry Potter")
                    # - author: co wpisał użytkownik ("Rowling")
                    # Funkcja zwraca krotkę (tuple):
                    # - is_match: True/False (czy pasuje)
                    # - score: liczba 0-100 (jak dobrze pasuje)
                    # Przykład: is_match=True, score=95

                    author_str = ", ".join(book_authors) if book_authors else "Unknown"
                    # Jeśli są autorzy, sklejam ich przecinkami
                    # ["J.K. Rowling", "John Tiffany"] → "J.K. Rowling, John Tiffany"
                    # Jeśli nie ma autorów, author_str = "Unknown"
                    # To jest tylko do wypisania w konsoli (ładniejszy format)

                    print(
                        f"    [{idx + 1}] '{book_title}' by {author_str} - Score: {score} {'✓ MATCH' if is_match else '✗'}")
                    # Wypisuję szczegóły znalezionej książki do konsoli
                    # idx+1 to numer książki (1, 2, 3...)
                    # Przykład outputu:
                    # "    [1] 'Harry Potter and the Philosopher's Stone' by J.K. Rowling - Score: 95 ✓ MATCH"
                    # "    [2] 'Harry Potter and the Chamber of Secrets' by J.K. Rowling - Score: 60 ✓ MATCH"
                    # {'✓ MATCH' if is_match else '✗'} to operator warunkowy:
                    # - jeśli is_match=True, wypisz "✓ MATCH"
                    # - jeśli is_match=False, wypisz "✗"

                    if is_match and score > best_score:
                        # Sprawdzam 2 warunki:
                        # 1. Czy książka pasuje (is_match=True)
                        # 2. Czy ma lepszy wynik niż dotychczasowy najlepszy (score > best_score)
                        # Przykład: best_score=60, a ta książka ma score=95
                        # Oba warunki True → wchodzę do bloku

                        best_score = score
                        # Aktualizuję najlepszy wynik
                        # best_score zmienia się z 60 na 95

                        best_match = current_thumbnail
                        # Aktualizuję najlepszy obrazek
                        # best_match = "https://books.google.com/books/content?id=abc..."
                        # To jest URL który ostatecznie zapiszę do bazy danych

                        print(f"      → New best match! (score: {score})")
                        # Wypisuję do konsoli że znalazłem lepszą książkę
                        # "      → New best match! (score: 95)"

                    if score >= 90:
                        # Jeśli znalazłem prawie perfekcyjne dopasowanie (90+ punktów)
                        print(f"      → Excellent match found, stopping search")
                        # Wypisuję informację
                        break
                        # Przerywam pętlę for (nie sprawdzam kolejnych książek)
                        # Po co szukać dalej skoro znalazłem prawie idealną?

                if best_score >= 70:
                    # Jeśli najlepszy wynik do tej pory jest >= 70 punktów
                    # To znaczy że znalazłem dobrą książkę
                    print(f"\n✓ Good match found (score: {best_score}), skipping remaining strategies")
                    # Wypisuję informację
                    break
                    # Przerywam pętlę for (nie próbuję kolejnych strategii wyszukiwania)
                    # Po co próbować strategii 4, 5, 6, 7 skoro strategia 1 już dała dobry wynik?

            else:
                # Ten blok wykonuje się jeśli resp.status_code NIE jest 200
                # Czyli coś poszło nie tak z API
                print(f"  API error: {resp.status_code}")
                # Wypisuję kod błędu
                # Przykład: "  API error: 429" (za dużo zapytań)
                # Przykład: "  API error: 500" (serwer Google się wysypał)

        except requests.exceptions.RequestException as e:
            # Ten blok wykonuje się jeśli requests.get() rzucił błąd
            # Przykłady błędów:
            # - ConnectionError (brak internetu)
            # - Timeout (Google nie odpowiedział w 10 sekund)
            # - TooManyRedirects (zbyt wiele przekierowań)
            print(f"  Request error: {e}")
            # Wypisuję błąd do konsoli
            # e to obiekt błędu zawierający szczegóły
            continue
            # Kontynuuj pętlę (spróbuj następnej strategii)
            # Nie przerywaj całego programu tylko dlatego że jedna strategia nie zadziałała

    # FALLBACK - OSTATNIA DESKA RATUNKU
    if not best_match and best_score < 30:
        # Warunek: jeśli NIE znalazłem żadnego dobrego obrazka (best_match=None)
        # ORAZ najlepszy wynik był słaby (best_score < 30)
        # To znaczy że wszystkie strategie zawiodły

        print(f"\n⚠ No good match found (best score: {best_score}), trying fallback...")
        # Wypisuję ostrzeżenie

        fallback_query = f'{title} {author}'
        # Tworzę najprostsze możliwe zapytanie
        # "Harry Potter Rowling"

        params = {
            "q": fallback_query,
            "maxResults": 5,
            "printType": "books",
            "key": GOOGLE_BOOKS_API_KEY
        }
        # Ustawiam parametry zapytania
        # Tym razem tylko 5 wyników (mniej bo to już desperacja)

        try:
            resp = requests.get(url, params=params, timeout=10)
            # Wysyłam zapytanie do Google

            if resp.status_code == 200:
                # Jeśli zapytanie się udało
                data = resp.json()
                # Zamieniam odpowiedź na słownik
                items = data.get("items", [])
                # Pobieram listę książek

                for volume in items:
                    # Przechodźę przez każdą książkę
                    volume_info = volume.get("volumeInfo", {})
                    image_links = volume_info.get("imageLinks", {})
                    fallback_thumbnail = (
                            image_links.get("thumbnail") or
                            image_links.get("smallThumbnail")
                    )
                    # Pobieram URL obrazka (preferuję thumbnail nad smallThumbnail)

                    if fallback_thumbnail:
                        # Jeśli znalazłem jakikolwiek obrazek
                        best_match = fallback_thumbnail
                        # Zapisuję go jako najlepszy (bo innego nie ma)
                        print(f"  Using fallback: {volume_info.get('title', 'Unknown')}")
                        # Wypisuję jakiej książki użyłem
                        break
                        # Przerywam pętlę (biorę pierwszy lepszy obrazek)
        except:
            # Jeśli nawet fallback się nie udał, po prostu nic nie rób
            pass
            # pass to pusta instrukcja - "nic nie rób, idź dalej"

    # FINALIZACJA
    if best_match:
        # Jeśli znalazłem jakikolwiek obrazek (best_match nie jest None)
        thumbnail = best_match.replace("http://", "https://")
        # Zamieniam protokół z http:// na https://
        # Czasami Google zwraca http, a my chcemy bezpieczny https
        # "http://books.google.com/..." → "https://books.google.com/..."
        print(f"\n✓ Final thumbnail found (score: {best_score})")
        # Wypisuję sukces
    else:
        # Jeśli nie znalazłem żadnego obrazka (best_match=None)
        print(f"\n✗ No thumbnail found")
        # Wypisuję porażkę
        # thumbnail pozostaje None (ustawione na początku funkcji)

    print(f"\nFinal: {title} | {author} | {category} | {thumbnail}\n")
    # Wypisuję końcowe dane które zapiszę do bazy
    # Przykład: "Final: Harry Potter | Rowling | Fantasy | https://books.google.com/..."

    add_book(title, author, category, thumbnail)
    # Wywołuję funkcję z pliku add_book.py
    # Ta funkcja:
    # 1. Otwiera połączenie z bazą danych
    # 2. Wykonuje zapytanie SQL INSERT
    # 3. Zapisuje: tytuł, autora, kategorię, thumbnail, datę dodania
    # 4. Zamyka połączenie
    # Teraz książka jest w bazie danych!

    return redirect(url_for("index"))
    # Przekierowuję użytkownika na stronę z listą książek
    # url_for("index") generuje URL "/books"
    # redirect() mówi przeglądarce "idź na /books"
    # Użytkownik zobaczy swoją nową książkę na liście


# ============================================================================
# SZCZEGÓŁY KSIĄŻKI
# ============================================================================

def get_book_by_id(book_id):
    """
    Pobiera szczegóły pojedynczej książki na podstawie ID

    Parametr:
    - book_id: liczba całkowita, np: 5

    Zwraca:
    - słownik z danymi książki lub None jeśli nie znaleziono
    """
    conn = get_connection()
    # Otwieram połączenie z bazą danych
    # conn to "kabel" między kodem a bazą

    cur = conn.cursor()
    # Tworzę kursor (wskaźnik) do wykonywania zapytań SQL

    cur.execute("""
                SELECT b.id,
                       b.title,
                       b.author,
                       b.category,
                       b.status,
                       b.date_added,
                       b.thumbnail,
                       r.date_finished,
                       r.rating,
                       r.review
                FROM books b
                         LEFT JOIN reviews r ON b.id = r.book_id
                WHERE b.id = ?
                """, (book_id,))
    # Wysyłam zapytanie SQL:
    # SELECT - pobieram kolumny
    # FROM books b - z tabeli books (alias 'b')
    # LEFT JOIN reviews r - dołączam tabelę reviews (alias 'r')
    # ON b.id = r.book_id - łączę po ID książki
    # WHERE b.id = ? - TYLKO książka o tym konkretnym ID
    # (book_id,) to tuple z parametrem - ? zostanie zastąpiony przez book_id
    # Przykład: jeśli book_id=5, to WHERE b.id = 5
    # Używamy ? zamiast f-stringa dla bezpieczeństwa (zapobiega SQL injection)

    book = cur.fetchone()
    # Pobieram JEDEN wiersz z wyniku
    # fetchone() zwraca pierwszą książkę lub None jeśli nie znaleziono
    # book to słownik (lub tuple w zależności od konfiguracji):
    # {'id': 5, 'title': 'Harry Potter', 'author': 'Rowling', ...}

    conn.close()
    # Zamykam połączenie z bazą
    # Ważne! Zawsze zamykaj połączenie

    return book
    # Zwracam dane książki do funkcji która mnie wywołała


@app.route("/book/<int:book_id>")
# Dekorator: definiuję stronę dla URL "/book/5", "/book/10", itp.
# <int:book_id> to zmienna w URL - musi być liczbą całkowitą
# Jeśli użytkownik wejdzie na "/book/5", to book_id=5
# Jeśli wejdzie na "/book/abc", dostanie błąd 404 (nie jest int)
def book_detail(book_id):
    """Wyświetla szczegóły jednej książki"""
    # Parametr book_id został automatycznie pobrany z URL przez Flask

    book = get_book_by_id(book_id)
    # Wywołuję funkcję get_book_by_id (zdefiniowaną wyżej)
    # book to teraz słownik z danymi książki
    # Przykład: {'id': 5, 'title': 'Harry Potter', 'thumbnail': 'https://...', ...}

    return render_template("book.html", book=book)
    # Renderuję szablon book.html
    # Przekazuję mu zmienną book
    # W HTML mogę użyć {{ book.title }}, {{ book.author }}, itp.
    # Flask zamieni szablon na gotowy HTML i wyśle do przeglądarki


# ============================================================================
# USUWANIE KSIĄŻKI
# ============================================================================

@app.route("/delete/<int:book_id>", methods=["POST"])
# Dekorator: URL "/delete/5" z metodą POST
# methods=["POST"] znaczy że akceptuję TYLKO POST (nie GET)
# POST to wysyłanie danych (formularz, przycisk)
# GET to pobieranie strony (wpisanie URL w przeglądarkę)
def delete(book_id):
    """Usuwa książkę z bazy danych"""
    # book_id został pobrany z URL

    remove_book(book_id)
    # Wywołuję funkcję z pliku remove_book.py
    # Ta funkcja:
    # 1. Otwiera połączenie z bazą
    # 2. Wykonuje SQL: DELETE FROM reviews WHERE book_id = ?
    # 3. Wykonuje SQL: DELETE FROM books WHERE id = ?
    # 4. Commituje zmiany (zapisuje)
    # 5. Zamyka połączenie
    # Książka została usunięta z bazy!

    return redirect(url_for("index"))
    # Przekierowuję użytkownika na listę książek
    # Użytkownik nie zobaczy już usuniętej książki


# ============================================================================
# OZNACZANIE KSIĄŻKI JAKO PRZECZYTANEJ
# ============================================================================

@app.route("/complete/<int:book_id>", methods=["POST"])
# URL "/complete/5" z metodą POST
def complete(book_id):
    """Oznacza książkę jako ukończoną i dodaje recenzję"""

    rating = int(request.form["rating"])
    # Pobieram ocenę z formularza
    # request.form["rating"] to string, np: "5"
    # int() zamienia string na liczbę całkowitą
    # rating = 5 (liczba, nie string)

    review = request.form["review"]
    # Pobieram tekst recenzji z formularza
    # review = "Świetna książka! Polecam wszystkim."

    complete_book(book_id, rating, review)
    # Wywołuję funkcję z pliku complete_book.py
    # Ta funkcja:
    # 1. Otwiera połączenie z bazą
    # 2. Aktualizuje status książki: UPDATE books SET status='completed' WHERE id=?
    # 3. Dodaje recenzję: INSERT INTO reviews (book_id, rating, review, date_finished) VALUES (?, ?, ?, ?)
    # 4. Commituje zmiany
    # 5. Zamyka połączenie
    # Książka teraz ma status "completed" i recenzję!

    return redirect(url_for("book_detail", book_id=book_id))
    # Przekierowuję użytkownika z powrotem na stronę tej samej książki
    # url_for("book_detail", book_id=book_id) generuje URL "/book/5"
    # Użytkownik zobaczy zaktualizowane dane (status, ocenę, recenzję)


# ============================================================================
# EDYCJA KSIĄŻKI
# ============================================================================

@app.route("/edit/<int:book_id>", methods=["POST"])
# URL "/edit/5" z metodą POST
def edit(book_id):
    """Edytuje podstawowe dane książki (tytuł, autor, kategoria)"""

    title = request.form["title"].strip()
    # Pobieram tytuł z formularza
    # .strip() usuwa białe znaki (spacje, taby) z początku i końca
    # "  Harry Potter  " → "Harry Potter"

    author = request.form["author"].strip()
    # Podobnie jak wyżej

    category = request.form["category"].strip()
    # Podobnie jak wyżej

    # Zamieniam puste stringi na None
    title = title if title else None
    # To jest skrócony if-else (operator warunkowy)
    # Jeśli title jest truthy (niepusty), zostaw title
    # Jeśli title jest falsy (pusty ""), zamień na None
    # Przykład: "" → None, "Harry" → "Harry"

    author = author if author else None
    # Podobnie

    category = category if category else None
    # Podobnie

    edit_book(book_id, title, author, category)
    # Wywołuję funkcję z pliku edit_book.py
    # Ta funkcja:
    # 1. Otwiera połączenie z bazą
    # 2. Jeśli title nie jest None: UPDATE books SET title=? WHERE id=?
    # 3. Jeśli author nie jest None: UPDATE books SET author=? WHERE id=?
    # 4. Jeśli category nie jest None: UPDATE books SET category=? WHERE id=?
    # 5. Commituje zmiany
    # 6. Zamyka połączenie
    # Dane książki zostały zaktualizowane!

    return redirect(url_for("index"))
    # Przekierowuję na listę książek
    # Użytkownik zobaczy zaktualizowane dane


@app.route("/book/<int:book_id>/edit", methods=["POST"])
# Alternatywny URL do edycji: "/book/5/edit"
# To jest drugi endpoint do tej samej funkcjonalności
# (możesz mieć 2 różne URL prowadzące do podobnej logiki)
def edit_book_route(book_id):
    """Edytuje dane książki (wersja alternatywna)"""

    title = request.form.get("title")
    # .get("title") pobiera wartość lub zwraca None jeśli nie ma
    # Bezpieczniejsze niż ["title"] który rzuciłby błąd jeśli pole nie istnieje

    author = request.form.get("author")
    # Podobnie

    category = request.form.get("category")
    # Podobnie

    edit_book(book_id, title, author, category)
    # Wywołuję tę samą funkcję edytującą co wyżej

    return redirect(url_for("book_detail", book_id=book_id))
    # Przekierowuję na stronę szczegółów książki (nie na listę)
    # Użytkownik zostaje na stronie tej samej książki


# ============================================================================
# OBSŁUGA BŁĘDÓW
# ============================================================================

@app.errorhandler(404)
# Dekorator: funkcja obsługująca błąd 404 Not Found
# 404 = strona nie istnieje
# Przykład: użytkownik wejdzie na "/asdasdasd"
@app.errorhandler(500)
# Dekorator: funkcja obsługująca błąd 500 Internal Server Error
# 500 = coś się zepsuło w kodzie (nieobsłużony wyjątek)
def handle_error(e):
    """Obsługuje błędy przekierowując na stronę główną"""
    # Parametr e to obiekt błędu (zawiera szczegóły co poszło nie tak)

    return redirect(url_for("home"))
    # Zamiast pokazywać brzydką stronę błędu
    # Przekierowuję użytkownika na stronę główną
    # Użytkownik zobaczy normalną stronę główną


# ============================================================================
# LOGOWANIE I AUTORYZACJA
# ============================================================================

ADMIN_USERNAME = "admin"
# Stała: nazwa użytkownika administratora
# Przechowywana w zmiennej zamiast w bazie (uproszczona autoryzacja)

ADMIN_PASSWORD_HASH = b"$2b$12$rHOwLdcakTzBDyJXm4NA1On.94bCm4bNLZaUps7sEBsj.KQxtW5xK"


# Stała: zahashowane hasło administratora
# b"..." to bytes (tablica bajtów), nie string
# To jest wynik bcrypt.hashpw("admin123", bcrypt.gensalt())
# Nawet jeśli ktoś zobaczy ten kod, nie odczyta hasła (jednostronne szyfrowanie)


@app.route("/login", methods=["GET", "POST"])
# URL "/login" obsługuje zarówno GET (wyświetlenie formularza) jak i POST (wysłanie formularza)
def login():
    """Obsługuje logowanie administratora"""

    if session.get("is_admin"):
        # Sprawdzam czy użytkownik jest już zalogowany
        # session to słownik z danymi sesji (ciasteczko w przeglądarce)
        # session.get("is_admin") zwraca True jeśli użytkownik jest zalogowany, None jeśli nie

        return redirect(session.get("pre_login_url") or url_for("index"))
        # Jeśli już zalogowany, przekierowuję na stronę z której przyszedł
        # session.get("pre_login_url") to URL zapisany przed logowaniem
        # "or url_for('index')" to fallback - jeśli nie ma pre_login_url, idź na /books

    if request.method == "GET":
        # Jeśli użytkownik OTWIERA stronę logowania (nie wysyła formularza)

        session["pre_login_url"] = request.referrer or url_for("index")
        # Zapisuję w sesji URL strony z której użytkownik przyszedł
        # request.referrer to URL poprzedniej strony
        # Przykład: użytkownik był na /books, kliknął "Login", referrer="/books"
        # Po zalogowaniu przekieruję go z powrotem na /books

        if session["pre_login_url"].endswith("/login"):
            # Jeśli użytkownik przyszedł ze strony logowania (np. odświeżył stronę)
            session["pre_login_url"] = url_for("index")
            # Ustaw domyślny URL na /books
            # Bo inaczej po zalogowaniu wróciłby na /login i byłaby pętla

    if request.method == "POST":
        # Jeśli użytkownik WYSŁAŁ formularz logowania

        username = request.form.get("username")
        # Pobieram nazwę użytkownika z formularza
        # Użytkownik wpisał w pole <input name="username">
        # Przykład: username = "admin"

        password = request.form.get("password")
        # Pobieram hasło z formularza
        # Użytkownik wpisał w pole <input name="password" type="password">
        # Przykład: password = "admin123"

        if username == ADMIN_USERNAME and bcrypt.checkpw(password.encode("utf-8"), ADMIN_PASSWORD_HASH):
            # Sprawdzam 2 warunki (oba muszą być True):
            # 1. username == ADMIN_USERNAME → czy nazwa użytkownika to "admin"
            # 2. bcrypt.checkpw(...) → czy hasło jest poprawne

            # bcrypt.checkpw(password, hash) działa tak:
            # - password.encode("utf-8") zamienia string na bytes
            # - bcrypt hashuje password tym samym algorytmem co podczas tworzenia ADMIN_PASSWORD_HASH
            # - porównuje hash z ADMIN_PASSWORD_HASH
            # - zwraca True jeśli są identyczne, False jeśli nie
            # Nie można odwrócić procesu (nie można odczytać hasła z hasha)

            session.permanent = True
            # Ustawiam sesję jako trwałą
            # Sesja nie wygaśnie po zamknięciu przeglądarki
            # Użytkownik pozostanie zalogowany nawet po restarcie przeglądarki

            session["is_admin"] = True
            # Zapisuję w sesji flagę że użytkownik jest zalogowany
            # Od teraz session.get("is_admin") zwróci True
            # Inne funkcje mogą sprawdzić czy użytkownik ma dostęp

            session["username"] = username
            # Zapisuję nazwę użytkownika w sesji
            # Mogę potem wyświetlić "Zalogowany jako: admin"

            flash("Logged in successfully!", "success")
            # Tworzę jednorazowy komunikat sukcesu
            # flash() zapisuje komunikat w sesji
            # W HTML mogę wyświetlić: {% with messages = get_flashed_messages() %}
            # "success" to kategoria (mogę stylować różne typy komunikatów)

            redirect_url = session.pop("pre_login_url", url_for("index"))
            # Pobieram i USUWAM z sesji URL do przekierowania
            # .pop("key", default) zwraca wartość i usuwa klucz
            # Jeśli nie ma "pre_login_url", użyj url_for("index")
            # redirect_url = "/books" (lub inna strona z której przyszedł)

            return redirect(redirect_url)
            # Przekierowuję użytkownika
            # Użytkownik wraca na stronę z której przyszedł przed logowaniem

        else:
            # Jeśli nazwa użytkownika lub hasło są niepoprawne
            return render_template("login.html", error="Invalid username or password")
            # Renderuję stronę logowania ponownie
            # Przekazuję zmienną error
            # W HTML mogę wyświetlić: {{ error }} → "Invalid username or password"
            # Użytkownik zobaczy błąd i może spróbować ponownie

    return render_template("login.html")
    # Jeśli request.method == "GET" i użytkownik nie jest zalogowany
    # Renderuję czysty formularz logowania
    # Użytkownik zobaczy pola: username, password, przycisk Submit


# ============================================================================
# WYLOGOWANIE
# ============================================================================

@app.route("/logout")
# URL "/logout" - gdy użytkownik kliknie "Wyloguj"
def logout():
    """Wylogowuje użytkownika"""

    session.clear()
    # Czyszczę CAŁĄ sesję (usuwam wszystkie dane)
    # Usuwa: is_admin, username, i wszystko inne
    # session = {} (pusty słownik)
    # Ciasteczko w przeglądarce staje się bezwartościowe
    # Użytkownik nie jest już zalogowany

    flash("Logged out successfully", "info")
    # Tworzę komunikat informacyjny
    # "info" to kategoria (może być inna niż "success")
    # W HTML mogę to stylować na niebiesko zamiast zielono

    referrer = request.referrer
    # Pobieram URL strony z której użytkownik przyszedł
    # Jeśli był na /books i kliknął "Wyloguj", referrer="/books"
    # Jeśli wpisał /logout bezpośrednio w przeglądarkę, referrer=None

    if referrer and is_safe_url(referrer):
        # Sprawdzam 2 warunki:
        # 1. referrer istnieje (nie jest None)
        # 2. referrer jest bezpieczny (nie prowadzi do http://evil.com)
        # is_safe_url() to funkcja zdefiniowana na początku pliku

        return redirect(referrer)
        # Przekierowuję użytkownika z powrotem na stronę z której przyszedł
        # Użytkownik zostaje na tej samej stronie (ale jest wylogowany)

    return redirect(url_for("home"))
    # Jeśli nie ma referrera lub jest niebezpieczny
    # Przekierowuję na stronę główną
    # Bezpieczny fallback


# ============================================================================
# INICJALIZACJA BAZY DANYCH
# ============================================================================

@app.route("/init_books_db", methods=["POST"])
# URL "/init_books_db" z metodą POST
# To jest endpoint administracyjny (tylko dla zalogowanych adminów)
def init_books_db():
    """Tworzy tabele w bazie danych (books, reviews)"""

    if not session.get("is_admin"):
        # Sprawdzam czy użytkownik jest zalogowany jako admin
        # session.get("is_admin") zwraca True jeśli zalogowany, None jeśli nie
        # not None = True → wchodzę do bloku
        # not True = False → pomijam blok

        flash("Unauthorized", "danger")
        # Tworzę komunikat błędu
        # "danger" to kategoria (czerwony kolor w HTML)
        # "Unauthorized" = "Nieautoryzowany" (brak uprawnień)

        return redirect(url_for("index"))
        # Przekierowuję niezalogowanego użytkownika na listę książek
        # Nie może tworzyć bazy danych bez logowania

    created = initialize_database()
    # Wywołuję funkcję z pliku db_init.py
    # Ta funkcja:
    # 1. Sprawdza czy books.db istnieje
    # 2. Jeśli nie istnieje, tworzy plik
    # 3. Tworzy tabelę books (id, title, author, category, status, date_added, thumbnail)
    # 4. Tworzy tabelę reviews (id, book_id, rating, review, date_finished)
    # 5. Zwraca True jeśli stworzyła, False jeśli już istniała

    if created:
        # Jeśli baza została właśnie stworzona (created=True)
        flash("Books database created successfully!", "success")
        # Komunikat sukcesu (zielony)
    else:
        # Jeśli baza już istniała (created=False)
        flash("Database already exists!", "info")
        # Komunikat informacyjny (niebieski)
        # Nie jest to błąd, po prostu baza już była

    return redirect(url_for("index"))
    # Przekierowuję na listę książek
    # Użytkownik zobaczy komunikat flash na górze strony


# ============================================================================
# WYSZUKIWANIE KSIĄŻEK (API DLA AUTOUZUPEŁNIANIA)
# ============================================================================

@app.route("/search")
# URL "/search?q=harry" - parametr w URL (query string)
# To jest endpoint API (zwraca JSON, nie HTML)
# Używany przez JavaScript do autouzupełniania w formularzu
def search_books():
    """Wyszukuje książki w Google Books API i zwraca wyniki jako JSON"""

    query = request.args.get("q", "")
    # Pobieram parametr 'q' z URL
    # request.args to słownik z parametrami URL
    # URL: /search?q=harry&max=10
    # request.args["q"] = "harry"
    # request.args["max"] = "10"
    # .get("q", "") = "jeśli nie ma 'q', zwróć pusty string"

    if not query:
        # Jeśli query jest pusty (użytkownik nic nie wpisał)
        return {"error": "Missing query"}, 400
        # Zwracam słownik z błędem i kod HTTP 400 (Bad Request)
        # 400 = złe zapytanie (brakujące dane)
        # JavaScript który to wywołał zobaczy błąd

    url = "https://www.googleapis.com/books/v1/volumes"
    # URL do Google Books API

    params = {
        "q": query,
        "maxResults": 8,
        "printType": "books",
        "key": GOOGLE_BOOKS_API_KEY
    }
    # Parametry zapytania do API:
    # q - zapytanie użytkownika (np: "harry")
    # maxResults - max 8 książek (dla autouzupełniania wystarczy)
    # printType - tylko książki (nie magazyny, nie gazety)
    # key - mój klucz API

    response = requests.get(url, params=params)
    # Wysyłam zapytanie GET do Google Books
    # requests automatycznie skleja URL z params:
    # https://www.googleapis.com/books/v1/volumes?q=harry&maxResults=8&printType=books&key=...

    if response.status_code != 200:
        # Jeśli kod statusu NIE jest 200 (coś poszło nie tak)
        return {"error": "Google API request failed"}, 500
        # Zwracam błąd z kodem 500 (Internal Server Error)
        # 500 = problem po naszej stronie (lub Google'a)

    data = response.json()
    # Zamieniam odpowiedź JSON na pythonowy słownik
    # data = {"items": [{"volumeInfo": {...}}, {"volumeInfo": {...}}]}

    return jsonify({
        "results": [
            {
                "title": item["volumeInfo"].get("title", ""),
                "authors": item["volumeInfo"].get("authors", []),
                "thumbnail": item["volumeInfo"].get("imageLinks", {}).get("thumbnail", ""),
                "categories": item["volumeInfo"].get("categories", [])
            }
            for item in data.get("items", [])
        ]
    })
    # Buduję odpowiedź JSON:
    # 1. Pobieram listę książek: data.get("items", [])
    # 2. Dla każdej książki ('item') tworzę słownik z:
    #    - title: tytuł książki
    #    - authors: lista autorów
    #    - thumbnail: URL obrazka
    #    - categories: lista kategorii
    # 3. Pakuję to w słownik {"results": [...]}
    # 4. jsonify() zamienia to na JSON i ustawia header Content-Type: application/json
    # 
    # Przykład wyniku:
    # {
    #   "results": [
    #     {
    #       "title": "Harry Potter and the Philosopher's Stone",
    #       "authors": ["J.K. Rowling"],
    #       "thumbnail": "http://books.google.com/...",
    #       "categories": ["Fiction", "Fantasy"]
    #     },
    #     {
    #       "title": "Harry Potter and the Chamber of Secrets",
    #       "authors": ["J.K. Rowling"],
    #       "thumbnail": "http://books.google.com/...",
    #       "categories": ["Fiction"]
    #     }
    #   ]
    # }
    #
    # JavaScript w przeglądarce odbiera ten JSON i wyświetla podpowiedzi


# ============================================================================
# URUCHOMIENIE APLIKACJI
# ============================================================================

if __name__ == "__main__":
    # Ten blok wykonuje się TYLKO gdy uruchamiasz plik bezpośrednio
    # python app.py → wykonuje się
    # from app import something → NIE wykonuje się
    # 
    # __name__ to specjalna zmienna:
    # - Jeśli uruchamiasz plik: __name__ = "__main__"
    # - Jeśli importujesz plik: __name__ = "app"

    app.run(debug=False)
    # Uruchamiam serwer Flask
    # app.run() startuje serwer HTTP na localhost:5000
    # 
    # debug=False oznacza tryb produkcyjny:
    # - NIE pokazuje szczegółów błędów użytkownikowi (bezpieczeństwo)
    # - NIE automatycznie restartuje przy zmianach w kodzie
    # - NIE włącza debuggera interaktywnego
    # 
    # W trakcie rozwoju lepiej użyć debug=True:
    # app.run(debug=True)
    # - Pokazuje szczegółowe błędy (łatwiej znaleźć problemy)
    # - Auto-restart przy zapisie pliku (nie musisz ręcznie restartować)
    # - Możesz wykonywać kod Python w przeglądarce przy błędzie
    # 
    # Po uruchomieniu zobaczysz w terminalu:
    # * Running on http://127.0.0.1:5000
    # * Running on http://192.168.1.100:5000
    # 
    # Teraz możesz otworzyć przeglądarkę i wejść na:
    # http://localhost:5000 → strona główna (home.html)
    # http://localhost:5000/books → lista książek (index.html)
    # http://localhost:5000/login → formularz logowania
    # 
    # Serwer działa dopóki nie zamkniesz programu (Ctrl+C)

# ============================================================================
# PODSUMOWANIE JAK TO WSZYSTKO DZIAŁA
# ============================================================================

# ARCHITEKTURA APLIKACJI:
# 
# 1. UŻYTKOWNIK (Przeglądarka)
#    ↓ wysyła żądanie HTTP (GET /books)
# 
# 2. FLASK (app.py)
#    ↓ @app.route("/books") → wywołuje funkcję index()
#    ↓ index() wywołuje get_books()
# 
# 3. BAZA DANYCH (books.db)
#    ↓ get_books() wykonuje SELECT ... i pobiera książki
#    ↓ zwraca listę książek do index()
# 
# 4. JINJA (szablon index.html)
#    ↓ render_template("index.html", books=books)
#    ↓ {{ book.title }} zamieniane na prawdziwe dane
#    ↓ {% for book in books %} tworzy pętlę
# 
# 5. FLASK
#    ↓ wysyła gotowy HTML do przeglądarki
# 
# 6. UŻYTKOWNIK
#    ↓ widzi stronę z listą książek
# 
# 
# FLOW DODAWANIA KSIĄŻKI:
# 
# 1. Użytkownik wypełnia formularz (tytuł, autor, kategoria)
# 2. Przycisk Submit wysyła POST /add
# 3. Flask wywołuje funkcję add()
# 4. add() normalizuje tytuł i autora
# 5. add() próbuje 7 różnych strategii wyszukiwania w Google Books API
# 6. Dla każdej znalezionej książki oblicza score (0-100 punktów)
# 7. Wybiera książkę z najwyższym score
# 8. Jeśli znalazł obrazek, zapisuje URL
# 9. Wywołuje add_book(title, author, category, thumbnail)
# 10. add_book() zapisuje dane do bazy SQL: INSERT INTO books ...
# 11. Flask przekierowuje użytkownika na /books
# 12. Użytkownik widzi swoją nową książkę na liście
# 
# 
# SESJE I LOGOWANIE:
# 
# - Sesja to ciasteczko (cookie) w przeglądarce
# - Flask szyfruje dane sesji używając app.secret_key
# - Po zalogowaniu: session["is_admin"] = True
# - Przy każdym żądaniu Flask odczytuje ciasteczko i sprawdza sesję
# - Funkcje mogą sprawdzić: if session.get("is_admin")
# - Po wylogowaniu: session.clear() usuwa wszystkie dane
# 
# 
# BEZPIECZEŃSTWO:
# 
# - Hasła hashowane bcryptem (nie można odczytać)
# - SQL używa parametrów (?, ?) zamiast f-stringów (zapobiega SQL injection)
# - URL sprawdzane przez is_safe_url() (zapobiega open redirect)
# - Sesje szyfrowane app.secret_key (nie można podrobić)
# - Admin endpoints sprawdzają session.get("is_admin")
# - HTTPS dla obrazków (bezpieczny protokół)
# 
# 
# CO SIĘ DZIEJE W PAMIĘCI:
# 
# PRZED: 
# title = None, author = None, books = []
# 
# UŻYTKOWNIK WYPEŁNIA FORMULARZ:
# (dane są w przeglądarce, nie na serwerze)
# 
# UŻYTKOWNIK KLIKA SUBMIT:
# POST /add
# title = "Harry Potter"
# author = "Rowling"
# 
# NORMALIZACJA:
# title = "Harry Potter" (bez zmian, już z wielkiej)
# author = "Rowling"
# 
# WYSZUKIWANIE:
# query = '"Harry Potter" "Rowling"'
# resp = requests.get(...) → odpowiedź z Google
# data = {"items": [...]} → lista 15 książek
# 
# SCORING:
# książka 1: score = 95 (świetne dopasowanie!)
# książka 2: score = 60 (ok dopasowanie)
# best_match = "https://books.google.com/..."
# best_score = 95
# 
# ZAPIS DO BAZY:
# thumbnail = "https://books.google.com/..."
# SQL: INSERT INTO books (title, author, category, thumbnail, ...) VALUES (?, ?, ?, ?, ...)
# 
# PRZEKIEROWANIE:
# return redirect("/books")
# 
# POBRANIE Z BAZY:
# books = [{'id': 1, 'title': 'Harry Potter', 'thumbnail': 'https://...', ...}, ...]
# 
# RENDEROWANIE:
# HTML: <img src="https://books.google.com/...">
# 
# UŻYTKOWNIK WIDZI:
# Książkę z obrazkiem okładki!