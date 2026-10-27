"""Tiny task service used to demonstrate secure coding and CI security gates."""

import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
DATABASE = Path(os.environ.get("DATABASE_PATH", "/tmp/tasks.db"))


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/tasks")
def list_tasks():
    owner = request.args.get("owner", "")
    with get_db() as db:
        rows = db.execute("SELECT id, title, owner FROM tasks WHERE owner = ?", (owner,)).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/tasks")
def create_task():
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", ""))[:200]
    owner = str(payload.get("owner", ""))[:80]
    if not title or not owner:
        return jsonify(error="title and owner are required"), 400
    with get_db() as db:
        cursor = db.execute("INSERT INTO tasks(title, owner) VALUES (?, ?)", (title, owner))
        task_id = cursor.lastrowid
    return jsonify(id=task_id, title=title, owner=owner), 201


def initialize_db():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as db:
        db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL, owner TEXT NOT NULL)")


initialize_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
