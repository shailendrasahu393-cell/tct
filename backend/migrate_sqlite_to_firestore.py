"""One-time, repeatable SQLite -> Firestore migration.

Run from backend after installing requirements and setting Firebase env vars:
    python migrate_sqlite_to_firestore.py --sqlite my_database.db
"""

import argparse
import os
import sqlite3

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore


def initialize_firebase():
    if not firebase_admin._apps:
        firebase_admin.initialize_app(
            credentials.Certificate(os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"]),
            {"projectId": os.environ.get("FIREBASE_PROJECT_ID")},
        )
    return firestore.client()


def write_rows(batch_writer, database, collection, rows, key):
    pending = []
    for row in rows:
        values = dict(row)
        document_id = str(values.pop(key))
        pending.append((database.collection(collection).document(document_id), values))
        if len(pending) == 450:
            for reference, data in pending:
                batch_writer.set(reference, data)
            batch_writer.commit()
            pending.clear()
    for reference, data in pending:
        batch_writer.set(reference, data)


def migrate(sqlite_path):
    database = initialize_firebase()
    connection = sqlite3.connect(sqlite_path)
    connection.row_factory = sqlite3.Row
    batch = database.batch()
    write_rows(batch, database, "users", connection.execute("SELECT * FROM users"), "username")
    write_rows(batch, database, "labs", connection.execute("SELECT * FROM labs"), "id")
    write_rows(batch, database, "links", connection.execute("SELECT * FROM links"), "id")
    write_rows(batch, database, "problems", connection.execute("SELECT * FROM problems"), "id")
    batch.commit()
    connection.close()
    print("Migration complete: users, labs, links, and problems copied.")


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", default=os.getenv("TCT_DATABASE_PATH", "my_database.db"))
    args = parser.parse_args()
    migrate(args.sqlite)