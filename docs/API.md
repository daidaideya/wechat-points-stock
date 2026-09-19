# API 业务接口参考

本文说明 Web 管理台和青龙脚本使用的业务接口。接口的机器可读契约以
[`docs/openapi.json`](./openapi.json) 为准；代码变更后请运行
`python scripts/export_openapi.py --check` 检查基线是否同步。

## 1. 基本约定

- 基础路径：`/api/v1`。
- JSON 接口使用 `Content-Type: application/json`；数据库导入和图片上传使用
  `multipart/form-data`。
- 成功响应通常返回 JSON；数据库导出返回下载文件。
- 业务错误使用 `{"detail": "..."}`，请求校验错误通常为 HTTP `422`。
- API 和健康检查响应带 `X-Request-ID`，排查问题时可同时记录该值和 HTTP 状态码。
- 时间字段会按各接口的历史兼容规则返回 ISO 字符串；前端展示统一经过
  `frontend/src/utils/date.js` 转换，不要在客户端直接截取字符串判断“今天”。

## 2. 鉴权边界

### 2.1 浏览器管理台接口

当设置页未开启访问保护时，浏览器接口无需额外凭据。开启后，先调用：

```http
POST /api/v1/access/verify
Content-Type: application/json

{"access_key":"<管理台访问密钥>"}
```

校验成功返回 `{"status":"success"}`，服务端通过 `Set-Cookie` 写入短时效
HttpOnly Cookie `site_access_session`。后续请求应使用浏览器自动携带的 Cookie；
服务端仍在迁移窗口接受 `X-Access-Key`，但新客户端不应把访问密钥持久化到
`localStorage`，也不能放进 URL、日志或错误信息。

启动访问页时可调用：

```http
GET /api/v1/access/status
```

响应包含 `enabled`、`configured`、`authenticated` 三个状态字段。访问审计查询
`/api/v1/access/audit-events` 也属于管理台鉴权范围，不返回数据库主键或任何密钥
材料。

### 2.2 青龙/采集脚本接口

积分、库存和图片上传属于机器接口，使用部署配置中的 `INGEST_TOKEN`（兼容旧变量
`API_TOKEN` 一版迁移）：

```http
Authorization: Bearer <INGEST_TOKEN>
```

该凭据与管理台访问密钥、青龙 OpenAPI 的 Client Secret 是三套不同的凭据，不能
互换。未配置或不匹配时返回 `401`。

## 3. 青龙上报接口

### 3.1 积分/现金上报

`POST /api/v1/qinglong/report`

请求体：

```json
{
  "script_id": "points-script",
  "execution_time": "2026-09-19T10:00:00+08:00",
  "data": {
    "wechat_accounts": [
      {
        "wechat_id": "wx_001",
        "nickname": "示例账号",
        "phone": "13800000000",
        "points_data": [
          {
            "program_id": "program_001",
            "program_name": "示例小程序",
            "current_points": 123.45,
            "current_cash": 6.8,
            "auth_type": "code"
          }
        ]
      }
    ]
  }
}
```

规则：

- `current_points` 与 `current_cash` 至少提供一个；只上报积分的旧脚本仍兼容。
- 数值必须是有限且非负的数字或数字字符串；缺失的维度会保存为“未上报”，不等于
  `0`。
- 单次最多 100 个账号、每个账号最多 500 个程序、总积分行最多 5000 行。
- `auth_type` 支持 `code`、`token`、`app`；未传时保留已有类型或使用默认类型。
- 服务端同时写入历史记录和当前余额快照，并按设置裁剪旧历史。

成功响应示例：

```json
{"status":"success","batch_id":"<server-generated-id>"}
```

### 3.2 库存全量快照上报

`POST /api/v1/stock-report`

请求体：

```json
{
  "program_id": "program_001",
  "snapshot_id": "snapshot-20260919-1000",
  "snapshot_complete": true,
  "expected_product_count": 2,
  "products": [
    {
      "product_id": "product_001",
      "product_name": "纯积分商品",
      "stock": 50,
      "points": 100,
      "last_updated": "2026-09-19T10:00:00+08:00"
    },
    {
      "product_id": "product_002",
      "product_name": "积分加钱购",
      "stock": 10,
      "points": 500,
      "cash": 9.9,
      "image_url": "https://example.test/product.jpg"
    }
  ]
}
```

