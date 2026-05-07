"""LangGraph 工作流状态定义

所有节点通过这个 TypedDict 共享数据。
每个节点读取需要的字段，返回要更新的字段。
"""

from typing import TypedDict, Optional


class WorkflowState(TypedDict):
    """测试工程师智能体的全局状态"""

    # ==================== 输入 ====================
    # 任务类型，由 router 节点判定
    # 可选值："testcase" | "bug" | "execute" | "chat"
    task_type: str

    # 输入来源类型：url / file / text
    input_type: str

    # 原始输入内容
    url: str                           # Mockplus 原型链接
    file_path: str                     # 本地需求文档路径
    raw_text: str                      # 用户直接输入的文字
    screenshot_paths: list             # 截图路径列表（Bug 单场景）

    # ==================== 中间产物 ====================
    raw_content: str                   # 从 URL/文件/文字提取的完整文本
    analysis: str                      # LLM 需求分析结果（JSON 字符串）
    project_name: str                  # 需求名称，用于文件命名
    testcases_json: str                # 生成的测试用例 JSON 字符串
    bug_report_md: str                 # 生成的 Bug 单 Markdown 内容
    test_script: str                   # 生成的 Playwright 测试脚本代码
    execution_result: str              # 测试脚本执行结果
    jmx_script: str                    # 生成的 JMeter 脚本 XML 内容

    # ==================== 输出路径 ====================
    output_xmind: str                  # Xmind 文件路径
    output_json: str                   # JSON 文件路径
    output_bug_md: str                 # Bug 单 Markdown 文件路径
    output_script: str                 # 测试脚本文件路径
    output_jmx: str                    # JMeter 脚本文件路径

    # ==================== RAG（预留） ====================
    rag_context: str                   # 从知识库检索到的相关上下文

    # ==================== 元信息 ====================
    error: Optional[str]               # 错误信息，非空则终止工作流
    model_name: str                    # 当前使用的模型名称
    chat_response: str                 # chat 模式的 LLM 回复
