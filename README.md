# 测试工程师智能体 - 项目指导文档

## 一、项目概述

本系统是一个基于 **LangGraph + LangChain** 的企业级测试工程师 AI 智能体，能够自动完成需求分析、测试用例生成、Bug 单编写、测试脚本生成与执行等测试工作流。

### 核心能力

| 能力 | 输入 | 输出 |
|------|------|------|
| 测试用例生成 | 需求文档 / Mockplus 原型 URL / 文字描述 | JSON + Xmind 思维导图 |
| Bug 单生成 | 缺陷描述 + 截图 | Markdown 缺陷报告 |
| 测试脚本生成与执行 | 测试用例 JSON | Playwright 脚本模板（含 TODO 占位符，需补充真实系统信息后运行） |
| JMeter 脚本生成 | Curl 命令 / 接口文档 | .jmx 脚本（含断言） |
| 测试知识问答 | 测试相关问题 | LLM 回答（限定 IT 领域） |
| 通用对话 | 自由文字 | LLM 回复 |

### 技术栈

- **工作流引擎**：LangGraph（多分支路由 + 条件终止）
- **LLM 框架**：LangChain（支持智谱 GLM / Claude / OpenAI）
- **浏览器自动化**：Playwright MCP（需求提取 + 测试执行）
- **导出工具**：Xmind Generator MCP
- **API 服务**：FastAPI + Uvicorn
- **知识库接口**：RAG 抽象层（预留，可接 Chroma/FAISS）

---

## 二、项目结构

```
qa-agent/
├── main.py                    # CLI 入口
├── server.py                  # FastAPI 服务入口
├── config.py                  # 配置中心（多模型、MCP、输出路径）
├── state.py                   # LangGraph 全局状态定义
├── graph.py                   # 工作流编排（路由 + 多分支）
│
├── prompts/                   # LLM Prompt 模板
│   ├── analysis.py            #   需求分析 prompt
│   ├── testcases.py           #   测试用例生成 prompt
│   ├── bug_report.py          #   Bug 单生成 prompt
│   ├── execution.py           #   测试脚本生成 prompt
│   ├── jmeter.py              #   JMeter 脚本生成 prompt
│   └── qa.py                  #   测试知识问答 prompt
│
├── nodes/                     # LangGraph 工作流节点
│   ├── router.py              #   意图路由（判断走哪条分支 + input_type 检测）
│   ├── extract.py             #   内容提取（URL/文件/文字）
│   ├── analyze.py             #   需求分析（LLM）
│   ├── generate_tc.py         #   测试用例生成（LLM，按模块分批）
│   ├── generate_bug.py        #   Bug 单生成（LLM）
│   ├── generate_script.py     #   测试脚本生成（LLM）
│   ├── generate_jmeter.py     #   JMeter 脚本生成（LLM，含自动修正）
│   ├── execute.py             #   脚本执行（asyncio 异步）
│   ├── export.py              #   Xmind 导出（MCP）
│   └── qa_handler.py          #   测试知识问答（LLM）
│
├── tools/                     # 外部工具集成
│   ├── model_factory.py       #   多模型工厂（智谱/Claude/OpenAI）
│   ├── browser.py             #   Playwright 浏览器工具
│   └── xmind.py               #   Xmind 生成工具
│
├── rag/                       # RAG 知识库（预留接口）
│   ├── base.py                #   抽象接口 RetrieverInterface
│   └── file_retriever.py      #   简单文件检索实现
│
├── api/                       # REST API 路由
│   └── routes.py              #   12 个 API 端点（任务提交 + 状态查询 + 文件下载）
│
├── web/                       # Vue.js 前端
│   ├── src/                   #   Vue 3 + Pinia + Vite
│   └── dist/                  #   构建产物（FastAPI 静态挂载）
│
├── output/                    # 输出文件目录（自动创建）
├── .env.example               # 环境变量模板
└── requirements.txt           # Python 依赖清单
```

---

## 三、工作流架构

### 流程图

