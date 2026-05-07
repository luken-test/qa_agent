# QA Agent 项目 - AI应用工程师入门教程

> **目标读者**：AI应用工程师新手  
> **学习目标**：理解基于LangGraph的AI智能体架构设计，掌握企业级AI应用的开发模式  
> **预计学习时间**：3-5天

---

## 📚 目录

1. [为什么这样设计？—— 核心设计理念](#1-为什么这样设计--核心设计理念)
2. [从0到1理解项目架构](#2-从0到1理解项目架构)
3. [工作流引擎 LangGraph 深度解析](#3-工作流引擎-langgraph-深度解析)
4. [逐模块代码精讲](#4-逐模块代码精讲)
5. [实战演练：添加新功能](#5-实战演练添加新功能)
6. [常见问题与最佳实践](#6-常见问题与最佳实践)

---

## 1. 为什么这样设计？—— 核心设计理念

### 1.1 为什么要用 LangGraph？

**问题背景**：  
传统的LLM应用通常是"一问一答"模式，但测试工作需要复杂的流程：
```
需求 → 分析 → 生成用例 → 导出Xmind → 完成
```

如果用普通的LangChain Chain，会遇到这些问题：
- ❌ 无法根据条件走不同分支（比如用户输入是"生成用例"还是"提Bug"？）
- ❌ 无法在中间节点出错时提前终止
- ❌ 无法灵活控制流程跳转

**LangGraph的优势**：
```python
# 传统 Chain（线性，无法分支）
chain = prompt | llm | output_parser

# LangGraph（有向图，支持分支和循环）
workflow = StateGraph(WorkflowState)
workflow.add_node("router", router_node)      # 路由节点
workflow.add_node("analyze", analyze_node)    # 分析节点
workflow.add_conditional_edges("router", route_function)  # 条件边
```

**核心思想**：将AI工作流建模为**状态机**，每个节点读取状态、更新状态，通过条件边决定下一步。

---

### 1.2 为什么要分离 Prompts 和 Nodes？

**错误示范**（Prompt硬编码在Node中）：
```python
# ❌ 不好的做法
async def analyze_node(state):
    prompt = """你是一个测试专家，请分析以下需求..."""  # 硬编码
    response = await llm.ainvoke(prompt)
```

**正确做法**（Prompt独立管理）：
```python
# ✅ 好的做法
# prompts/analysis.py
ANALYSIS_PROMPT = """你是一个测试专家，请分析以下需求..."""

# nodes/analyze.py
from prompts.analysis import ANALYSIS_PROMPT

async def analyze_node(state):
    prompt = ANALYSIS_PROMPT.format(content=state["raw_content"])
    response = await llm.ainvoke(prompt)
```

**为什么要这样设计？**
1. **可维护性**：修改Prompt不需要改业务逻辑代码
2. **可测试性**：可以单独测试Prompt的效果
3. **版本管理**：Prompt可以独立版本化、A/B测试
4. **团队协作**：提示词工程师和后端工程师可以并行工作

---

### 1.3 为什么要用 State 共享数据？

**问题**：工作流有多个节点，如何传递数据？

**方案对比**：

```python
# ❌ 方案1：函数参数传递（耦合严重）
async def router(input_text):
    task_type, content = analyze_input(input_text)
    return await analyze(content)  # 直接调用下一个节点

async def analyze(content):
    result = llm.analyze(content)
    return await generate_tc(result)  # 又直接调用下一个

# 问题：节点之间强耦合，无法灵活调整流程


# ✅ 方案2：State 模式（解耦）
class WorkflowState(TypedDict):
    raw_text: str
    task_type: str
    analysis: str
    testcases_json: str

async def router_node(state: WorkflowState) -> dict:
    # 只读取 state，返回要更新的字段
    return {"task_type": "testcase"}

async def analyze_node(state: WorkflowState) -> dict:
    # 读取 state["raw_text"]，返回分析结果
    return {"analysis": "..."}

# 优势：
# 1. 节点之间完全解耦，只通过 State 通信
# 2. 可以轻松插入新节点，不影响其他节点
# 3. 便于调试：随时查看 State 的完整状态
```

**核心理念**：每个节点都是**纯函数**，输入State，输出State更新，不依赖外部状态。

---

### 1.4 为什么要异步（async/await）？

**原因**：LLM调用是IO密集型操作，异步可以并发执行。

```python
# ❌ 同步方式（慢）
def generate_tc_for_modules(modules):
    results = []
    for module in modules:
        result = llm.invoke(prompt)  # 阻塞等待，假设每次2秒
        results.append(result)
    # 5个模块 = 10秒

# ✅ 异步方式（快）
async def generate_tc_for_modules(modules):
    tasks = [llm.ainvoke(prompt) for module in modules]
    results = await asyncio.gather(*tasks)  # 并发执行
    # 5个模块 = 2秒（同时发起请求）
```

**实际应用场景**：
- `nodes/generate_tc.py`：按模块分批生成用例，异步并发
- `nodes/execute.py`：异步执行多个测试脚本

---

## 2. 从0到1理解项目架构

### 2.1 整体架构图

```
用户输入
   │
   ▼
┌─────────────┐
│  FastAPI     │ ← API层：接收HTTP请求，返回JSON
│  (server.py) │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ LangGraph    │ ← 工作流层：编排AI任务流程
│  (graph.py)  │
└──────┬──────┘
       │
       ├─→ router_node      ← 意图识别：判断用户想做什么
       ├─→ extract_node     ← 内容提取：从URL/文件提取文本
       ├─→ analyze_node     ← 需求分析：LLM结构化分析
       ├─→ generate_tc_node ← 用例生成：LLM生成测试用例
       ├─→ export_node      ← Xmind导出：调用MCP工具
       └─→ ...其他节点
       │
       ▼
┌─────────────┐
│  Tools       │ ← 工具层：LLM、浏览器、Xmind等
│  (tools/)    │
└─────────────┘
```

### 2.2 数据流转示例

以"生成测试用例"为例：

```python
# Step 1: 用户提交请求
POST /api/testcases
{
  "input": "https://app.mockplus.cn/xxx",
  "input_type": "url"
}

# Step 2: server.py 创建初始 State
initial_state = {
  "task_type": "testcase",
  "input_type": "url",
  "url": "https://app.mockplus.cn/xxx",
  "raw_text": "",
  # ... 其他字段为空
}

# Step 3: LangGraph 执行工作流
workflow.invoke(initial_state)

# Step 4: 节点依次执行
router_node → 检测到 input_type="url"，走 testcase 分支
extract_node → 用 Playwright 访问 URL，提取页面文本 → 更新 raw_content
analyze_node → LLM 分析需求 → 更新 analysis, project_name
generate_tc_node → LLM 生成用例 JSON → 更新 testcases_json, output_json
export_node → 调用 xmind-generator MCP → 更新 output_xmind

# Step 5: 返回最终 State
{
  "output_json": "output/测试用例_20240507.json",
  "output_xmind": "output/测试用例_20240507.xmind",
  "error": None
}

# Step 6: server.py 返回响应
{
  "task_id": "xxx",
  "status": "completed",
  "files": ["测试用例_20240507.json", "测试用例_20240507.xmind"]
}
```

---

## 3. 工作流引擎 LangGraph 深度解析

### 3.1 StateGraph 核心概念

**三个核心组件**：
1. **State**：共享数据结构（TypedDict）
2. **Node**：处理函数（读取State，返回更新）
3. **Edge**：连接关系（决定下一个节点）

**代码示例**（graph.py）：

```python
from langgraph.graph import StateGraph, END
from state import WorkflowState

def build_workflow():
    # 1. 创建 StateGraph，传入 State 类型
    workflow = StateGraph(WorkflowState)
    
    # 2. 添加节点（名称 + 处理函数）
    workflow.add_node("router", router_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("generate_tc", generate_tc_node)
    workflow.add_node("export", export_node)
    
    # 3. 设置入口点（从哪个节点开始）
    workflow.set_entry_point("router")
    
    # 4. 添加条件边（根据返回值决定走哪条路）
    workflow.add_conditional_edges(
        "router",                    # 从 router 节点出发
        route_by_task_type,          # 路由函数
        {
            "testcase": "extract",   # 如果返回 "testcase"，去 extract
            "bug": "extract",        # 如果返回 "bug"，去 extract
            "execute": "generate_script",
            "jmeter": "generate_jmeter",
            "qa": "qa_handler",
            "chat": "chat_handler",
        }
    )
    
    # 5. 添加普通边（固定流向）
    workflow.add_edge("extract", "analyze")
    workflow.add_edge("analyze", "generate_tc")
    workflow.add_edge("generate_tc", "export")
    workflow.add_edge("export", END)  # 完成后结束
    
    # 6. 编译成可执行对象
    return workflow.compile()
```

---

### 3.2 条件边的路由函数

**关键代码**（nodes/router.py）：

```python
def route_by_task_type(state: WorkflowState) -> str:
    """根据 task_type 决定下一步走哪个节点"""
    
    # 如果之前节点出错了，直接结束
    if state.get("error"):
        return END
    
    task_type = state.get("task_type", "")
    
    # 返回下一个节点的名称
    if task_type == "testcase":
        return "extract"
    elif task_type == "bug":
        return "extract"
    elif task_type == "execute":
        return "generate_script"
    # ... 其他分支
```

**为什么这样设计？**
- ✅ **灵活性**：可以根据 State 的任何字段做路由决策
- ✅ **可扩展**：新增分支只需修改路由函数
- ✅ **可测试**：路由函数是纯函数，容易单元测试

---

### 3.3 错误处理机制

**传统方式**（try-catch）：
```python
# ❌ 每个节点都要 try-catch，代码冗余
async def analyze_node(state):
    try:
        result = await llm.ainvoke(prompt)
        return {"analysis": result}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"error": str(e)}  # 手动返回错误
```

**LangGraph 方式**（统一错误边）：
```python
# ✅ 在 graph.py 中统一处理
workflow.add_conditional_edges(
    "analyze",
    lambda state: END if state.get("error") else "generate_tc",
    {
        "generate_tc": "generate_tc",
        END: END,
    }
)
```

**工作原理**：
1. 任何节点出错时，设置 `state["error"] = "错误信息"`
2. 条件边检测到 error 字段，直接跳转到 END
3. 后续节点不会执行，避免级联错误

---

## 4. 逐模块代码精讲

### 4.1 配置中心（config.py）

**为什么需要配置中心？**

```python
# ❌ 硬编码配置（难以维护）
api_key = "sk-xxx"  # 写在代码里，泄露风险
model_name = "glm-4-flash"  # 换模型要改代码

# ✅ 从环境变量读取（灵活安全）
import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件

class Config:
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "zhipu")
    ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
    ZHIPU_MODEL = os.getenv("ZHIPU_MODEL", "glm-4-flash")
```

**关键设计点**：

```python
# 1. 支持多模型切换
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "zhipu")  # zhipu / claude / openai

# 2. MCP 服务器配置（用于调用外部工具）
MCP_SERVERS = {
    "playwright": {
        "command": "npx",
        "args": ["-y", "@executeautomation/playwright-mcp-server"],
    },
    "xmind": {
        "command": "npx",
        "args": ["-y", "xmind-generator"],
    },
}

# 3. 输出路径配置
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)  # 自动创建目录
```

**学习要点**：
- 使用 `.env` 管理敏感信息（API Key），不要提交到 Git
- 配置项要有默认值，避免缺少配置导致崩溃
- 目录自动创建，提升用户体验

---

### 4.2 状态定义（state.py）

**完整的 State 设计**：

```python
from typing import TypedDict, Optional, List

class WorkflowState(TypedDict):
    # ========== 输入区（用户提供的数据）==========
    task_type: str          # 任务类型：testcase / bug / execute / jmeter / qa / chat
    input_type: str         # 输入类型：text / url / file
    url: str                # Mockplus 原型 URL
    file_path: str          # 本地文件路径
    raw_text: str           # 用户输入的文字描述
    screenshot_paths: List[str]  # Bug 截图路径
    
    # ========== 中间产物区（节点产生的数据）==========
    raw_content: str        # 提取后的原始内容（从URL/文件提取）
    analysis: str           # 需求分析结果（LLM输出）
    project_name: str       # 项目名称
    testcases_json: str     # 测试用例 JSON
    bug_report_md: str      # Bug 报告 Markdown
    test_script: str        # 测试脚本代码
    execution_result: str   # 脚本执行结果
    jmx_script: str         # JMeter 脚本内容
    
    # ========== 输出区（最终生成的文件路径）==========
    output_xmind: str       # Xmind 文件路径
    output_json: str        # JSON 文件路径
    output_bug_md: str      # Bug 报告文件路径
    output_script: str      # 测试脚本文件路径
    output_jmx: str         # JMeter 脚本文件路径
    
    # ========== 元信息区（辅助信息）==========
    error: Optional[str]    # 错误信息（如果有）
    model_name: str         # 使用的模型名称
    chat_response: str      # 聊天回复
    rag_context: str        # RAG 检索到的上下文
```

**设计原则**：

1. **分区管理**：输入、中间产物、输出分开，职责清晰
2. **可选字段**：用 `Optional` 标记可能为空的字段
3. **类型提示**：所有字段都有类型，IDE 可以自动补全

**为什么不用类（Class）而用 TypedDict？**

```python
# ❌ 用 Class（复杂，需要实例化）
class WorkflowState:
    def __init__(self):
        self.task_type = ""
        self.raw_text = ""

state = WorkflowState()
state.task_type = "testcase"

# ✅ 用 TypedDict（简洁，像字典一样使用）
state: WorkflowState = {
    "task_type": "testcase",
    "raw_text": "..."
}
state["task_type"] = "bug"  # 直接修改
```

**优势**：
- LangGraph 原生支持 TypedDict
- 更像字典，方便序列化（JSON）
- 类型检查依然有效

---

### 4.3 多模型工厂（tools/model_factory.py）

**核心代码**：

```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from config import cfg

def create_llm(temperature=0.1, model=None):
    """工厂函数：根据配置创建 LLM 实例"""
    
    provider = cfg.LLM_PROVIDER.lower()
    
    if provider == "zhipu":
        # 智谱 GLM（通过 OpenAI 兼容接口）
        return ChatOpenAI(
            model=model or cfg.ZHIPU_MODEL,
            api_key=cfg.ZHIPU_API_KEY,
            base_url=cfg.ZHIPU_API_BASE,
            temperature=temperature,
        )
    elif provider == "claude":
        # Anthropic Claude
        return ChatAnthropic(
            model=model or cfg.CLAUDE_MODEL,
            api_key=cfg.ANTHROPIC_API_KEY,
            temperature=temperature,
        )
    elif provider == "openai":
        # OpenAI GPT
        return ChatOpenAI(
            model=model or cfg.OPENAI_MODEL,
            api_key=cfg.OPENAI_API_KEY,
            temperature=temperature,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
```

**为什么要用工厂模式？**

```python
# ❌ 不使用工厂（每个节点都要判断模型）
async def analyze_node(state):
    if cfg.LLM_PROVIDER == "zhipu":
        llm = ChatOpenAI(...)
    elif cfg.LLM_PROVIDER == "claude":
        llm = ChatAnthropic(...)
    
    response = await llm.ainvoke(prompt)

# ✅ 使用工厂（业务代码无关模型选择）
from tools.model_factory import create_llm

async def analyze_node(state):
    llm = create_llm(temperature=0.1)  # 一行搞定
    response = await llm.ainvoke(prompt)
```

**优势**：
- **单一职责**：模型选择逻辑集中在工厂函数
- **开闭原则**：新增模型只需修改工厂，不改业务代码
- **易于测试**：可以 mock 工厂函数，返回假 LLM

---

### 4.4 意图路由（nodes/router.py）

**核心功能**：判断用户想做什么（生成用例？提Bug？问答？）

**完整代码解析**：

```python
import re
from state import WorkflowState

def detect_input_type(raw_text: str) -> str:
    """检测输入类型：URL / 文件路径 / 纯文本"""
    
    # 1. 检测是否是 URL（http/https 开头）
    if re.match(r'^https?://', raw_text.strip()):
        return "url"
    
    # 2. 检测是否是文件路径（包含 .txt/.md/.pdf 等扩展名）
    if re.search(r'\.(txt|md|pdf|docx)$', raw_text.strip(), re.IGNORECASE):
        return "file"
    
    # 3. 默认是纯文本
    return "text"

def detect_task_type(raw_text: str) -> str:
    """检测任务类型：testcase / bug / execute / jmeter / qa / chat"""
    
    text_lower = raw_text.lower()
    
    # 关键词匹配（简单但有效）
    if any(keyword in text_lower for keyword in ["生成用例", "测试用例", "test case"]):
        return "testcase"
    elif any(keyword in text_lower for keyword in ["bug", "缺陷", "报错"]):
        return "bug"
    elif any(keyword in text_lower for keyword in ["执行测试", "运行脚本"]):
        return "execute"
    elif any(keyword in text_lower for keyword in ["jmeter", "性能测试"]):
        return "jmeter"
    elif any(keyword in text_lower for keyword in ["怎么测试", "如何设计"]):
        return "qa"
    else:
        return "chat"  # 默认闲聊

async def router_node(state: WorkflowState) -> dict:
    """路由节点：分析输入，设置 task_type 和 input_type"""
    
    raw_text = state.get("raw_text", "")
    
    # 检测输入类型
    input_type = detect_input_type(raw_text)
    
    # 检测任务类型
    task_type = detect_task_type(raw_text)
    
    # 如果是 URL，额外提取域名（用于日志）
    url_domain = ""
    if input_type == "url":
        match = re.search(r'https?://([^/]+)', raw_text)
        if match:
            url_domain = match.group(1)
    
    return {
        "input_type": input_type,
        "task_type": task_type,
        "url": raw_text if input_type == "url" else "",
    }
```

**设计思考**：

**Q: 为什么不用 LLM 做意图识别？**  
A: 关键词匹配更快、更便宜。LLM 适合复杂语义理解，简单场景用规则即可。

**Q: 如果关键词匹配不准怎么办？**  
A: 可以在前端让用户明确选择任务类型（下拉框），或者用 LLM 做二次确认。

---

### 4.5 内容提取（nodes/extract.py）

**三种输入来源的处理**：

```python
from tools.browser import crawl_mockplus
from pathlib import Path

async def extract_node(state: WorkflowState) -> dict:
    """根据 input_type 提取内容"""
    
    input_type = state.get("input_type", "text")
    
    if input_type == "url":
        # 1. URL 类型：用 Playwright 爬取 Mockplus 原型
        url = state.get("url", "")
        try:
            content = await crawl_mockplus(url)
            return {"raw_content": content}
        except Exception as e:
            return {"error": f"Failed to crawl URL: {str(e)}"}
    
    elif input_type == "file":
        # 2. 文件类型：读取文件内容
        file_path = state.get("file_path", "")
        try:
            content = Path(file_path).read_text(encoding="utf-8")
            return {"raw_content": content}
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}
    
    else:
        # 3. 文本类型：直接使用
        raw_text = state.get("raw_text", "")
        return {"raw_content": raw_text}
```

**Playwright 爬虫详解**（tools/browser.py）：

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from config import MCP_SERVERS

async def crawl_mockplus(url: str) -> str:
    """用 Playwright MCP 爬取 Mockplus 原型页面"""
    
    # 1. 创建 MCP 客户端（连接到 Playwright 服务）
    client = MultiServerMCPClient({
        "playwright": MCP_SERVERS["playwright"]
    })
    
    # 2. 获取可用工具
    tools = {t.name: t for t in await client.get_tools()}
    
    # 3. 导航到目标页面
    navigate = tools["browser_navigate"]
    await navigate.ainvoke({"url": url})
    
    # 4. 等待页面加载
    import asyncio
    await asyncio.sleep(3)
    
    # 5. 提取页面文本（accessibility tree）
    snapshot = tools["browser_snapshot"]
    page_data = await snapshot.ainvoke({})
    
    # 6. 转换为字符串
    content = str(page_data)
    
    return content
```

**什么是 MCP（Model Context Protocol）？**

MCP 是 Anthropic 提出的协议，让 LLM 可以调用外部工具。本项目用 MCP 集成：
- **Playwright MCP**：浏览器自动化（爬取页面、执行测试）
- **Xmind Generator MCP**：生成思维导图

**优势**：
- 标准化接口，无需自己封装浏览器操作
- 社区生态丰富，有很多现成的 MCP 服务器

---

### 4.6 需求分析（nodes/analyze.py）

**核心代码**：

```python
from tools.model_factory import create_llm
from prompts.analysis import ANALYSIS_PROMPT, PROJECT_NAME_PROMPT

async def analyze_node(state: WorkflowState) -> dict:
    """LLM 深度分析需求，提取结构化信息"""
    
    raw_content = state.get("raw_content", "")
    
    if not raw_content:
        return {"error": "No content to analyze"}
    
    # 1. 创建 LLM 实例
    llm = create_llm(temperature=0.1)  # 低温度，保证输出稳定
    
    # 2. 第一步：提取项目名称（简单任务）
    project_name_prompt = PROJECT_NAME_PROMPT.format(content=raw_content[:500])
    project_name_response = await llm.ainvoke(project_name_prompt)
    project_name = project_name_response.content.strip()
    
    # 3. 第二步：深度分析需求（复杂任务）
    analysis_prompt = ANALYSIS_PROMPT.format(content=raw_content)
    analysis_response = await llm.ainvoke(analysis_prompt)
    analysis = analysis_response.content
    
    return {
        "project_name": project_name,
        "analysis": analysis,
    }
```

**Prompt 设计技巧**（prompts/analysis.py）：

```python
PROJECT_NAME_PROMPT = """从以下需求中提取项目名称（不超过20字）：

{content}

项目名称："""

ANALYSIS_PROMPT = """你是资深测试工程师，请分析以下需求：

## 需求内容
{content}

## 分析要求
1. 列出所有功能模块
2. 每个模块的输入字段、校验规则
3. 字段之间的联动关系
4. 边界条件和异常场景

## 输出格式
### 模块1：XXX
- 字段：...
- 规则：...

### 模块2：YYY
...
"""
```

**为什么要分两步分析？**
1. **提取项目名**：短文本，快速响应，用于文件命名
2. **深度分析**：长文本，详细拆解，用于生成用例

**好处**：避免一个 Prompt 太长，LLM 容易遗漏细节。

---

### 4.7 测试用例生成（nodes/generate_tc.py）

**这是最复杂的节点**，涉及：
- 分批生成（避免单次 Token 超限）
- JSON 格式校验
- 文件保存

**核心代码**：

```python
import json
from datetime import datetime
from tools.model_factory import create_llm
from prompts.testcases import MODULE_PROMPT

async def generate_tc_node(state: WorkflowState) -> dict:
    """按模块分批生成测试用例"""
    
    analysis = state.get("analysis", "")
    project_name = state.get("project_name", "未命名项目")
    
    # 1. 从分析结果中提取模块列表
    modules = extract_modules(analysis)  # ["登录模块", "注册模块", ...]
    
    # 2. 并发生成每个模块的用例
    tasks = []
    for module in modules:
        task = generate_module_tc(module, analysis)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 3. 合并所有模块的用例
    all_testcases = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Module {modules[i]} failed: {result}")
            continue
        
        try:
            module_tc = json.loads(result)
            all_testcases.append(module_tc)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from module {modules[i]}")
    
    # 4. 构建完整的用例树
    full_testcases = {
        "title": project_name,
        "children": all_testcases
    }
    
    # 5. 保存到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"测试用例_{project_name}_{timestamp}.json"
    filepath = f"output/{filename}"
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(full_testcases, f, ensure_ascii=False, indent=2)
    
    return {
        "testcases_json": json.dumps(full_testcases, ensure_ascii=False),
        "output_json": filepath,
    }
```

**分批生成的原因**：

```python
# ❌ 一次性生成所有用例（Token 超限）
prompt = f"""为以下所有模块生成测试用例：
{all_modules}  # 可能有 20+ 模块
"""
# LLM 输出可能超过 8000 tokens，容易被截断

# ✅ 按模块分批生成（可控）
for module in modules:
    prompt = MODULE_PROMPT.format(module=module, analysis=analysis)
    result = await llm.ainvoke(prompt)  # 每次只生成一个模块
```

**JSON 修补逻辑**（应对 LLM 输出不完整）：

```python
def _repair_truncated_json(text: str) -> str:
    """修复被截断的 JSON"""
    
    # 1. 找到最后一个完整的对象
    last_comma = text.rfind(",")
    last_brace = text.rfind("}")
    
    if last_comma > last_brace:
        # 去掉末尾的逗号
        text = text[:last_comma] + "}"
    
    # 2. 补充缺失的括号
    open_braces = text.count("{")
    close_braces = text.count("}")
    text += "}" * (open_braces - close_braces)
    
    return text
```

**注意**：这部分代码很脆弱，更好的方案是用 `instructor` 库做结构化输出（见 README 第 443 行）。

---

### 4.8 Xmind 导出（nodes/export.py）

**调用 MCP 工具生成思维导图**：

```python
from tools.xmind import generate_xmind

async def export_node(state: WorkflowState) -> dict:
    """将测试用例 JSON 转为 Xmind"""
    
    testcases_json = state.get("testcases_json", "")
    project_name = state.get("project_name", "未命名")
    
    if not testcases_json:
        return {"error": "No testcases to export"}
    
    try:
        # 调用 xmind-generator MCP
        xmind_path = await generate_xmind(testcases_json, project_name)
        return {"output_xmind": xmind_path}
    except Exception as e:
        return {"error": f"Failed to generate Xmind: {str(e)}"}
```

**Xmind 生成工具**（tools/xmind.py）：

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from config import MCP_SERVERS

async def generate_xmind(testcases_json: str, project_name: str) -> str:
    """用 xmind-generator MCP 生成思维导图"""
    
    # 1. 连接 MCP 服务器
    client = MultiServerMCPClient({
        "xmind": MCP_SERVERS["xmind"]
    })
    
    # 2. 获取工具
    tools = {t.name: t for t in await client.get_tools()}
    generate_tool = tools["generate_xmind"]
    
    # 3. 调用工具
    result = await generate_tool.ainvoke({
        "data": testcases_json,
        "filename": f"{project_name}.xmind"
    })
    
    return result["filepath"]
```

**Xmind JSON 格式要求**：

```json
{
  "title": "项目名称",
  "children": [
    {
      "title": "模块1",
      "children": [
        {
          "title": "测试场景1",
          "children": [
            {"title": "用例1：正常登录"},
            {"title": "用例2：密码错误"}
          ]
        }
      ]
    }
  ]
}
```

---

## 5. 实战演练：添加新功能

### 任务：添加"生成接口文档"功能

**需求**：用户输入 API 描述，自动生成 Swagger/OpenAPI 格式的接口文档。

---

### Step 1: 创建 Prompt

新建 `prompts/api_doc.py`：

```python
API_DOC_PROMPT = """你是 API 设计专家，请根据以下描述生成 OpenAPI 3.0 格式的接口文档。

## 接口描述
{description}

## 输出要求
1. 使用 YAML 格式
2. 包含 path、method、parameters、requestBody、responses
3. 添加详细的字段说明和示例

## 输出格式
```yaml
openapi: 3.0.0
info:
  title: XXX API
  version: 1.0.0
paths:
  /xxx:
    get:
      summary: XXX
      parameters:
        - name: id
          in: query
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Success
```
"""
```

---

### Step 2: 创建 Node

新建 `nodes/generate_api_doc.py`：

```python
from tools.model_factory import create_llm
from prompts.api_doc import API_DOC_PROMPT
from pathlib import Path
from datetime import datetime

async def generate_api_doc_node(state: WorkflowState) -> dict:
    """生成接口文档"""
    
    description = state.get("raw_content", "")
    
    if not description:
        return {"error": "No description provided"}
    
    # 1. 调用 LLM 生成文档
    llm = create_llm(temperature=0.2)
    prompt = API_DOC_PROMPT.format(description=description)
    response = await llm.ainvoke(prompt)
    
    api_doc_yaml = response.content
    
    # 2. 保存到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"API文档_{timestamp}.yaml"
    filepath = f"output/{filename}"
    
    Path(filepath).write_text(api_doc_yaml, encoding="utf-8")
    
    return {
        "output_api_doc": filepath,
    }
```

---

### Step 3: 注册到工作流

修改 `graph.py`：

```python
from nodes.generate_api_doc import generate_api_doc_node

def build_workflow():
    workflow = StateGraph(WorkflowState)
    
    # 添加新节点
    workflow.add_node("generate_api_doc", generate_api_doc_node)
    
    # 在路由函数中添加新分支
    workflow.add_conditional_edges(
        "router",
        route_by_task_type,
        {
            "testcase": "extract",
            "bug": "extract",
            "api_doc": "generate_api_doc",  # ← 新增
            # ... 其他分支
        }
    )
    
    # 添加边
    workflow.add_edge("generate_api_doc", END)
    
    return workflow.compile()
```

修改 `nodes/router.py`：

```python
def detect_task_type(raw_text: str) -> str:
    text_lower = raw_text.lower()
    
    if any(keyword in text_lower for keyword in ["接口文档", "API 文档", "swagger"]):
        return "api_doc"  # ← 新增
    # ... 其他判断
```

---

### Step 4: 添加 API 端点

修改 `api/routes.py`：

```python
from pydantic import BaseModel

class ApiDocRequest(BaseModel):
    description: str
    model: Optional[str] = None

@router.post("/api_doc")
async def generate_api_doc(req: ApiDocRequest):
    """生成接口文档"""
    
    initial_state = {
        "task_type": "api_doc",
        "input_type": "text",
        "raw_text": req.description,
        "raw_content": req.description,
        # ... 其他字段初始化
    }
    
    # 执行工作流
    final_state = await app.ainvoke(initial_state)
    
    if final_state.get("error"):
        raise HTTPException(status_code=500, detail=final_state["error"])
    
    return {
        "file": final_state.get("output_api_doc"),
    }
```

---

### Step 5: 测试

```bash
curl -X POST http://localhost:8000/api_doc \
  -H "Content-Type: application/json" \
  -d '{
    "description": "用户登录接口，POST /api/login，需要 username 和 password"
  }'
```

---

## 6. 常见问题与最佳实践

### 6.1 LLM 输出不稳定怎么办？

**问题**：LLM 有时输出 JSON 格式错误，有时漏掉字段。

**解决方案**：

1. **使用结构化输出**（推荐）：
```python
from pydantic import BaseModel
from instructor import patch

# 定义输出 schema
class TestCase(BaseModel):
    title: str
    steps: list[str]
    expected: str

# 绑定到 LLM
client = patch(OpenAI())
result = client.chat.completions.create(
    model="gpt-4",
    response_model=TestCase,  # ← 强制输出符合 schema
    messages=[{"role": "user", "content": prompt}]
)
# result 直接是 TestCase 对象，无需 JSON 解析
```

2. **增加 Few-shot 示例**：
```python
prompt = """生成测试用例。

示例1：
输入：登录功能
输出：{"title": "正常登录", "steps": ["输入用户名", "输入密码"], "expected": "登录成功"}

示例2：
输入：注册功能
输出：{"title": "邮箱重复", "steps": ["输入已注册邮箱"], "expected": "提示邮箱已存在"}

现在请为以下功能生成用例：
{input}
"""
```

3. **降低 Temperature**：
```python
llm = create_llm(temperature=0.1)  # 越低越稳定，但创造性越差
```

---

### 6.2 如何调试 LangGraph 工作流？

**方法1：打印 State**

```python
async def analyze_node(state: WorkflowState) -> dict:
    print("=== Analyze Node Input ===")
    print(f"raw_content length: {len(state.get('raw_content', ''))}")
    
    result = {"analysis": "..."}
    
    print("=== Analyze Node Output ===")
    print(result)
    
    return result
```

**方法2：使用 LangGraph Studio**

```bash
pip install langgraph-cli
langgraph dev  # 启动可视化调试界面
```

**方法3：记录每步耗时**

```python
import time

async def generate_tc_node(state):
    start = time.time()
    
    # ... 业务逻辑
    
    elapsed = time.time() - start
    logger.info(f"generate_tc_node took {elapsed:.2f}s")
```

---

### 6.3 如何处理大文件？

**问题**：用户上传 10MB 的需求文档，LLM Context 不够。

**解决方案**：

1. **分块处理**：
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=4000,  # 每块 4000 字符
    chunk_overlap=200  # 重叠 200 字符，保持上下文连贯
)

chunks = splitter.split_text(large_text)

# 分别处理每块
for chunk in chunks:
    result = await llm.ainvoke(prompt.format(content=chunk))
```

2. **Map-Reduce**：
```python
# Map：每块单独分析
map_results = await asyncio.gather(*[analyze_chunk(chunk) for chunk in chunks])

# Reduce：合并结果
final_result = merge_results(map_results)
```

3. **RAG 检索**（高级）：
```python
# 将文档存入向量数据库
retriever.index(large_text)

# 只检索相关片段
relevant_chunks = retriever.retrieve("登录功能", top_k=5)

# 用相关片段生成用例
prompt = f"""基于以下内容生成用例：
{relevant_chunks}
"""
```

---

### 6.4 安全性注意事项

**1. API Key 保护**：
```python
# ✅ 从环境变量读取
api_key = os.getenv("OPENAI_API_KEY")

# ❌ 硬编码
api_key = "sk-xxx"
```

**2. 输入验证**：
```python
# 限制输入长度
if len(raw_text) > 50000:
    return {"error": "Input too long"}

# 过滤危险字符
raw_text = html.escape(raw_text)  # 防止 XSS
```

**3. 速率限制**：
```python
from fastapi import Request
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@router.post("/testcases")
@limiter.limit("10/minute")  # 每分钟最多 10 次
async def generate_testcases(request: Request):
    ...
```

---

### 6.5 性能优化技巧

**1. 缓存 LLM 响应**：
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_llm_response(prompt_hash: str) -> str:
    # 相同 prompt 直接返回缓存
    ...
```

**2. 并发执行**：
```python
# 串行（慢）
result1 = await llm.ainvoke(prompt1)
result2 = await llm.ainvoke(prompt2)
# 总耗时 = 2s + 2s = 4s

# 并行（快）
results = await asyncio.gather(
    llm.ainvoke(prompt1),
    llm.ainvoke(prompt2)
)
# 总耗时 = max(2s, 2s) = 2s
```

**3. 流式输出**：
```python
# 用户无需等待全部生成完成，看到第一个字就有反馈
async for chunk in llm.astream(prompt):
    yield chunk.content  # SSE 推送给前端
```

---

## 🎓 学习路线建议

### 第1天：理解架构
- [ ] 阅读 `state.py`，理解 State 设计
- [ ] 阅读 `graph.py`，画出工作流图
- [ ] 运行 `python main.py --help`，体验 CLI

### 第2天：深入节点
- [ ] 逐行阅读 `nodes/router.py`
- [ ] 逐行阅读 `nodes/generate_tc.py`
- [ ] 修改 Prompt，观察输出变化

### 第3天：实战练习
- [ ] 按照第5章添加"生成接口文档"功能
- [ ] 添加一个新的 LLM Provider（如通义千问）
- [ ] 优化 JSON 修补逻辑，改用 instructor

### 第4-5天：进阶主题
- [ ] 集成 LangFuse 做可观测性
- [ ] 实现 SSE 流式输出
- [ ] 添加单元测试

---

## 📖 延伸阅读

1. **LangGraph 官方文档**：https://langchain-ai.github.io/langgraph/
2. **LangChain  Cookbook**：https://python.langchain.com/docs/cookbook/
3. **MCP 协议规范**：https://modelcontextprotocol.io/
4. **FastAPI 最佳实践**：https://fastapi.tiangolo.com/tutorial/

---

## 💡 总结

**本项目的核心价值**：
1. **模块化设计**：Prompts、Nodes、Tools 分离，易于维护
2. **状态机思维**：用 LangGraph 建模复杂工作流
3. **工厂模式**：多模型切换无需改业务代码
4. **异步并发**：充分利用 IO 等待时间

**作为 AI 应用工程师，你需要掌握**：
- ✅ Prompt Engineering（提示词工程）
- ✅ LangGraph/LangChain（工作流编排）
- ✅ FastAPI（API 服务）
- ✅ Asyncio（异步编程）
- ✅ MCP（工具集成）

**下一步行动**：
1. 克隆项目，本地运行
2. 按照教程添加一个新功能
3. 尝试优化现有代码（如结构化输出）

祝你学习顺利！🚀
