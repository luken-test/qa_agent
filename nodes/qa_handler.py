"""节点：测试知识智能问答

使用 LLM 回答用户关于测试知识的提问，
限定只回答互联网 IT 相关领域的问题。
"""

from langchain_core.messages import SystemMessage, HumanMessage

from state import WorkflowState
from tools.model_factory import create_llm
from prompts.qa import QA_SYSTEM_PROMPT
from utils.logger import get_logger

logger = get_logger("qa_handler")


async def qa_handler_node(state: WorkflowState) -> dict:
    """测试知识 Q&A 节点"""
    raw_text = state.get("raw_text", "")
    if not raw_text or not raw_text.strip():
        return {"error": "请输入您的问题"}

    llm = create_llm(temperature=0.3)

    try:
        logger.info(f"收到 Q&A 问题，长度: {len(raw_text)}")

        response = await llm.ainvoke([
            SystemMessage(content=QA_SYSTEM_PROMPT),
            HumanMessage(content=raw_text),
        ])

        logger.debug(f"LLM 返回(QA), 长度={len(response.content)}: {response.content[:3000]}")
        return {"chat_response": response.content}

    except Exception as e:
        logger.error(f"Q&A 回答失败: {e}")
        return {"error": f"Q&A 回答失败: {e}"}
