# -*- coding: utf-8 -*-
"""历史记录与错题本存储（SQLite，零依赖）"""

import json
import os
import sqlite3
import time

_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiz_history.db")


def _conn():
    conn = sqlite3.connect(_DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS quiz_sessions ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "created_at TEXT, topic TEXT, difficulty TEXT,"
        "total INTEGER, correct INTEGER, detail TEXT)"
    )
    return conn


def save_session(topic: str, difficulty: str, questions: list) -> int:
    """保存一次答题会话。questions 为含 user_answer/correct 的题目列表。"""
    total = len(questions)
    correct = sum(1 for q in questions if q.get("correct"))
    conn = _conn()
    cur = conn.execute(
        "INSERT INTO quiz_sessions (created_at, topic, difficulty, total, correct, detail) VALUES (?,?,?,?,?,?)",
        (time.strftime("%Y-%m-%d %H:%M:%S"), topic, difficulty, total, correct,
         json.dumps(questions, ensure_ascii=False)),
    )
    conn.commit()
    hid = cur.lastrowid
    conn.close()
    return hid


def list_sessions() -> list:
    conn = _conn()
    rows = conn.execute(
        "SELECT id, created_at, topic, difficulty, total, correct FROM quiz_sessions ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session(hid: int):
    conn = _conn()
    row = conn.execute("SELECT * FROM quiz_sessions WHERE id=?", (hid,)).fetchone()
    conn.close()
    if row is None:
        return None
    d = dict(row)
    d["detail"] = json.loads(d["detail"])
    return d


def stats() -> dict:
    """学习统计：总量 + 最近 7 天趋势 + 主题分布"""
    conn = _conn()
    rows = conn.execute(
        "SELECT topic, total, correct, created_at FROM quiz_sessions"
    ).fetchall()
    conn.close()
    total_q = sum(r["total"] for r in rows)
    total_c = sum(r["correct"] for r in rows)
    # 主题分布（按答题数）
    topics = {}
    for r in rows:
        t = r["topic"] or "未知"
        d = topics.setdefault(t, {"sessions": 0, "total": 0, "correct": 0})
        d["sessions"] += 1
        d["total"] += r["total"]
        d["correct"] += r["correct"]
    topic_list = sorted(
        [{"topic": k, "total": v["total"], "correct": v["correct"], "sessions": v["sessions"]} for k, v in topics.items()],
        key=lambda x: -x["total"],
    )[:10]
    # 最近 7 天趋势
    import datetime
    days = {}
    today = datetime.date.today()
    for i in range(6, -1, -1):
        days[(today - datetime.timedelta(days=i)).strftime("%m-%d")] = {"total": 0, "correct": 0, "sessions": 0}
    for r in rows:
        day = r["created_at"][:10]
        try:
            key = (datetime.datetime.strptime(day, "%Y-%m-%d").date() - (today - datetime.timedelta(days=6))).days
            if 0 <= key < 7:
                k = (today - datetime.timedelta(days=6 - key)).strftime("%m-%d")
                days[k]["total"] += r["total"]
                days[k]["correct"] += r["correct"]
                days[k]["sessions"] += 1
        except ValueError:
            pass
    return {
        "sessions": len(rows),
        "total_questions": total_q,
        "total_correct": total_c,
        "accuracy": round(total_c / total_q * 100, 1) if total_q else 0,
        "trend": [{"date": k, "total": v["total"], "correct": v["correct"], "sessions": v["sessions"]} for k, v in days.items()],
        "topics": topic_list,
    }


def delete_session(hid: int):
    conn = _conn()
    conn.execute("DELETE FROM quiz_sessions WHERE id=?", (hid,))
    conn.commit()
    conn.close()

