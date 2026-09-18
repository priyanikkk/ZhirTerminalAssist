import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zhirterminalassist.config import HISTORY_FILE, ensure_directories

class HistoryManager:
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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    commands_json TEXT,
                    created_at TIMESTAMP NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS command_executions (
                    id TEXT PRIMARY KEY,
                    command TEXT NOT NULL,
                    status TEXT NOT NULL,
                    exit_code INTEGER,
                    output TEXT,
                    risk_level TEXT,
                    created_at TIMESTAMP NOT NULL
                )
            """)
            conn.commit()

    def add_interaction(self, query: str, response: str, commands: Optional[List[str]] = None) -> str:
        item_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        commands_json = json.dumps(commands or [], ensure_ascii=False)
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO interactions (id, query, response, commands_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (item_id, query, response, commands_json, now)
            )
            conn.commit()
        return item_id

    def add_execution(self, command: str, status: str, exit_code: Optional[int] = None,
                      output: str = "", risk_level: str = "SAFE") -> str:
        exec_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO command_executions 
                   (id, command, status, exit_code, output, risk_level, created_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (exec_id, command, status, exit_code, output, risk_level, now)
            )
            conn.commit()
        return exec_id

    def get_history(self, limit: int = 30, search: str = "") -> List[Dict[str, Any]]:
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
            return [dict(r) for r in rows]

    def clear(self):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM command_executions")
            conn.execute("DELETE FROM interactions")
            conn.commit()

_history_instance: Optional[HistoryManager] = None

def get_history_manager() -> HistoryManager:
    global _history_instance
    if _history_instance is None:
        _history_instance = HistoryManager()
    return _history_instance
