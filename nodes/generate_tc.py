"""节点：测试用例生成

使用 LLM 根据需求分析结果，生成结构化的测试用例 JSON。
按模块分批调用 LLM，避免单次输出超出模型 token 限制。
"""

import json
import os
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from state import WorkflowState
from tools.model_factory import create_llm
from prompts.testcases import MODULE_PROMPT, FULL_PROMPT
from config import OUTPUT_DIR
from utils.logger import get_logger

logger = get_logger("generate_tc")


def _repair_truncated_json(text: str) -> str:
    """修复被截断的 JSON：移除末尾不完整的键值对，补齐缺失的闭合括号"""
    text = text.rstrip().rstrip(",")

    for _ in range(20):
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError as e:
            msg = str(e)
            if "Unterminated string" in msg:
                last_quote = text.rfind('"')
                if last_quote > 0:
                    cut_pos = text.rfind(",", 0, last_quote)
                    brace_pos = text.rfind("{", 0, last_quote)
                    bracket_pos = text.rfind("[", 0, last_quote)
                    cut_pos = max(cut_pos, brace_pos, bracket_pos)
                    if cut_pos > 0:
                        text = text[:cut_pos].rstrip().rstrip(",")
            elif "Expecting" in msg or "Extra data" in msg:
                last_complete = max(text.rfind("},"), text.rfind("],"), text.rfind("}"), text.rfind("]"))
                if last_complete > 0:
                    text = text[:last_complete + 1]

    open_curly = text.count("{") - text.count("}")
    open_bracket = text.count("[") - text.count("]")
    if open_bracket > 0:
        text += "]" * open_bracket
    if open_curly > 0:
        text += "}" * open_curly

    return text


def _extract_json_from_response(content: str) -> dict | None:
    """从 LLM 返回内容中提取并解析 JSON"""
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    # 直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 尝试截断修复
    repaired = _repair_truncated_json(content)
    try:
        result = json.loads(repaired)
        logger.warning("JSON 被截断，已自动修复")
        return result
    except json.JSONDecodeError:
        return None


def _extract_modules_from_analysis(analysis: str) -> list[dict]:
    """从分析结果 JSON 中提取模块列表"""
    data = _extract_json_from_response(analysis)
    if data and "modules" in data:
        return data["modules"]

    # analysis 本身可能是纯文本模块列表，尝试按行提取
    return []


async def _generate_for_module(llm, analysis_text: str, module: dict, module_index: int) -> dict | None:
    """为单个模块生成测试用例"""
    module_name = module.get("name", f"模块{module_index}")
    module_info = json.dumps(module, ensure_ascii=False) if isinstance(module, dict) else str(module)

    prompt = MODULE_PROMPT % (analysis_text, module_name, module_info)

    system_msg = (
        "你是一位资深测试工程师。只输出纯 JSON，不要包含注释、尾逗号或任何非法 JSON 语法。"
        "只生成当前指定模块的用例，不要生成其他模块。"
    )

    for attempt in range(3):
        response = await llm.ainvoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt),
        ])

        content = response.content
        logger.debug(f"LLM 返回(模块={module_name}, 尝试={attempt+1}), 长度={len(content)}")

        result = _extract_json_from_response(content)
        if result:
            # 确保 title 是模块名
            result.setdefault("title", module_name)
            return result

        if attempt < 2:
            logger.warning(f"模块 [{module_name}] JSON 解析失败，正在重试")
            prompt = (
                f"上一次输出的 JSON 有误，请为模块 [{module_name}] 重新生成测试用例 JSON。\n"
                f"只输出该模块的 JSON，确保完整闭合。\n\n"
                f"模块信息: {module_info}"
            )

    logger.error(f"模块 [{module_name}] 生成失败（已重试 3 次）")
    return None


