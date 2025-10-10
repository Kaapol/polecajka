from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from add_book import add_book
from remove_book import remove_book
from edit_book import edit_book
from complete_book import complete_book

app = Flask(__name__)

DB_NAME = "books.db"


def get_books():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM books ORDER BY date_added DESC")
    books = cur.fetchall()
    conn.close()
    return books


@app.route("/")
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


@app.route("/delete/<int:book_id>")
def delete(book_id):
    remove_book(book_id)
    return redirect(url_for("index"))


@app.route("/complete/<int:book_id>", methods=["POST"])
def complete(book_id):
    rating = int(request.form["rating"])
    review = request.form["review"]
    complete_book(book_id, rating, review)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=False)
