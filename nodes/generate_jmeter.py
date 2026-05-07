"""节点：JMeter 脚本生成

使用 LLM 根据 Curl 命令或接口文档生成可执行的 JMeter 脚本（.jmx 格式）。
"""

import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from state import WorkflowState
from tools.model_factory import create_llm
from prompts.jmeter import JMX_GENERATION_PROMPT
from config import OUTPUT_DIR
from utils.logger import get_logger

logger = get_logger("generate_jmeter")


def _parse_input_content(raw_text: str, file_path: str) -> str:
    """解析输入内容，提取 Curl 命令或接口文档"""
    if file_path and os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return raw_text


def _generate_project_name(content: str) -> str:
    """根据内容生成项目名称"""
    curl_match = re.search(r"curl\s+['\"]?https?://[^/'\"]+/([^/'\"]+)", content)
    if curl_match:
        return curl_match.group(1)

    title_match = re.search(r'#\s+(.+?)\n|接口名称[：:]\s*(.+?)\n', content)
    if title_match:
        title = title_match.group(1) or title_match.group(2)
        title = re.sub(r'[^\w一-鿿]+', '_', title)
        return title[:50]

    return f"jmeter_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def _clean_xml_output(xml_content: str) -> str:
    """清理 LLM 输出的 XML，去除 markdown 标记等"""
    if "```xml" in xml_content:
        xml_content = xml_content.split("```xml")[1].split("```")[0].strip()
    elif "```" in xml_content:
        xml_content = xml_content.split("```")[1].split("```")[0].strip()

    if not xml_content.startswith('<?xml'):
        xml_start = xml_content.find('<?xml')
        if xml_start > 0:
            xml_content = xml_content[xml_start:]

    return xml_content.strip()


def _auto_fix_jmx(xml_content: str) -> tuple:
    """自动修正常见的 JMX 结构错误

    使用正则表达式修正常见的 LLM 生成错误：
    1. Asserion -> Assertion 拼写修正
    2. ResponseAssertion(response_time) -> DurationAssertion
    3. 缺少 hashTree 终止符的元素补上 <hashTree/>
    """
    fixes = []

    # Fix 1: 拼写错误 Asserion -> Assertion
    if 'Asserion.test_strings' in xml_content:
        xml_content = xml_content.replace('Asserion.test_strings', 'Assertion.test_strings')
        fixes.append("修正拼写: 'Asserion.test_strings' -> 'Assertion.test_strings'")

    # Fix 1b: HTTPHeaderManager -> HeaderManager (JMeter saveservice 别名)
    if '<HTTPHeaderManager' in xml_content or '</HTTPHeaderManager>' in xml_content:
        xml_content = xml_content.replace('<HTTPHeaderManager', '<HeaderManager')
        xml_content = xml_content.replace('</HTTPHeaderManager>', '</HeaderManager>')
        xml_content = xml_content.replace('testclass="HTTPHeaderManager"', 'testclass="HeaderManager"')
        fixes.append("修正标签名: 'HTTPHeaderManager' -> 'HeaderManager'")

    # Fix 1b-2: HeaderManagerGui -> HeaderPanel (JMeter 5.0 GUI class alias)
    if 'HeaderManagerGui' in xml_content:
        xml_content = xml_content.replace('guiclass="HeaderManagerGui"', 'guiclass="HeaderPanel"')
        fixes.append("修正 guiclass: 'HeaderManagerGui' -> 'HeaderPanel'")

    # Fix 1c: ThreadGroup 缺少 LoopController 时自动注入
    if '<ThreadGroup' in xml_content and 'ThreadGroup.main_controller' not in xml_content:
        loop_controller = (
            '<stringProp name="ThreadGroup.on_sample_error">continue</stringProp>\n'
            '        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" '
            'guiclass="LoopControlPanelGui" testclass="LoopController" testname="循环控制器" enabled="true">\n'
            '          <stringProp name="LoopController.loops">1</stringProp>\n'
            '          <boolProp name="LoopController.continue_forever">false</boolProp>\n'
            '        </elementProp>'
        )
        # 在 ThreadGroup 的第一个子属性前插入 LoopController
        xml_content = re.sub(
            r'(<ThreadGroup[^>]*>\s*\n)',
            r'\1        ' + loop_controller + '\n',
            xml_content
        )
        # 移除无效的 ThreadGroup.loops 属性（循环次数由 LoopController 控制）
        xml_content = re.sub(r'\s*<stringProp name="ThreadGroup\.loops">[^<]*</stringProp>\n?', '', xml_content)
        fixes.append("为 ThreadGroup 注入必需的 LoopController")

    # Fix 2: 将 ResponseAssertion(response_time) 替换为 DurationAssertion
    def _fix_duration_assertion(match):
        block = match.group(0)
        duration_val = "5000"
        for prop_name in ['Assertion.test_expression', 'Assertion.test_value', 'Assertion.test_string']:
            val_match = re.search(rf'<stringProp name="{re.escape(prop_name)}">(\d+)</stringProp>', block)
            if val_match:
                duration_val = val_match.group(1)
                break
        return (f'<DurationAssertion guiclass="DurationAssertionGui" testclass="DurationAssertion" testname="响应时间断言">\n'
                f'  <stringProp name="DurationAssertion.duration">{duration_val}</stringProp>\n'
                f'</DurationAssertion>')

    pattern = re.compile(
        r'<ResponseAssertion[^>]*>.*?Assertion\.response_time.*?</ResponseAssertion>',
        re.DOTALL
    )
    if pattern.search(xml_content):
        xml_content = pattern.sub(_fix_duration_assertion, xml_content)
        fixes.append("将 ResponseAssertion(response_time) 替换为 DurationAssertion")

    # Fix 3: 为缺少 hashTree 的元素补上 <hashTree/>
    testable_tags = [
        'HeaderManager', 'ResponseAssertion', 'DurationAssertion',
        'JSONPathAssertion', 'ResultCollector', 'JSONPostProcessor',
        'RegexExtractor', 'UniformRandomTimer', 'CookieManager',
        'CSVDataSet'
    ]
    for tag in testable_tags:
        close_pattern = re.compile(
            rf'(</{tag}>)\s*(?!<hashTree)',
        )
        if close_pattern.search(xml_content):
            xml_content = close_pattern.sub(r'\1\n          <hashTree/>', xml_content)
            fixes.append(f"为 {tag} 补充缺失的 hashTree")

    # Fix 4: 去除重复的 <hashTree/>
    xml_content = re.sub(r'(<hashTree/>)\s+\1', r'\1', xml_content)

    return xml_content, fixes


