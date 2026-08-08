# -*- coding: utf-8 -*-
"""AI 出题引擎：根据主题生成选择题，并支持判题与讲解"""

import json
import re

from openai import OpenAI
from app.secret import DEEPSEEK_API_KEY, BASE_URL, MODEL

_client = None


def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=BASE_URL)
    return _client


def _clean_option(text) -> str:
    """去掉选项里自带的前缀（如 'A. 硬盘' -> '硬盘'），兼容 . 、 ： 等分隔符"""
    if not text:
        return ""
    return re.sub(r"^[A-Da-d][.、:：)\s]+\s*", "", text.strip()).strip()


def _extract_json(text):
    """从模型输出中提取 JSON（兼容 markdown 代码块 / 前后夹杂文字的情况）"""
    if not text:
        raise ValueError("模型返回内容为空")
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except Exception:
        # 尝试截取第一个 [ 或 { 到最后一个 ] 或 } 之间的内容再解析
        for open_c, close_c in (("[", "]"), ("{", "}")):
            i, j = text.find(open_c), text.rfind(close_c)
            if i >= 0 and j > i:
                try:
                    return json.loads(text[i:j + 1])
                except Exception:
                    continue
        raise


def generate_quiz(topic: str, num: int = 5, difficulty: str = "混合", material: str | None = None) -> list:
    """根据主题（或项目材料）生成 num 道选择题。返回:
    [{question, options: [A..], answer: "A", explanation}, ...]
    material: 候选人的项目内容（README/源码），用于面试模拟出题。
    """
    client = get_client()
    if material:
        scope = (
            "以下是候选人的项目内容（README / 源码 / 说明），请围绕这个项目出题，"
            "考察候选人对该项目设计思路、关键实现、技术选型、潜在问题的理解：\n\n"
            f"===== 项目内容 =====\n{material[:6000]}\n===== 项目内容结束 =====\n\n"
        )
        prompt_head = "你是一名资深技术面试官，正在模拟面试一位候选人，请根据他的项目内容出高质量选择题来拷问他。\n"
    else:
        scope = ""
        prompt_head = "你是一名资深出题专家，擅长出高质量选择题。主题可以是任何领域（技术、娱乐、游戏、生活、常识等）。\n"
    prompt = prompt_head + scope + (
        f"请围绕「{topic}」出 {num} 道选择题，难度：{difficulty}。\n"
        "要求：\n"
        "1. 题目必须直接围绕主题「" + topic + "」出题，绝不跑题；娱乐/游戏等主题就出该领域的题目\n"
        "2. 题目必须准确、有区分度，错误选项要有迷惑性（不能太傻）\n"
        "3. 覆盖概念、原理、应用场景，尽量由浅入深\n"
        "4. 每题都要有解析（explanation），讲清为什么对、错在哪，100-200字\n"
        '4. 输出一个 JSON 对象，格式：\n'
        '{"questions": [{"question": "题干", "options": ["选项A文本","选项B文本","选项C文本","选项D文本"], '
        '"answer": "A", "explanation": "解析"}]}\n'
        "answer 只能是 A/B/C/D 之一。只输出 JSON，不要输出任何其他文字。"
    )
    # 调用模型并解析，失败自动重试一次（DeepSeek 偶尔返回不合法 JSON）
    last_err = None
    for attempt in range(2):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=8192,
                response_format={"type": "json_object"},
            )
            data = _extract_json(resp.choices[0].message.content)
            if "questions" in data:
                data = data["questions"]
            # 规范化字段
            out = []
            for i, q in enumerate(data):
                if not isinstance(q, dict):
                    continue
                opts = q.get("options", [])
                if isinstance(opts, dict):
                    opts = [opts.get(k, "") for k in "ABCD" if opts.get(k)]
                opts = [_clean_option(o) for o in opts]
                out.append({
                    "id": i + 1,
                    "question": q.get("question", ""),
                    "options": list(opts)[:4],
                    "answer": q.get("answer", "").strip().upper(),
                    "explanation": q.get("explanation", ""),
                })
            if out:
                return out
            last_err = "模型未返回有效题目"
        except Exception as e:
            last_err = str(e)[:200]
    raise RuntimeError(f"AI 出题失败（已自动重试一次）：{last_err}")


