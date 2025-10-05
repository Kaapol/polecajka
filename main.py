import sys

#import functions from other files
from add_book import add_book
from list_books import list_books
from remove_book import remove_book
from complete_book import complete_book
from edit_book import edit_book

import sqlite3


#menu function
def menu():
    while True:
        print("\n--- MENU ---")
        print("1. Show a list of books")
        print("2. Add a new book")
        print("3. Delete a book from the list")
        print("4. Mark a book as read")
        print("5. Edit a book")
        print("6. Exit")

        choice = input("\nChoose option: ")

        if choice == "1":
            list_books()


        elif choice == "2":
            title = input("Title: ").title()
            author = input("Author: ").title()
            category = input("Category: ").title()
            add_book(title, author, category)


        elif choice == "3":
            if list_books(show=False) == 0:
                print("❌ No books to remove.")
                continue

            try:
                book_id = int(input("Enter book ID to remove: "))
                remove_book(book_id)
            except ValueError:
                print("❌ ID must be an integer.")


        elif choice == "4":
            if list_books(show=False) == 0:
                print("❌ No books to mark as complete.")
                continue

            conn = sqlite3.connect("books.db")
            cur = conn.cursor()

            while True:
                try:
                    book_id = int(input("Enter book ID to mark as completed: "))
                except ValueError:
                    print("❌ ID must be an integer.")
                    continue



                cur.execute("SELECT * FROM books WHERE id = ?", (book_id,))
                if not cur.fetchone():
                    print(f"❌ No book found with ID: {book_id}")
                    continue

                else:
                    break

            conn.close()

            while True:
                try:
                    rating = int(input("Your rating (1-10): "))
                    if 1 <= rating <= 10:
                        break
                    else:
                        print("❌ Rating must be between 1 and 10.")
                except ValueError:
                    print("❌ Please enter a number.")

            review = input("Your review: ")

            complete_book(book_id, rating, review)

        elif choice == "5":
            if list_books(show=False) == 0:
                print("❌ No books to edit.")
                continue

            conn = sqlite3.connect("books.db")
            cur = conn.cursor()

            while True:
                try:
                    book_id = int(input("Enter book ID to update: "))
                except ValueError:
                    print("❌ ID must be an integer.")
                    continue

                cur.execute("SELECT * FROM books WHERE id = ?", (book_id,))
                if not cur.fetchone():
                    print(f"❌ No book found with ID: {book_id}")
                    continue

                else:
                    break
            conn.close()

            title = input("Enter book title: ").title()
            author = input("Enter book author: ").title()
            category = input("Enter book category: ").title()

            edit_book(book_id, title, author, category)

        elif choice == "6":
            print("Application closed.")
            sys.exit()


        else:
            print("❌ Wrong option. Try again.")

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:

        print("\nProgram closed.")
        sys.exit(0)
