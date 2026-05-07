"""节点：内容提取

从 URL、本地文件或直接文字中提取需求内容。
所有后续节点都依赖这个节点产出的 raw_content。
"""

from state import WorkflowState
from tools.browser import extract_from_url, extract_from_file
from utils.logger import get_logger

logger = get_logger("extract")


async def extract_node(state: WorkflowState) -> dict:
    """内容提取节点

    根据 input_type 决定提取方式：
    - url: 通过 Playwright MCP 从网页提取
    - file: 读取本地文件
    - text: 直接使用用户输入的文字
    """
    input_type = state.get("input_type", "text")
    url = state.get("url", "")
    file_path = state.get("file_path", "")
    raw_text = state.get("raw_text", "")

    try:
        if input_type == "url":
            # 优先用 router 修正后的 url，否则取 raw_text
            target_url = url or raw_text.strip()
            logger.info(f"从 URL 提取内容: {target_url}")
            content = await extract_from_url(target_url)
        elif input_type == "file":
            logger.info(f"从文件提取内容: {file_path}")
            content = await extract_from_file(file_path)
        else:
            logger.info(f"直接使用文本输入，长度: {len(raw_text)}")
            content = raw_text

        if not content:
            return {"error": "未能提取到内容，页面可能需要登录或文件为空"}

        logger.info(f"内容提取完成，长度: {len(content)} 字符")
        return {"raw_content": content}

    except Exception as e:
        logger.error(f"内容提取失败: {e}")
        return {"error": f"内容提取失败: {e}"}
