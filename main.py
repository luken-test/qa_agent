"""测试工程师智能体 —— CLI 入口

用法:
  # 生成测试用例（默认）
  python main.py --file 需求文档.txt
  python main.py --url https://app.mockplus.cn/...

  # 生成 Bug 单
  python main.py --bug "xxx页面查询无响应"
  python main.py --bug "描述文字" --screenshot 截图路径

  # 生成并执行测试脚本
  python main.py --execute 测试用例.json

  # 生成 JMeter 脚本
  python main.py --jmeter "curl 'https://api.example.com/users' -H 'Authorization: Bearer token'"
  python main.py --jmeter 接口文档.txt

  # 指定模型
  python main.py --file 需求文档.txt --model claude

环境变量:
  LLM_PROVIDER  - 模型提供商：zhipu（默认）/ claude / openai
  ZHIPU_API_KEY - 智谱 API Key
  ANTHROPIC_API_KEY - Claude API Key
  OPENAI_API_KEY - OpenAI API Key
"""

import argparse
import asyncio
import json
import os
import sys
import time
import re

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import build_workflow


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="测试工程师智能体 - 基于 LangGraph 的多能力测试 AI"
    )

    # 输入来源（多选一）
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--file", help="本地需求文档路径")
    input_group.add_argument("--url", help="Mockplus 原型链接")
    input_group.add_argument("--bug", help="Bug 描述文字（生成 Bug 单）")
    input_group.add_argument("--execute", help="测试用例 JSON 路径���生成并执行脚本）")
    input_group.add_argument("--jmeter", help="Curl 命令或接口文档路径（生成 JMeter 脚本）")
    input_group.add_argument("--qa", help="测试知识问答（限定互联网 IT 领域）")

    # 可选参数
    parser.add_argument("--model", default=None, help="模型提供商: zhipu/claude/openai")
    parser.add_argument("--screenshot", nargs="*", help="Bug 截图路径（配合 --bug 使用）")

    return parser.parse_args()


