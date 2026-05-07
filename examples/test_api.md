# 用户登录接口

**请求地址**: POST https://api.example.com/api/login

**请求头**:
- Content-Type: application/json
- Accept: application/json

**请求体**:
```json
{
  "username": "testuser",
  "password": "123456"
}
```

**响应示例**（成功）:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "userId": "123456",
    "username": "testuser",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expireTime": 3600
  }
}
```

**响应示例**（失败）:
```json
{
  "code": 401,
  "message": "用户名或密码错误",
  "data": null
}
```

**业务规则**:
1. 用户名必须存在
2. 密码长度不少于6位
3. 登录成功后返回 token，有效期1小时

**断言要求**:
1. HTTP 状态码为 200
2. 响应 code 字���为 200
3. 响应包含 userId 和 token 字段
4. 响应时间小于 2000ms
