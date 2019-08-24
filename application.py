"""Books - Project 1"""
import os
import sys

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


@APP.route("/")
def index():
    """Start page"""

    return render_template("index.html")

@APP.route("/book/<isbn>")
@login_required
def book(isbn):
    """Book Page: When users click on a book from the results of the search page, they should be taken to a book page, with details about the book: its title, author, publication year, ISBN number, and any reviews that users have left for the book on your website."""

    book = DB.execute("""SELECT  b.title, a.name, b.year, b.isbn
                FROM books b
                INNER JOIN authors a
                ON b.author_id = a.author_id
                WHERE b.isbn = :isbn""",
                {"isbn": isbn}).fetchone()

    # TODO: Have this return a nicer 404 page
    # Check to see if it's a valid isbn, if not return 404
    if book is None:
        abort(404)
        
    # Otherwise, display title, author, year, isbn (for now)
    return render_template("book.html", book=book)

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




"""Review Submission: On the book page, users should be able to submit a review: consisting of a rating on a scale of 1 to 5, as well as a text component to the review where the user can write their opinion about a book. Users should not be able to submit multiple reviews for the same book.

Goodreads Review Data: On your book page, you should also display (if available) the average rating and number of ratings the work has received from Goodreads.

API Access: If users make a GET request to your website’s /api/<isbn> route, where <isbn> is an ISBN number, your website should return a JSON response containing the book’s title, author, publication date, ISBN number, review count, and average score. The resulting JSON should follow the format:
{
    "title": "Memory",
    "author": "Doug Lloyd",
    "year": 2015,
    "isbn": "1632168146",
    "review_count": 28,
    "average_score": 5.0
}
If the requested ISBN number isn’t in your database, your website should return a 404 error.

You should be using raw SQL commands (as via SQLAlchemy’s execute method) in order to make database queries. You should not use the SQLAlchemy ORM (if familiar with it) for this project.

In README.md, include a short writeup describing your project, what’s contained in each file, and (optionally) any other additional information the staff should know about your project.

If you’ve added any Python packages that need to be installed in order to run your web application, be sure to add them to requirements.txt!

Beyond these requirements, the design, look, and feel of the website are up to you! You’re also welcome to add additional features to your website, so long as you meet the requirements laid out in the above specification!"""