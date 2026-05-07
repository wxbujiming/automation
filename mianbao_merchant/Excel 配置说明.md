# Excel 接口测试配置指南

## 📋 表格列结构总览

本配置文件使用 Excel 表格格式管理 API 接口测试用例，共包含 8 列（A-H 列）。

| 列号 | 字段名 | 中文名称 | 必填 | 填写说明 |
|------|--------|----------|------|----------|
| A | `api_id` | 接口编号 | 否 | API 唯一标识符，用于区分不同接口 |
| B | `api_name` | 接口名称 | 是 | 接口的功能描述或业务名称 |
| C | `method` | 请求方式 | 是 | HTTP 请求方法 |
| D | `url` | 接口路径 | 是 | API 的访问地址或端点路径 |
| E | `params` | 查询参数 | 否 | URL 查询字符串参数（GET 请求常用） |
| F | `headers` | 请求头 | 否 | HTTP 请求头信息 |
| G | `body` | 请求体 | 否 | 请求体数据（POST/PUT 请求使用） |
| H | `assertions` | 验证规则 | 否 | 响应结果的验证配置 |

---

## 📝 各列详细配置说明

### A 列：接口编号 (`api_id`)

**作用：** 为每个接口分配唯一标识符，便于日志追踪和问题定位。

**填写规则：**
- 可选填，不填时系统会自动生成编号
- 建议使用有意义的命名，如 `API_001`、`LOGIN_01`、`USER_GET_001`
- 同一工作簿内编号应唯一

**示例：**
```
API_001
LOGIN_01
USER_INFO_GET
ORDER_CREATE_001
```

---

### B 列：接口名称 (`api_name`)

**作用：** 描述接口的功能用途，在测试报告中显示。

**填写规则：**
- **必填项**
- 使用简洁清晰的中文或英文描述
- 建议体现业务场景和操作类型

**示例：**
```
用户登录接口
获取用户详细信息
创建订单
查询商品列表
更新个人资料
删除指定记录
```

---

### C 列：请求方式 (`method`)

**作用：** 指定 HTTP 请求方法。

**填写规则：**
- **必填项**
- 支持的值：`GET`、`POST`、`PUT`、`DELETE`、`PATCH`、`HEAD`、`OPTIONS`
- 不区分大小写（推荐大写）

**示例：**
```
GET
POST
PUT
DELETE
PATCH
```

**使用场景参考：**
| 方法 | 用途 |
|------|------|
| GET | 获取资源/查询数据 |
| POST | 创建新资源/提交数据 |
| PUT | 完整更新资源 |
| PATCH | 部分更新资源 |
| DELETE | 删除资源 |

---

### D 列：接口路径 (`url`)

**作用：** 指定 API 的访问地址。

**填写规则：**
- **必填项**
- 支持两种格式：
  1. **完整 URL**：`https://api.example.com/v1/login`
  2. **相对路径**：`/api/v1/login`（需配合基础 URL 配置使用）
- 可包含路径参数：`/api/users/{userId}`

**示例：**
```
https://api.example.com/v1/login
/api/v1/users
/api/v1/orders/{orderId}
http://localhost:8080/api/test
/api/v1/products?category=electronics
```

---

### E 列：查询参数 (`params`)

**作用：** 配置 URL 查询字符串参数，常用于 GET 请求的筛选、分页等。

**填写规则：**
- 可选项
- 格式：`{键=值，键=值}`（使用花括号包裹，等号连接，逗号分隔）
- 参数会自动拼接到 URL 后面形成完整查询串

**示例：**
```
{pageSize=10,pageNum=1}
{keyword=手机，category=electronics,sort=price_asc}
{status=active,limit=100}
{startDate=2024-01-01,endDate=2024-12-31}
```

**实际效果示例：**
- 填写：`{pageSize=10,pageNum=1}`
- 最终 URL：`/api/v1/users?pageSize=10&pageNum=1`

---

### F 列：请求头 (`headers`)

**作用：** 配置 HTTP 请求头信息，如认证 Token、内容类型等。

**填写规则：**
- 可选项
- 格式：`键：值，键：值`（冒号连接，逗号分隔）
- 常见用途：设置 `Content-Type`、`Authorization`、自定义头等

