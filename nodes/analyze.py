"""节点：需求分析

使用 LLM 对需求文档进行深度分析：
1. 提取项目名称（用于文件命名）
2. 分析功能模块、字段、联动规则等结构化信息
"""

from langchain_core.messages import SystemMessage, HumanMessage

from state import WorkflowState
from tools.model_factory import create_llm
from prompts.analysis import ANALYSIS_PROMPT, PROJECT_NAME_PROMPT
from utils.logger import get_logger

logger = get_logger("analyze")


async def analyze_node(state: WorkflowState) -> dict:
    """需求分析节点"""
    raw_content = state.get("raw_content", "")
    if not raw_content:
        return {"error": "没有可分析的需求内容"}

    llm = create_llm(temperature=0.1)

    try:
        # 步骤 1：提取项目名称
        logger.info("正在提取项目名称...")
        name_prompt = PROJECT_NAME_PROMPT.format(content=raw_content[:2000])
        name_response = await llm.ainvoke([HumanMessage(content=name_prompt)])
        project_name = name_response.content.strip().strip('"').strip('"'"'「」")
        logger.debug(f"LLM 返回(项目名称): {name_response.content}")
        logger.info(f"项目名称: {project_name}")

        # 步骤 2：深度分析需求
        logger.info("正在深度分析需求...")
        analysis_prompt = ANALYSIS_PROMPT.format(content=raw_content)
        response = await llm.ainvoke([
            SystemMessage(content="你是一位资深需求分析师，擅长从需求文档中提取结构化信息。"),
            HumanMessage(content=analysis_prompt),
        ])

        analysis = response.content
        logger.debug(f"LLM 返回(需求分析), 长度={len(analysis)}: {analysis[:2000]}")
        if "```json" in analysis:
            analysis = analysis.split("```json")[1].split("```")[0].strip()
        elif "```" in analysis:
            analysis = analysis.split("```")[1].split("```")[0].strip()

        logger.info(f"分析完成，长度: {len(analysis)} 字符")
        return {"analysis": analysis, "project_name": project_name}

    except Exception as e:
        logger.error(f"需求分析失败: {e}")
        return {"error": f"需求分析失败: {e}"}
