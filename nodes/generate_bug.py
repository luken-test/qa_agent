"""节点：Bug 单生成"""

import os
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from state import WorkflowState
from tools.model_factory import create_llm
from prompts.bug_report import BUG_REPORT_PROMPT
from config import OUTPUT_DIR
from utils.logger import get_logger

logger = get_logger("generate_bug")


async def generate_bug_node(state: WorkflowState) -> dict:
    """Bug 单生成节点"""
    raw_content = state.get("raw_content", "")
    screenshot_paths = state.get("screenshot_paths", [])

    if not raw_content:
        return {"error": "没有可用的缺陷描述内容"}

    llm = create_llm(temperature=0.1)

    try:
        logger.info("开始生成 Bug 单...")

        if screenshot_paths:
            screenshot_info = "用户提供了以下截图：\n"
            for path in screenshot_paths:
                screenshot_info += f"- {path}\n"
        else:
            screenshot_info = "用户未提供截图"

        bug_prompt = BUG_REPORT_PROMPT.format(
            content=raw_content,
            screenshot_info=screenshot_info,
        )

        response = await llm.ainvoke([
            SystemMessage(content="你是一位资深测试工程师，擅长编写规范的缺陷报告。只输出 Markdown。"),
            HumanMessage(content=bug_prompt),
        ])

        bug_report_md = response.content
        logger.debug(f"LLM 返回(Bug单), 长度={len(bug_report_md)}: {bug_report_md[:3000]}")
        title = raw_content[:30].replace("\n", "").replace(" ", "_")
        title = "".join(c for c in title if c.isalnum() or c in "_-")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bug单_{timestamp}_{title}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(bug_report_md)

        logger.info(f"Bug 单已保存: {filepath}")

        return {
            "bug_report_md": bug_report_md,
            "output_bug_md": filepath,
        }

    except Exception as e:
        logger.error(f"Bug 单生成失败: {e}")
        return {"error": f"Bug 单生成失败: {e}"}
