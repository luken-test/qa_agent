# JMeter 脚本生成功能 - 快速开始

## 功能概述

新增的 JMeter 脚本生成智能体可以：
- 解析 Curl 命令
- 解析接口文档
- 生成完整的 JMeter .jmx 脚本
- 自动添加断言（HTTP 状态码、响应数据、响应时间）
- 支持参数化和数据关联

## 快速开始

### 1. 使用 Curl 命令生成

```bash
# 简单的 GET 请求
python main.py --jmeter "curl 'https://api.example.com/users' -H 'Authorization: Bearer token123'"

# POST 请求
python main.py --jmeter "curl -X POST 'https://api.example.com/login' -H 'Content-Type: application/json' -d '{\"username\":\"test\",\"password\":\"123456\"}'"
```

### 2. 使用接口文档生成

创建接口文档文件 `api_doc.md`：

```markdown
# 用户登录接口

**请求地址**: POST /api/login

**请求头**:
- Content-Type: application/json

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

**断言要求**:
- HTTP 状态码为 200
- 响应包含 userId 和 token 字段
- 响应时间小于 5000ms
```

然后执行：
```bash
python main.py --jmeter api_doc.md
```

### 3. 通过 API 使用

```bash
# 启动服务
python server.py

# 生成 JMeter 脚本
curl -X POST http://localhost:8000/api/jmeter \
  -H "Content-Type: application/json" \
  -d '{
    "input": "curl '\''https://api.example.com/users'\'' -H '\''Authorization: Bearer token'\''",
    "input_type": "text"
  }'

# 查询任务状态
curl http://localhost:8000/api/tasks/{task_id}
```

## 生成的脚本特性

### 1. 标准组件
- ✅ TestPlan（测试计划）
- ✅ ThreadGroup（线程组）
- ✅ HTTP Request（HTTP 请求）
- ✅ HTTP Header Manager（请求头管理器）
- ✅ Cookie Manager（Cookie 管理器）
- ✅ Listeners（结果监听器）

### 2. 自动断言
- ✅ Response Code Assertion（状态码断言）
- ✅ Response Data Assertion（响应数据断言）
- ✅ Duration Assertion（响应时间断言）

### 3. 参数提取
- ✅ JSON Extractor（JSON 提取器）
- ✅ Regex Extractor（正则提取器）
- ✅ CSS Selector Extractor（CSS 选择器提取器）

### 4. 变量化
- ✅ User Defined Variables（用户定义变量）
- ✅ CSV Data Set Config（CSV 数据配置）

## 实际案例

### 案例 1：REST API 登录测试

**输入**：
```bash
curl -X POST 'https://api.example.com/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"testuser","password":"123456"}'
```

**输出**：
- 完整的 HTTP POST 请求
- Content-Type 请求头
- JSON 请求体
- 状态码断言（200）
- 响应时间断言（<5000ms）
- JSON Path 断言验证响应字段

### 案例 2：多步骤场景（登录 → 获取用户信息）

**输入**：接口文档包含多个接口

**输出**：
- 多个 HTTP 请求按顺序执行
- 从登录响应提取 token
- 后续请求使用提取的 token
- 完整的断言链

## 输出说明

生成的 .jmx 文件默认保存在 `output/` 目录。

### 输出示例

```
============================================
  执行完成! — JMeter 脚本生成
  脚本文件: E:\测试用例\qa-agent\output\jmeter_test_20250106_143022.jmx
  项目名称: jmeter_test_20250106_143022
  HTTP 请求数: 1
  断言数量: 2
  提取器数量: 0
  总耗时: 3.5s
============================================
```

## 使用生成的脚本

### 1. 在 JMeter GUI 中打开

```bash
# 启动 JMeter
jmeter

# 打开生成的 .jmx 文件
File -> Open -> 选择 output/ 目录下的 .jmx 文件
```

### 2. 命令行运行（推荐）

```bash
# 非GUI 模式运行
jmeter -n -t output/test_script.jmx -l result.jtl

# 运行并生成 HTML 报告
jmeter -n -t output/test_script.jmx -l result.jtl -e -o report/
```

### 3. 调整性能测试参数

编辑 .jmx 文件，修改 ThreadGroup 配置：

```xml
<stringProp name="ThreadGroup.num_threads">10</stringProp>
<stringProp name="ThreadGroup.ramp_time">5</stringProp>
<stringProp name="ThreadGroup.loops">100</stringProp>
```

含义：
- `num_threads`: 10 个并发用户
- `ramp_time`: 5 秒内启动所有线程
- `loops`: 每个线程执行 100 次

## 高级用法

### 1. 参数化测试

创建 CSV 文件 `users.csv`：
```csv
username,password
user1,pass1
user2,pass2
user3,pass3
```

在 JMeter 中配置 CSV Data Set Config，使用 `${username}` 和 `${password}` 变量。

### 2. 关联处理

从响应中提取数据用于后续请求：

```xml
<JSONPostProcessor guiclass="JSONPostProcessorGui" testclass="JSONPostProcessor" testname="提取Token">
  <stringProp name="JSONPostProcessor.referenceNames">token</stringProp>
  <stringProp name="JSONPostProcessor.jsonPathExprs">$.data.token</stringProp>
</JSONPostProcessor>
```

后续请求使用 `${token}` 变量。

### 3. 思考时间

在请求之间添加随机延迟：

```xml
<UniformRandomTimer guiclass="UniformRandomTimerGui" testclass="UniformRandomTimer" testname="思考时间">
  <stringProp name="ConstantTimer.delay">1000</stringProp>
  <stringProp name="RandomTimer.range">500</stringProp>
</UniformRandomTimer>
```

含义：延迟 1000±500 毫秒。

## 测试功能

运行测试脚本验证功能：

```bash
python test_jmeter.py
```

测试内容：
- ✅ Curl 命令解析
- ✅ 接口文档解析
- ✅ JMX 脚本生成
- ✅ 断言配置
- ✅ 文件保存

## 常见问题

### Q: 生成的脚本无法在 JMeter 中打开？
A: 确保使用 JMeter 5.0 或更高版本。

### Q: 断言配置不符合需求？
A: 手动编辑 .jmx 文件中的断言配置，或提供更详细的接口文档。

### Q: 如何处理 HTTPS 证书问题？
A: 在 JMeter 中配置 SSL Context Manager，或在 HTTP Request 取消 "Use KeepAlive"。

### Q: 如何调试脚本？
A: 在 JMeter GUI 中添加 "View Results Tree" 监听器查看请求响应详情。

## 技术实现

- **Prompt 工程**: 精心设计的 JMX 生成模板
- **LLM 驱动**: 使用 Claude/智谱/GPT 生成 XML 脚本
- **自动解析**: 智能解析 Curl 命令和接口文档
- **验证机制**: 自动验证 XML 格式和脚本结构

## 下一步计划

- [ ] 支持更多请求类型（WebSocket, gRPC）
- [ ] 自动生成性能测试报告
- [ ] 支持分布式测试配置
- [ ] 集成到 CI/CD 流程

---

如有问题，请查看 `examples/jmeter_example.txt` 获取更多示例。
