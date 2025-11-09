from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from edit_book import edit_book, edit_review_date
import os
import bcrypt
# usunięto 'import sqlite3'
from add_book import add_book
from remove_book import remove_book
# usunięto 'from edit_book import edit_book' (był duplikat)
from complete_book import complete_book
from datetime import datetime
# Zmienione importy z db_init
from db_init import client, initialize_database, rows_to_dicts, row_to_dict
from urllib.parse import urlparse, urljoin, quote
from dotenv import load_dotenv
import requests

load_dotenv()
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
app = Flask(__name__)
app.secret_key = "9e6663d956531a9dbdad7a8e5196119e6d6b8cf8a6154be26834db2789038a8d"


def is_safe_url(target):
    # ... (reszta kodu bez zmian)
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    # Zauważ dodany apostrof po https
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_books():
    # usunięto 'if not os.path.exists("books.db"):' - to już nie ma sensu
    if not client:
        return []  # Zwróć pustą listę, jeśli baza nie jest połączona

    # Zmieniona logika pobierania danych
    rs = client.execute("""
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
    books = rows_to_dicts(rs)  # Konwersja na słowniki
    return books


@app.route("/")
def home():
    # ... (bez zmian)
    return render_template("home.html")


@app.route("/books")
def index():
    # usunięto 'db_exists = os.path.exists("books.db")'
    books = get_books()
    # Przekazujemy 'client', żeby sprawdzić, czy baza w ogóle istnieje (jest połączona)
    return render_template("index.html", books=books, db_exists=(client is not None))


@app.route("/add", methods=["POST"])
def add():
    # ... (cała logika Google Books API bez zmian) ...
    title = request.form["title"].title()
    author = request.form["author"].title()
    category = request.form["category"].title()
    thumbnail = None

    def normalize_text(text):
        import re
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        return text

    def get_key_words(text):
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'by'}
        words = normalize_text(text).split()
        return [w for w in words if w not in stop_words and len(w) > 2]

    def check_match(book_title, book_authors, search_title, search_author):
        norm_book_title = normalize_text(book_title)
        norm_search_title = normalize_text(search_title)
        search_title_words = set(get_key_words(search_title))
        book_title_words = set(get_key_words(book_title))
        if not search_title_words:
            title_match = 0
        else:
            common_words = search_title_words.intersection(book_title_words)
            title_match = len(common_words) / len(search_title_words)
        author_match = False
        if book_authors:
            norm_search_author = normalize_text(search_author)
            search_author_words = set(get_key_words(search_author))
            for author in book_authors:
                norm_book_author = normalize_text(author)
                if norm_search_author == norm_book_author:
                    author_match = True
                    break
                if search_author_words:
                    book_author_words = set(get_key_words(author))
                    common = search_author_words.intersection(book_author_words)
                    if len(common) >= 1:
                        author_match = True
                        break
        score = 0
        if title_match >= 0.5:
            score += int(title_match * 60)
        if author_match:
            score += 40
        return score > 40, score

    search_queries = []
    search_queries.append(f'"{title}" "{author}"')
    search_queries.append(f'{title} {author}')
    search_queries.append(f'intitle:{title} inauthor:{author}')
    search_queries.append(f'"{title}"')
    author_words = get_key_words(author)
    if author_words:
        search_queries.append(f'{title} {" ".join(author_words)}')
    title_words = get_key_words(title)
    if len(title_words) >= 2:
        search_queries.append(f'{" ".join(title_words[:3])} {author}')
    if title_words:
        search_queries.append(f'{title_words[0]} {author}')

    print(f"\n=== Searching for: {title} by {author} ===")
    best_match = None
    best_score = 0
    url = "https://www.googleapis.com/books/v1/volumes"

    for i, query in enumerate(search_queries):
        print(f"\nStrategy {i + 1}: {query}")
        params = {
            "q": query,
            "maxResults": 15,
            "printType": "books",
            "key": GOOGLE_BOOKS_API_KEY,
            "langRestrict": "",
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                print(f"  Found {len(items)} results")
                for idx, volume in enumerate(items):
                    volume_info = volume.get("volumeInfo", {})
                    book_title = volume_info.get("title", "")
                    book_authors = volume_info.get("authors", [])
                    image_links = volume_info.get("imageLinks", {})
                    current_thumbnail = (
                            image_links.get("thumbnail") or
                            image_links.get("smallThumbnail") or
                            image_links.get("small") or
                            image_links.get("medium")
                    )
                    if not current_thumbnail:
                        continue
                    is_match, score = check_match(book_title, book_authors, title, author)
                    author_str = ", ".join(book_authors) if book_authors else "Unknown"
                    print(
                        f"    [{idx + 1}] '{book_title}' by {author_str} - Score: {score} {'✓ MATCH' if is_match else '✗'}")
                    if is_match and score > best_score:
                        best_score = score
                        best_match = current_thumbnail
                        print(f"      → New best match! (score: {score})")
                    if score >= 90:
                        print(f"      → Excellent match found, stopping search")
                        break
                if best_score >= 70:
                    print(f"\n✓ Good match found (score: {best_score}), skipping remaining strategies")
                    break
            else:
                print(f"  API error: {resp.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  Request error: {e}")
            continue

    if not best_match and best_score < 30:
        print(f"\n⚠ No good match found (best score: {best_score}), trying fallback...")
        fallback_query = f'{title} {author}'
        params = {
            "q": fallback_query,
            "maxResults": 5,
            "printType": "books",
            "key": GOOGLE_BOOKS_API_KEY
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                for volume in items:
                    volume_info = volume.get("volumeInfo", {})
                    image_links = volume_info.get("imageLinks", {})
                    fallback_thumbnail = (
                            image_links.get("thumbnail") or
                            image_links.get("smallThumbnail")
                    )
                    if fallback_thumbnail:
                        best_match = fallback_thumbnail
                        print(f"  Using fallback: {volume_info.get('title', 'Unknown')}")
                        break
        except:
            pass

    if best_match:
        thumbnail = best_match.replace("http://", "https://")
        print(f"\n✓ Final thumbnail found (score: {best_score})")
    else:
        print(f"\n✗ No thumbnail found")
    print(f"\nFinal: {title} | {author} | {category} | {thumbnail}\n")
    # ... (koniec logiki Google Books API) ...

    try:
        add_book(title, author, category, thumbnail)
        flash(f"Book '{title}' added successfully!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("index"))


def get_book_by_id(book_id):
    if not client:
        return None

    # Zmieniona logika pobierania
    rs = client.execute("""
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
    book = row_to_dict(rs)  # Używamy nowej funkcji pomocniczej
    return book


@app.route("/book/<int:book_id>")
def book_detail(book_id):
    # ... (bez zmian)
    book = get_book_by_id(book_id)
    return render_template("book.html", book=book)


@app.route("/delete/<int:book_id>", methods=["POST"])
def delete(book_id):
    # ... (bez zmian)
    remove_book(book_id)
    return redirect(url_for("index"))


@app.route("/complete/<int:book_id>", methods=["POST"])
def complete(book_id):
    # ... (bez zmian)
    rating = int(request.form["rating"])
    review = request.form["review"]
    complete_book(book_id, rating, review)
    return redirect(url_for("book_detail", book_id=book_id))


@app.route("/edit/<int:book_id>", methods=["POST"])
def edit(book_id):
    # ... (bez zmian)
    title = request.form["title"].strip() or None
    author = request.form["author"].strip() or None
    category = request.form["category"].strip() or None
    date_finished = request.form.get("date_finished")
    if date_finished:
        date_finished = date_finished.strip() or None
    title = title if title else None
    author = author if author else None
    category = category if category else None
    date_finished = date_finished if date_finished else None
    edit_book(book_id, title, author, category, date_finished)
    return redirect(url_for("index"))


@app.route("/book/<int:book_id>/edit", methods=["POST"])
def edit_book_route(book_id):
    # ... (bez zmian)
    title = request.form.get("title") or None
    author = request.form.get("author") or None
    category = request.form.get("category") or None
    date_finished = request.form.get("date_finished") or None
    edit_book(book_id, title, author, category)
    edit_review_date(book_id, date_finished)
    flash(f"Book has been successfully updated!", "success")
    return redirect(url_for("book_detail", book_id=book_id))


@app.template_filter('datetimeformat')
def datetimeformat(value):
    # ... (bez zmian)
    try:
        return datetime.strptime(value, "%d-%m-%Y").strftime("%Y-%m-%d")
    except:
        return ""


@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(e):
    # ... (bez zmian)
    return redirect(url_for("home"))


ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = b"$2b$12$rHOwLdcakTzBDyJXm4NA1On.94bCm4bNLZaUps7sEBsj.KQxtW5xK"


@app.route("/login", methods=["GET", "POST"])
def login():
    # ... (bez zmian)
    if session.get("is_admin"):
        return redirect(session.get("pre_login_url") or url_for("index"))
    if request.method == "GET":
        session["pre_login_url"] = request.referrer or url_for("index")
        if session["pre_login_url"].endswith("/login"):
            session["pre_login_url"] = url_for("index")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and bcrypt.checkpw(password.encode("utf-8"), ADMIN_PASSWORD_HASH):
            session.permanent = True
            session["is_admin"] = True
            session["username"] = username
            flash("Logged in successfully!", "success")
            redirect_url = session.pop("pre_login_url", url_for("index"))
            return redirect(redirect_url)
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")


@app.route("/logout")
def logout():
    # ... (bez zmian)
    session.clear()
    flash("Logged out successfully", "info")
    referrer = request.referrer
    if referrer and is_safe_url(referrer):
        return redirect(referrer)
    return redirect(url_for("home"))


@app.route("/init_books_db", methods=["POST"])
def init_books_db():
    # ... (logika bez zmian, ale funkcja initialize_database() działa teraz na Turso)
    if not session.get("is_admin"):
        flash("Unauthorized", "danger")
        return redirect(url_for("index"))
    created = initialize_database()
    if created:
        flash("Books database created successfully!", "success")
    else:
        flash("Database already exists or failed to create!", "info")
    return redirect(url_for("index"))


@app.route("/search")
def search_books():
    # ... (bez zmian)
    query = request.args.get("q", "")
    if not query:
        return {"error": "Missing query"}, 400
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "maxResults": 8,
        "printType": "books",
        "key": GOOGLE_BOOKS_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return {"error": "Google API request failed"}, 500
    data = response.json()
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


if __name__ == "__main__":
    app.run(debug=False)