```
START → router（意图路由）
          │
          ├── testcase 流程 ──→ extract → analyze → generate_tc → export → END
          │
          ├── bug 流程 ───────→ extract → generate_bug → END
          │
          ├── execute 流程 ──→ generate_script → execute → END
          │
          ├── jmeter 流程 ──→ generate_jmeter → END
          │
          ├── qa 流程 ───────→ qa_handler → END
          │
          └── chat 流程 ─────→ chat_handler → END
```

### 节点说明

| 节点 | 文件 | 职责 |
|------|------|------|
| router | `nodes/router.py` | 分析输入，判断 task_type 和 input_type；检测 raw_text 中的 URL 并更新到 state |
| extract | `nodes/extract.py` | 根据来源提取需求文本（Playwright 浏览器 / 文件读取 / 直接使用） |
| analyze | `nodes/analyze.py` | 调用 LLM 深度分析需求，提取模块、字段、联动规则等结构化信息 |
| generate_tc | `nodes/generate_tc.py` | 调用 LLM 生成 5 层嵌套的测试用例 JSON（按模块分批生成），保存到磁盘 |
| generate_bug | `nodes/generate_bug.py` | 调用 LLM 生成规范 Bug 单 Markdown，保存到磁盘 |
| generate_script | `nodes/generate_script.py` | 调用 LLM 生成 Playwright Python 测试脚本（支持 testcases_json 或 raw_content 输入） |
| generate_jmeter | `nodes/generate_jmeter.py` | 调用 LLM 生成 JMeter .jmx 脚本（含自动修正和结构验证） |
| execute | `nodes/execute.py` | 通过 asyncio 异步执行测试脚本，收集结果 |
| export | `nodes/export.py` | 通过 MCP 调用 xmind-generator 生成思维导图 |
| chat_handler | `graph.py` 内联 | 直接调用 LLM 进行通用对话 |
| qa_handler | `nodes/qa_handler.py` | 测试知识 Q&A（限定 IT 领域） |

### 错误处理

每个节点返回一个 dict 更新 state。如果某个节点出错，将 `error` 字段设为错误信息，工作流通过条件边 `should_stop` 检测到错误后直接跳转到 END，不会继续执行后续节点。

---

## 四、快速开始

### 4.1 安装依赖

```bash
cd E:/测试用例/qa-agent

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（如果需要测试执行功能）
playwright install chromium
```

### 4.2 配置环境变量

```bash
# 从模板复制
cp .env.example .env

# 编辑 .env，填入 API Key
# 必须配置的：
LLM_PROVIDER=zhipu           # 选择模型提供商
ZHIPU_API_KEY=your_key_here   # 对应的 API Key
```

三种模型的配置方式：

```ini
# 智谱 GLM（默认，成本低）
LLM_PROVIDER=zhipu
ZHIPU_API_KEY=your_zhipu_key
ZHIPU_MODEL=glm-4-flash

# Anthropic Claude（效果好）
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your_anthropic_key
CLAUDE_MODEL=claude-sonnet-4-6

# OpenAI GPT
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o
```

### 4.3 CLI 使用

```bash
# 生成测试用例（从文件）
python main.py --file 需求文档.txt

# 生成测试用例（从 Mockplus 原型）
python main.py --url "https://app.mockplus.cn/app/xxx/preview/xxx"

# 生成测试用例（从文字描述）
python main.py --file "这是一个登录功能的需求..."

# 生成 Bug 单
python main.py --bug "客户签到记录页面查询按钮无响应"
python main.py --bug "描述文字" --screenshot 截图路径

# 生成并执行测试脚本（传入测试用例 JSON）
python main.py --execute output/测试用例.json

# 生成 JMeter 脚本（从 curl 命令）
python main.py --jmeter "curl 'https://api.example.com/users' -H 'Authorization: Bearer token'"

# 生成 JMeter 脚本（从接口文档文件）
python main.py --jmeter examples/test_api.md

# 测试知识问答
python main.py --qa "如何设计登录功能的测试用例"

# 指定模型
python main.py --file 需求文档.txt --model claude
```

### 4.4 API 服务

```bash
# 启动服务
python server.py

# 访问 API 文档
# http://localhost:8000/docs
```