async def _generate_all_at_once(llm, analysis: str) -> dict | None:
    """fallback：一次性生成所有用例（当分析结果无法拆分模块时使用）"""
    prompt = FULL_PROMPT % analysis

    for attempt in range(3):
        response = await llm.ainvoke([
            SystemMessage(content="你是一位资深测试工程师。只输出纯 JSON，确保完整闭合。"),
            HumanMessage(content=prompt),
        ])

        content = response.content
        result = _extract_json_from_response(content)
        if result:
            return result

        if attempt < 2:
            logger.warning(f"完整生成 JSON 解析失败，正在重试 ({attempt+1}/3)")
            prompt = (
                f"上一次输出的 JSON 被截断或有误，请重新生成。\n"
                f"请控制用例数量，每个模块仅 2-3 条核心用例，确保 JSON 完整输出。\n\n"
                f"需求分析:\n{analysis}"
            )

    return None


def _normalize_testcases(data) -> dict | None:
    """自动修正 LLM 输出的 JSON 结构，统一为标准格式"""
    if isinstance(data, list):
        return {"title": "测试用例", "topics": data}

    if not isinstance(data, dict):
        return None

    if "topics" in data:
        return data

    for key in ("modules", "children", "cases", "data", "items"):
        if key in data and isinstance(data[key], list):
            return {"title": data.get("title", "测试用例"), "topics": data[key]}

    if "title" in data and "children" in data:
        return {"title": "测试用例", "topics": [data]}

    return None


async def generate_tc_node(state: WorkflowState) -> dict:
    """测试用例生成节点（按模块分批生成）"""
    analysis = state.get("analysis", "")
    project_name = state.get("project_name", "测试项目")

    if not analysis:
        return {"error": "没有可用的分析结果"}

    llm = create_llm(temperature=0.2)

    try:
        logger.info("开始生成测试用例...")
        timestamp = datetime.now().strftime("%Y%m%d")

        # 尝试从分析结果中提取模块列表
        modules = _extract_modules_from_analysis(analysis)

        if modules:
            # 按模块分批生成
            logger.info(f"检测到 {len(modules)} 个模块，按模块分批生成用例")
            all_topics = []

            for i, module in enumerate(modules):
                module_name = module.get("name", f"模块{i+1}")
                logger.info(f"正在生成模块 [{module_name}] 的用例 ({i+1}/{len(modules)})")

                topic = await _generate_for_module(llm, analysis, module, i + 1)
                if topic:
                    all_topics.append(topic)
                else:
                    logger.warning(f"跳过模块 [{module_name}]")

            if not all_topics:
                return {"error": "所有模块的用例生成均失败"}

            testcases = {
                "title": "测试用例",
                "topics": all_topics,
            }
        else:
            # fallback：无法拆分模块，一次性生成（使用精简版 prompt）
            logger.info("无法拆分模块，使用 fallback 方式一次性生成")
            testcases = await _generate_all_at_once(llm, analysis)
            if not testcases:
                return {"error": "测试用例生成失败（已重试多次）"}
            testcases = _normalize_testcases(testcases)
            if testcases is None:
                return {"error": "生成的 JSON 结构无法识别"}

        # 补全标准字段
        testcases.setdefault("title", "测试用例")
        testcases.setdefault("filename", f"{timestamp}_测试用例")
        testcases["outputPath"] = OUTPUT_DIR
        testcases_json = json.dumps(testcases, ensure_ascii=False, indent=2)

        # 统计
        total_cases = 0
        tc_modules = testcases.get("topics", [])
        for module in tc_modules:
            total_cases += len(module.get("children", module.get("fields", [])))

        logger.info(f"生成完成: {len(tc_modules)} 个模块, {total_cases} 条用例")

        # 保存 JSON 文件
        json_filename = f"{timestamp}_{project_name}_测试用例.json"
        json_path = os.path.join(OUTPUT_DIR, json_filename)
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(testcases_json)
        logger.info(f"JSON 已保存: {json_path}")

        return {
            "testcases_json": testcases_json,
            "output_json": json_path,
        }

    except Exception as e:
        logger.error(f"测试用例生成失败: {e}")
        return {"error": f"测试用例生成失败: {e}"}
