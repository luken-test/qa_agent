"""简单的 JMeter 测试"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import build_workflow

async def test():
    print("测试简单 JMeter 生成...")

    # 使用更简单的 curl 命令
    curl_cmd = "curl 'https://api.example.com/users' -H 'Authorization: Bearer token123'"

    print(f"Curl: {curl_cmd}")

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
        # 添加超时控制
        import asyncio
        result = await asyncio.wait_for(app.ainvoke(initial_state), timeout=60.0)

        if result.get("error"):
            print(f"错误: {result['error']}")
            return False

        print(f"成功!")
        print(f"项目: {result.get('project_name')}")
        print(f"文件: {result.get('output_jmx')}")
        return True
    except asyncio.TimeoutError:
        print("超时了（60秒）")
        return False
    except Exception as e:
        print(f"异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