API 调用示例：

```bash
# 生成测试用例
curl -X POST http://localhost:8000/api/testcases \
  -H "Content-Type: application/json" \
  -d '{"input": "需求文档内容...", "input_type": "text"}'

# 生成 Bug 单
curl -X POST http://localhost:8000/api/bug \
  -H "Content-Type: application/json" \
  -d '{"description": "xxx页面查询无响应"}'

# 生成并执行测试脚本
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"testcases_json": "..."}'

# 生成 JMeter 脚本
curl -X POST http://localhost:8000/api/jmeter \
  -H "Content-Type: application/json" \
  -d '{"input": "curl '\''https://api.example.com/users'\'' -H '\''Authorization: Bearer token'\''", "input_type": "text"}'

# 测试知识问答
curl -X POST http://localhost:8000/api/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "如何设计接口测试用例"}'

# 通用对话
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我分析这个需求的测试点"}'

# 查询任务状态
curl http://localhost:8000/api/tasks/{task_id}

# 查看所有任务
curl http://localhost:8000/api/tasks

# 下载生成的文件
curl -O http://localhost:8000/api/download/{filename}
```

---

## 五、核心模块详解

### 5.1 多模型工厂（tools/model_factory.py）

通过环境变量 `LLM_PROVIDER` 切换模型，业务代码无需改动：

```python
from tools.model_factory import create_llm, get_model_name

# 创建 LLM 实例（自动选择配置的模型）
llm = create_llm(temperature=0.1)

# 获取当前模型名称（用于日志）
name = get_model_name()
```

扩展新模型：在 `config.py` 添加配置项，在 `model_factory.py` 的 `create_llm()` 中添加新的 elif 分支。

### 5.2 状态流转（state.py）

`WorkflowState` 是所有节点共享的数据结构，分 4 个区域：

- **输入区**：task_type, input_type, url, file_path, raw_text, screenshot_paths
- **中间产物区**：raw_content, analysis, project_name, testcases_json, bug_report_md, test_script, execution_result, jmx_script
- **输出区**：output_xmind, output_json, output_bug_md, output_script, output_jmx
- **元信息区**：error, model_name, chat_response, rag_context

每个节点只读取需要的字段，返回要更新的字段。

### 5.3 Prompt 管理（prompts/）

每个 prompt 都是独立的 Python 模块，使用 `{变量}` 格式化：

```python
from prompts.analysis import ANALYSIS_PROMPT, PROJECT_NAME_PROMPT
from prompts.testcases import MODULE_PROMPT, FULL_PROMPT
from prompts.bug_report import BUG_REPORT_PROMPT
from prompts.execution import TEST_SCRIPT_PROMPT
from prompts.jmeter import JMX_GENERATION_PROMPT
from prompts.qa import QA_SYSTEM_PROMPT

# 使用时格式化变量
prompt = ANALYSIS_PROMPT.format(content=raw_content)
```

修改 prompt 只需编辑对应的 `.py` 文件，不需要改动任何业务代码。

### 5.4 RAG 知识库（rag/）

目前提供了抽象接口和简单的文件检索实现：

```python
from rag.file_retriever import FileRetriever

# 创建检索器（从目录加载知识文档）
retriever = FileRetriever("/path/to/knowledge/dir")

# 检索相关内容
results = await retriever.retrieve("登录功能测试", top_k=5)
```

扩展向量检索：创建新类继承 `RetrieverInterface`，实现 `index()` 和 `retrieve()` 方法。

---

## 六、扩展指南

### 6.1 添加新的工作流能力

1. 在 `prompts/` 下创建新 prompt 文件
2. 在 `nodes/` 下创建新节点文件，实现 `async def xxx_node(state) -> dict`
3. 在 `graph.py` 的 `build_workflow()` 中注册节点和边
4. 在 `main.py` 添加 CLI 参数
5. 在 `api/routes.py` 添加 API 端点

### 6.2 接入向量数据库

1. 安装依赖：`pip install chromadb langchain-chroma`
2. 在 `rag/` 下创建 `chroma_retriever.py`
3. 继承 `RetrieverInterface`，实现 `index()` 和 `retrieve()`
4. 在需要知识检索的节点中调用