规则：

- `product_id` 可省略，省略时使用 `product_name` 作为兼容 ID。
- `cash` 为元；省略或 `0` 表示纯积分商品。
- 单次最多 2000 个商品，商品积分、库存、现金价必须非负。
- 完整快照需要 `snapshot_complete=true`（默认）且数量与
  `expected_product_count` 一致；空快照、部分快照或数量不一致不会自动下架旧商品。
- 服务端会在响应的 `snapshot` 中返回判定状态、商品数量和是否执行下架。

响应重点字段：

```json
{
  "status": "success",
  "updated_products": [],
  "unlisted_products": [],
  "snapshot": {
    "id": "snapshot-20260919-1000",
    "is_complete": true,
    "status": "complete",
    "reported_product_count": 2,
    "expected_product_count": 2,
    "unlisting_applied": true,
    "unlisting_skipped_reason": null
  }
}
```

完整的采集脚本示例和快照迁移说明见
[`docs/库存上报.md`](./库存上报.md)。

## 4. 管理台查询接口

以下接口使用浏览器管理台鉴权边界。返回字段以 OpenAPI 基线为准。

### 4.1 总览、积分和账号

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/dashboard` | 仪表盘统计、未上报摘要和最近更新 |
| `GET` | `/points` | 按账号返回积分/现金概览和程序摘要 |
| `GET` | `/accounts` | 账号列表及活跃程序、活跃 APP 数 |
| `GET` | `/accounts/{wechat_id}` | 单个账号及积分摘要 |
| `GET` | `/accounts/{wechat_id}/points_details` | 单个账号的积分明细 |
| `PUT` | `/accounts/{wechat_id}` | 新增或更新昵称、设备、手机号 |
| `PUT` | `/accounts/sort-order` | 按 `{"wechat_ids":[...]}` 保存账号顺序 |
| `DELETE` | `/accounts/{wechat_id}` | 删除账号及其积分历史/余额快照 |
| `DELETE` | `/accounts/{wechat_id}/programs/{program_id}` | 删除一个账号-程序的积分记录 |

账号更新体示例：

```json
{"nickname":"新昵称","device":"iPhone","phone":"13800000000"}
```

### 4.2 小程序和 APP

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/programs` | 分页、搜索、标签、收藏、青龙状态和类型筛选 |
| `GET` | `/programs/favorites` | 收藏程序列表 |
| `GET` | `/programs/unreported` | 当前业务日未上报程序 |
| `GET` | `/programs/{program_id}` | 程序详情和积分排行 |
| `GET` | `/programs/{program_id}/ranking` | 程序积分排行 |
| `GET` | `/programs/{program_id}/rankings` | `/ranking` 的兼容复数别名 |
| `GET` | `/programs/{program_id}/stock` | 程序库存、库存变化和余额摘要 |
| `PUT` | `/programs/{program_id}` | 更新类型、置顶、收藏、备注、标签、归档状态 |
| `DELETE` | `/programs/{program_id}` | 删除程序及关联业务数据 |

`GET /programs` 常用查询参数：

- `page`、`size`：分页，默认 `1`、`21`。
- `q`：按程序名、ID 或拼音搜索。
- `kind=mini|app`：程序类型。
- `status=active|archived`：归档状态。
- `is_favorite=true|false`、`tag`：收藏和标签筛选。
- `ql_status=all|enabled|disabled|unknown`：青龙状态筛选。
- `sort=default|cron`：默认排序或按 cron 最早时间排序。

程序更新体字段为 `auth_type`、`is_pinned`、`is_favorite`、`note`、`tags` 和
`is_archived`；未提供的字段保持不变。归档程序会自动取消收藏。

