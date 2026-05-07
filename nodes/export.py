"""节点：Xmind 导出

通过 MCP 调用 xmind-generator 工具，将测试用例 JSON 转换为 Xmind 文件。
导出是附加功能，失败不影响测试用例本身的展示和下载。
"""

from state import WorkflowState
from tools.xmind import generate_xmind
from utils.logger import get_logger

logger = get_logger("export")


async def export_node(state: WorkflowState) -> dict:
    """Xmind 导出节点"""
    testcases_json = state.get("testcases_json", "")

    if not testcases_json:
        return {}

    try:
        logger.info("正在通过 MCP 生成 Xmind 文件...")
        result = await generate_xmind(testcases_json)
        logger.info(f"Xmind 文件生成完成: {result}")
        return {"output_xmind": result}

    except Exception as e:
        logger.warning(f"Xmind 导出失败（不影响测试用例）: {e}")
        return {}
