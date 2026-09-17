"""CyberSnake's zero-dependency SQLite-backed web server."""
from __future__ import annotations

import json
import sqlite3
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).parent.resolve()
DATA_DIR = ROOT / "data"
DATABASE_PATH = DATA_DIR / "cybersnake.db"
SCHEMA_PATH = DATA_DIR / "schema.sql"
SEED_PATH = DATA_DIR / "seed.sql"


def database_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialise_database() -> None:
    """Create the local SQLite database and seed it once from versioned SQL."""
    DATA_DIR.mkdir(exist_ok=True)
    with database_connection() as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        count = connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        if count == 0:
            connection.executescript(SEED_PATH.read_text(encoding="utf-8"))


def random_questions(limit: int) -> list[dict]:
    limit = max(1, min(limit, 40))
    with database_connection() as connection:
        question_rows = connection.execute(
            "SELECT id, topic, question_text FROM questions ORDER BY RANDOM() LIMIT ?", (limit,)
        ).fetchall()
        questions = []
        for row in question_rows:
            answers = connection.execute(
                "SELECT id, answer_text FROM answer_choices WHERE question_id = ? ORDER BY position",
                (row["id"],),
            ).fetchall()
            questions.append(
                {
                    "id": row["id"],
                    "topic": row["topic"],
                    "question": row["question_text"],
                    "answers": [{"id": answer["id"], "text": answer["answer_text"]} for answer in answers],
                }
            )
    return questions


def check_answer(question_id: int, answer_id: int) -> dict | None:
    with database_connection() as connection:
        selected = connection.execute(
            """SELECT is_correct FROM answer_choices
               WHERE id = ? AND question_id = ?""",
            (answer_id, question_id),
        ).fetchone()
        correct = connection.execute(
            "SELECT id FROM answer_choices WHERE question_id = ? AND is_correct = 1",
            (question_id,),
        ).fetchone()
    if selected is None or correct is None:
        return None
    return {"is_correct": bool(selected["is_correct"]), "correct_answer_id": correct["id"]}


class CyberSnakeHandler(SimpleHTTPRequestHandler):
    def send_json(self, status: HTTPStatus, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/questions":
            try:
                limit = int(parse_qs(parsed.query).get("limit", [10])[0])
            except ValueError:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Le paramètre limit doit être un entier."})
                return
            self.send_json(HTTPStatus.OK, {"questions": random_questions(limit)})
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/answers":
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Ressource introuvable."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length))
            result = check_answer(int(data["question_id"]), int(data["answer_id"]))
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Réponse invalide."})
            return
        if result is None:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Question ou réponse introuvable."})
            return
        self.send_json(HTTPStatus.OK, result)


def main() -> None:
    initialise_database()
    server = ThreadingHTTPServer(("127.0.0.1", 8000), CyberSnakeHandler)
    print("CyberSnake disponible sur http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
