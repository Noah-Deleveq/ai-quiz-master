# -*- coding: utf-8 -*-
"""AI 面试官：生成题目、点评与追问、总结报告"""

import json

from app.quiz import get_client, _extract_json, MODEL


def start_interview(role: str, resume: str = "") -> list:
    """根据岗位+简历生成面试题目列表。返回 [{text, type}]"""
    client = get_client()
    resume_part = f"\n候选人简历/项目内容：\n{resume[:4000]}\n" if resume.strip() else "\n（候选人未提供简历，按通用岗位要求提问）\n"
    prompt = (
        "你是一名资深技术面试官。\n"
        f"目标岗位：{role}\n{resume_part}"
        "请生成 5 道面试题目：\n"
        "1. 第 1 题固定为：请先做一个简短的自我介绍（1-2 分钟）\n"
        "2. 第 2-3 题：深挖候选人简历/项目中的关键点（若无简历，改为岗位相关基础问题）\n"
        "3. 第 4 题：岗位技术知识题（结合该岗位的核心技能）\n"
        "4. 第 5 题：行为/软技能题（如：讲一次你解决棘手问题的经历）\n"
        '只输出 JSON 对象：{"questions": [{"text": "题目", "type": "自我介绍|项目深挖|技术题|行为题"}]}\n'
        "题目要专业、有区分度，贴合岗位。不要输出任何其他文字。"
    )
    last_err = None
    for _ in range(2):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2048,
                response_format={"type": "json_object"},
            )
            data = _extract_json(resp.choices[0].message.content)
            qs = data.get("questions") if isinstance(data, dict) else data
            out = []
            for i, q in enumerate(qs):
                if isinstance(q, dict) and q.get("text"):
                    out.append({
                        "index": i + 1,
                        "text": q["text"],
                        "type": q.get("type", "面试题"),
                    })
            if out:
                if not out[0]["text"].startswith(("请先", "自我介绍")):
                    out.insert(0, {"index": 1, "text": "请先做一个简短的自我介绍（1-2 分钟）", "type": "自我介绍"})
                for idx, q in enumerate(out):
                    q["index"] = idx + 1
                return out
        except Exception as e:
            last_err = str(e)[:200]
    raise RuntimeError(f"AI 生成面试题失败（已重试）：{last_err}")


def evaluate_answer(role: str, question: dict, answer: str) -> dict:
    """点评回答 + 决定是否追问。返回 {comment, score, follow_up}"""
    client = get_client()
    prompt = (
        "你是一名资深技术面试官。\n"
        f"岗位：{role}\n"
        f"当前问题（{question.get('type', '面试题')}）：{question['text']}\n"
        f"候选人的回答：{answer}\n\n"
        "请以面试官口吻做两件事：\n"
        "1. comment：简短点评（先肯定亮点，再指出不足，2-3 句，中文）\n"
        "2. score：给这个回答打 0-100 分\n"
        "3. follow_up：如果回答明显太浅、跑题或有漏洞，给 1 个追问（不能重复原问题）；如果回答充分，填 null\n"
        '只输出 JSON：{"comment": "", "score": 0, "follow_up": null}\n'
        "不要输出任何其他文字。"
    )
    last_err = None
    for _ in range(2):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            data = _extract_json(resp.choices[0].message.content)
            score = data.get("score", 0)
            return {
                "comment": data.get("comment", ""),
                "score": int(score) if isinstance(score, (int, float)) else 0,
                "follow_up": data.get("follow_up") or None,
            }
        except Exception as e:
            last_err = str(e)[:200]
    raise RuntimeError(f"AI 点评失败（已重试）：{last_err}")


def generate_report(role: str, history: list) -> str:
    """根据完整面试记录生成评估报告（Markdown）。history: [{q, a, comment, score}, ...]"""
    client = get_client()
    lines = []
    for i, h in enumerate(history, 1):
        lines.append(f"第{i}题（{h.get('type', '')}）：{h['q']}\n候选人回答：{h['a']}\n点评：{h.get('comment', '')}\n得分：{h.get('score', '-')}")
    record = "\n\n".join(lines)
    prompt = (
        "你是资深技术面试官，请根据下面的面试记录，为候选人生成一份完整的面试评估报告（Markdown 格式，中文）：\n"
        f"目标岗位：{role}\n\n===== 面试记录 =====\n{record}\n===== 记录结束 =====\n\n"
        "报告结构：\n"
        "## 面试总评（2-3 句整体印象与结论）\n"
        "## 分维度评估（用表格：维度 | 得分 | 评语；维度：技术深度、项目/经验匹配度、表达能力、逻辑思维、学习潜力）\n"
        "## 各题表现（每题：得分、表现亮点、不足）\n"
        "## 改进建议（3-5 条具体可执行的建议）\n"
        "## 岗位匹配度结论（是否建议进入下一轮，一句话）\n"
        "只输出 Markdown 报告本身。"
    )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=2048,
    )
    return resp.choices[0].message.content
