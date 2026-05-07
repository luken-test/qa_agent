"""节点：测试脚本生成"""

import json
import os
import re

from langchain_core.messages import SystemMessage, HumanMessage

from state import WorkflowState
from tools.model_factory import create_llm
from prompts.execution import TEST_SCRIPT_PROMPT
from config import OUTPUT_DIR
from utils.logger import get_logger

logger = get_logger("generate_script")


def _extract_project_name(testcases_json: str, fallback: str = "test") -> str:
    """从 testcases_json 或 state 中提取项目名称"""
    try:
        data = json.loads(testcases_json)
        for key in ("title", "project_name", "filename"):
            name = data.get(key, "")
            if name and name not in ("测试用例", "test"):
                return re.sub(r'[^\w一-鿿]', '_', name)[:30]
    except (json.JSONDecodeError, AttributeError):
        pass
    return fallback


def _validate_python_syntax(code: str) -> tuple:
    """校验 Python 语法，返回 (是否合法, 错误信息)"""
    try:
        compile(code, "<generated_script>", "exec")
        return True, ""
    except SyntaxError as e:
        return False, f"语法错误: 行{e.lineno}: {e.msg}"


async def generate_script_node(state: WorkflowState) -> dict:
    """测试脚本生成节点"""
    testcases_json = state.get("testcases_json", "") or state.get("raw_content", "")

    if not testcases_json:
        return {"error": "没有可用的测试用例数据"}

    project_name = state.get("project_name", "") or _extract_project_name(testcases_json)

    # 使用更大的 max_tokens 避免截断
    llm = create_llm(temperature=0.2, max_tokens=32768)

    try:
        logger.info("开始生成测试脚本...")

        script_prompt = TEST_SCRIPT_PROMPT.format(testcases=testcases_json)

        system_msg = (
            "你是一位资深自动化测试工程师，擅长编写 Playwright 测试脚本。只输出 Python 代码。\n"
            "重要：必须输出完整可运行的脚本，不要省略任何函数体或截断代码。"
        )

        for attempt in range(2):
            response = await llm.ainvoke([
                SystemMessage(content=system_msg),
                HumanMessage(content=script_prompt),
            ])

            script_content = response.content
            logger.debug(f"LLM 返回(测试脚本, 尝试={attempt+1}), 长度={len(script_content)}: {script_content[:3000]}")

            if "```python" in script_content:
                script_content = script_content.split("```python")[1].split("```")[0].strip()
            elif "```" in script_content:
                script_content = script_content.split("```")[1].split("```")[0].strip()

            valid, err_msg = _validate_python_syntax(script_content)
            if valid:
                break

            logger.warning(f"生成的脚本语法校验失败: {err_msg}")
            if attempt < 1:
                logger.info("正在重试生成...")
                script_prompt = (
                    f"上次生成的脚本在末尾被截断了，语法错误: {err_msg}\n\n"
                    "请重新生成完整的测试脚本。要求：\n"
                    "1. 只保留核心测试函数，去掉冗长注释\n"
                    "2. 每个测试函数精简到 10-15 行\n"
                    "3. 确保脚本完整输出，不要截断\n\n"
                    f"测试用例数据:\n{testcases_json[:8000]}"
                )

        # 最终仍校验失败则警告但不阻塞
        valid, err_msg = _validate_python_syntax(script_content)
        if not valid:
            logger.warning(f"脚本语法仍有问题（已重试）: {err_msg}")

        filename = f"test_{project_name}.py"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(script_content)

        logger.info(f"测试脚本已保存: {filepath}")

        return {
            "test_script": script_content,
            "output_script": filepath,
            "project_name": project_name,
        }

    except Exception as e:
        logger.error(f"测试脚本生成失败: {e}")
        return {"error": f"测试脚本生成失败: {e}"}
