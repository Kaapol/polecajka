from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from add_book import add_book
from remove_book import remove_book
from edit_book import edit_book
from complete_book import complete_book
from db_init import get_connection

app = Flask(__name__)



def get_books():
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
    books = get_books()
    return render_template("index.html", books=books)


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

if __name__ == "__main__":
    app.run(debug=False)
