# -*- coding: utf-8 -*-
"""项目材料存储（SQLite）：上传的项目文件/说明，用于面试模拟出题"""

import json
import os
import sqlite3
import time

_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiz_history.db")


def _conn():
    conn = sqlite3.connect(_DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS materials ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "created_at TEXT, name TEXT, content TEXT)"
    )
    return conn


def save_material(name: str, content: str) -> int:
    conn = _conn()
    cur = conn.execute(
        "INSERT INTO materials (created_at, name, content) VALUES (?,?,?)",
        (time.strftime("%Y-%m-%d %H:%M:%S"), name, content),
    )
    conn.commit()
    hid = cur.lastrowid
    conn.close()
    return hid


def list_materials() -> list:
    conn = _conn()
    rows = conn.execute(
        "SELECT id, created_at, name, length(content) AS chars FROM materials ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_material(mid: int):
    conn = _conn()
    row = conn.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_material(mid: int):
    conn = _conn()
    conn.execute("DELETE FROM materials WHERE id=?", (mid,))
    conn.commit()
    conn.close()
