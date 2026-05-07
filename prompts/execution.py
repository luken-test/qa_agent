"""Prompt 模板：测试脚本生成

根据测试用例 JSON，生成结构化的 Playwright 测试脚本模板。
使用 TODO 标注需要人工补充的真实系统信息。
"""

TEST_SCRIPT_PROMPT = """你是一位资深自动化测试工程师。请根据以下测试用例，生成 Playwright 测试脚本模板。

## 测试用例数据
{testcases}

## 核心规则

你只能看到需求描述，看不到真实系统的代码和页面。因此必须遵守以下规则：

1. **URL 必须用常量占位**，不要编造真实地址：
   ```python
   BASE_URL = "TODO: 填入实际测试环境地址，如 http://staging.example.com"
   LOGIN_URL = f"{{BASE_URL}}/login"
   ```

2. **页面元素用语义化定位 + TODO 标注**，不要编造 CSS 选择器：
   ```python
   # TODO: 根据实际页面确认定位器
   page.get_by_role("button", name="下载")
   page.get_by_placeholder("请输入用户名")
   page.locator("[data-testid='submit-btn']")  # TODO: 确认 testid
   ```

3. **测试数据用变量占位**，不要编造账号密码：
   ```python
   TEST_USER = {{"username": "TODO", "password": "TODO"}}
   ```

4. **断言写业务语义**，不要编造具体的返回值：
   ```python
   assert "成功" in result.text_content()  # TODO: 确认实际提示文案
   assert page.url == f"{{BASE_URL}}/success"  # TODO: 确认实际跳转路径
   ```

## 代码要求

1. 使用 Python + Playwright（同步 API）
2. 每个测试用例对应一个独立函数：test_tc{{编号}}_{{简述}}
3. 每个函数 10-20 行，包含 docstring + 断言
4. 顶部集中定义所有 TODO 常量（BASE_URL、测试账号等）
5. 登录逻辑提取为辅助函数 login(page)
6. 包含 if __name__ == "__main__" 入口
7. 只输出 Python 代码，不要输出其他内容

重要：必须输出完整代码，不要截断。"""
