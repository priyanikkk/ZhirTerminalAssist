import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zhirterminalassist.config import HISTORY_FILE, ensure_directories

class HistoryDB:
    def __init__(self, db_path: Optional[Path] = None):
        ensure_directories()
        self.db_path = db_path or HISTORY_FILE
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    commands_json TEXT,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS command_executions (
                    id TEXT PRIMARY KEY,
                    command TEXT NOT NULL,
                    status TEXT NOT NULL,
                    exit_code INTEGER,
                    output TEXT,
                    error TEXT,
                    risk_level TEXT,
                    created_at TIMESTAMP NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_exec_date ON command_executions(created_at)")
            conn.commit()

    def create_conversation(self, title: str = "New Session") -> str:
        conv_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO conversations (id, title, created_at) VALUES (?, ?, ?)",
                (conv_id, title, now)
            )
            conn.commit()
        return conv_id

    def get_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM conversations ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

    def add_message(self, conversation_id: str, role: str, content: str, commands: Optional[List[str]] = None) -> str:
        msg_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        commands_json = json.dumps(commands or [], ensure_ascii=False)
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (id, conversation_id, role, content, commands_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (msg_id, conversation_id, role, content, commands_json, now)
            )
            conn.commit()
        return msg_id

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
                (conversation_id,)
            ).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                try:
                    item["commands"] = json.loads(item.get("commands_json") or "[]")
                except Exception:
                    item["commands"] = []
                result.append(item)
            return result

    def record_execution(self, command: str, status: str, exit_code: Optional[int] = None,
                         output: str = "", error: str = "", risk_level: str = "SAFE") -> str:
        exec_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO command_executions 
                   (id, command, status, exit_code, output, error, risk_level, created_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (exec_id, command, status, exit_code, output, error, risk_level, now)
            )
            conn.commit()
        return exec_id

    def get_executions(self, limit: int = 100, search: str = "") -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            if search:
                rows = conn.execute(
                    """SELECT * FROM command_executions 
                       WHERE command LIKE ? OR output LIKE ? 
                       ORDER BY created_at DESC LIMIT ?""",
                    (f"%{search}%", f"%{search}%", limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM command_executions ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(row) for row in rows]

    def clear_all(self):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM conversations")
            conn.execute("DELETE FROM command_executions")
            conn.commit()

_db_instance = None

def get_history_db() -> HistoryDB:
    global _db_instance
    if _db_instance is None:
        _db_instance = HistoryDB()
    return _db_instance
