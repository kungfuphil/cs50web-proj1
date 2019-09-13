"""Books - Project 1
https://docs.cs50.net/web/2019/x/projects/1/project1.html"""
import os
import sys
import requests

from flask import Flask, session, render_template, request, redirect, url_for, abort
from passlib.hash import sha256_crypt
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_session import Session
from helpers import login_required

APP = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
APP.config["SESSION_PERMANENT"] = False
APP.config["SESSION_TYPE"] = "filesystem"
Session(APP)

# Set up database
ENGINE = create_engine(os.getenv("DATABASE_URL"))
DB = scoped_session(sessionmaker(bind=ENGINE))

# Queries used more than once
QUERY_BOOK_BY_ISBN = """SELECT  b.title, a.name, b.year, b.isbn, r.rating, r.review_title, r.review
                        FROM books b
                        INNER JOIN authors a
                        ON b.author_id = a.author_id
                        LEFT JOIN reviews r
                        ON b.isbn = r.isbn
                        AND r.user_id = :user_id
                        WHERE b.isbn = :isbn"""

@APP.route("/")
def index():
    """Start page"""

    return render_template("index.html")

@APP.route("/book/<isbn>")
@login_required
def book(isbn):
    """Book Page: When users click on a book from the results of the search page, they should be taken to a book page, with details about the book: its title, author, publication year, ISBN number, and any reviews that users have left for the book on your website."""

    book = DB.execute(QUERY_BOOK_BY_ISBN, {"isbn": isbn, "user_id": session["user_id"]}).fetchone()

    # TODO: Have this return a nicer 404 page
    # Check to see if it's a valid isbn, if not return 404
    if book is None:
        abort(404)

    # Get the average rating and number of ratings from Goodreads, if any
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
            params={"key": os.getenv("GOODREADS_KEY"), "isbns": isbn})
    goodreads_info = res.json()
    goodreads_ratings_count = goodreads_info["books"][0]["ratings_count"]
    goodreads_average_rating = goodreads_info["books"][0]["average_rating"]
        
    # Otherwise, display title, author, year, isbn (for now)
    return render_template("book.html", 
        book=book, goodreads_ratings_count=goodreads_ratings_count, goodreads_average_rating=goodreads_average_rating)

@APP.route("/login", methods=["GET", "POST"])
def login():
    """Login a user"""

    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        # Make sure all fields are filled out
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return "Please enter your username"

        if not password:
            return "Please enter your password"

        # Check password against hash in database
        row = DB.execute("SELECT user_id, username, password FROM users WHERE UPPER(username) = UPPER(:username)",
                         {"username": username}).fetchone()

        if not row:
            return "Username does not exist"

        if not sha256_crypt.verify(password, row.password):
            return "Username/password combination incorrect"

        # set session["user_id"] = whoever is logged in
        session["user_id"] = row.user_id

        return redirect(url_for("search"))


@APP.route("/logout")
def logout():
    """Logs out"""
    session.clear()

    return redirect(url_for("index"))

@APP.route("/register", methods=["GET", "POST"])
def register():
    """Registers a new user"""

    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        # Make sure all fields are filled out
        if not username:
            return "Username required"
        if not password:
            return "Password required"
        if not confirm:
            return "Must validate password"

        # Make sure passwords match
        if password != confirm:
            return "Passwords do not match"

        # Check if username already exists
        rows = DB.execute("SELECT * FROM users WHERE upper(username) = upper(:username)", 
                          {"username": username}).fetchall()
        print(f"rows: {rows}", file=sys.stdout)

        if rows:
            return "Username already exists"

        # Hash password and store
        hashed_password = sha256_crypt.encrypt(password)

        DB.execute("INSERT INTO users (username, password) values (:username, :password)",
                   {"username": username, "password": hashed_password})
        DB.commit()

        return "Successfully registered user"

@APP.route("/search")
@login_required
def search():
    """Search books by title, author, and/or isbn"""

    is_querying = False

    # For whatever reason, ternary operators don't work correctly here.
    if request.args.get("title"):
        is_querying = True
        title = f"%{request.args.get('title').lower()}%"
    else:
        title = "%"

    if request.args.get('author'):
        is_querying = True
        author = f"%{request.args.get('author').lower()}%"
    else:
        author = "%"

    if request.args.get('isbn'):
        is_querying = True
        isbn = f"%{request.args.get('isbn').lower()}%"
    else:
        isbn = "%"

    query = """SELECT b.title, a.name, b.year, b.isbn
                FROM books b
                INNER JOIN authors a
                ON b.author_id = a.author_id
                WHERE LOWER(b.title) LIKE :title
                AND LOWER(a.name) LIKE :author
                AND LOWER(b.isbn) LIKE :isbn"""

    if is_querying:
        books = DB.execute(query, {"title": title, "author": author, "isbn": isbn}).fetchall()
    else:
        books = []

    return render_template("search.html", books=books)

@APP.route("/review/<isbn>", methods=["GET", "POST"])
@login_required
def review(isbn):
    """Add or edit a book review"""

    # Query what book this is
    book = DB.execute(QUERY_BOOK_BY_ISBN, {"isbn": isbn, "user_id": session["user_id"]}).fetchone()

    # If a rating already exists, don't let the user create another
    if book.rating:
        return redirect(url_for("book", isbn=isbn))

    if request.method == "POST":
        # Get all the values from the form
        star_rating = request.form.get("starRating")
        review_title = request.form.get("reviewTitle")
        review = request.form.get("review")

        if not star_rating:
            return "Star Rating required"

        # Make sure Star Rating is only 1 - 5. This one is required. The actual review is not.
        star_rating = int(star_rating)
        if not (star_rating >= 1 and star_rating <= 5):
            return "Invalid Star Rating"

        # If everything looks good, save to the DB
        query = """INSERT INTO reviews 
                    (rating, isbn, user_id, review_title, review)
                    VALUES
                    (:rating, :isbn, :user_id, :review_title, :review)"""

        DB.execute(query, {
            "rating": star_rating,
            "isbn": isbn,
            "user_id": session["user_id"],
            "review_title": review_title,
            "review": review
        })
        DB.commit()

        # Go back to the book page
        return redirect(url_for("book", isbn=isbn))
    elif request.method == "GET":
        return render_template("review.html", isbn=isbn, book=book.title)

@APP.route("/api/<isbn>")
def api(isbn):
    """Retrieves book data in JSON form"""
    query = """SELECT title, name AS author, year, isbn
               FROM books b
               INNER join authors a
               ON b.author_id = a.author_id
               WHERE isbn = :isbn"""
    book = DB.execute(query, {"isbn": isbn}).fetchone()

    if not book:
        abort(404)

    output = {
        "title": book.title,
        "author": book.author,
        "year": str(book.year),
        "isbn": isbn
    }

    # Get the average rating and number of ratings from Goodreads, if any
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": os.getenv("GOODREADS_KEY"), "isbns": isbn})
    goodreads_info = res.json()
    goodreads_ratings_count = goodreads_info["books"][0]["ratings_count"]
    goodreads_average_rating = goodreads_info["books"][0]["average_rating"]

    output.update({"review_count": goodreads_ratings_count})
    output.update({"average_score": goodreads_average_rating})

    return output
