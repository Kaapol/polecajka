from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from edit_item import edit_item, edit_review_date
import os
import bcrypt
from add_item import add_item
from remove_item import remove_item
from complete_item import complete_item
from datetime import datetime
from db_init import get_client, initialize_database, rs_to_dicts, row_to_dict, is_database_initialized
from urllib.parse import urlparse, urljoin
from dotenv import load_dotenv
import requests

load_dotenv()
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
app = Flask(__name__)
app.secret_key = "9e6663d956531a9dbdad7a8e5196119e6d6b8cf8a6154be26834db2789038a8d"

client = get_client()

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = b"$2b$12$rHOwLdcakTzBDyJXm4NA1On.94bCm4bNLZaUps7sEBsj.KQxtW5xK"

# Typy itemów
VALID_TYPES = ['books', 'games', 'movies', 'series']


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_items(item_type):
    """Zwraca itemy danego typu dla zalogowanego użytkownika (lub wszystkie dla admina)"""
    if not client or item_type not in VALID_TYPES:
        return []

    # Admin widzi wszystkie itemy danego typu
    if session.get('is_admin'):
        try:
            rs = client.execute("""
                SELECT i.id, i.title, i.creator, i.category, i.status, i.type,
                       r.rating, r.review, i.thumbnail, i.date_added
                FROM items i
                LEFT JOIN reviews r ON i.id = r.item_id
                WHERE i.type = ?
                ORDER BY i.date_added DESC
            """, (item_type,))
            return rs_to_dicts(rs)
        except Exception as e:
            print(f"Database error in get_items: {e}")
            return []

    # Zwykły użytkownik widzi tylko swoje
    user_id = session.get('user_id')
    if not user_id:
        return []

    try:
        rs = client.execute("""
            SELECT i.id, i.title, i.creator, i.category, i.status, i.type,
                   r.rating, r.review, i.thumbnail, i.date_added
            FROM items i
            LEFT JOIN reviews r ON i.id = r.item_id
            WHERE i.type = ? AND i.user_id = ?
            ORDER BY i.date_added DESC
        """, (item_type, user_id))
        return rs_to_dicts(rs)
    except Exception as e:
        print(f"Database error in get_items: {e}")
        return []


