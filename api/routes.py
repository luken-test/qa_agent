"""FastAPI 路由定义

定义测试工程师智能体的 REST API 接口。
每个接口对应一种任务类型，支持同步和异步执行。
"""

import asyncio
import os
import time
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from graph import build_workflow
from state import WorkflowState
from utils.logger import get_logger

logger = get_logger("api")

router = APIRouter(prefix="/api", tags=["测试工程师智能体"])

# 全局任务状态存储（生产环境应替换为 Redis/数据库）
task_store: dict = {}


# ========== 请求体模型 ==========

class TestcaseRequest(BaseModel):
    input: str
    input_type: str = "text"
    model: Optional[str] = None
    thread_id: Optional[str] = None


class BugRequest(BaseModel):
    description: str
    screenshots: Optional[list[str]] = []
    model: Optional[str] = None
    thread_id: Optional[str] = None


class ExecuteRequest(BaseModel):
    testcases_json: str
    model: Optional[str] = None
    thread_id: Optional[str] = None


class JMeterRequest(BaseModel):
    input: str
    input_type: str = "text"
    model: Optional[str] = None
    thread_id: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None
    thread_id: Optional[str] = None


class QARequest(BaseModel):
    question: str
    model: Optional[str] = None
    thread_id: Optional[str] = None


# ========== 辅助函数 ==========

def _build_initial_state(task_type: str, **kwargs) -> dict:
    """构建工作流初始状态的通用方法"""
    state = {
        "task_type": task_type,
        "input_type": kwargs.get("input_type", "text"),
        "url": kwargs.get("url", ""),
        "file_path": kwargs.get("file_path", ""),
        "raw_text": kwargs.get("raw_text", ""),
        "screenshot_paths": kwargs.get("screenshot_paths", []),
        "raw_content": "", "analysis": "", "project_name": "",
        "testcases_json": "", "bug_report_md": "", "test_script": "",
        "execution_result": "", "jmx_script": "", "output_xmind": "",
        "output_json": "", "output_bug_md": "", "output_script": "",
        "output_jmx": "", "rag_context": "",
        "error": None, "model_name": "", "chat_response": "",
    }
    return state


async def _run_workflow(task_id: str, initial_state: dict, thread_id: str = None):
    """异步执行工作流并更新任务状态"""
    import os
    model = initial_state.pop("_model", None)
    if model:
        if ":" in model:
            provider, model_name = model.split(":", 1)
            os.environ["LLM_PROVIDER"] = provider
            provider_model_map = {
                "zhipu": "ZHIPU_MODEL",
                "claude": "CLAUDE_MODEL",
                "openai": "OPENAI_MODEL",
            }
            env_key = provider_model_map.get(provider)
            if env_key:
                os.environ[env_key] = model_name
            initial_state["model_name"] = model_name
        else:
            os.environ["LLM_PROVIDER"] = model
            initial_state["model_name"] = model

        import importlib
        import config
        importlib.reload(config)

    if not initial_state.get("model_name"):
        import config
        provider = os.environ.get("LLM_PROVIDER", "zhipu")
        model_key = {"zhipu": "ZHIPU_MODEL", "claude": "CLAUDE_MODEL", "openai": "OPENAI_MODEL"}.get(provider)
        initial_state["model_name"] = getattr(config, model_key, provider) if model_key else provider

    task_store[task_id]["status"] = "running"
    t0 = time.time()
    task_type = initial_state.get("task_type", "unknown")
    logger.info(f"[{task_id}] 开始执行工作流, 类型={task_type}, 模型={initial_state.get('model_name', 'unknown')}")
    try:
        app = build_workflow()
        config_kw = {}
        if thread_id:
            config_kw["configurable"] = {"thread_id": thread_id}
        result = await app.ainvoke(initial_state, config=config_kw)
        task_store[task_id]["status"] = "completed"
        task_store[task_id]["result"] = result
        elapsed = time.time() - t0
        has_error = bool(result.get("error"))
        logger.info(f"[{task_id}] 工作流完成, 耗时={elapsed:.1f}s, 错误={has_error}")
    except Exception as e:
        task_store[task_id]["status"] = "failed"
        task_store[task_id]["error"] = str(e)
        elapsed = time.time() - t0
        logger.error(f"[{task_id}] 工作流异常, 耗时={elapsed:.1f}s, 错误={e}")


# ========== API 端点 ==========

@router.post("/testcases")
async def generate_testcases(req: TestcaseRequest, bg: BackgroundTasks):
    """生成测试用例（异步任务）"""
    task_id = str(uuid.uuid4())[:8]

    # 根据输入类型构建状态
    if req.input_type == "url":
        state = _build_initial_state("testcase", input_type="url", url=req.input)
    elif req.input_type == "file":
        state = _build_initial_state("testcase", input_type="file", file_path=req.input)
    else:
        state = _build_initial_state("testcase", input_type="text", raw_text=req.input)

    state["_model"] = req.model
    task_store[task_id] = {"status": "pending", "type": "testcase"}

    bg.add_task(_run_workflow, task_id, state, req.thread_id)
    return {"task_id": task_id, "status": "pending", "thread_id": req.thread_id}


