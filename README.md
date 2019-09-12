# Books - Project 1

Web Programming with Python and JavaScript

## Set-up

### Install Required Modules

```dos
pip3 install -r requirements.txt
```

### Environment Variables (Windows)

```dos
set FLASK_APP=application.py

REM If you want to enable debugging
set FLASK_DEBUG=1

REM Set this to whatever the URL of your database is
set DATABASE_URL=<URL>

REM Set this to your Goodreads API Key
set GOODREADS_KEY=<KEY>
```

## Tables

### Authors

|Column          |Type        |Comment        |
|----------------|------------|---------------|
|author_id       |serial      |               |
|name            |varchar(50) |               |

### Books

|Column          |Type        |Comment        |
|----------------|------------|---------------|
|isbn            |varchar(13) |               |
|title           |varchar(50) |               |
|author_id       |int         |               |
|year            |number(4)   |               |

### Reviews

|Column          |Type         |Comment|
|----------------|-------------|-------|
|review_id       |serial       |       |
|rating          |number(2,1)  |       |
|review          |varchar(2000)|       |
|isbn            |varchar(13)  |       |
|user_id         |int          |       |
|insert_timestamp|timestamp    |       |
|update_timestamp|timestamp    |       |
|review_title    |varchar(140) |       |

### Users

|Column          |Type        |Comment        |
|----------------|------------|---------------|
|user_id         |serial      |               |
|username        |varchar(10) |               |
|password        |varchar(100)|Hashed password|
|insert_timestamp|timestamp   |               |
|update_timestamp|timestamp   |               |

## import.py

This file is used to import the records in books.csv into the database.
