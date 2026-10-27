"""Secure Task Manager: a small Flask UI and JSON API backed by SQLite."""

from __future__ import annotations

import os
import sqlite3
import tempfile
from contextlib import closing, contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request


def create_app(database_path: str | Path | None = None) -> Flask:
    app = Flask(__name__)
    default_path = Path(tempfile.gettempdir()) / "secure-task-manager.db"
    configured_path = database_path or os.environ.get("DATABASE_PATH", str(default_path))
    app.config["DATABASE_PATH"] = str(configured_path)

    def connect_db() -> sqlite3.Connection:
        connection = sqlite3.connect(app.config["DATABASE_PATH"], timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def db_session():
        with closing(connect_db()) as connection:
            with connection:
                yield connection

    def initialize_db() -> None:
        Path(app.config["DATABASE_PATH"]).parent.mkdir(parents=True, exist_ok=True)
        with db_session() as db:
            db.execute("PRAGMA journal_mode = WAL")
            db.execute(
                """CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 120),
                    description TEXT NOT NULL DEFAULT '' CHECK(length(description) <= 2000),
                    status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'in_progress', 'done')),
                    priority TEXT NOT NULL DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high')),
                    due_date TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )

    def task_dict(row: sqlite3.Row) -> dict[str, Any]:
        return dict(row)

    def read_payload() -> tuple[dict[str, Any] | None, tuple[Any, int] | None]:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return None, (jsonify(error="Send a JSON object in the request body."), 400)
        return payload, None

    def validate_task(payload: dict[str, Any], partial: bool = False) -> tuple[dict[str, Any] | None, str | None]:
        allowed = {"title", "description", "status", "priority", "due_date"}
        unexpected = set(payload) - allowed
        if unexpected:
            return None, "Unsupported field(s): " + ", ".join(sorted(unexpected))

        values: dict[str, Any] = {}
        if "title" in payload or not partial:
            title = payload.get("title", "")
            if not isinstance(title, str) or not title.strip() or len(title.strip()) > 120:
                return None, "Title is required and must be 1–120 characters."
            values["title"] = title.strip()

        if "description" in payload or not partial:
            description = payload.get("description", "")
            if not isinstance(description, str) or len(description) > 2000:
                return None, "Description must be 2,000 characters or fewer."
            values["description"] = description.strip()

        if "status" in payload or not partial:
            status = payload.get("status", "open")
            if not isinstance(status, str) or status not in {"open", "in_progress", "done"}:
                return None, "Status must be open, in_progress, or done."
            values["status"] = status

        if "priority" in payload or not partial:
            priority = payload.get("priority", "medium")
            if not isinstance(priority, str) or priority not in {"low", "medium", "high"}:
                return None, "Priority must be low, medium, or high."
            values["priority"] = priority

        if "due_date" in payload or not partial:
            due_date = payload.get("due_date") or None
            if due_date is not None:
                if not isinstance(due_date, str):
                    return None, "Due date must use YYYY-MM-DD format."
                try:
                    date.fromisoformat(due_date)
                except ValueError:
                    return None, "Due date must use YYYY-MM-DD format."
            values["due_date"] = due_date

        return values, None

    initialize_db()

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'self'; frame-ancestors 'none'")
        return response

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        try:
            with db_session() as db:
                db.execute("SELECT 1")
        except sqlite3.Error:
            app.logger.exception("Database health check failed")
            return jsonify(status="error"), 503
        return jsonify(status="ok", service="secure-task-manager")

    @app.get("/api/tasks")
    def list_tasks():
        status = request.args.get("status")
        query = request.args.get("q", "").strip()[:120]
        if status and status not in {"open", "in_progress", "done"}:
            return jsonify(error="Unknown status filter."), 400
        sql = "SELECT * FROM tasks WHERE 1 = 1"
        parameters: list[Any] = []
        if status:
            sql += " AND status = ?"
            parameters.append(status)
        if query:
            sql += " AND (title LIKE ? OR description LIKE ?)"
            parameters.extend((f"%{query}%", f"%{query}%"))
        sql += " ORDER BY CASE status WHEN 'open' THEN 0 WHEN 'in_progress' THEN 1 ELSE 2 END, " \
               "CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, updated_at DESC"
        with db_session() as db:
            rows = db.execute(sql, parameters).fetchall()
            counts = db.execute(
                "SELECT COUNT(*) AS total, SUM(status = 'open') AS open, "
                "SUM(status = 'in_progress') AS in_progress, SUM(status = 'done') AS done FROM tasks"
            ).fetchone()
        return jsonify(tasks=[task_dict(row) for row in rows], stats={key: counts[key] or 0 for key in counts.keys()})

    @app.post("/api/tasks")
    def create_task():
        payload, error = read_payload()
        if error:
            return error
        values, message = validate_task(payload)
        if message:
            return jsonify(error=message), 400
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with db_session() as db:
            cursor = db.execute(
                "INSERT INTO tasks(title, description, status, priority, due_date, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (values["title"], values["description"], values["status"], values["priority"], values["due_date"], now, now),
            )
            row = db.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return jsonify(task=task_dict(row)), 201

    @app.patch("/api/tasks/<int:task_id>")
    def update_task(task_id: int):
        payload, error = read_payload()
        if error:
            return error
        if not payload:
            return jsonify(error="Provide at least one field to update."), 400
        values, message = validate_task(payload, partial=True)
        if message:
            return jsonify(error=message), 400
        values["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        assignments = ", ".join(f"{field} = ?" for field in values)
        with db_session() as db:
            cursor = db.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", [*values.values(), task_id])
            if cursor.rowcount == 0:
                return jsonify(error="Task not found."), 404
            row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return jsonify(task=task_dict(row))

    @app.delete("/api/tasks/<int:task_id>")
    def delete_task(task_id: int):
        with db_session() as db:
            cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            return jsonify(error="Task not found."), 404
        return "", 204

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify(error="Not found."), 404
        return render_template("index.html"), 404

    @app.errorhandler(413)
    def payload_too_large(_error):
        return jsonify(error="Request body is too large."), 413

    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
