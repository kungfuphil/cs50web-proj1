# Books - Project 1

Web Programming with Python and JavaScript

## Set-up

### Environment Variables (Windows)

```dos
set FLASK_APP=application.py

REM If you want to enable debugging
set FLASK_DEBUG=1

REM Set this to whatever the URL of your database is
set DATABASE_URL=<URL>
```

## Tables

### Users

|Column          |Type        |Comment        |
|----------------|------------|---------------|
|user_id         |serial      |               |
|username        |varchar(10) |               |
|password        |varchar(100)|Hashed password|
|insert_timestamp|timestamp   |               |
|update_timestamp|timestamp   |               |
