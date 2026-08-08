# -*- coding: utf-8 -*-
"""学习路线：AI 拆解主题为章节 + SQLite 记录每章掌握进度"""

import json
import os
import re
import sqlite3
import time

from openai import OpenAI
from app.secret import DEEPSEEK_API_KEY, BASE_URL, MODEL

_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiz_history.db")

_client = None


def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=BASE_URL)
    return _client


def _conn():
    conn = sqlite3.connect(_DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS roadmaps ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "created_at TEXT, topic TEXT, chapters TEXT, material_id INTEGER)"
    )
    # 兼容旧表：无 material_id 列时补上
    try:
        conn.execute("ALTER TABLE roadmaps ADD COLUMN material_id INTEGER")
    except sqlite3.OperationalError:
        pass
    conn.execute(
        "CREATE TABLE IF NOT EXISTS chapter_progress ("
        "roadmap_id INTEGER, chapter_index INTEGER,"
        "answered INTEGER DEFAULT 0, correct INTEGER DEFAULT 0,"
        "PRIMARY KEY (roadmap_id, chapter_index))"
    )
    return conn


def generate_roadmap(topic: str, material: str | None = None) -> list:
    """AI 把主题（或项目材料）拆成 3-6 个学习章节（由浅入深），返回 [{title, desc}]"""
    client = get_client()
    if material:
        scope = (
            "以下是候选人的项目内容，请把这个项目拆解成 3-6 个学习章节，"
            "按项目架构/模块/知识点的由浅入深排序（比如：架构总览 → 核心模块 → 关键技术 → 部署实践），"
            "让候选人可以按路线系统掌握这个项目。\n\n"
            f"===== 项目内容 =====\n{material[:6000]}\n===== 项目内容结束 =====\n\n"
        )
    else:
        scope = ""
    prompt = (
        "你是一名资深课程设计专家。" + scope +
        "请把「" + topic + "」拆解成 3-6 个学习章节，按由浅入深、循序渐进排序，覆盖核心知识点。\n"
        "每章给：title（章节名，8字内）、desc（一句话简介，说明这章学什么）。\n"
        '只输出 JSON 对象：{"chapters": [{"title": "章节名", "desc": "简介"}]}'
    )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    text = resp.choices[0].message.content.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    data = json.loads(text)
    return [{"title": c.get("title", ""), "desc": c.get("desc", "")} for c in data.get("chapters", [])]


def create_roadmap(topic: str, material: str | None = None, material_id: int | None = None) -> int:
    chapters = generate_roadmap(topic, material)
    conn = _conn()
    cur = conn.execute(
        "INSERT INTO roadmaps (created_at, topic, chapters, material_id) VALUES (?,?,?,?)",
        (time.strftime("%Y-%m-%d %H:%M:%S"), topic, json.dumps(chapters, ensure_ascii=False), material_id),
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


def get_roadmap(rid: int):
    conn = _conn()
    row = conn.execute("SELECT * FROM roadmaps WHERE id=?", (rid,)).fetchone()
    if row is None:
        conn.close()
        return None
    chapters = json.loads(row["chapters"])
    # 查每章进度
    rows = conn.execute(
        "SELECT chapter_index, answered, correct FROM chapter_progress WHERE roadmap_id=?", (rid,)
    ).fetchall()
    conn.close()
    prog = {r["chapter_index"]: r for r in rows}
    for i, ch in enumerate(chapters):
        p = prog.get(i)
        if p and p["answered"] > 0:
            pct = round(p["correct"] / p["answered"] * 100)
            status = "已掌握" if pct >= 80 else "学习中"
        else:
            pct = 0
            status = "未开始"
        ch["answered"] = p["answered"] if p else 0
        ch["correct"] = p["correct"] if p else 0
        ch["pct"] = pct
        ch["status"] = status
    return {"id": rid, "created_at": row["created_at"], "topic": row["topic"], "chapters": chapters,
            "material_id": row["material_id"]}


def list_roadmaps() -> list:
    """列出所有学习路线（含章节数与总掌握度）"""
    conn = _conn()
    rows = conn.execute(
        "SELECT id, created_at, topic, material_id, chapters FROM roadmaps ORDER BY id DESC LIMIT 50"
    ).fetchall()
    # 每条的章节进度聚合
    prog_rows = conn.execute(
        "SELECT roadmap_id, SUM(answered) AS total, SUM(correct) AS correct FROM chapter_progress GROUP BY roadmap_id"
    ).fetchall()
    conn.close()
    prog = {r["roadmap_id"]: r for r in prog_rows}
    out = []
    for r in rows:
        chapters = json.loads(r["chapters"])
        p = prog.get(r["id"])
        total = p["total"] if p else 0
        correct = p["correct"] if p else 0
        out.append({
            "id": r["id"],
            "created_at": r["created_at"],
            "topic": r["topic"],
            "is_project": 1 if r["material_id"] else 0,
            "chapters": len(chapters),
            "total": total,
            "correct": correct,
            "pct": round(correct / total * 100) if total else 0,
        })
    return out


def delete_roadmap(rid: int):
    conn = _conn()
    conn.execute("DELETE FROM roadmaps WHERE id=?", (rid,))
    conn.execute("DELETE FROM chapter_progress WHERE roadmap_id=?", (rid,))
    conn.commit()
    conn.close()


def report_progress(rid: int, chapter_index: int, total: int, correct: int):
    conn = _conn()
    conn.execute(
        "INSERT INTO chapter_progress (roadmap_id, chapter_index, answered, correct) VALUES (?,?,?,?) "
        "ON CONFLICT(roadmap_id, chapter_index) DO UPDATE SET "
        "answered = answered + ?, correct = correct + ?",
        (rid, chapter_index, total, correct, total, correct),
    )
    conn.commit()
    conn.close()