def generate_essay(topic: str, num: int = 3, difficulty: str = "混合", material: str | None = None) -> list:
    """生成简答题（面试风格）。返回 [{question, reference}]，reference 为参考答案要点。"""
    client = get_client()
    if material:
        scope = (
            "以下是候选人的项目内容，请围绕项目出简答题，考察设计思路与实现细节：\n\n"
            f"===== 项目内容 =====\n{material[:6000]}\n===== 项目内容结束 =====\n\n"
        )
        head = "你是一名资深技术面试官，正在模拟面试，请根据候选人的项目内容出简答题。\n"
    else:
        scope = ""
        head = "你是一名资深出题专家，擅长出面试简答题。主题可以是任何领域（技术、娱乐、游戏、生活等）。\n"
    prompt = head + scope + (
        f"请围绕「{topic}」出 {num} 道简答题，难度：{difficulty}。\n"
        "要求：\n"
        "1. 题目必须直接围绕主题「" + topic + "」出题，绝不跑题；娱乐/游戏等主题就出该领域的题目\n"
        "2. 题目是典型面试问法（解释概念 / 讲设计思路 / 处理场景问题，不限于技术）\n"
        "3. 每题附带参考答案要点（reference），列出答到哪些点算合格\n"
        '3. 只输出 JSON 对象：{"questions": [{"question": "题干", "reference": "参考答案要点"}]}\n'
        "只输出 JSON，不要任何其他文字。"
    )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )
    data = _extract_json(resp.choices[0].message.content)
    qs = data.get("questions", [])
    out = []
    for i, q in enumerate(qs):
        out.append({
            "id": i + 1,
            "question": q["question"],
            "reference": q.get("reference", ""),
        })
    return out


def grade_essay(question: dict, user_answer: str) -> dict:
    """AI 评分简答题：返回 score(0-100) + comment + reference"""
    client = get_client()
    prompt = (
        "你是一名严格的面试官。候选人回答了下面的技术简答题，请评分。\n"
        f"题目：{question['question']}\n"
        f"参考答案要点：{question.get('reference', '')}\n"
        f"候选人回答：{user_answer}\n"
        "请输出：1) score：0-100 的整数；2) comment：100-200 字评语，指出优点、"
        "不足、遗漏的关键点；3) reference：参考答案要点。\n"
        '只输出 JSON 对象：{"score": 0, "comment": "", "reference": ""}'
    )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    data = _extract_json(resp.choices[0].message.content)
    return {
        "score": int(data.get("score", 0)),
        "comment": data.get("comment", ""),
        "reference": data.get("reference", question.get("reference", "")),
    }


def explain_wrong(question: dict, user_answer: str) -> str:
    """针对性答疑：针对用户选错的选项，解释为什么不对、为什么正确答案才对。"""
    client = get_client()
    letters = "ABCD"
    picked_text = ""
    for i, opt in enumerate(question.get("options", [])):
        if letters[i] == user_answer.strip().upper():
            picked_text = opt
    prompt = (
        "你是耐心的技术面试官。候选人在选择题里选了错误答案，请你针对性地讲解。\n"
        f"题目：{question['question']}\n"
        f"候选人选的：{user_answer} - {picked_text or '（未知）'}\n"
        f"正确答案：{question['answer']}\n"
        "请用 150-250 字讲清楚：1) 候选人选的选项为什么不对（指出其中的错误理解）；"
        "2) 正确答案为什么对；3) 给一个记忆要点。语气鼓励，别打击。"
    )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=1024,
    )
    return resp.choices[0].message.content


def grade(question: dict, user_answer: str) -> dict:
    """判题：返回是否正确 + 解析"""
    ua = (user_answer or "").strip().upper()
    correct = ua == question["answer"]
    # 根据正确性给讲解语气
    if correct:
        tip = "✅ 回答正确！"
    else:
        tip = f"❌ 回答错误（正确答案是 {question['answer']}）。"
    return {
        "correct": correct,
        "user_answer": ua,
        "right_answer": question["answer"],
        "tip": tip,
        "explanation": question["explanation"],
    }









def suggest_topics(hint: str, num: int = 6) -> list:
    """AI 推荐相关学习主题：输入方向描述，返回 [{topic, category}]"""
    client = get_client()
    prompt = (
        f"用户想准备的主题方向：{hint}\n"
        f"请推荐 {num} 个具体、可出题的学习主题，覆盖该方向下的不同子领域。\n"
        '只输出 JSON 数组，格式：[{"topic": "具体主题", "category": "所属分类"}]\n'
        "不要输出任何其他文字。"
    )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024,
    )
    data = _extract_json(resp.choices[0].message.content)
    out = []
    for i, t in enumerate(data[:num]):
        out.append({
            "id": i + 1,
            "topic": t.get("topic", ""),
            "category": t.get("category", "AI 推荐"),
        })
    return out
