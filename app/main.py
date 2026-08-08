# -*- coding: utf-8 -*-
"""AI 出题官入口"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import router

app = FastAPI(title="AI 出题官")
app.include_router(router)


class NoCacheStaticFiles(StaticFiles):
    """静态文件禁用缓存，开发期保证前端改动立即生效"""

    def file_response(self, *args, **kwargs):
        resp = super().file_response(*args, **kwargs)
        resp.headers["Cache-Control"] = "no-store"
        return resp


app.mount("/", NoCacheStaticFiles(directory="app/static", html=True), name="static")

