"""Single-user SQLite persistence. All SQL uses parameter substitution."""
import sqlite3
from datetime import datetime, timezone
from .config import DATA_DIR, DB_PATH


def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA busy_timeout=10000')
    return db


def initialize():
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id=1),
            name TEXT NOT NULL DEFAULT '',
            target_role TEXT NOT NULL DEFAULT '',
            experience TEXT NOT NULL DEFAULT '',
            job_description TEXT NOT NULL DEFAULT '',
            resume_text TEXT NOT NULL DEFAULT '',
            resume_filename TEXT NOT NULL DEFAULT ''
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            style TEXT NOT NULL,
            created_at TEXT NOT NULL
        )''')
        db.execute("INSERT OR IGNORE INTO profile (id) VALUES (1)")


def get_profile():
    with connect() as db:
        row = db.execute('SELECT * FROM profile WHERE id=1').fetchone()
        return dict(row) if row else {}


def save_profile(fields):
    with connect() as db:
        db.execute('''UPDATE profile SET name=?, target_role=?, experience=?, job_description=?
            WHERE id=1''', (fields['name'], fields['target_role'], fields['experience'], fields['job_description']))
    return get_profile()


def set_resume(filename, text):
    with connect() as db:
        db.execute('UPDATE profile SET resume_filename=?, resume_text=? WHERE id=1', (filename, text))
    return get_profile()


def recent_answers(limit=5):
    with connect() as db:
        rows = db.execute('SELECT question, answer FROM history ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    return [dict(row) for row in reversed(rows)]


def add_answer(question, answer, style):
    created_at = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        cursor = db.execute('INSERT INTO history (question, answer, style, created_at) VALUES (?, ?, ?, ?)',
                            (question, answer, style, created_at))
        return {'id': cursor.lastrowid, 'question': question, 'answer': answer,
                'style': style, 'created_at': created_at}


def list_history(limit=100):
    with connect() as db:
        rows = db.execute('SELECT * FROM history ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    return [dict(row) for row in rows]


def clear_history():
    with connect() as db:
        db.execute('DELETE FROM history')