async def run(args):
    """执行工作流主函数"""
    # 如果指定了模型，覆盖环境变量
    if args.model:
        os.environ["LLM_PROVIDER"] = args.model

    print("=" * 60)
    print("  测试工程师智能体")
    print("  基于 LangChain + LangGraph + 多模型")
    print("=" * 60)
    print()

    # 构建工作流
    app = build_workflow()

    # 根据 CLI 参数构建初始状态
    if args.file:
        initial_state = {
            "task_type": "testcase", "input_type": "file",
            "url": "", "file_path": args.file, "raw_text": "",
            "screenshot_paths": [],
        }
    elif args.url:
        initial_state = {
            "task_type": "testcase", "input_type": "url",
            "url": args.url, "file_path": "", "raw_text": "",
            "screenshot_paths": [],
        }
    elif args.bug:
        initial_state = {
            "task_type": "bug", "input_type": "text",
            "url": "", "file_path": "", "raw_text": args.bug,
            "screenshot_paths": args.screenshot or [],
        }
    elif args.execute:
        # 读取 JSON 文件内容作为 testcases_json
        tc_json = ""
        if os.path.exists(args.execute):
            with open(args.execute, "r", encoding="utf-8") as f:
                tc_json = f.read()
        initial_state = {
            "task_type": "execute", "input_type": "text",
            "url": "", "file_path": "", "raw_text": "",
            "screenshot_paths": [],
            "testcases_json": tc_json,
        }
    elif args.jmeter:
        # 判断是文件还是直接输入
        if os.path.exists(args.jmeter):
            initial_state = {
                "task_type": "jmeter", "input_type": "file",
                "url": "", "file_path": args.jmeter, "raw_text": "",
                "screenshot_paths": [],
            }
        else:
            initial_state = {
                "task_type": "jmeter", "input_type": "text",
                "url": "", "file_path": "", "raw_text": args.jmeter,
                "screenshot_paths": [],
            }
    elif args.qa:
        initial_state = {
            "task_type": "qa", "input_type": "text",
            "url": "", "file_path": "", "raw_text": args.qa,
            "screenshot_paths": [],
        }
    else:
        print("请提供输入参数，使用 --help 查看帮助")
        return

    # 填充所有 state 字段的默认值
    defaults = {
        "raw_content": "", "analysis": "", "project_name": "",
        "testcases_json": "", "bug_report_md": "", "test_script": "",
        "execution_result": "", "jmx_script": "", "output_xmind": "",
        "output_json": "", "output_bug_md": "", "output_script": "",
        "output_jmx": "", "rag_context": "",
        "error": None, "model_name": "", "chat_response": "",
    }
    initial_state.update(defaults)

    # 执行工作流
    print("[Workflow] 开始执行...")
    t0 = time.time()
    result = await app.ainvoke(initial_state)
    elapsed = time.time() - t0

    # 输出结果
    print()
    print("=" * 60)

    if result.get("error"):
        print(f"  执行失败: {result['error']}")
        print("=" * 60)
        sys.exit(1)

    task_type = result.get("task_type", "")

    if task_type == "testcase":
        # 测试用例结果
        json_path = result.get("output_json", "")
        total_cases = 0
        modules = []
        if json_path and os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            modules = [m["title"] for m in data.get("topics", [])]
            for m in data.get("topics", []):
                total_cases += len(m.get("children", []))

        xmind_raw = result.get("output_xmind", "")
        xmind_match = re.search(r"saved to:\s*(.+\.xmind)", xmind_raw)
        xmind_path = xmind_match.group(1).strip() if xmind_match else xmind_raw

        print("  执行完成! — 测试用例生成")
        print(f"  项目名称: {result.get('project_name', 'N/A')}")
        print(f"  用例数量: {total_cases} 条")
        print(f"  覆盖模块: {len(modules)} 个")
        for m in modules:
            print(f"    - {m}")
        print(f"  JSON 文件: {json_path}")
        print(f"  Xmind 文件: {xmind_path}")

    elif task_type == "bug":
        # Bug 单结果
        print("  执行完成! — Bug 单生成")
        print(f"  Bug 单文件: {result.get('output_bug_md', 'N/A')}")

    elif task_type == "execute":
        # 脚本执行结果
        print("  执行完成! — 测试脚本执行")
        print(f"  脚本文件: {result.get('output_script', 'N/A')}")
        print(f"  执行结果:")
        print(result.get("execution_result", "无结果"))

    elif task_type == "jmeter":
        # JMeter 脚本结果
        print("  执行完成! — JMeter 脚本生成")
        print(f"  脚本文件: {result.get('output_jmx', 'N/A')}")
        print(f"  项目名称: {result.get('project_name', 'N/A')}")
        # 显示统计信息
        jmx_script = result.get("jmx_script", "")
        if jmx_script:
            http_requests = jmx_script.count('<HTTPSamplerProxy')
            assertions = (jmx_script.count('<ResponseAssertion')
                          + jmx_script.count('<DurationAssertion')
                          + jmx_script.count('<JSONPathAssertion'))
            extractors = jmx_script.count('<JSONPostProcessor') + jmx_script.count('<RegexExtractor')
            print(f"  HTTP 请求数: {http_requests}")
            print(f"  断言数量: {assertions}")
            print(f"  提取器数量: {extractors}")

    elif task_type == "qa":
        # 测试知识问答结果
        print("  执行完成! — 测试知识问答")
        print(f"  回答:")
        print(result.get("chat_response", "无回答"))

    print(f"  总耗时: {elapsed:.1f}s")
    print("=" * 60)


def main():
    args = parse_args()
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(run(args))
    finally:
        # 清理所有未关闭的 transport，避免 Windows 上的 pipe 警告
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        all_tasks = asyncio.all_tasks(loop)
        for task in all_tasks:
            task.cancel()
        if all_tasks:
            loop.run_until_complete(asyncio.gather(*all_tasks, return_exceptions=True))
        loop.close()


if __name__ == "__main__":
    main()
