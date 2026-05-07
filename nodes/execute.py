"""节点：测试脚本执行"""

import asyncio
import os

from state import WorkflowState
from utils.logger import get_logger

logger = get_logger("execute")


async def execute_node(state: WorkflowState) -> dict:
    """测试脚本执行节点"""
    script_path = state.get("output_script", "")

    if not script_path or not os.path.exists(script_path):
        return {"error": f"测试脚本文件不存在: {script_path}"}

    try:
        logger.info(f"正在执行测试脚本: {script_path}")

        proc = await asyncio.create_subprocess_exec(
            "python", script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.path.dirname(script_path),
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            logger.error("测试脚本执行超时（5分钟）")
            return {"error": "测试脚本执行超时（5分钟）"}

        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")

        execution_result = (
            f"=== 测试执行结果 ===\n"
            f"退出码: {proc.returncode}\n"
            f"{'✅ 全部通过' if proc.returncode == 0 else '❌ 存在失败'}\n\n"
            f"--- 标准输出 ---\n{stdout_text}\n"
        )
        if stderr_text:
            execution_result += f"--- 错误输出 ---\n{stderr_text}\n"

        logger.info(f"执行完成，退出码: {proc.returncode}")

        return {"execution_result": execution_result}

    except Exception as e:
        logger.error(f"测试脚本执行失败: {e}")
        return {"error": f"测试脚本执行失败: {e}"}
