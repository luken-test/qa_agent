"""测试单个 JMeter 生成"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import build_workflow

async def test():
    print("=" * 60)
    print("测试 JMeter 脚本生成")
    print("=" * 60)

    curl_cmd = """curl --location --request POST 'https://test-inner-jlc.jlcerp.com/cms/consultation/v1/queryServerMenuConsultants' --header 'api_key: JlcBbsPlatformApiKey' --header 'Content-Type: application/json' --data-raw '{"businessLine": "PCB", "customerCodes": ["00012A", "00013A"]}' """

    print(f"\n输入的 Curl 命令:")
    print(curl_cmd)
    print()

    app = build_workflow()

    initial_state = {
        "task_type": "jmeter",
        "input_type": "text",
        "url": "",
        "file_path": "",
        "raw_text": curl_cmd,
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

    print("[Test] 开始执行工作流...")
    result = await app.ainvoke(initial_state)

    print()
    print("=" * 60)

    if result.get("error"):
        print(f"❌ 执行失败: {result['error']}")
        print("=" * 60)
        sys.exit(1)

    print("✅ 执行成功!")
    print(f"项目名称: {result.get('project_name', 'N/A')}")
    print(f"输出文件: {result.get('output_jmx', 'N/A')}")

    # 统计信息
    jmx_script = result.get("jmx_script", "")
    if jmx_script:
        http_requests = jmx_script.count('<HTTPSamplerProxy')
        assertions = (jmx_script.count('<ResponseAssertion')
                      + jmx_script.count('<DurationAssertion')
                      + jmx_script.count('<JSONPathAssertion'))
        extractors = jmx_script.count('<JSONPostProcessor') + jmx_script.count('<RegexExtractor')
        print(f"HTTP 请求数: {http_requests}")
        print(f"断言数量: {assertions}")
        print(f"提取器数量: {extractors}")

    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test())