### 6.3 Web UI（Vue.js）

项目已内置 Vue.js 前端，位于 `web/` 目录：

```bash
# 开发模式
cd web && npm run dev

# 构建（产物自动被 FastAPI 挂载为静态文件）
cd web && npm run build
```

前端技术栈：Vue 3 + Pinia + Vite + Axios + Marked。

---

## 七、常见问题

### Q: Mockplus 原型无法提取？
在 `.env` 中配置 `MOCKPLUS_PHONE` 和 `MOCKPLUS_PASSWORD`，系统会自动登录。

### Q: Xmind 生成失败？
确保已安装 Node.js 和 npx，MCP 服务需要通过 npx 启动。

### Q: 如何切换模型？
方法一：修改 `.env` 中的 `LLM_PROVIDER`
方法二：CLI 使用 `--model claude` 参数
方法三：API 请求中传 `"model": "openai"`

### Q: 输出文件在哪里？
默认在 `qa-agent/output/` 目录下，可通过 `.env` 中的 `OUTPUT_DIR` 修改。

---

## 八、技术栈演进规划

> 以下为 AI 应用工程角度的改进项，按优先级排序，供后续迭代参考。

### P0 - 立即可做

#### 1. 可观测性（LLM 调用追踪）

**现状**：仅有文件日志，无法追踪单次 LLM 调用的 token 用量、延迟、输入输出。

**方案**：集成 LangFuse（自部署，免费）或 LangSmith（SaaS）。

```
所需依赖：langfuse / langsmith
涉及文件：
  - config.py       → 新增 LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_HOST
  - tools/model_factory.py → create_llm() 中绑定 callback handler
  - requirements.txt → 添加依赖
```

关键改动点：
```python
# model_factory.py 示例
from langfuse.callback import CallbackHandler

langfuse_handler = CallbackHandler(
    public_key=cfg.LANGFUSE_PUBLIC_KEY,
    secret_key=cfg.LANGFUSE_SECRET_KEY,
    host=cfg.LANGFUSE_HOST,
)

# 每个 LLM 调用传入 callbacks
response = await llm.ainvoke(messages, config={"callbacks": [langfuse_handler]})
```

效果：每次工作流执行后在 LangFuse 面板可查看完整调用链、token 消耗、延迟分布。

---

#### 2. SSE 流式输出

**现状**：前端等待 2-3 分钟无反馈，用户体验差。

**方案**：FastAPI SSE + LangGraph `astream_events`，前端逐字渲染 LLM 输出。

```
所需依赖：sse-starlette
涉及文件：
  - requirements.txt     → 添加 sse-starlette
  - api/routes.py        → 新增流式端点 /api/chat/stream, /api/testcases/stream
  - graph.py             → 暴露 astream_events 接口
  - web/src/api/         → 前端 EventSource 对接
```

关键改动点：
```python
# routes.py 流式端点示例
from sse_starlette.sse import EventSourceResponse

@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def event_generator():
        async for event in app.astream_events(initial_state, version="v2"):
            if event["event"] == "on_chat_model_stream":
                token = event["data"]["chunk"].content
                yield {"data": json.dumps({"token": token})}
    return EventSourceResponse(event_generator())
```

---

#### 3. 结构化输出（消除 JSON 修补逻辑）

**现状**：`generate_tc.py` 中 `_repair_truncated_json` 有 50+ 行 JSON 修补代码，说明 LLM 输出不稳定是常态。

**方案**：使用 `instructor` 或 LangChain `with_structured_output`，用 Pydantic schema 约束输出。

```
所需依赖：instructor / 或 langchain-core 自带
涉及文件：
  - nodes/generate_tc.py    → 用 Pydantic model 替代手动 JSON 解析
  - nodes/analyze.py        → 同理
  - nodes/generate_bug.py   → 同理
  - 可删除 _repair_truncated_json / _extract_json_from_response 等修补函数
```

