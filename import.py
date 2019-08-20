"""Imports the list of books to the database"""
import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
ENGINE = create_engine(os.getenv("DATABASE_URL"))
DB = scoped_session(sessionmaker(bind=ENGINE))

# SQL STATEMENTS
SQL_RETURN_AUTHOR = "SELECT author_id, name FROM authors WHERE UPPER(name) = UPPER(:name)"

with open("books.csv", mode="r") as books:
    READER = csv.DictReader(books)
    rowNum = 0
    for row in READER:
        rowNum += 1

        # Get rid of trailing and leading whitespace
        title = row["title"].strip()
        author = row["author"].strip()
        isbn = row["isbn"].strip()

        print(f"In row {rowNum}, importing {title} by {author}")

        # See if the author already exists
        authorRow = DB.execute(SQL_RETURN_AUTHOR, {"name": author}).fetchone()

        # If not, then add the author
        if not authorRow:
            print(f"{author} does not already exist. Adding now.")

            DB.execute("INSERT INTO authors (name) VALUES (:name)", {"name": author})
            DB.commit()

            authorRow = DB.execute(SQL_RETURN_AUTHOR, {"name": author}).fetchone()

        print(f"Author ID is {authorRow['author_id']}")

        # Now see if the book already exists
        book = DB.execute("SELECT title FROM books WHERE UPPER(title) = UPPER(:title)",
                          {"title": title}).fetchone()

        # If not, then add the book
        if not book:
            DB.execute("INSERT INTO books (isbn, title, author_id, year) VALUES (:isbn, :title, :author_id, :year)",
                       {
                           "isbn": isbn,
                           "title": title,
                           "author_id": authorRow["author_id"],
                           "year": row["year"]
                       })
            DB.commit()
