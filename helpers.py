"""Helper functions to use"""
from functools import wraps
from flask import redirect, url_for, session

def login_required(f):
    """Login Required decorator. Half from Flask documentation, half from CS50 finance project"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("/login"))
        return f(*args, **kwargs)
    return decorated_function