关键改动点：
```python
# 用 Pydantic 定义输出 schema
from pydantic import BaseModel

class TestCase(BaseModel):
    title: str
    children: list["TestCase"]

class ModuleTestCases(BaseModel):
    title: str
    children: list[TestCase]

# 绑定 schema 到 LLM
structured_llm = llm.with_structured_output(ModuleTestCases)
result = await structured_llm.ainvoke(messages)
# result 直接是 Pydantic 对象，无需 JSON 解析和修补
```

---

### P1 - 下一阶段

#### 4. 向量数据库 + RAG 增强

**现状**：`rag/` 下仅有空壳 `file_retriever.py`，无真正语义检索能力。

**方案**：集成 Chroma（轻量嵌入）用于历史用例/缺陷的相似度检索。

```
所需依赖：chromadb, langchain-chroma, langchain-embedding
涉及文件：
  - rag/chroma_retriever.py  → 新建，继承 RetrieverInterface
  - config.py                → 新增 CHROMA_PERSIST_DIR 配置
  - nodes/analyze.py         → 检索相似历史需求辅助分析
  - nodes/generate_tc.py     → 检索相似历史用例作为 few-shot 示例
```

场景价值：
- 输入新需求时，自动检索历史相似需求的测试用例作为参考
- Bug 报告生成时，检索历史类似缺陷避免重复

---

#### 5. Prompt 外置管理

**现状**：Prompt 硬编码在 `prompts/*.py`，修改需要改代码重新部署。

**方案**：将 prompt 模板迁移到 YAML/JSON 文件，支持热加载。

```
涉及文件：
  - prompts/                    → 每个 .py 对应一个 .yaml
  - prompts/loader.py           → 新建，统一加载 + 缓存 + 热重载
  - config.py                   → 新增 PROMPTS_DIR 配置
```

目录结构：
```
prompts/
  ├── templates/
  │   ├── analysis.yaml
  │   ├── testcases.yaml
  │   ├── bug_report.yaml
  │   └── execution.yaml
  └── loader.py
```

---

#### 6. 任务队列替代 BackgroundTasks

**现状**：FastAPI BackgroundTasks 服务重启后任务丢失，无法重试，无并发控制。

**方案**：引入 `arq`（轻量，基于 Redis）或 Celery。

```
所需依赖：arq, redis / celery, redis
涉及文件：
  - api/routes.py  → 改为投递任务到队列
  - tasks/worker.py → 新建，arq worker 消费任务
  - config.py      → 新增 REDIS_URL 配置
```

---

### P2 - 生产加固

#### 7. Guardrails（输入输出护栏）

**方案**：使用 `guardrails-ai` 或自建校验规则，防止 prompt 注入、过滤敏感信息。

```
涉及文件：
  - guardrails/          → 新建目录
  - guardrails/input.py  → 输入校验（长度限制、敏感词过滤）
  - guardrails/output.py → 输出校验（JSON 格式、字段完整性）
  - api/routes.py        → 在入口处挂载校验
```

#### 8. 评测体系

**方案**：使用 `promptfoo` 或 `DeepEval`，自动评估生成用例的覆盖率和准确性。

```
所需依赖：deepeval / promptfoo
涉及文件：
  - evals/                    → 新建评测目录
  - evals/test_cases_eval.py  → 用例质量评估（覆盖率、去重率）
  - evals/dataset/            → 黄金数据集
```

#### 9. 模型网关（智能路由）

**方案**：简单查询用便宜模型（glm-4-flash），复杂分析用强模型（claude-opus），按任务复杂度自动路由。

```
涉及文件：
  - tools/model_factory.py → 新增 create_llm_by_complexity() 方法
  - nodes/analyze.py       → 复杂任务用强模型
  - nodes/router.py        → 简单路由用轻量模型
```

#### 10. Playwright 抓取真实页面生成脚本（消除 LLM 编造选择器）

**现状**：LLM 只能看到需求描述，看不到真实系统页面，生成的脚本中 URL、CSS 选择器、测试数据全部是编造的，无法直接运行。

**方案**：复用项目已有的 Playwright MCP 集成，在生成脚本前先用 Playwright 访问真实系统，抓取页面 DOM 结构（accessibility tree），再基于真实元素生成脚本。

