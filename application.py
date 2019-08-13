"""Books - Project 1"""
import os
import sys

from flask import Flask, session, render_template, request
from passlib.hash import sha256_crypt
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_session import Session

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

        return render_template("index.html")


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