def _validate_jmx_structure(xml_content: str) -> list:
    """验证 JMX XML 结构，返回警告列表"""
    warnings = []

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        return [f"XML 解析错误: {e}"]

    for elem in root.iter():
        tag = elem.tag

        # 检测 HTTPSampler.headers（错误的请求头放置方式）
        if tag == 'HTTPSamplerProxy':
            headers_prop = elem.find("stringProp[@name='HTTPSampler.headers']")
            if headers_prop is not None:
                warnings.append("检测到 HTTPSampler.headers 属性，应使用 HTTPHeaderManager 元素")

        # 检测 ResponseAssertion 被用于持续时间断言
        if tag == 'ResponseAssertion':
            test_field = elem.find("stringProp[@name='Assertion.test_field']")
            if test_field is not None and test_field.text and 'response_time' in test_field.text:
                warnings.append("检测到 ResponseAssertion 用作持续时间断言，应使用 DurationAssertion")

    return warnings


async def generate_jmeter_node(state: WorkflowState) -> dict:
    """JMeter 脚本生成节点

    处理流程：
    1. 获取 Curl 命令或接口文档
    2. 调用 LLM 生成 JMeter .jmx XML 脚本
    3. 清理输出（去除 markdown 标记）
    4. 自动修正常见结构错误
    5. 验证 XML 格式
    6. 保存 .jmx 文件到磁盘
    """
    raw_text = state.get("raw_text", "")
    file_path = state.get("file_path", "")

    input_content = _parse_input_content(raw_text, file_path)

    if not input_content or not input_content.strip():
        return {"error": "没有可用的输入内容，请提供 Curl 命令或接口文档"}

    project_name = _generate_project_name(input_content)

    llm = create_llm(temperature=0.1)

    try:
        logger.info("开始生成 JMeter 脚本...")
        logger.info(f"项目名称: {project_name}, 输入内容长度: {len(input_content)}")

        jmx_prompt = JMX_GENERATION_PROMPT % input_content

        response = await llm.ainvoke([
            SystemMessage(content="你是一位资深性能测试工程师，精通 JMeter 工具和 XML 格式。只输出有效的 XML 代码，不要输出任何解释。"),
            HumanMessage(content=jmx_prompt),
        ])

        jmx_content = response.content
        logger.debug(f"LLM ��回(JMX), 长度={len(jmx_content)}: {jmx_content[:3000]}")
        jmx_content = _clean_xml_output(jmx_content)

        # 验证 XML 格式（基本检查）
        if not jmx_content.startswith('<?xml') or '<jmeterTestPlan' not in jmx_content:
            logger.warning("生成的 XML 格式可能不标准")
        else:
            logger.info("XML 格式验证通过")

        # 自动修正常见结构错误
        jmx_content, auto_fixes = _auto_fix_jmx(jmx_content)
        if auto_fixes:
            for fix in auto_fixes:
                logger.info(f"自动修正: {fix}")
        else:
            logger.debug("未发现需要自动修正的问题")

        # 结构验证（修正后检查）
        warnings = _validate_jmx_structure(jmx_content)
        if warnings:
            for w in warnings:
                logger.warning(f"结构警告: {w}")
        else:
            logger.info("结构验证通过")

        # 保存 .jmx 文件
        filename = f"{project_name}.jmx"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(jmx_content)

        logger.info(f"JMeter 脚本已保存: {filepath}")

        # 统计脚本信息
        http_requests = jmx_content.count('<HTTPSamplerProxy')
        assertions = (jmx_content.count('<ResponseAssertion')
                      + jmx_content.count('<DurationAssertion')
                      + jmx_content.count('<JSONPathAssertion'))
        extractors = jmx_content.count('<JSONPostProcessor') + jmx_content.count('<RegexExtractor')

        logger.info(f"脚本统计: HTTP请求={http_requests}, 断言={assertions}, 提取器={extractors}")

        return {
            "jmx_script": jmx_content,
            "output_jmx": filepath,
            "project_name": project_name,
            "raw_content": input_content,
        }

    except Exception as e:
        import traceback
        logger.error(f"JMeter 脚本生成失败: {type(e).__name__}: {e}")
        logger.debug(f"错误详情:\n{traceback.format_exc()}")
        return {"error": f"JMeter 脚本生成失败: {str(e)}"}
