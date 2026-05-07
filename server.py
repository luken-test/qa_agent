"""测试工程师智能体 —— FastAPI 服务入口

启动 API 服务：
  python server.py

访问 API 文档：
  http://localhost:8000/docs
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import router


@asynccontextmanager
async def lifespan(app):
    """应用生命周期：启动时初始化 checkpointer，关闭时清理"""
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    from graph import setup_checkpointer

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qa_agent.db")
    async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
        setup_checkpointer(checkpointer)
        yield


app = FastAPI(
    title="测试工程师智能体",
    description="基于 LangGraph 的多能力测试 AI，支持测试用例生成、Bug 单生成、测试脚本执行",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

dist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "dist")
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")


if __name__ == "__main__":
    print("启动测试工程师智能体 API 服务...")
    print("API 文档: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
# cd "e:/测试用例/qa-agent" && "E:/code/im_test_tools/yunxin-mcp-server-main/.venv/Scripts/python.exe" server.py