**示例：**
```
Content-Type:application/json
Authorization:Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type:application/json,Accept:application/json
X-Request-ID:req_123456,User-Agent:APITestClient/1.0
```

**常用请求头参考：**
| 请求头 | 说明 | 示例 |
|--------|------|------|
| Content-Type | 请求体格式 | `application/json` |
| Authorization | 认证令牌 | `Bearer <token>` |
| Accept | 期望响应格式 | `application/json` |
| User-Agent | 客户端标识 | `APITestClient/1.0` |
| X-Request-ID | 请求追踪 ID | `req_123456` |

---

### G 列：请求体 (`body`)

**作用：** 配置请求体数据，用于 POST、PUT、PATCH 等需要提交数据的请求。

**填写规则：**
- 可选项（GET/DELETE 请求通常不需要）
- 格式：标准 JSON 对象
- 确保 JSON 语法正确（双引号、逗号、括号匹配）

**示例：**
```json
{"username":"admin","password":"123456"}
{"productId":1001,"quantity":2,"address":"北京市朝阳区"}
{"name":"张三","age":28,"email":"zhangsan@example.com"}
{"status":"ACTIVE","priority":1,"tags":["urgent","vip"]}
```

**使用场景参考：**
| 请求方法 | 是否需要 Body | 典型用途 |
|----------|---------------|----------|
| GET | 否 | 查询数据（参数放在 URL 或 params 列） |
| POST | 是 | 创建资源、提交表单 |
| PUT | 是 | 完整更新资源 |
| PATCH | 是 | 部分更新资源 |
| DELETE | 通常否 | 删除资源（ID 常放在 URL 中） |

---

### H 列：验证规则 (`assertions`)

**作用：** 配置响应结果的验证条件，自动判断接口调用是否成功。

**填写规则：**
- 可选项
- 格式：标准 JSON 对象
- 键：响应数据中的字段路径（支持嵌套，用点分隔）
- 值：期望值（支持具体值、特殊标记 `"存在"`、数值、布尔值等）

**示例：**
```json
{"code":0,"message":"success"}
{"code":0,"data.token":"存在","data.userId":123}
{"status":200,"data.list.0.id":1,"data.total":100}
{"success":true,"data.username":"admin","data.role":"manager"}
```

**字段路径写法：**
| 路径示例 | 说明 |
|----------|------|
| `code` | 响应根层级的 code 字段 |
| `data.token` | data 对象下的 token 字段 |
| `data.user.id` | data.user 对象下的 id 字段 |
| `data.list.0.id` | data 数组第一个元素的 id 字段 |
| `data.items.1.name` | data 数组第二个元素的 name 字段 |

**特殊值说明：**
| 期望值 | 说明 | 示例 |
|--------|------|------|
| `"存在"` | 检查字段是否存在且有值 | `{"data.token":"存在"}` |
| 数字 | 精确匹配数值 | `{"code":0,"total":100}` |
| true/false | 匹配布尔值 | `{"success":true}` |
| 字符串 | 精确匹配文本（区分大小写） | `{"message":"操作成功"}` |

---

## 📊 完整配置示例

### 示例 1：用户登录接口

| A-接口编号 | B-接口名称 | C-请求方式 | D-接口路径 | E-查询参数 | F-请求头 | G-请求体 | H-验证规则 |
|------------|------------|------------|------------|------------|----------|----------|------------|
| LOGIN_01 | 用户登录接口 | POST | /api/v1/login | | Content-Type:application/json | {"username":"admin","password":"123456"} | {"code":0,"data.token":"存在","data.userId":"存在"} |

---

### 示例 2：获取用户信息接口

| A-接口编号 | B-接口名称 | C-请求方式 | D-接口路径 | E-查询参数 | F-请求头 | G-请求体 | H-验证规则 |
|------------|------------|------------|------------|------------|----------|----------|------------|
| USER_GET_01 | 获取用户详细信息 | GET | /api/v1/users/{userId} | {includeProfile=true} | Authorization:Bearer {{token}},Accept:application/json | | {"code":0,"data.username":"admin","data.email":"存在"} |

---

### 示例 3：创建订单接口

