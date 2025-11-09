from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from edit_book import edit_book, edit_review_date
import os
import bcrypt
from add_book import add_book
from remove_book import remove_book
from complete_book import complete_book
from datetime import datetime
# POPRAWIONY IMPORT: Bierzemy klienta i funkcje pomocnicze
from db_init import get_client, initialize_database, rs_to_dicts, row_to_dict
from urllib.parse import urlparse, urljoin, quote
from dotenv import load_dotenv
import requests

load_dotenv()
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
app = Flask(__name__)
app.secret_key = "9e6663d956531a9dbdad7a8e5196119e6d6b8cf8a6154be26834db2789038a8d"

# Pobieramy klienta RAZ przy starcie
client = get_client()


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_books():
    if not client: return []
    rs = client.execute("""
                SELECT b.id, b.title, b.author, b.category, b.status,
                       r.rating, r.review, b.thumbnail
                FROM books b
                LEFT JOIN reviews r ON b.id = r.book_id
                ORDER BY b.date_added DESC
                """)
    # TERAZ TO ZADZIAŁA
    return rs_to_dicts(rs)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/books")
def index():
    books = get_books()
    return render_template("index.html", books=books, db_exists=(client is not None))


@app.route("/add", methods=["POST"])
def add():
    # ... (Wklej tutaj swoją pełną logikę Google Books API z poprzedniego pliku app.py) ...
    # ... (Ja wklejam tylko logikę bazy danych)
    title = request.form["title"].title()
    author = request.form["author"].title()
    category = request.form["category"].title()
    thumbnail = None  # Twoja logika API powinna to znaleźć

    # ... (Reszta logiki API) ...

    try:
        add_book(title, author, category, thumbnail)
        flash(f"Book '{title}' added successfully!", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("index"))


def get_book_by_id(book_id):
    if not client: return None
    rs = client.execute("""
                SELECT b.id, b.title, b.author, b.category, b.status, b.date_added, b.thumbnail,
                       r.date_finished, r.rating, r.review
                FROM books b
                LEFT JOIN reviews r ON b.id = r.book_id
                WHERE b.id = ?
                """, (book_id,))
    # TERAZ TO ZADZIAŁA
    return row_to_dict(rs)


@app.route("/book/<int:book_id>")
def book_detail(book_id):
    book = get_book_by_id(book_id)
    if not book:
        flash("Book not found", "danger")
        return redirect(url_for("index"))
    return render_template("book.html", book=book)


@app.route("/delete/<int:book_id>", methods=["POST"])
def delete(book_id):
    remove_book(book_id)
    return redirect(url_for("index"))


@app.route("/complete/<int:book_id>", methods=["POST"])
def complete(book_id):
    complete_book(book_id, int(request.form["rating"]), request.form["review"])
    return redirect(url_for("book_detail", book_id=book_id))


@app.route("/edit/<int:book_id>", methods=["POST"])
def edit(book_id):
    edit_book(book_id, request.form.get("title"), request.form.get("author"), request.form.get("category"))
    return redirect(url_for("index"))


@app.route("/book/<int:book_id>/edit", methods=["POST"])
def edit_book_route(book_id):
    edit_book(book_id, request.form.get("title"), request.form.get("author"), request.form.get("category"))
    edit_review_date(book_id, request.form.get("date_finished"))
    flash("Book updated", "success")
    return redirect(url_for("book_detail", book_id=book_id))


@app.template_filter('datetimeformat')
def datetimeformat(value):
    try:
        return datetime.strptime(value, "%d-%m-%Y").strftime("%Y-%m-%d")
    except:
        return value or ""


# --- LOGIN / ADMIN (Reszta bez zmian) ---
@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(e):
    return redirect(url_for("home"))


ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = b"$2b$12$rHOwLdcakTzBDyJXm4NA1On.94bCm4bNLZaUps7sEBsj.KQxtW5xK"


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("is_admin"): return redirect(session.get("pre_login_url") or url_for("index"))
    if request.method == "GET":
        session["pre_login_url"] = request.referrer or url_for("index")
        if session["pre_login_url"].endswith("/login"): session["pre_login_url"] = url_for("index")
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USERNAME and bcrypt.checkpw(
                request.form.get("password").encode("utf-8"), ADMIN_PASSWORD_HASH):
            session.permanent = True
            session["is_admin"] = True
            flash("Logged in!", "success")
            return redirect(session.pop("pre_login_url", url_for("index")))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("home"))


@app.route("/init_books_db", methods=["POST"])
def init_books_db():
    if not session.get("is_admin"): return redirect(url_for("index"))
    if initialize_database():
        flash("Database initialized!", "success")
    else:
        flash("Init failed.", "info")
    return redirect(url_for("index"))


@app.route("/search")
def search_books():
    # ... (Twoja logika API, bez zmian) ...
    query = request.args.get("q", "")
    if not query: return {"error": "Missing query"}, 400
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": query, "maxResults": 8, "printType": "books", "key": GOOGLE_BOOKS_API_KEY}
    resp = requests.get(url, params=params)
    if resp.status_code != 200: return {"error": "API failed"}, 500
    data = resp.json()
    return jsonify({"results": [
        {"title": i["volumeInfo"].get("title", ""), "authors": i["volumeInfo"].get("authors", []),
         "thumbnail": i["volumeInfo"].get("imageLinks", {}).get("thumbnail", "")} for i in data.get("items", [])]})


if __name__ == "__main__":
    app.run(debug=True)