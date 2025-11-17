import os
import psycopg2
import psycopg2.extras
from typing import Optional
from server_scrappe.config import DATABASE_URL


def get_connection():
    """Return a new psycopg2 connection using DATABASE_URL env var.
    Caller is responsible for closing the connection.
    """
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set in environment. Set it or add to .env")

    conn = psycopg2.connect(DATABASE_URL)
    return conn


def get_cursor(conn, dict_cursor: bool = True):
    if dict_cursor:
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return conn.cursor()
