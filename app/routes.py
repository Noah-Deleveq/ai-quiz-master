# -*- coding: utf-8 -*-
"""API 路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app import quiz
from app import interview, history, materials, roadmap

router = APIRouter()


class GenReq(BaseModel):
    topic: str
    num: int = 5
    difficulty: str = "混合"
    material_id: int | None = None


class GradeReq(BaseModel):
    question: dict
    answer: str


@router.post("/quiz/generate")
def generate(req: GenReq):
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(400, "请输入想学习的主题")
    if not (1 <= req.num <= 10):
        raise HTTPException(400, "题目数量需在 1-10 之间")
    material = None
    if req.material_id is not None:
        m = materials.get_material(req.material_id)
        if m is None:
            raise HTTPException(404, "项目材料不存在")
        material = m["content"]
    try:
        return {"questions": quiz.generate_quiz(topic, req.num, req.difficulty, material)}
    except Exception as e:
        raise HTTPException(500, f"出题失败: {e}")


@router.post("/quiz/grade")
def grade(req: GradeReq):
    try:
        return quiz.grade(req.question, req.answer)
    except Exception as e:
        raise HTTPException(500, f"判题失败: {e}")


class SaveReq(BaseModel):
    topic: str
    difficulty: str = ""
    questions: list


class EssayGenReq(BaseModel):
    topic: str
    num: int = 3
    difficulty: str = "混合"
    material_id: int | None = None


class EssayGradeReq(BaseModel):
    question: dict
    answer: str


class ExplainReq(BaseModel):
    question: dict
    answer: str


@router.post("/quiz/essay/generate")
def essay_generate(req: EssayGenReq):
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(400, "请输入想学习的主题")
    if not (1 <= req.num <= 10):
        raise HTTPException(400, "题目数量需在 1-10 之间")
    material = None
    if req.material_id is not None:
        m = materials.get_material(req.material_id)
        if m is None:
            raise HTTPException(404, "项目材料不存在")
        material = m["content"]
    try:
        return {"questions": quiz.generate_essay(topic, req.num, req.difficulty, material)}
    except Exception as e:
        raise HTTPException(500, f"出题失败: {e}")


@router.post("/quiz/essay/grade")
def essay_grade(req: EssayGradeReq):
    try:
        return quiz.grade_essay(req.question, req.answer)
    except Exception as e:
        raise HTTPException(500, f"评分失败: {e}")


@router.post("/quiz/explain")
def explain(req: ExplainReq):
    try:
        return {"explanation": quiz.explain_wrong(req.question, req.answer)}
    except Exception as e:
        raise HTTPException(500, f"讲解失败: {e}")


@router.post("/quiz/save")
def save(req: SaveReq):
    hid = history.save_session(req.topic, req.difficulty, req.questions)
    return {"ok": True, "id": hid}


class RoadmapReq(BaseModel):
    topic: str
    material_id: int | None = None


class ReportReq(BaseModel):
    chapter_index: int
    total: int
    correct: int


@router.post("/roadmap/generate")
def roadmap_generate(req: RoadmapReq):
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(400, "请输入主题")
    material = None
    if req.material_id is not None:
        m = materials.get_material(req.material_id)
        if m is None:
            raise HTTPException(404, "项目材料不存在")
        material = m["content"]
    try:
        rid = roadmap.create_roadmap(topic, material, req.material_id)
        return roadmap.get_roadmap(rid)
    except Exception as e:
        raise HTTPException(500, f"生成学习路线失败: {e}")


@router.get("/roadmaps")
def roadmap_list():
    return {"items": roadmap.list_roadmaps()}


@router.delete("/roadmap/{rid}")
def roadmap_delete(rid: int):
    roadmap.delete_roadmap(rid)
    return {"ok": True}


@router.get("/roadmap/{rid}")
def roadmap_detail(rid: int):
    item = roadmap.get_roadmap(rid)
    if item is None:
        raise HTTPException(404, "学习路线不存在")
    return item


@router.post("/roadmap/{rid}/report")
def roadmap_report(rid: int, req: ReportReq):
    if roadmap.get_roadmap(rid) is None:
        raise HTTPException(404, "学习路线不存在")
    roadmap.report_progress(rid, req.chapter_index, req.total, req.correct)
    return roadmap.get_roadmap(rid)


class UploadReq(BaseModel):
    name: str
    content: str


@router.post("/materials")
def upload_material(req: UploadReq):
    name = req.name.strip()
    content = req.content.strip()
    if not name or not content:
        raise HTTPException(400, "项目名称和内容不能为空")
    mid = materials.save_material(name, content)
    return {"ok": True, "id": mid}


@router.get("/materials")
def get_materials():
    return {"items": materials.list_materials()}


@router.delete("/materials/{mid}")
def delete_material(mid: int):
    materials.delete_material(mid)
    return {"ok": True}


@router.get("/stats")
def get_stats():
    return history.stats()


@router.get("/history")
def get_history():
    return {"items": history.list_sessions()}


@router.delete("/history/by-topic/{topic}")
def delete_history_topic(topic: str):
    """删除某主题的全部答题会话（学习统计主题清零）"""
    history.delete_topic(topic)
    return {"ok": True}


@router.get("/history/{hid}")
def get_history_detail(hid: int):
    item = history.get_session(hid)
    if item is None:
        raise HTTPException(404, "记录不存在")
    return item


@router.delete("/history/{hid}")
def delete_history(hid: int):
    history.delete_session(hid)
    return {"ok": True}








class SuggestReq(BaseModel):
    hint: str


@router.post("/topics/suggest")
def topics_suggest(req: SuggestReq):
    """AI 生成相关主题（各行各业）"""
    if not req.hint.strip():
        raise HTTPException(400, "请输入想准备的方向")
    try:
        return {"topics": quiz.suggest_topics(req.hint.strip())}
    except Exception as e:
        raise HTTPException(500, f"AI 生成失败：{e}")


class InterviewStartReq(BaseModel):
    role: str
    resume: str = ""


class InterviewAnswerReq(BaseModel):
    role: str
    question: dict
    answer: str


class InterviewReportReq(BaseModel):
    role: str
    history: list


@router.post("/interview/start")
def interview_start(req: InterviewStartReq):
    if not req.role.strip():
        raise HTTPException(400, "请填写目标岗位")
    try:
        return {"questions": interview.start_interview(req.role.strip(), req.resume)}
    except Exception as e:
        raise HTTPException(500, f"生成面试题失败: {e}")


@router.post("/interview/answer")
def interview_answer(req: InterviewAnswerReq):
    if not req.answer.strip():
        raise HTTPException(400, "回答不能为空")
    try:
        return interview.evaluate_answer(req.role, req.question, req.answer.strip())
    except Exception as e:
        raise HTTPException(500, f"点评失败: {e}")


@router.post("/interview/report")
def interview_report(req: InterviewReportReq):
    try:
        return {"report": interview.generate_report(req.role, req.history)}
    except Exception as e:
        raise HTTPException(500, f"生成报告失败: {e}")

