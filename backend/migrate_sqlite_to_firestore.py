"""One-time, repeatable SQLite -> Firestore migration.

Run from backend after installing requirements and setting Firebase env vars:
    python migrate_sqlite_to_firestore.py --sqlite my_database.db
"""

import argparse
import json
import os
import sqlite3

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore


def initialize_firebase():
    if not firebase_admin._apps:
        credential_value = os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"]
        credential = (
            credentials.Certificate(credential_value)
            if os.path.isfile(credential_value)
            else credentials.Certificate(json.loads(credential_value))
        )
        firebase_admin.initialize_app(
            credential,
            {"projectId": os.environ.get("FIREBASE_PROJECT_ID")},
        )
    return firestore.client()


def write_rows(database, collection, rows, key):
    pending = []
    for row in rows:
        values = dict(row)
        document_id = str(values.pop(key))
        pending.append((database.collection(collection).document(document_id), values))
        if len(pending) == 450:
            commit_batch(database, pending)
            pending.clear()
    if pending:
        commit_batch(database, pending)


def commit_batch(database, pending):
    batch = database.batch()
    for reference, data in pending:
        batch.set(reference, data)
    batch.commit()


def migrate(sqlite_path):
    database = initialize_firebase()
    connection = sqlite3.connect(sqlite_path)
    connection.row_factory = sqlite3.Row
    try:
        write_rows(database, "users", connection.execute("SELECT * FROM users"), "username")
        write_rows(database, "labs", connection.execute("SELECT * FROM labs"), "id")
        write_rows(database, "links", connection.execute("SELECT * FROM links"), "id")
        write_rows(database, "problems", connection.execute("SELECT * FROM problems"), "id")
    finally:
        connection.close()
    print("Migration complete: users, labs, links, and problems copied.")


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", default=os.getenv("TCT_DATABASE_PATH", "my_database.db"))
    args = parser.parse_args()
    migrate(args.sqlite)
