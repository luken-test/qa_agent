"""节点：意图路由

直接使用调用方（前端/CLI）指定的 task_type 和 input_type，
不再通过关键词猜测意图，避免误判。
"""

import os

from state import WorkflowState
from utils.logger import get_logger

logger = get_logger("router")


async def router_node(state: WorkflowState) -> dict:
    """路由节点

    从 state 中读取 task_type 和 input_type，确定输入来源类型。
    task_type 由调用方（前端 API / CLI）明确指定，不做关键词推断。
    """
    url = state.get("url", "")
    file_path = state.get("file_path", "")
    raw_text = state.get("raw_text", "")
    task_type = state.get("task_type", "chat")

    # 确定 input_type
    if url and url.startswith("http"):
        input_type = "url"
    elif file_path and os.path.exists(file_path):
        input_type = "file"
    elif raw_text and raw_text.strip().startswith(("http://", "https://")):
        # raw_text 是 URL，修正为 url 输入
        input_type = "url"
        url = raw_text.strip()
    else:
        input_type = "text"

    logger.info(f"任务类型: {task_type}, 输入类型: {input_type}")
    result = {"task_type": task_type, "input_type": input_type}
    if input_type == "url" and url:
        result["url"] = url
    return result
