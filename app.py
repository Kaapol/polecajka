from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from edit_book import edit_book, edit_review_date
import os
import bcrypt
from add_book import add_book
from remove_book import remove_book
from complete_book import complete_book
from datetime import datetime
from db_init import get_client, initialize_database, rs_to_dicts, row_to_dict, is_database_initialized
from urllib.parse import urlparse, urljoin
from dotenv import load_dotenv
import requests
import time

load_dotenv()
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
app = Flask(__name__)
app.secret_key = "9e6663d956531a9dbdad7a8e5196119e6d6b8cf8a6154be26834db2789038a8d"

client = get_client()

# Admin credentials (zachowane z oryginalnego kodu)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = b"$2b$12$rHOwLdcakTzBDyJXm4NA1On.94bCm4bNLZaUps7sEBsj.KQxtW5xK"


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_books():
    """Zwraca książki dla zalogowanego użytkownika (lub wszystkie dla admina)"""
    if not client:
        return []

    # Admin widzi wszystkie książki
    if session.get('is_admin'):
        try:
            rs = client.execute("""
                SELECT b.id, b.title, b.author, b.category, b.status,
                       r.rating, r.review, b.thumbnail
                FROM books b
                LEFT JOIN reviews r ON b.id = r.book_id
                ORDER BY b.date_added DESC
            """)
            return rs_to_dicts(rs)
        except Exception as e:
            print(f"Database error in get_books: {e}")
            return []

    # Zwykły użytkownik widzi tylko swoje
    user_id = session.get('user_id')
    if not user_id:
        return []

    try:
        rs = client.execute("""
            SELECT b.id, b.title, b.author, b.category, b.status,
                   r.rating, r.review, b.thumbnail
            FROM books b
            LEFT JOIN reviews r ON b.id = r.book_id
            WHERE b.user_id = ?
            ORDER BY b.date_added DESC
        """, (user_id,))
        return rs_to_dicts(rs)
    except Exception as e:
        print(f"Database error in get_books: {e}")
        return []


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/books")
def index():
    if not session.get('user_id') and not session.get('is_admin'):
        flash("Please login first", "warning")
        return redirect(url_for('login'))

    books = get_books()
    db_exists = is_database_initialized(client)
    return render_template("index.html", books=books, db_exists=db_exists)


@app.route("/add", methods=["POST"])
def add():
    if not session.get('user_id') and not session.get('is_admin'):
        flash("Please login first", "danger")
        return redirect(url_for('login'))

    # Admin dodaje jako user_id = 0 (specjalny ID)
    user_id = session.get('user_id', 0)

    title = request.form["title"].title()
    author = request.form["author"].title()
    category = request.form["category"].title()
    thumbnail = request.form.get("thumbnail")

    # Tutaj możesz dodać logikę szukania thumbnail (skopiuj z poprzedniej wersji)

    try:
        add_book_with_user(user_id, title, author, category, thumbnail)
        flash(f"Book '{title}' added successfully!", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("index"))


