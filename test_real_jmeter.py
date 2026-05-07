"""测试实际的 JMeter curl 命令"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import build_workflow

async def test():
    print("=" * 60)
    print("测试实际 API 的 JMeter 生成")
    print("=" * 60)

    # 用户提供的实际 curl 命令
    curl_cmd = """curl --location --request POST 'https://test-inner-jlc.jlcerp.com/cms/consultation/v1/queryServerMenuConsultants' --header 'api_key: JlcBbsPlatformApiKey' --header 'Content-Type: application/json' --data-raw '{"businessLine": "PCB", "customerCodes": ["00012A", "00013A"]}' """

    print(f"\n输入的 Curl 命令:")
    print(curl_cmd[:100] + "...")
    print()

    app = build_workflow()

    initial_state = {
        "task_type": "jmeter",
        "input_type": "text",
        "url": "", "file_path": "", "raw_text": curl_cmd,
        "screenshot_paths": [],
        "raw_content": "", "analysis": "", "project_name": "",
        "testcases_json": "", "bug_report_md": "", "test_script": "",
        "execution_result": "", "jmx_script": "", "output_xmind": "",
        "output_json": "", "output_bug_md": "", "output_script": "",
        "output_jmx": "", "rag_context": "",
        "error": None, "model_name": "", "chat_response": "",
    }

    try:
        print("[Test] 开始生成（设置90秒超时）...")
        result = await asyncio.wait_for(app.ainvoke(initial_state), timeout=90.0)

        print()
        print("=" * 60)

        if result.get("error"):
            print(f"❌ 失败: {result['error']}")
            print("=" * 60)
            return False

        print("✅ 成功!")
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
            print(f"\n脚本统计:")
            print(f"  - HTTP 请求数: {http_requests}")
            print(f"  - 断言数量: {assertions}")
            print(f"  - 提取器数量: {extractors}")

        print("=" * 60)
        return True

    except asyncio.TimeoutError:
        print("\n❌ 超时（90秒）")
        print("提示: LLM 生成复杂 XML 可能需要较长时间")
        print("=" * 60)
        return False
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