```
用户提交 → testcases_json + system_url
                ↓
     Playwright MCP 打开 system_url
                ↓
     browser_snapshot 获取 accessibility tree
     （包含元素 role、name、层级关系）
                ↓
     真实 DOM 结构 + 测试用例 → LLM 生成脚本
     （page.get_by_role("button", name="下载") 等）
```

```
所需依赖：已有（Playwright MCP 已集成）
涉及文件：
  - state.py               → 新增 system_url 字段
  - tools/browser.py       → 新增 crawl_system(url) 函数
                              复用 MultiServerMCPClient + browser_snapshot
                              返回 accessibility tree 原始数据
  - nodes/generate_script.py → 调用 crawl_system 获取页面上下文
                                传入 prompt 供 LLM 使用真实选择器
  - prompts/execution.py   → 新增 PAGE_CONTEXT_PROMPT 模板
                              将 accessibility tree 转换为 Playwright 定位器建议
  - api/routes.py          → ExecuteRequest 新增 system_url 可选参数
  - web/src/api/index.js   → submitExecute 传入 system_url
  - web/src/components/MessageItem.vue → 执行测试时弹出 URL 输入
```

关键改动点：

```python
# tools/browser.py - 新增函数
async def crawl_system(url: str, login_creds: dict = None) -> str:
    """用 Playwright MCP 抓取系统页面结构，返回 accessibility tree"""
    client = MultiServerMCPClient({"playwright": MCP_SERVERS["playwright"]})
    tools = {t.name: t for t in await client.get_tools()}
    navigate = tools["browser_navigate"]
    snapshot = tools["browser_snapshot"]

    await navigate.ainvoke({"url": url})
    await asyncio.sleep(2)

    # 如需登录，自动处理
    page_data = await snapshot.ainvoke({})
    content = str(page_data)

    # 检测登录页并自动登录
    if "登录" in content[:300] and login_creds:
        # ... 自动填表登录逻辑
        pass

    return content  # 返回 accessibility tree
```

```python
# nodes/generate_script.py - 核心改动
async def generate_script_node(state: WorkflowState) -> dict:
    testcases_json = state.get("testcases_json", "")
    system_url = state.get("system_url", "")

    page_context = ""
    if system_url:
        from tools.browser import crawl_system
        logger.info(f"正在抓取系统页面: {system_url}")
        page_context = await crawl_system(system_url)
        logger.info(f"页面抓取完成，长度: {len(page_context)}")

    # 将真实页面结构加入 prompt
    if page_context:
        script_prompt = TEST_SCRIPT_PROMPT_WITH_CONTEXT.format(
            testcases=testcases_json,
            page_context=page_context[:8000],  # 限制长度
        )
    else:
        script_prompt = TEST_SCRIPT_PROMPT.format(testcases=testcases_json)
```

```python
# prompts/execution.py - 带 page context 的 prompt
TEST_SCRIPT_PROMPT_WITH_CONTEXT = \"\"\"...
## 真实系统页面结构（从 Playwright 抓取的 accessibility tree）

以下是你需要测试的系统的真实页面结构，包含元素的角色(role)、名称(name)和层级关系。
请基于这些真实元素生成 Playwright 定位器。

{page_context}

## 定位器映射规则
- accessibility tree 中的 role="button" name="下载" → page.get_by_role("button", name="下载")
- role="textbox" name="用户名" → page.get_by_label("用户名") 或 page.get_by_placeholder("用户名")
- role="link" name="首页" → page.get_by_role("link", name="首页")

请基于以上真实页面结构生成测试脚本。
...
\"\"\"
```

**多页面扩展**（后续迭代）：
- 从 accessibility tree 中提取导航链接
- 自动跟随链接抓取子页面（限制 3-5 页）
- 将多个页面的 DOM 结构一起提供给 LLM

**预期效果**：
- 之前：`page.click('.download-btn')`（编造的选择器，运行必报错）
- 之后：`page.get_by_role("button", name="下载文件")`（从真实页面抓取，定位准确）
