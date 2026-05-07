"""JMeter 脚本生成功能测试

运行此脚本测试 JMeter 生成功能是否正常工作。
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import build_workflow


async def test_curl_input():
    """测试通过 Curl 命令生成 JMeter 脚本"""
    print("=" * 60)
    print("测试1: 通过 Curl 命令生成 JMeter 脚本")
    print("=" * 60)

    curl_command = """curl 'https://api.example.com/users' \\
  -H 'Authorization: Bearer token123' \\
  -H 'Content-Type: application/json'"""

    initial_state = {
        "task_type": "jmeter",
        "input_type": "text",
        "url": "",
        "file_path": "",
        "raw_text": curl_command,
        "screenshot_paths": [],
        "raw_content": "",
        "analysis": "",
        "project_name": "",
        "testcases_json": "",
        "bug_report_md": "",
        "test_script": "",
        "execution_result": "",
        "jmx_script": "",
        "output_xmind": "",
        "output_json": "",
        "output_bug_md": "",
        "output_script": "",
        "output_jmx": "",
        "rag_context": "",
        "error": None,
        "model_name": "",
        "chat_response": "",
    }

    app = build_workflow()
    result = await app.ainvoke(initial_state)

    if result.get("error"):
        print(f"❌ 测试失败: {result['error']}")
        return False

    print(f"✅ 测试成功!")
    print(f"   项目名称: {result.get('project_name', 'N/A')}")
    print(f"   输出文件: {result.get('output_jmx', 'N/A')}")

    # 统计信息
    jmx_script = result.get("jmx_script", "")
    if jmx_script:
        http_requests = jmx_script.count('<HTTPSamplerProxy')
        assertions = (jmx_script.count('<ResponseAssertion')
                      + jmx_script.count('<DurationAssertion')
                      + jmx_script.count('<JSONPathAssertion'))
        extractors = jmx_script.count('<JSONPostProcessor') + jmx_script.count('<RegexExtractor')
        print(f"   HTTP 请求数: {http_requests}")
        print(f"   断言数量: {assertions}")
        print(f"   提取器数量: {extractors}")

    print()
    return True


async def test_api_doc():
    """测试通过接口文档生成 JMeter 脚本"""
    print("=" * 60)
    print("测试2: 通过接口文档生成 JMeter 脚本")
    print("=" * 60)

    # 检查示例文件是否存在
    doc_path = os.path.join(os.path.dirname(__file__), "examples", "test_api.md")
    if not os.path.exists(doc_path):
        print(f"⚠️  跳过测试：示例文件不存在 {doc_path}")
        return True

    initial_state = {
        "task_type": "jmeter",
        "input_type": "file",
        "url": "",
        "file_path": doc_path,
        "raw_text": "",
        "screenshot_paths": [],
        "raw_content": "",
        "analysis": "",
        "project_name": "",
        "testcases_json": "",
        "bug_report_md": "",
        "test_script": "",
        "execution_result": "",
        "jmx_script": "",
        "output_xmind": "",
        "output_json": "",
        "output_bug_md": "",
        "output_script": "",
        "output_jmx": "",
        "rag_context": "",
        "error": None,
        "model_name": "",
        "chat_response": "",
    }

    app = build_workflow()
    result = await app.ainvoke(initial_state)

    if result.get("error"):
        print(f"❌ 测试失败: {result['error']}")
        return False

    print(f"✅ 测试成功!")
    print(f"   项目名称: {result.get('project_name', 'N/A')}")
    print(f"   输出文件: {result.get('output_jmx', 'N/A')}")

    # 统计信息
    jmx_script = result.get("jmx_script", "")
    if jmx_script:
        http_requests = jmx_script.count('<HTTPSamplerProxy')
        assertions = (jmx_script.count('<ResponseAssertion')
                      + jmx_script.count('<DurationAssertion')
                      + jmx_script.count('<JSONPathAssertion'))
        extractors = jmx_script.count('<JSONPostProcessor') + jmx_script.count('<RegexExtractor')
        print(f"   HTTP 请求数: {http_requests}")
        print(f"   断言数量: {assertions}")
        print(f"   提取器数量: {extractors}")

    print()
    return True


async def main():
    """运行所有测试"""
    print("\n开始测试 JMeter 脚本生成功能...")
    print()

    results = []

    # 运行测试
    results.append(await test_curl_input())
    results.append(await test_api_doc())

    # 输出总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("✅ 所有测试通过!")
        return 0
    else:
        print(f"❌ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        exit_code = loop.run_until_complete(main())
    finally:
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

    sys.exit(exit_code)
