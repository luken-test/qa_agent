"""LangGraph 工作流编排

定义测试工程师智能体的完整工作流：
- router: 意图路由，判断任务类型
- testcase_flow: 提取 → 分析 → 生成用例 → 导出 Xmind
- bug_flow: 提取 → 生成 Bug 单
- execute_flow: 提取 → 生成脚本 → 执行脚本
- chat_flow: 直接 LLM 对话

每条分支都有条件错误检查，出错时立即终止。
"""

from langgraph.graph import StateGraph, END

from state import WorkflowState
from nodes.router import router_node
from nodes.extract import extract_node
from nodes.analyze import analyze_node
from nodes.generate_tc import generate_tc_node
from nodes.generate_bug import generate_bug_node
from nodes.generate_script import generate_script_node
from nodes.generate_jmeter import generate_jmeter_node
from nodes.execute import execute_node
from nodes.export import export_node
from nodes.qa_handler import qa_handler_node


def should_stop(state: WorkflowState) -> str:
    """检查是否有错误，决定是否继续执行

    Returns:
        "end": 有错误，终止工作流
        "continue": 无错误，继续下一步
    """
    if state.get("error"):
        return "end"
    return "continue"


def route_task(state: WorkflowState) -> str:
    """根据 router 节点判定的 task_type，决定走哪条分支

    Returns:
        节点名称字符串
    """
    task_type = state.get("task_type", "chat")
    routes = {
        "testcase": "extract",
        "bug": "extract",
        "execute": "generate_script",
        "jmeter": "generate_jmeter",
        "qa": "qa_handler",
        "chat": "chat_handler",
    }
    return routes.get(task_type, "chat_handler")


def route_after_extract(state: WorkflowState) -> str:
    """提取完成后的路由：先检查错误，再根据 task_type 决定下一步

    Returns:
        节点名称字符串或 "end"
    """
    # 有错误则终止
    if state.get("error"):
        return "end"
    # 无错误，按任务类型路由
    task_type = state.get("task_type", "chat")
    routes = {
        "testcase": "analyze",
        "bug": "generate_bug",
        "execute": "execute",
    }
    return routes.get(task_type, "end")


def build_workflow() -> StateGraph:
    """构建测试工程师智能体的 LangGraph 工作流

    工作流结构：
    START → router → [testcase | bug | execute | chat]
                        ↓
                      extract → [analyze | generate_bug | generate_script]
                                   ↓              ↓              ↓
                              generate_tc    (END)         execute
                                   ↓
                                 export → END

    Returns:
        编译后的 LangGraph 执行图
    """
    graph = StateGraph(WorkflowState)

    # ========== 添加所有节点 ==========
    graph.add_node("router", router_node)
    graph.add_node("extract", extract_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("generate_tc", generate_tc_node)
    graph.add_node("generate_bug", generate_bug_node)
    graph.add_node("generate_script", generate_script_node)
    graph.add_node("generate_jmeter", generate_jmeter_node)
    graph.add_node("execute", execute_node)
    graph.add_node("export", export_node)
    graph.add_node("qa_handler", qa_handler_node)

    async def chat_handler(state: WorkflowState) -> dict:
        """QA Agent 对话处理节点"""
        from tools.model_factory import create_llm
        from langchain_core.messages import SystemMessage, HumanMessage
        from utils.logger import get_logger
        logger = get_logger("chat")
        llm = create_llm(temperature=0.3)
        response = await llm.ainvoke([
            SystemMessage(content=(
                "你是一位资深测试工程师智能体（QA Agent）。你的职责是：\n"
                "1. 根据用户的需求描述，帮助用户分析测试点、生成测试用例\n"
                "2. 回答测试相关的问题\n"
                "3. 如果用户需要生成 JMeter 脚本，提示用户输入 curl 命令\n"
                "4. 如果用户需要 Bug 报告，提示用户描述具体的 Bug 现象\n"
                "请简洁、专业地回答用户的问题，不要自行生成无关的文档或报告。"
            )),
            HumanMessage(content=state.get("raw_text", "")),
        ])
        logger.debug(f"LLM 返回(chat), 长度={len(response.content)}: {response.content[:3000]}")
        return {"chat_response": response.content}

    graph.add_node("chat_handler", chat_handler)

    # ========== 定义入口和路由 ==========
    graph.set_entry_point("router")

    # router 根据任务类型路由到不同分支
    graph.add_conditional_edges("router", route_task, {
        "extract": "extract",
        "generate_script": "generate_script",
        "generate_jmeter": "generate_jmeter",
        "qa_handler": "qa_handler",
        "chat_handler": "chat_handler",
    })

    # chat 分支直接结束
    graph.add_edge("chat_handler", END)

    # qa 分支直接结束
    graph.add_edge("qa_handler", END)

    # ========== 提取后的分支 ==========
    # extract 完成后：有错误→END，无错误→按任务类型路由到对应节点
    graph.add_conditional_edges("extract", route_after_extract, {
        "end": END,
        "analyze": "analyze",
        "generate_bug": "generate_bug",
        "execute": "execute",
    })

    # ========== testcase 流程 ==========
    graph.add_conditional_edges("analyze", should_stop, {
        "continue": "generate_tc",
        "end": END,
    })
    graph.add_conditional_edges("generate_tc", should_stop, {
        "continue": "export",
        "end": END,
    })
    graph.add_edge("export", END)

    # ========== bug 流程 ==========
    graph.add_edge("generate_bug", END)

    # ========== execute 流程 ==========
    graph.add_conditional_edges("generate_script", should_stop, {
        "continue": "execute",
        "end": END,
    })
    graph.add_edge("execute", END)

    # ========== jmeter 流程 ==========
    graph.add_edge("generate_jmeter", END)

    return graph.compile(checkpointer=_checkpointer)


# ========== Checkpointer ==========
# 通过 setup_checkpointer() 在 server.py lifespan 中初始化
_checkpointer = None

def setup_checkpointer(checkpointer):
    """由 server.py 在启动时调用，设置全局 checkpointer"""
    global _checkpointer
    _checkpointer = checkpointer


def get_checkpointer():
    """获取当前 checkpointer 实例"""
    return _checkpointer