| A-接口编号 | B-接口名称 | C-请求方式 | D-接口路径 | E-查询参数 | F-请求头 | G-请求体 | H-验证规则 |
|------------|------------|------------|------------|------------|----------|----------|------------|
| ORDER_CREATE_01 | 创建新订单 | POST | /api/v1/orders | | Content-Type:application/json,Authorization:Bearer {{token}} | {"productId":1001,"quantity":2,"shippingAddress":"北京市朝阳区"} | {"code":0,"message":"创建成功","data.orderId":"存在"} |

---

### 示例 4：查询商品列表接口

| A-接口编号 | B-接口名称 | C-请求方式 | D-接口路径 | E-查询参数 | F-请求头 | G-请求体 | H-验证规则 |
|------------|------------|------------|------------|------------|----------|----------|------------|
| PRODUCT_LIST_01 | 查询商品列表 | GET | /api/v1/products | {category=electronics,page=1,pageSize=20} | Accept:application/json | | {"code":0,"data.total":">=1","data.list.0.price":">0"} |

---

## ⚠️ 配置注意事项

### 1. JSON 格式规范
- ✅ 正确：`{"code":0,"message":"success"}`
- ❌ 错误：`{code:0,message:'success'}`（键必须用双引号，不能用单引号）

### 2. Excel 单元格格式
- 建议将包含 JSON 的列（E、F、G、H 列）设置为**文本格式**
- 如果 Excel 自动转换格式，可在内容前加单引号强制识别为文本：`'{\"code\":0}`

### 3. 特殊字符处理
- JSON 中的双引号需要正确转义或在 Excel 中使用文本格式
- 路径参数 `{userId}` 不要与 params 的花括号格式混淆

### 4. 引用变量
- 使用 `{{变量名}}` 语法引用前置接口返回的值
- 示例：`Authorization:Bearer {{token}}` 会替换为实际的 token 值

### 5. 空值处理
- 不需要填写的列保持空白即可
- GET/DELETE 请求的 Body 列通常留空
- 无查询参数时 params 列留空

---

## 🧪 测试执行

配置完成后，运行测试程序：

```bash
python main.py
```

程序执行流程：
1. 读取 Excel 文件中的所有接口配置行
2. 解析每一列的配置信息（A-H 列）
3. 构建完整的 HTTP 请求（URL + 参数 + 头 + 体）
4. 发送请求并获取响应
5. 根据 H 列验证规则校验响应结果
6. 输出测试报告（包含每个接口的详细结果）
7. 生成统计汇总（成功数/失败数/通过率）

---

## 📈 测试报告示例

```
============================================================
📋 开始执行接口测试...
============================================================

[1/4] LOGIN_01 - 用户登录接口
    请求：POST https://api.example.com/api/v1/login
    状态码：200
    ✅ 验证通过：code=0, data.token 存在，data.userId 存在

[2/4] USER_GET_01 - 获取用户详细信息
    请求：GET https://api.example.com/api/v1/users/123?includeProfile=true
    状态码：200
    ✅ 验证通过：code=0, data.username=admin, data.email 存在

[3/4] ORDER_CREATE_01 - 创建新订单
    请求：POST https://api.example.com/api/v1/orders
    状态码：200
    ❌ 验证失败：
       - 字段 'data.orderId' 期望='存在', 实际=未返回该字段
       - 字段 'message' 期望='创建成功', 实际='订单已存在'

[4/4] PRODUCT_LIST_01 - 查询商品列表
    请求：GET https://api.example.com/api/v1/products?category=electronics&page=1&pageSize=20
    状态码：200
    ✅ 验证通过：code=0, data.total=156, data.list.0.price>0

============================================================
📊 测试完成统计：
    总接口数：4
    ✅ 成功：3
    ❌ 失败：1
    通过率：75%
============================================================
```

---

## 📞 技术支持

如遇到配置问题，请检查：
1. Excel 文件格式是否正确（.xlsx 或 .xlsm）
2. 必填列（B、C、D 列）是否已填写
3. JSON 格式是否合法（可使用在线 JSON 验证工具）
4. 网络连通性和接口地址是否正确
5. 认证 Token 是否有效且未过期
