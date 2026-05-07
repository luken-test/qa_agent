"""项目配置：多模型、MCP 服务器、输出路径"""

import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# ---------- 模型提供商选择 ----------
# 可选值："zhipu" | "claude" | "openai"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "zhipu")

# ---------- 智谱 GLM 配置 ----------
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_API_BASE = os.getenv("ZHIPU_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
ZHIPU_MODEL = os.getenv("ZHIPU_MODEL", "glm-4-flash")

# ---------- Anthropic Claude 配置 ----------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# ---------- OpenAI 配置（也用于 OpenAI 兼容的 Claude 代理） ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ---------- Mockplus 登录凭证 ----------
MOCKPLUS_PHONE = os.getenv("MOCKPLUS_PHONE", "")
MOCKPLUS_PASSWORD = os.getenv("MOCKPLUS_PASSWORD", "")

# ---------- MCP 服务器配置 ----------
# Playwright 用于浏览器自动化（需求提取 + 测试执行）
# Xmind Generator 用于导出思维导图
MCP_SERVERS = {
    "playwright": {
        "command": "npx",
        "args": ["@playwright/mcp@latest"],
        "transport": "stdio",
    },
    "xmind-generator": {
        "command": "npx",
        "args": ["xmind-generator-mcp"],
        "transport": "stdio",
    },
}

# ---------- 输出目录 ----------
# 默认输出到项目根目录下的 output 文件夹
_output_default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "") or _output_default

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)
