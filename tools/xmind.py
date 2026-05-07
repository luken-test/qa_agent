"""工具：Xmind MCP 文件生成

通过 MCP 协议调用 xmind-generator 生成思维导图文件。
将测试用例 JSON 结构转换为 Xmind 文件。
"""

import json
import re
from langchain_mcp_adapters.client import MultiServerMCPClient

from config import MCP_SERVERS
from utils.logger import get_logger

logger = get_logger("xmind")


def _convert_topics(topics: list) -> list:
    """将 LLM 输出的 topics 结构转换为 Xmind MCP 要求的 title/topics 格式

    支持两种输入结构：
    1. 测试用例结构：每个 item 有 title 和 children（5 层嵌套）
    2. 分析结构：每个 item 有 fields、linkage_rules 等字段
    """
    result = []
    for item in topics:
        title = item.get("title") or item.get("name") or "未命名"
        children = []

        # 优先处理 children（测试用例的 5 层嵌套结构）
        if "children" in item:
            children = _convert_topics(item["children"])

        # 兼容旧的 fields 结构
        for field in item.get("fields", []):
            field_title = field.get("name", "未命名字段")
            details = []
            if field.get("type"):
                details.append(f"类型: {field['type']}")
            if field.get("required"):
                details.append("必填")
            if field.get("default"):
                details.append(f"默认: {field['default']}")
            if field.get("enum_values"):
                details.append(f"可选: {', '.join(field['enum_values'])}")
            child = {"title": field_title}
            if details:
                child["note"] = "\n".join(details)
            children.append(child)

        for rule in item.get("linkage_rules", []):
            children.append({"title": f"联动规则: {rule}"})

        converted = {"title": title}
        if item.get("description"):
            converted["note"] = item["description"]
        if children:
            converted["children"] = children
        result.append(converted)
    return result


async def generate_xmind(testcases_json: str) -> str:
    """调用 Xmind Generator MCP 生成 Xmind 文件

    Returns:
        xmind 文件的绝对路径
    """
    data = json.loads(testcases_json)

    topics = _convert_topics(data.get("topics", []))

    # 调试：确认转换后的结构是否包含子节点
    logger.info(f"转换后 topics 数量: {len(topics)}")
    for i, t in enumerate(topics):
        has_sub = "children" in t
        sub_count = len(t.get("children", []))
        logger.info(f"  topic[{i}]: title={t.get('title')}, 有子节点={has_sub}, 子节点数={sub_count}")

    client = MultiServerMCPClient({"xmind-generator": MCP_SERVERS["xmind-generator"]})
    tools = {t.name: t for t in await client.get_tools()}

    gen_tool = tools["generate-mind-map"]

    invoke_args = {
        "title": data.get("title", "测试用例"),
        "topics": topics,
        "filename": data.get("filename", "测试用例"),
        "outputPath": data.get("outputPath", ""),
    }
    logger.debug(f"调用 xmind-generator 参数: {json.dumps(invoke_args, ensure_ascii=False)[:2000]}")

    result = await gen_tool.ainvoke(invoke_args)

    # 从 MCP 响应中提取文件路径
    path = _extract_path(result)
    logger.info(f"生成结果: {path}")
    return path


def _extract_path(result) -> str:
    """从 MCP 工具返回值中提取 xmind 文件路径"""
    # result 可能是 list[dict] 或其他类型
    text = ""
    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict):
                text = item.get("text", "")
                if text:
                    break
    if not text:
        text = str(result)

    # 尝试匹配文件路径（saved to: xxx.xmind 或直接路径）
    match = re.search(r'(?:saved to:\s*)?([A-Za-z]:\\[^\s"\'\]]+\.xmind|[^\s"\'\]]+\.xmind)', text)
    if match:
        return match.group(1).strip()

    return text.strip()
