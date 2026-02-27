# Simple wrapper, just in case for future extension
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../knowledge/brainforce.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
