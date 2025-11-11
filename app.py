from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from edit_book import edit_book, edit_review_date
import os
import bcrypt
from add_book import add_book
from remove_book import remove_book
from complete_book import complete_book
from datetime import datetime
from db_init import get_client, initialize_database, rs_to_dicts, row_to_dict, is_database_initialized
from urllib.parse import urlparse, urljoin, quote
from dotenv import load_dotenv
import requests
import time

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
    if not client:
        return []
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



@app.route("/")
def home():
    return render_template("home.html")


@app.route("/books")
def index():
    books = get_books()
    db_exists = is_database_initialized(client)
    return render_template("index.html", books=books, db_exists=db_exists)


import time


@app.route("/add", methods=["POST"])
def add():
    title = request.form["title"].title()
    author = request.form["author"].title()
    category = request.form["category"].title()

    thumbnail = request.form.get("thumbnail")

    if not thumbnail:

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
                # RETRY LOGIC - spróbuj 3 razy
                resp = None
                for attempt in range(3):
                    try:
                        resp = requests.get(url, params=params, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
                        break  # Jeśli sukces, wyjedź z pętli retry
                    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                        if attempt < 2:
                            print(f"  Timeout/Connection error, retrying... (attempt {attempt + 1}/3)")
                            time.sleep(2)
                        else:
                            print(f"  Failed after 3 attempts")
                            continue  # Pomiń ten query, idź do następnego

                if resp and resp.status_code == 200:
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
                elif resp:
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
                # RETRY LOGIC DLA FALLBACK
                for attempt in range(3):
                    try:
                        resp = requests.get(url, params=params, timeout=15)
                        break
                    except requests.exceptions.Timeout:
                        if attempt < 2:
                            time.sleep(1)
                        else:
                            raise

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

    try:
        add_book(title, author, category, thumbnail)
        flash(f"Book '{title}' added successfully!", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("index"))


def get_book_by_id(book_id):
    if not client:
        return None

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
        print(f"Database error in get_book_by_id: {e}")
        return None


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
    pre_logout_url = request.referrer or url_for("home")

    session.clear()
    flash("Logged out", "info")

    if pre_logout_url.endswith("/login"):
        return redirect(url_for("home"))

    return redirect(pre_logout_url)

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
    query = request.args.get("q", "")
    if not query: return {"error": "Missing query"}, 400

    url = "https://www.googleapis.com/books/v1/volumes"

    params = {
        "q": query,
        "maxResults": 15,
        "printType": "books",
        "key": GOOGLE_BOOKS_API_KEY,
        "langRestrict": "",
        "orderBy": "relevance"
    }

    resp = None
    for attempt in range(3):
        try:
            resp = requests.get(
                url,
                params=params,
                timeout=30,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < 2:
                print(f"Retry attempt {attempt + 1}/3")
                time.sleep(1)
            else:
                return {"error": "API timeout"}, 500

    if not resp or resp.status_code != 200:
        return {"error": "API failed"}, 500

    data = resp.json()

    return jsonify({"results": [
        {
            "title": i["volumeInfo"].get("title", ""),
            "authors": i["volumeInfo"].get("authors", []),
            "categories": i["volumeInfo"].get("categories", []),  # <--- DODAŁEM TO
            "thumbnail": i["volumeInfo"].get("imageLinks", {}).get("thumbnail", "")
        } for i in data.get("items", [])
    ]})



if __name__ == "__main__":
    pass