def get_item_by_id(item_id):
    """Zwraca item TYLKO jeśli należy do zalogowanego użytkownika (lub admin)"""
    if not client:
        return None

    # Admin widzi wszystko
    if session.get('is_admin'):
        try:
            rs = client.execute("""
                SELECT i.id, i.title, i.creator, i.category, i.status, i.date_added, i.thumbnail, i.type,
                       r.date_finished, r.rating, r.review
                FROM items i
                LEFT JOIN reviews r ON i.id = r.item_id
                WHERE i.id = ?
            """, (item_id,))
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
            SELECT i.id, i.title, i.creator, i.category, i.status, i.date_added, i.thumbnail, i.type,
                   r.date_finished, r.rating, r.review
            FROM items i
            LEFT JOIN reviews r ON i.id = r.item_id
            WHERE i.id = ? AND i.user_id = ?
        """, (item_id, user_id))
        return row_to_dict(rs)
    except Exception as e:
        print(f"Database error: {e}")
        return None


def add_item_with_user(user_id, item_type, title, creator, category, thumbnail=None):
    """Dodaje item dla konkretnego użytkownika"""
    if not client:
        raise Exception("No DB client")

    if item_type not in VALID_TYPES:
        raise ValueError(f"Invalid item type: {item_type}")

    # Sprawdź duplikat DLA TEGO UŻYTKOWNIKA I TYPU
    rs = client.execute(
        "SELECT id FROM items WHERE LOWER(title) = LOWER(?) AND user_id = ? AND type = ?",
        (title, user_id, item_type)
    )
    if rs.rows:
        raise ValueError(f"'{title}' already exists in your {item_type}!")

    date_added = datetime.now().strftime("%d-%m-%Y")
    client.execute("""
        INSERT INTO items (user_id, type, title, creator, category, date_added, thumbnail, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'To Read')
    """, (user_id, item_type, title, creator, category, date_added, thumbnail))
    print(f"✅ Added: {title} ({item_type}) for user {user_id}")


@app.route("/")
def home():
    return render_template("home.html")


# === DYNAMICZNE ROUTES DLA KAŻDEGO TYPU ===
@app.route("/books")
def books_list():
    if not session.get('user_id') and not session.get('is_admin'):
        flash("Please login first", "warning")
        return redirect(url_for('login'))
    return items_list_view('books')


@app.route("/games")
def games_list():
    if not session.get('user_id') and not session.get('is_admin'):
        flash("Please login first", "warning")
        return redirect(url_for('login'))
    return items_list_view('games')


@app.route("/movies")
def movies_list():
    if not session.get('user_id') and not session.get('is_admin'):
        flash("Please login first", "warning")
        return redirect(url_for('login'))
    return items_list_view('movies')


@app.route("/series")
def series_list():
    if not session.get('user_id') and not session.get('is_admin'):
        flash("Please login first", "warning")
        return redirect(url_for('login'))
    return items_list_view('series')


def items_list_view(item_type):
    """Wspólna logika dla listy itemów"""
    items = get_items(item_type)
    db_exists = is_database_initialized(client)
    return render_template("items_list.html", items=items, db_exists=db_exists, item_type=item_type)


@app.route("/add/<string:item_type>", methods=["POST"])
def add_item_route(item_type):
    if item_type not in VALID_TYPES:
        return redirect(url_for('home'))

    if not session.get('user_id') and not session.get('is_admin'):
        flash("Please login first", "danger")
        return redirect(url_for('login'))

    user_id = session.get('user_id', 0)
    title = request.form["title"].title()
    creator = request.form["creator"].title()
    category = request.form["category"].title()
    thumbnail = request.form.get("thumbnail", "")

    try:
        add_item_with_user(user_id, item_type, title, creator, category, thumbnail)
        flash(f"'{title}' added successfully!", "success")
    except Exception as e:
        flash(str(e), "danger")

    # Redirect do odpowiedniej listy
    return redirect(url_for(f'{item_type}_list'))


@app.route("/item/<int:item_id>")
def item_detail(item_id):
    if not session.get('user_id') and not session.get('is_admin'):
        flash("Please login first", "warning")
        return redirect(url_for('login'))

    item = get_item_by_id(item_id)
    if not item:
        flash("Item not found", "danger")
        return redirect(url_for("home"))

    # Używamy item zamiast book
    return render_template("item.html", item=item)


@app.route("/item/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    if not session.get('user_id') and not session.get('is_admin'):
        return redirect(url_for('login'))

    item = get_item_by_id(item_id)
    if item:
        item_type = item.get('type', 'books')
        remove_item(item_id)
        return redirect(url_for(f'{item_type}_list'))

    return redirect(url_for("home"))


@app.route("/item/<int:item_id>/complete", methods=["POST"])
def complete_item_route(item_id):
    if not session.get('user_id') and not session.get('is_admin'):
        return redirect(url_for('login'))

    item = get_item_by_id(item_id)
    if item:
        complete_item(item_id, int(request.form["rating"]), request.form["review"])

    return redirect(url_for("item_detail", item_id=item_id))


@app.route("/item/<int:item_id>/edit", methods=["POST"])
def edit_item_route(item_id):
    if not session.get('user_id') and not session.get('is_admin'):
        return redirect(url_for('login'))

    item = get_item_by_id(item_id)
    if item:
        edit_item(item_id, request.form.get("title"), request.form.get("creator"), request.form.get("category"))
        edit_review_date(item_id, request.form.get("date_finished"))
        flash("Item updated", "success")

    return redirect(url_for("item_detail", item_id=item_id))


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


# === LOGIN ===
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get('user_id') or session.get('is_admin'):
        return redirect(url_for("home"))

    if request.method == "GET":
        session["pre_login_url"] = request.referrer or url_for("home")
        if session["pre_login_url"].endswith(("/login", "/register")):
            session["pre_login_url"] = url_for("home")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and bcrypt.checkpw(password.encode('utf-8'), ADMIN_PASSWORD_HASH):
            session.permanent = True
            session["is_admin"] = True
            flash("Welcome admin!", "success")
            return redirect(session.pop("pre_login_url", url_for("home")))

        try:
            rs = client.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
            user = row_to_dict(rs)

            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                session.permanent = True
                session["user_id"] = user['id']
                session["username"] = username
                flash(f"Welcome back, {username}!", "success")
                return redirect(session.pop("pre_login_url", url_for("home")))
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


@app.route("/init_db", methods=["POST"])
def init_db():
    if not session.get("is_admin"):
        flash("Admin access required", "danger")
        return redirect(url_for("home"))

    if initialize_database():
        flash("Database initialized!", "success")
    else:
        flash("Init failed.", "danger")
    return redirect(url_for("home"))


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