### 4.3 青龙任务和审计

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/qinglong/crons` | 从已配置的青龙 OpenAPI 拉取任务列表 |
| `POST` | `/qinglong/crons/schedules` | 批量更新任务 cron 并重新同步 |
| `GET` | `/access/audit-events` | 分页查询不含凭据的访问审计事件 |

青龙批量更新体：

```json
{"items":[{"id":"cron-id","schedule":"0 9 * * *"}]}
```

需要先在设置中配置青龙 URL、Client ID 和 Client Secret；单次最多更新 500 个
任务，cron 表达式必须包含 5 或 6 个字段。审计查询支持 `page`、`size`、
`event_type`、`client_id`，`size` 最大为 100。

## 5. 库存管理接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/stock/center` | 库存中心分页、筛选、汇总 |
| `GET` | `/stock/programs` | 按程序汇总商品数和库存数 |
| `GET` | `/stock/programs/{program_id}/products` | 程序商品分页 |
| `GET` | `/stock/search` | 全局商品名搜索 |
| `GET` | `/stock/hidden` | 手动隐藏商品分页 |
| `GET` | `/stock/off-shelf` | 自动下架商品按程序分组分页 |
| `POST` | `/stock/product` | 手工新增或更新商品 |
| `PUT` | `/stock/products/{product_id}/hide` | 手动隐藏商品 |
| `PUT` | `/stock/products/{product_id}/restore` | 取消手动隐藏 |
| `PUT` | `/stock/products/{product_id}/relist` | 恢复自动下架商品 |

`GET /stock/center` 常用查询参数：

- `page`、`size`：默认 `1`、`20`，`size` 最大为 100。
- `q`：匹配商品名、商品 ID、程序 ID 或程序名。
- `tag`：按程序标签筛选。
- `status=all|in_stock|out_of_stock|redeemable`：库存/可兑换状态。
- `price_mode=all|points_only|points_plus_cash`：价格类型。
- `cash_max`：仅在积分加钱购筛选时限制现金价上限。

响应包含 `items`、`total`、`page`、`size`、`summary`、`available_tags`、
`hidden_total` 和 `off_shelf_total`。SQLite 下库存中心使用数据版本生成 ETag：

```http
GET /api/v1/stock/center?page=1&size=20
If-None-Match: "..."
```

数据未变化时返回 `304`；客户端必须保留现有数据，不要把 `304` 当成空列表。

手工商品写入体：

```json
{
  "program_id":"program_001",
  "product_id":"product_001",
  "product_name":"纯积分商品",
  "points":100,
  "cash":0,
  "stock":50,
  "image_url":"https://example.test/product.jpg"
}
```

## 6. 设置、备份和上传

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET/POST` | `/settings/logs` | 日志保留、访问保护和访问密钥更新 |
| `GET/POST` | `/settings/qinglong` | 青龙 URL、凭据、同步间隔和同步模式 |
| `POST` | `/settings/qinglong/sync` | 立即触发青龙同步 |
| `GET/POST` | `/settings/bark` | Bark 开关、服务器、设备密钥和推送时间 |
| `POST` | `/settings/bark/test` | 发送测试推送 |
| `GET` | `/settings/database/export` | 下载当前 SQLite 数据库备份 |
| `POST` | `/settings/database/import` | 上传并校验 SQLite 备份后恢复 |
| `POST` | `/upload/image` | 上传商品图片并可回写商品本地图片路径 |

设置更新时，空的青龙 Secret、Bark Device Key 和访问密钥字段表示“不修改”，
不会因为保存其他设置而清空现有凭据。数据库导入会执行文件大小、SQLite 完整性、
核心表校验和维护锁；导入失败应保留当前数据库。

图片上传要求：

- `file` 为必填文件字段，支持 JPEG、PNG、GIF、WebP，并校验文件头。
- 单文件最大 10 MiB，最大像素数 25 MP；失败时服务端清理临时文件。
- 可选 `product_id`、`program_id`，同时提供时会更新商品的本地图片路径。

## 7. 健康检查和问题排查

健康检查不在 `/api/v1` 下：

```http
GET /health/live
GET /health/ready
```

前者只确认进程存活，后者还检查数据库等就绪条件。排查业务请求时建议记录：

1. 请求方法和完整路径（不要记录访问密钥、Bearer token 或 Secret）；
2. HTTP 状态码和响应中的 `detail`；
3. 响应头 `X-Request-ID`；
4. 对库存中心请求，另外记录 `ETag`、筛选参数和是否收到 `304`。

完整的路径、参数、请求体 schema 和响应 schema 以
[`docs/openapi.json`](./openapi.json) 为准。