@router.post("/bug")
async def generate_bug(req: BugRequest, bg: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]
    state = _build_initial_state(
        "bug", input_type="text",
        raw_text=req.description,
        screenshot_paths=req.screenshots,
    )
    state["_model"] = req.model
    task_store[task_id] = {"status": "pending", "type": "bug"}

    bg.add_task(_run_workflow, task_id, state, req.thread_id)
    return {"task_id": task_id, "status": "pending", "thread_id": req.thread_id}


@router.post("/execute")
async def execute_tests(req: ExecuteRequest, bg: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]
    state = _build_initial_state("execute", input_type="text", raw_text="")
    state["testcases_json"] = req.testcases_json
    state["_model"] = req.model
    task_store[task_id] = {"status": "pending", "type": "execute"}

    bg.add_task(_run_workflow, task_id, state, req.thread_id)
    return {"task_id": task_id, "status": "pending", "thread_id": req.thread_id}


@router.post("/jmeter")
async def generate_jmeter(req: JMeterRequest, bg: BackgroundTasks):
    """生成 JMeter 脚本（异步任务）"""
    task_id = str(uuid.uuid4())[:8]

    # 根据输入类型构建状态
    if req.input_type == "file":
        state = _build_initial_state("jmeter", input_type="file", file_path=req.input)
    else:
        state = _build_initial_state("jmeter", input_type="text", raw_text=req.input)

    state["_model"] = req.model
    task_store[task_id] = {"status": "pending", "type": "jmeter"}

    bg.add_task(_run_workflow, task_id, state, req.thread_id)
    return {"task_id": task_id, "status": "pending", "thread_id": req.thread_id}


@router.post("/chat")
async def chat(req: ChatRequest, bg: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]
    state = _build_initial_state("chat", input_type="text", raw_text=req.message)
    state["_model"] = req.model
    task_store[task_id] = {"status": "pending", "type": "chat"}

    bg.add_task(_run_workflow, task_id, state, req.thread_id)
    return {"task_id": task_id, "status": "pending", "thread_id": req.thread_id}


@router.post("/qa")
async def qa(req: QARequest, bg: BackgroundTasks):
    """测试知识智能问答（限定互联网 IT 领域）"""
    task_id = str(uuid.uuid4())[:8]
    state = _build_initial_state("qa", input_type="text", raw_text=req.question)
    state["_model"] = req.model
    task_store[task_id] = {"status": "pending", "type": "qa"}

    bg.add_task(_run_workflow, task_id, state, req.thread_id)
    return {"task_id": task_id, "status": "pending", "thread_id": req.thread_id}


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """查询异步任务状态"""
    if task_id not in task_store:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task_store[task_id]


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "测试工程师智能体"}


@router.get("/tasks")
async def get_all_tasks():
    """获取所有任务列表"""
    return [
        {"task_id": tid, **info}
        for tid, info in task_store.items()
    ]


@router.get("/threads")
async def get_all_threads():
    """获取所有会话列表"""
    from graph import get_checkpointer
    checkpointer = get_checkpointer()
    try:
        # 列出所有 thread_id
        threads = {}
        for task_id, info in task_store.items():
            tid = info.get("thread_id")
            if tid and info.get("status") == "completed" and info.get("result"):
                result = info["result"]
                raw = result.get("raw_text", "") or result.get("raw_content", "")
                title = raw[:50] if raw else f"任务 {task_id}"
                threads[tid] = {
                    "thread_id": tid,
                    "title": title,
                    "type": info.get("type", ""),
                    "task_id": task_id,
                }
        return list(threads.values())
    except Exception as e:
        return []


@router.get("/history/{thread_id}")
async def get_thread_history(thread_id: str):
    """获取某个会话的历史状态"""
    from graph import get_checkpointer
    checkpointer = get_checkpointer()
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state_history = list(checkpointer.list(config))
        if not state_history:
            return {"messages": [], "thread_id": thread_id}
        # 获取最新状态
        latest = state_history[-1]
        state = latest.checkpoint.get("channel_values", {})
        return {
            "thread_id": thread_id,
            "state": {
                "raw_text": state.get("raw_text", ""),
                "jmx_script": state.get("jmx_script", ""),
                "output_jmx": state.get("output_jmx", ""),
                "testcases_json": state.get("testcases_json", ""),
                "bug_report_md": state.get("bug_report_md", ""),
                "chat_response": state.get("chat_response", ""),
                "error": state.get("error"),
                "project_name": state.get("project_name", ""),
            },
        }
    except Exception as e:
        return {"messages": [], "thread_id": thread_id, "error": str(e)}


@router.get("/download/{filename}")
async def download_file(filename: str):
    """下载生成的文件"""
    from fastapi.responses import FileResponse
    from config import OUTPUT_DIR

    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(filepath, filename=filename)
