# Polecajka
Catalog of books, games, movies &amp; more!

# 📚 Book Tracker App (Flask)

A simple Python/Flask project for tracking books - you can add, edit, remove, and mark books as completed.  
It also includes a **search bar powered by Google Books API** (optional - works only if you have your own API key).

---

## ⚙️ 1. Requirements

- Python **3.10+**
- `pip` (Python package manager)
- Google account (only if you want to use the book search feature)

---

## 🧠 2. Clone the Project

Open your terminal and run:
```bash
git clone https://github.com/<your_username>/<your_repo>.git
cd <your_repo>
````

---

## 📦 3. Install Dependencies

Run the following command inside the project folder:

```bash
pip install -r requirements.txt
```

This installs everything your app needs (Flask, bcrypt, requests, dotenv, etc.).

---

## 🔑 4. Create a `.env` File

In the **root directory** of your project, create a file called `.env`
Then paste the following inside:

```
GOOGLE_API_KEY=YOUR_OWN_KEY_HERE
```

This key is required for the Google Books API search to work.

---

## 🧙‍♂️ 5. How to Get a Google Books API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Log in with your Google account.
3. Click **"Select a project" → "New Project"**.
4. Name it something like `book-tracker`.
5. Once created, open the sidebar and go to **APIs & Services → Library**.
6. Search for **"Books API"** and click **Enable**.
7. Then go to **APIs & Services → Credentials**.
8. Click **"Create Credentials → API Key"**.
9. Copy your key and paste it into the `.env` file you just created.

---

## 🧰 6. Initialize the Database (SQLite)

This project uses a simple local SQLite database (`db.sqlite3`).

You are able to initilize the database in the app,
but if you want to do it manually, run:

```bash
python db_init.py
```

If you want to initilize the database in the app, you need to be logged in as admin.

**Username**: admin
**Password**: admin

---

## 🚀 7. Run the Application

Start the app with:

```bash
python app.py
```

If everything’s fine, you’ll see something like:

```
 * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)
```

Then open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser
and enjoy your local **Book Tracker App** 📚

---

## 🌍 8. Using the Google Books Search Feature

If your `.env` contains a valid `GOOGLE_API_KEY`,
you’ll see the **book search bar** which fetches results from Google Books.

If you don’t provide the key, the app will simply skip this feature — everything else will still work normally.

---

## 🧹 9. Common Issues & Fixes

| Problem                           | Solution                                                                                |
| --------------------------------- | --------------------------------------------------------------------------------------- |
| `ModuleNotFoundError`             | Run `pip install -r requirements.txt` again                                             |
| `OSError: Address already in use` | Close the previous Flask process or use a different port: `python app.py --port=5001`   |
| Search doesn’t work               | Make sure your `.env` has a valid `GOOGLE_API_KEY`                                      |
| `.env` ignored / not loading      | Check that you have `python-dotenv` installed and `load_dotenv()` is called in `app.py` |

---

## 🎨 10. Extra Features

* Supports **dark / light mode** with smooth icon transitions 🌙🌞
* Modern responsive CSS design
* Clean codebase (easy to expand or restyle)

---

## 💡 11. Dev Tip

⚠️ Never upload .env to GitHub!
It’s already ignored via .gitignore, so you’re safe - just don’t force add it manually.

To check if `.env` is really ignored by git, run:

```bash
git check-ignore -v .env
```

You should see something like:

```
.gitignore:123:.env
.env
```

That means you’re good - the file won’t get uploaded.

---

## ☕ Author

Created by **Kapol**
Fork it, tweak it, break it, fix it - just don’t delete my sun and moon icons 🌞🌙

---