def add_book_with_user(user_id, title, author, category, thumbnail=None):
    """Dodaje książkę dla konkretnego użytkownika"""
    if not client:
        raise Exception("No DB client")

    # Sprawdź duplikat DLA TEGO UŻYTKOWNIKA
    rs = client.execute(
        "SELECT id FROM books WHERE LOWER(title) = LOWER(?) AND user_id = ?",
        (title, user_id)
    )
    if rs.rows:
        raise ValueError(f"Book '{title}' already exists in your library!")

    date_added = datetime.now().strftime("%d-%m-%Y")
    client.execute("""
        INSERT INTO books (user_id, title, author, category, date_added, thumbnail)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, title, author, category, date_added, thumbnail))
    print(f"✅ Added: {title} for user {user_id}")


def get_book_by_id(book_id):
    """Zwraca książkę TYLKO jeśli należy do zalogowanego użytkownika (lub admin)"""
    if not client:
        return None

    # Admin widzi wszystko
    if session.get('is_admin'):
        try:
            rs = client.execute("""
                SELECT b.id, b.title, b.author, b.category, b.status, b.date_added, b.thumbnail,
                       r.date_finished, r.rating, r.review
                FROM books b
                LEFT JOIN reviews r ON b.id = r.book_id
                WHERE b.id = ?
            """, (book_id,))
            return row_to_dict(rs)
        except Exception as e:
            print(f"Database error: {e}")
            return None

    # Zwykły użytkownik
    user_id = session.get('user_id')
    if not user_id:
        return None

    try:
        rs = client.execute("""
            SELECT b.id, b.title, b.author, b.category, b.status, b.date_added, b.thumbnail,
                   r.date_finished, r.rating, r.review
            FROM books b
            LEFT JOIN reviews r ON b.id = r.book_id
            WHERE b.id = ? AND b.user_id = ?
        """, (book_id, user_id))
        return row_to_dict(rs)
    except Exception as e:
        print(f"Database error: {e}")
        return None


@app.route("/book/<int:book_id>")
def book_detail(book_id):
    if not session.get('user_id') and not session.get('is_admin'):
        flash("Please login first", "warning")
        return redirect(url_for('login'))

    book = get_book_by_id(book_id)
    if not book:
        flash("Book not found", "danger")
        return redirect(url_for("index"))
    return render_template("book.html", book=book)


@app.route("/delete/<int:book_id>", methods=["POST"])
def delete(book_id):
    if not session.get('user_id') and not session.get('is_admin'):
        return redirect(url_for('login'))

    book = get_book_by_id(book_id)
    if book:
        remove_book(book_id)

    return redirect(url_for("index"))


@app.route("/complete/<int:book_id>", methods=["POST"])
def complete(book_id):
    if not session.get('user_id') and not session.get('is_admin'):
        return redirect(url_for('login'))

    book = get_book_by_id(book_id)
    if book:
        complete_book(book_id, int(request.form["rating"]), request.form["review"])

    return redirect(url_for("book_detail", book_id=book_id))


@app.route("/edit/<int:book_id>", methods=["POST"])
def edit(book_id):
    if not session.get('user_id') and not session.get('is_admin'):
        return redirect(url_for('login'))

    book = get_book_by_id(book_id)
    if book:
        edit_book(book_id, request.form.get("title"), request.form.get("author"), request.form.get("category"))

    return redirect(url_for("index"))


@app.route("/book/<int:book_id>/edit", methods=["POST"])
def edit_book_route(book_id):
    if not session.get('user_id') and not session.get('is_admin'):
        return redirect(url_for('login'))

    book = get_book_by_id(book_id)
    if book:
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


# === REGISTRATION ===
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password:
            return render_template("register.html", error="Username and password required")

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match")

        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters")

        # Hash hasła
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            client.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash.decode('utf-8'))
            )
            flash("Account created! Please login.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Registration error: {e}")
            return render_template("register.html", error="Username already exists")

    return render_template("register.html")


# === LOGIN (z adminem + zwykłymi userami) ===
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get('user_id') or session.get('is_admin'):
        return redirect(url_for("index"))

    if request.method == "GET":
        session["pre_login_url"] = request.referrer or url_for("index")
        if session["pre_login_url"].endswith("/login") or session["pre_login_url"].endswith("/register"):
            session["pre_login_url"] = url_for("index")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Najpierw sprawdź czy to admin
        if username == ADMIN_USERNAME and bcrypt.checkpw(password.encode('utf-8'), ADMIN_PASSWORD_HASH):
            session.permanent = True
            session["is_admin"] = True
            flash("Welcome admin!", "success")
            return redirect(session.pop("pre_login_url", url_for("index")))

        # Jeśli nie admin, sprawdź zwykłych użytkowników
        try:
            rs = client.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
            user = row_to_dict(rs)

            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                session.permanent = True
                session["user_id"] = user['id']
                session["username"] = username
                flash(f"Welcome back, {username}!", "success")
                return redirect(session.pop("pre_login_url", url_for("index")))
            else:
                return render_template("login.html", error="Invalid credentials")
        except Exception as e:
            print(f"Login error: {e}")
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/logout")
def logout():
    username = session.get('username', 'Admin' if session.get('is_admin') else 'User')
    pre_logout_url = request.referrer or url_for("home")

    session.clear()
    flash(f"Goodbye, {username}!", "info")

    if pre_logout_url.endswith("/login"):
        return redirect(url_for("home"))

    return redirect(url_for("home"))


@app.route("/init_books_db", methods=["POST"])
def init_books_db():
    if not session.get("is_admin"):
        flash("Admin access required", "danger")
        return redirect(url_for("index"))

    if initialize_database():
        flash("Database initialized!", "success")
    else:
        flash("Init failed.", "danger")
    return redirect(url_for("index"))


@app.route("/search")
def search_books():
    query = request.args.get("q", "")
    if not query:
        return {"error": "Missing query"}, 400

    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "maxResults": 15,
        "printType": "books",
        "key": GOOGLE_BOOKS_API_KEY,
        "orderBy": "relevance"
    }

    try:
        resp = requests.get(url, params=params, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})

        if resp.status_code != 200:
            return {"error": f"API failed with {resp.status_code}"}, 500

        data = resp.json()

        results = [
            {
                "title": i["volumeInfo"].get("title", ""),
                "authors": i["volumeInfo"].get("authors", []),
                "categories": i["volumeInfo"].get("categories", []),
                "thumbnail": i["volumeInfo"].get("imageLinks", {}).get("thumbnail", "")
            }
            for i in data.get("items", [])
        ]

        return jsonify({"results": results})

    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return {"error": str(e)}, 500


@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(e):
    return redirect(url_for("home"))


if __name__ == "__main__":
    pass