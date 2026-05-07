"""Prompt 模板：JMeter 脚本生成

根据 Curl 命令或接口文档，生成可执行的 JMeter 脚本（.jmx 格式）。
"""

JMX_GENERATION_PROMPT = """你是一位资深性能测试工程师，精通 JMeter 工具。请根据以下输入内容，生成完整的 JMeter 测试脚本（.jmx XML 格式）。

## 输入内容
%s

## 重要结构规则（必须严格遵守）

1. **hashTree 规则**：每个可测试元素（HTTPSamplerProxy、HeaderManager、ResponseAssertion、DurationAssertion、JSONPathAssertion、ResultCollector 等）后面必须紧跟一个 `<hashTree>` 或 `<hashTree/>`。如果该元素没有子元素，使用 `<hashTree/>`。如果有子元素，使用 `<hashTree>...</hashTree>`。

2. **嵌套规则**：断言、管理器和提取器是 HTTP 采样器 hashTree 的**兄弟元素**，而不是彼此的后代。正确的结构是：
   ```
   <HTTPSamplerProxy ...>...</HTTPSamplerProxy>
   <hashTree>
     <HeaderManager ...>...</HeaderManager>
     <hashTree/>
     <ResponseAssertion ...>...</ResponseAssertion>
     <hashTree/>
     <DurationAssertion ...>...</DurationAssertion>
     <hashTree/>
   </hashTree>
   ```
   **错误**：一个断言嵌套在另一个断言的 hashTree 内部。

3. **请求头规则**：**绝不**在 HTTPSamplerProxy 上使用 `HTTPSampler.headers` 属性。始终使用单独的 `<HeaderManager>` 元素作为采样器 hashTree 的子元素。

4. **持续时间断言**：对于响应时间验证，**必须**使用 `<DurationAssertion guiclass="DurationAssertionGui" testclass="DurationAssertion">`，带有一个 `<stringProp name="DurationAssertion.duration">5000</stringProp>` 属性。**绝不**使用带有 `response_time` 字段的 `ResponseAssertion` 来检查持续时间——那是无效的 JMeter XML。

5. **POST 请求体**：对于带有 JSON 请求体的 POST 请求，在 HTTPSamplerProxy 上设置 `<boolProp name="HTTPSampler.postBodyRaw">true</boolProp>`，并将请求体字符串放在嵌套的参数元素内部：
   ```xml
   <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
     <collectionProp name="Arguments.arguments">
       <elementProp name="" elementType="HTTPArgument">
         <stringProp name="Argument.value">{"key":"value"}</stringProp>
         <stringProp name="Argument.metadata">=</stringProp>
       </elementProp>
     </collectionProp>
   </elementProp>
   ```
   **绝不**在采样器外部使用独立的 `<Arguments>` 元素来表示 POST 请求体。

6. **监听器**：始终在 ThreadGroup 内包含一个 `<ResultCollector>`（查看结果树），以便在 JMeter 中查看结果。

## 要求

### 1. 脚本结构
生成标准的 JMeter .jmx XML 文件，包含以下组件：
- **TestPlan**: 测试计划
- **ThreadGroup**: 线程组（设置合理的默认值：线程数1，循环1次，Ramp-Up Period 1秒）
- **HTTPSamplerProxy**: HTTP 请求采样器
- **HeaderManager**: 请求头管理器（从 Curl 中提取所有请求头）
- **CookieManager**: Cookie 管理器（如果需要）
- **ResultCollector**: 结果监听器（查看结果树）
- **ResponseAssertion / DurationAssertion / JSONPathAssertion**: 断言（见下方详细要求）

### 2. 断言配置（重要）
为每个 HTTP 请求添加以下断言：
- **Response Code Assertion**: 使用 `ResponseAssertion` 元素，`Assertion.test_field` 设为 `Assertion.response_code`，`Assertion.test_type` 设为 `2`（包含），在 `Assertion.test_strings` 集合中添加状态码
- **Response Data Assertion**: 使用 `ResponseAssertion` 元素，`Assertion.test_field` 设为 `Assertion.response_data`，在 `Assertion.test_strings` 集合中添加预期内容
  - 如果是 JSON API，可额外添加 `JSONPathAssertion` 验证关键业务字段
- **Duration Assertion**: 使用 `DurationAssertion` 元素（guiclass="DurationAssertionGui" testclass="DurationAssertion"），`DurationAssertion.duration` 设为毫秒数（默认 5000）

### 3. 参数提取
如果响应数据需要后续使用，添加：
- **JSONPostProcessor** 或 **RegexExtractor**：从响应中提取变量
- **CSS Selector Extractor**：从 HTML 中提取元素

### 4. 变量化
- 将请求中的动态值（如 ID、时间戳等）提取为 JMeter 变量
- 添加 **User Defined Variables** 元素管理常用变量
- 使用 **CSVDataSet** 支持参数化测试

### 5. 关联处理
- 如果是多个相关请求，添加 **Post Processors** 处理数据关联
- 使用 **JSONPostProcessor** 或 **RegexExtractor** 提取关联数据

### 6. 思考处理器（Think Time）
- 在请求之间添加合理的思考时间（使用 **UniformRandomTimer**）

## 输入格式处理

### Curl 命令格式
```bash
curl 'https://api.example.com/users' \\
  -H 'Authorization: Bearer token123' \\
  -H 'Content-Type: application/json' \\
  -d '{"name":"test"}'
```
需要解析：
- URL 和方法（GET/POST/PUT/DELETE）
- 请求头（-H 参数）
- 请求体（-d 参数）

### 接口文档格式
```markdown
# 用户登录接口

**请求地址**: POST /api/login
**请求头**:
  Content-Type: application/json
  Authorization: Bearer {{token}}

**请求体**:
```json
{
  "username": "testuser",
  "password": "123456"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "userId": "123",
    "token": "abc123"
  }
}
```

**业务规则**:
- 用户名必须存在
- 密码长度不少于6位
```
根据文档生成完整的测试场景。

## 输出格式

1. **只输出完整的 XML 代码**，不要包含任何解释文字
2. XML 必须是有效的 .jmx 格式，可直接在 JMeter 中打开
3. XML 声明：`<?xml version="1.0" encoding="UTF-8"?>`
4. 根元素：`<jmeterTestPlan>`
5. 使用合理的 guiclass 和 testclass 属性
6. 确保所有元素都包含必要的 hashTree 子元素

## 示例 .jmx 结构（GET + POST 完整示例）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="测试计划">
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="线程组" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanelGui" testclass="LoopController" testname="循环控制器" enabled="true">
          <stringProp name="LoopController.loops">1</stringProp>
          <boolProp name="LoopController.continue_forever">false</boolProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">1</stringProp>
        <stringProp name="ThreadGroup.ramp_time">1</stringProp>
        <boolProp name="ThreadGroup.scheduler">false</boolProp>
        <stringProp name="ThreadGroup.duration"></stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="GET请求">
          <stringProp name="HTTPSampler.domain">api.example.com</stringProp>
          <stringProp name="HTTPSampler.port">443</stringProp>
          <stringProp name="HTTPSampler.protocol">https</stringProp>
          <stringProp name="HTTPSampler.path">/users</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
        </HTTPSamplerProxy>
        <hashTree>
          <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="请求头管理器">
            <collectionProp name="HeaderManager.headers">
              <elementProp name="Authorization" elementType="Header">
                <stringProp name="Header.name">Authorization</stringProp>
                <stringProp name="Header.value">Bearer token123</stringProp>
              </elementProp>
              <elementProp name="Content-Type" elementType="Header">
                <stringProp name="Header.name">Content-Type</stringProp>
                <stringProp name="Header.value">application/json</stringProp>
              </elementProp>
            </collectionProp>
          </HeaderManager>
          <hashTree/>
          <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="响应码断言">
            <collectionProp name="Assertion.test_strings">
              <stringProp name="49586">200</stringProp>
            </collectionProp>
            <stringProp name="Assertion.test_field">Assertion.response_code</stringProp>
            <intProp name="Assertion.test_type">2</intProp>
          </ResponseAssertion>
          <hashTree/>
          <DurationAssertion guiclass="DurationAssertionGui" testclass="DurationAssertion" testname="响应时间断言">
            <stringProp name="DurationAssertion.duration">5000</stringProp>
          </DurationAssertion>
          <hashTree/>
        </hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="POST请求">
          <stringProp name="HTTPSampler.domain">api.example.com</stringProp>
          <stringProp name="HTTPSampler.port">443</stringProp>
          <stringProp name="HTTPSampler.protocol">https</stringProp>
          <stringProp name="HTTPSampler.path">/users</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
            <collectionProp name="Arguments.arguments">
              <elementProp name="" elementType="HTTPArgument">
                <stringProp name="Argument.value">{"name":"test","age":25}</stringProp>
                <stringProp name="Argument.metadata">=</stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
        </HTTPSamplerProxy>
        <hashTree>
          <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="请求头管理器">
            <collectionProp name="HeaderManager.headers">
              <elementProp name="Content-Type" elementType="Header">
                <stringProp name="Header.name">Content-Type</stringProp>
                <stringProp name="Header.value">application/json</stringProp>
              </elementProp>
            </collectionProp>
          </HeaderManager>
          <hashTree/>
          <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="响应码断言">
            <collectionProp name="Assertion.test_strings">
              <stringProp name="49586">200</stringProp>
            </collectionProp>
            <stringProp name="Assertion.test_field">Assertion.response_code</stringProp>
            <intProp name="Assertion.test_type">2</intProp>
          </ResponseAssertion>
          <hashTree/>
          <DurationAssertion guiclass="DurationAssertionGui" testclass="DurationAssertion" testname="响应时间断言">
            <stringProp name="DurationAssertion.duration">5000</stringProp>
          </DurationAssertion>
          <hashTree/>
        </hashTree>
        <ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="查看结果树">
          <boolProp name="ResultCollector.error_logging">false</boolProp>
          <objProp>
            <name>saveConfig</name>
            <value class="SampleSaveConfiguration">
              <time>true</time>
              <latency>true</latency>
              <timestamp>true</timestamp>
              <success>true</success>
              <label>true</label>
              <code>true</code>
              <message>true</message>
              <threadName>true</threadName>
              <dataType>true</dataType>
              <encoding>false</encoding>
              <assertions>true</assertions>
              <subresults>true</subresults>
              <responseData>false</responseData>
              <samplerData>false</samplerData>
              <xml>false</xml>
              <fieldNames>true</fieldNames>
              <responseHeaders>true</responseHeaders>
              <requestHeaders>true</requestHeaders>
              <responseDataOnError>true</responseDataOnError>
              <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
              <assertionsResultsToSave>0</assertionsResultsToSave>
              <bytes>true</bytes>
              <sentBytes>true</sentBytes>
              <url>true</url>
              <threadCounts>true</threadCounts>
              <idleTime>true</idleTime>
              <connectTime>true</connectTime>
            </value>
          </objProp>
          <stringProp name="filename"></stringProp>
        </ResultCollector>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
```

请根据输入内容生成完整的 JMeter .jmx 脚本。只输出 XML 代码。"""
