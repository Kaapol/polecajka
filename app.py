from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import bcrypt
import sqlite3
from add_book import add_book
from remove_book import remove_book
from edit_book import edit_book
from complete_book import complete_book
from db_init import get_connection, initialize_database
from urllib.parse import urlparse, urljoin

app = Flask(__name__)

app.secret_key = "9e6663d956531a9dbdad7a8e5196119e6d6b8cf8a6154be26834db2789038a8d"


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc



def get_books():
    if not os.path.exists("books.db"):
        return []

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.id, b.title, b.author, b.category, b.status,
               r.rating, r.review
        FROM books b
        LEFT JOIN reviews r ON b.id = r.book_id
        ORDER BY b.date_added DESC
    """)
    books = cur.fetchall()
    conn.close()
    return books


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/books")
def index():
    db_exists = os.path.exists("books.db")
    books = get_books()
    return render_template("index.html", books=books, db_exists=db_exists)


@app.route("/add", methods=["POST"])
def add():
    title = request.form["title"].title()
    author = request.form["author"].title()
    category = request.form["category"].title()
    add_book(title, author, category)
    return redirect(url_for("index"))

#get book ID
def get_book_by_id(book_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.id, b.title, b.author, b.category, b.status, b.date_added,
               r.date_finished, r.rating, r.review
        FROM books b
        LEFT JOIN reviews r ON b.id = r.book_id
        WHERE b.id = ?
    """, (book_id,))
    book = cur.fetchone()
    conn.close()
    return book


@app.route("/book/<int:book_id>")
def book_detail(book_id):
    book = get_book_by_id(book_id)
    return render_template("book.html", book=book)

@app.route("/delete/<int:book_id>", methods=["POST"])
def delete(book_id):
    remove_book(book_id)
    return redirect(url_for("index"))


@app.route("/complete/<int:book_id>", methods=["POST"])
def complete(book_id):
    rating = int(request.form["rating"])
    review = request.form["review"]
    complete_book(book_id, rating, review)
    return redirect(url_for("book_detail", book_id=book_id))

@app.route("/edit/<int:book_id>", methods=["POST"])
def edit(book_id):
    title = request.form["title"].strip()
    author = request.form["author"].strip()
    category = request.form["category"].strip()

    # Puste stringi zamień na None, żeby edit_book je pominął
    title = title if title else None
    author = author if author else None
    category = category if category else None

    edit_book(book_id, title, author, category)
    return redirect(url_for("index"))



@app.route("/book/<int:book_id>/edit", methods=["POST"])
def edit_book_route(book_id):
    title = request.form.get("title")
    author = request.form.get("author")
    category = request.form.get("category")
    edit_book(book_id, title, author, category)
    return redirect(url_for("book_detail", book_id=book_id))

@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(e):
    return redirect(url_for("home"))


ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = b"$2b$12$rHOwLdcakTzBDyJXm4NA1On.94bCm4bNLZaUps7sEBsj.KQxtW5xK"

@app.route("/login", methods=["GET", "POST"])
def login():
    # Jeżeli użytkownik jest już zalogowany, to niech nie wraca na login
    if session.get("is_admin"):
        return redirect(session.get("pre_login_url") or url_for("index"))

    if request.method == "GET":
        # referrer can be none if entering directly
        session["pre_login_url"] = request.referrer or url_for("index")
        # dont save if referrer is login
        if session["pre_login_url"].endswith("/login"):
            session["pre_login_url"] = url_for("index")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and bcrypt.checkpw(password.encode("utf-8"), ADMIN_PASSWORD_HASH):
            session.permanent = True  # zachowuje sesję
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
    session.clear()
    flash("Logged out successfully", "info")

    referrer = request.referrer
    if referrer and is_safe_url(referrer):
        return redirect(referrer)
    return redirect(url_for("home"))


@app.route("/init_books_db", methods=["POST"])
def init_books_db():
    if not session.get("is_admin"):
        flash("Unauthorized", "danger")
        return redirect(url_for("index"))

    created = initialize_database()
    if created:
        flash("Books database created successfully!", "success")
    else:
        flash("Database already exists!", "info")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=False)
