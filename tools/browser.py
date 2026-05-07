"""工具：Playwright MCP 浏览器操作"""

import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

from config import MCP_SERVERS, MOCKPLUS_PHONE, MOCKPLUS_PASSWORD
from utils.logger import get_logger

logger = get_logger("browser")


async def extract_from_url(url: str) -> str:
    """通过 Playwright MCP 打开 URL 并提取页面文本内容"""
    client = MultiServerMCPClient({"playwright": MCP_SERVERS["playwright"]})
    tools = {t.name: t for t in await client.get_tools()}

    navigate = tools["browser_navigate"]
    snapshot = tools["browser_snapshot"]

    logger.info(f"正在打开: {url}")
    await navigate.ainvoke({"url": url})
    await asyncio.sleep(2)

    page_data = await snapshot.ainvoke({})
    content = str(page_data)

    if "登录" in content[:200] or "密码" in content[:200]:
        if MOCKPLUS_PHONE and MOCKPLUS_PASSWORD:
            logger.info("检测到登录页，尝试自动登录...")
            content = await _mockplus_login(tools, url)
        else:
            logger.warning("页面需要登录，请先配置 MOCKPLUS_PHONE/MOCKPLUS_PASSWORD")
            return ""

    logger.info(f"成功提取页面内容，长度: {len(content)} 字符")
    return content


async def _mockplus_login(tools: dict, original_url: str) -> str:
    """Mockplus 自动登录流程"""
    fill_form = tools["browser_fill_form"]
    click = tools["browser_click"]

    await fill_form.ainvoke({
        "fields": [
            {"target": 'textbox "邮箱/手机号"', "type": "textbox", "value": MOCKPLUS_PHONE},
            {"target": 'textbox "密码"', "type": "textbox", "value": MOCKPLUS_PASSWORD},
        ]
    })
    await click.ainvoke({"target": 'text "登录"', "element": "登录按钮"})

    await asyncio.sleep(2)
    navigate = tools["browser_navigate"]
    await navigate.ainvoke({"url": original_url})
    await asyncio.sleep(2)

    snapshot = tools["browser_snapshot"]
    page_data = await snapshot.ainvoke({})
    return str(page_data)


async def extract_from_file(file_path: str) -> str:
    """从本地文件读取需求文档"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    logger.info(f"从文件读取内容，长度: {len(content)} 字符")
    return content
