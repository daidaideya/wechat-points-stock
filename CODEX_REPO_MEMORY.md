# `wechat-points-stock` 仓库记忆

> 供后续 Codex/开发者快速恢复上下文使用。本文档记录的是代码实际行为优先的结论；如果本文档、README、技术文档与代码不一致，以代码为准，并在修改时同步更新文档。

后续优化清单和实施顺序见 `docs/优化路线图.md`。

## 0. 快照信息

- 仓库：`https://github.com/daidaideya/wechat-points-stock`
- 本地路径：`D:\pythonCode\wechat-points-stock`
- 分支：`main`
- 快照提交：`aabf612a47eb13f28f7f83f8ab4129dbf791628f`（2026-08-29）
- 工作区：当前正在按 `docs/优化路线图.md` 实施第二批安全/性能/运行可靠性改造；不要覆盖现有未提交修改
- 后端静态检查：`python -m compileall -q app tests` 通过
- 前端构建：已执行 `npm run build` 通过；构建会生成/刷新 `frontend/dist`
- 回归测试：`requirements-dev.txt` + `tests/`，当前 `21 passed`
- 运行可靠性：FastAPI 使用 lifespan 管理 Bark/QingLong 调度器；调度线程可由 Event 唤醒并在关闭时 join
- 可观测性：API/健康请求返回 `X-Request-ID`，并记录 route、status、duration_ms 等安全 key-value 日志
- 部署：Dockerfile 使用 Node 构建前端、Python 运行阶段，镜像自带 `frontend/dist`，运行用户为非 root

## 1. 一句话定位

这是一个“青龙脚本上报数据 + Web 管理台”的积分/现金/库存监控系统：外部脚本向 FastAPI 写入账号余额和商品全量库存，Vue SPA 从 SQLite 读取并提供用户、小程序/APP、积分、库存、青龙定时任务和 Bark 提醒管理。

## 2. 总体架构

```text
青龙脚本 / 自写采集脚本
        │ Bearer INGEST_TOKEN（兼容旧 API_TOKEN 一版）
        ├── POST /api/v1/qinglong/report
        └── POST /api/v1/stock-report
                    │
                    ▼
          FastAPI routers + services
                    │ SQLAlchemy
                    ▼
              SQLite data/database.db
                    ▲
                    │
浏览器 ── Vue 3/Vite SPA ── Axios /api/v1
                    │
        QingLong OpenAPI / Bark（后台线程）
```

技术栈：

- 后端：Python 3.11+、FastAPI、SQLAlchemy 2、SQLite、requests、pypinyin
- 前端：Vue 3、Vite、Element Plus、Axios、SortableJS
- 运行：本地 uvicorn、Docker Compose，另有 systemd 示例
- 前端基路径：`/app/`；生产时由 FastAPI 托管 `frontend/dist`

## 3. 目录与职责

| 路径 | 作用 |
|---|---|
| `app/main.py` | FastAPI 组装、lifespan 启停、启动前校验兼容 schema/index、后台线程、健康检查、request ID/请求日志、GZip、静态资源、SPA fallback |
| `app/config.py` | 从 `.env` 读取 `INGEST_TOKEN`（兼容旧 `API_TOKEN`）、`DATABASE_URL`、上传目录并校验启动配置 |
| `app/database.py` | SQLAlchemy engine/session；SQLite 开启 WAL、busy timeout、NORMAL synchronous |
| `app/models.py` | `SystemSettings`、`WechatAccount`、`MiniProgram`、`PointsHistory`、`Product`、`StockHistory` |
| `app/schemas.py` | 外部积分/现金上报与库存上报的 Pydantic 请求模型 |
| `app/schemas_stock.py` | 库存管理 CRUD/分页响应模型 |
| `app/dependencies.py` | Bearer 上报鉴权、UI `require_ui_access()` 统一访问保护、8 小时签名 HttpOnly Cookie 会话 |
| `app/access_control.py` | UI access-key 失败尝试的单进程 IP 限流：60 秒最多 5 次，随后锁定 5 分钟 |
| `app/routers/web.py` | 大部分 UI API：仪表盘、账号、积分、小程序、设置、备份、青龙定时；同步 I/O 路由使用普通 `def` 交给 FastAPI 线程池 |
| `app/routers/qinglong.py` | 外部脚本上报积分/现金、库存 |
| `app/routers/stock.py` | 库存中心、商品隐藏/恢复/下架恢复和商品 CRUD |
| `app/routers/images.py` | Bearer 保护的图片上传；仅允许常见栅格 MIME/文件头，单文件默认不超过 10 MiB |
| `app/services/qinglong_service.py` | 账号解析、积分入库、库存快照 upsert/下架判断 |
| `app/services/qinglong_open_service.py` | QingLong OpenAPI token、任务列表、匹配、同步和定时器 |
| `app/services/bark_service.py` | 今日未上报小程序计算、Bark 推送和定时器 |
| `app/services/cleanup_service.py` | 设置单例、懒迁移、积分/库存历史清理 |
| `app/maintenance.py` | 数据库恢复期间的进程内维护态标记 |
| `app/timeutil.py` | Asia/Shanghai 与 UTC 转换辅助函数；Windows 缺少 IANA tzdata 时回退到固定 UTC+08:00 |
| `app/static_assets.py` | 优先返回 Vite 生成的 `.gz` 资源 |
| `frontend/src/App.vue` | 全局布局、桌面/移动导航、页面标题、图片预览关闭处理 |
| `frontend/src/router.js` | SPA 路由、访问保护路由守卫、30 秒 access-status 缓存 |
| `frontend/src/api.js` | Axios 实例，baseURL=`/api/v1`；新 UI 鉴权依赖 HttpOnly Cookie，旧 `site_access_key` 仅迁移时注入 `X-Access-Key` |
| `frontend/src/stockCache.js` | 库存中心第一页短 TTL 跨组件内存缓存与失效 |
| `frontend/src/views/` | 各业务页；最大文件是 `ProgramsPage.vue`、`StockPage.vue`、`QinglongCronsPage.vue` |
| `scripts/api_template.py` | 给青龙/自写脚本复用的 `PointsReporter`、`StockReporter` |
| `scripts/init_db.py` | 新库执行 `Base.metadata.create_all()` |
| `scripts/migrate_add_phone_index.py` | 一次性创建手机号索引 |
| `migrate_note.py` | 旧版本一次性补 `mini_programs.note` |
| `docs/库存上报.md` | 编写库存上报脚本时的首选完整接口文档 |
| `.gitleaks.toml`、`.github/workflows/ci.yml` | secret scan 配置和 CI；当前 `main` 可达历史已清理运行时敏感文件，本机旧上报凭据已轮换 |
| `README.md`、`技术文档.md`、`CLAUDE.md` | 项目说明、技术说明、开发约束 |

前端目录中的 `components/HelloWorld.vue`、`public/vite.svg`、`src/assets/vue.svg` 是 Vite 初始模板遗留物，目前不是业务入口。

## 4. 数据模型与不变量

### 4.1 表关系

```text
WechatAccount (wechat_id 唯一)
    └── PointsHistory.wechat_id

MiniProgram (program_id 唯一)
    ├── PointsHistory.program_id
    └── Product.program_id + product_id 唯一

Product
    └── StockHistory 通过 program_id/product_id 逻辑关联

SystemSettings：单行全局设置
```

### 4.2 关键字段语义

| 表 | 字段 | 语义 |
|---|---|---|
| `wechat_accounts` | `wechat_id` | 内部主身份，唯一；手机号型 APP 上报会保留手机号作为兼容 ID |
| `wechat_accounts` | `phone` | 规范化后的中国手机号；手机号上报优先按此字段绑定账号 |
| `wechat_accounts` | `sort_order` | 账号列表顺序，越小越靠前；拖拽排序写入完整序列 |
| `mini_programs` | `auth_type` | `code` / `token` / `app`；`app` 决定进入 APP 列表，其余归入小程序列表 |
| `mini_programs` | `sort_order` | 当前主要表示是否置顶：置顶写 `1`，取消置顶写 `0` |
| `mini_programs` | `tags` | 实际保存为 JSON 数组字符串；读取时兼容数组、逗号分隔、中文逗号 |
| `mini_programs` | `is_archived` | 归档标记；默认列表隐藏，归档时同时清除收藏 |
| `mini_programs` | `ql_*` | QingLong 任务匹配缓存，只读镜像，不是数据上报来源 |
| `points_history` | `points` / `cash` | 账户余额历史；均可为 `NULL`，`NULL` 表示该次没有上报该维度，不等于 0 |
| `points_history` | `batch_id` | 一次积分上报请求生成一个 UUID，便于识别批次 |
| `products` | `points` / `cash` | 商品兑换价；`cash` 单位为人民币元，0/NULL 表示纯积分商品 |
| `products` | `stock` | 当前库存，没货应报 `0`，不要因为没货就从快照列表删除 |
| `products` | `is_hidden` | 用户手动隐藏；由“ 不感兴趣 ”操作控制 |
| `products` | `is_unlisted` | 系统根据全量库存快照判断商品已不再上架；与 `is_hidden` 独立 |
| `stock_history` | `old_stock` / `new_stock` | 新商品或库存变化时记录；不是每次上报都写一行 |

### 4.3 懒迁移规则

没有 Alembic。新库用 `Base.metadata.create_all()`；旧库由以下 helper 在请求开始时检查并执行 `ALTER TABLE ADD COLUMN`：

- `web.py:ensure_mini_program_columns`
- `stock.py:ensure_product_columns`
- `cleanup_service.py:ensure_system_settings_columns`
- `cleanup_service.py:ensure_points_history_columns`

增加模型字段时必须同时把字段加入对应 `ensure_*_columns` 映射，否则旧 `data/database.db` 会在运行时缺列。非列变更再使用一次性脚本。

## 5. 外部上报业务

完整库存脚本规范见 `docs/库存上报.md`；模板见 `scripts/api_template.py`。

### 5.1 积分/现金余额：`POST /api/v1/qinglong/report`

该路由挂在 `qinglong.router` 上，整个 router 要求：

```http
Authorization: Bearer <INGEST_TOKEN>
```

请求形状：

```json
{
  "script_id": "script-name",
  "execution_time": "2026-07-16 20:00:00",
  "data": {
    "wechat_accounts": [
      {
        "wechat_id": "wx_001",
        "nickname": "可选",
        "phone": "可选",
        "points_data": [
          {
            "program_id": "p_001",
            "program_name": "示例",
            "current_points": 100,
            "current_cash": 1.25,
            "auth_type": "code"
          }
        ]
      }
    ]
  }
}
```

规则：

1. `current_points`、`current_cash` 至少提供一个；两者支持数字字符串、小数和 0。
2. 缺少的维度写入 `NULL`，不要在服务端把“未上报”伪装成 0。
3. `wechat_id` 若是中国手机号格式 `^1[3-9]\d{9}$`，优先按 `phone` 找已有账号；必要时把手机号写入 `phone` 列。手机号型账号不会被请求里的空昵称覆盖。
4. 非手机号身份按 `wechat_id` 查找，不存在则创建，并使用请求昵称。
5. 小程序不存在则自动创建；`program_name` 和有效的 `auth_type` 会更新已有记录。
6. 每个余额快照写入 `PointsHistory`，`report.execution_time` 优先作为时间，否则用当前 UTC。
7. 请求结束后按 `SystemSettings.max_log_entries` 与 `max_retention_days` 裁剪积分历史；裁剪失败只打印日志，不让上报失败。

“活跃”在 UI 汇总中通常指当前积分或现金至少一个大于 0；纯 0 余额不算活跃。

### 5.2 库存：`POST /api/v1/stock-report`

同样要求 Bearer `INGEST_TOKEN`（旧部署可在兼容窗口继续使用环境变量 `API_TOKEN`）。一次请求代表一个 `program_id` 的**全量在架商品快照**：

```json
{
  "program_id": "p_001",
  "products": [
    {
      "product_id": "sku_001",
      "product_name": "纯积分商品",
      "stock": 20,
      "points": 300,
      "cash": 0,
      "image_url": "https://example/a.jpg"
    },
    {
      "product_id": "sku_002",
      "product_name": "积分加钱购",
      "stock": 5,
      "points": 800,
      "cash": 19.9
    }
  ]
}
```

关键行为：

1. `product_id` 不传时用 `product_name` 代替；生产脚本强烈建议传稳定 ID，否则商品改名会被当成新商品。
2. 商品按 `(program_id, product_id)` upsert；名称、积分价、现金价每次刷新，图片 URL 只有传非空值时覆盖。
3. 新商品或库存变化会写 `StockHistory`；库存一直不变不重复写历史。
4. 当前请求中出现的商品会自动清除 `is_unlisted`，但不会清除用户的 `is_hidden`。
5. 当前在架商品如果本次全量快照没有出现，会被标记 `is_unlisted=1`。再次出现会自动恢复上架。
6. `products=[]` 的空报告跳过下架检测，防止采集脚本异常返回空列表导致全量误下架。
7. 上报结束后按同一套日志保留设置裁剪库存历史。

因此脚本侧必须：每个小程序报全量在架商品、保持 `product_id` 稳定、没库存报 `stock: 0`、不要过滤掉积分加钱购商品。

商品是否当前可兑换由前端判断：库存大于 0、用户最高积分不低于 `points`，且当 `cash > 0` 时用户最高现金也不低于 `cash`。

## 6. API 速查

所有路径都基于 `/api/v1`，除非特别注明。访问保护开启且配置密钥时，`web` 与 `stock` router 的 UI API 统一检查签名 HttpOnly Cookie；旧 `X-Access-Key` 仅用于迁移兼容。只有 `/access/status`、`/access/verify` 作为访问入口豁免。

### 6.1 访问与设置

| 方法 | 路径 | 作用 |
|---|---|---|
| `GET` | `/access/status` | 返回访问保护是否开启、是否已认证 |
| `POST` | `/access/verify` | 验证访问密钥 |
| `GET/POST` | `/settings/logs` | 日志数量/天数、访问保护和密钥 |
| `GET/POST` | `/settings/qinglong` | QingLong URL、Client ID、Secret、同步模式/间隔 |
| `POST` | `/settings/qinglong/sync` | 立即同步任务状态 |
| `GET/POST` | `/settings/bark` | Bark 开关、服务器、Device Key、推送时间 |
| `POST` | `/settings/bark/test` | 立即推送未上报列表 |
| `GET` | `/settings/database/export` | SQLite 在线备份下载 |
| `POST` | `/settings/database/import` | 限大小、校验后同卷原子替换数据库并留下带时间戳回滚副本 |

### 6.2 账号、积分、小程序

| 方法 | 路径 | 作用 |
|---|---|---|
| `GET` | `/dashboard` | 仪表盘聚合统计、前 5 个未上报小程序、近期更新 |
| `GET` | `/accounts` | 用户列表及活跃小程序/APP 数 |
| `GET` | `/accounts/{wechat_id}` | 单用户完整积分摘要 |
| `GET` | `/accounts/{wechat_id}/points_details` | 单用户积分明细数组 |
| `PUT` | `/accounts/{wechat_id}` | 新增/编辑用户 |
| `PUT` | `/accounts/sort-order` | 保存拖拽后的账号顺序 |
| `DELETE` | `/accounts/{wechat_id}` | 删除账号和其积分记录 |
| `DELETE` | `/accounts/{wechat_id}/programs/{program_id}` | 删除该账号该小程序的积分记录 |
| `GET` | `/points` | 所有账号积分总览 |
| `GET` | `/programs` | 分页、搜索、标签、收藏、归档、青龙状态、cron 排序；`kind=mini|app|all` |
| `GET` | `/programs/favorites` | 收藏小程序 |
| `GET` | `/programs/unreported` | 今日未上报活跃小程序 |
| `GET` | `/programs/{program_id}` | 小程序详情和账号排行 |
| `GET` | `/programs/{program_id}/stock` | 单小程序库存、今日变化、最高积分/现金 |
| `GET` | `/programs/{program_id}/ranking` | 排行榜 |
| `GET` | `/programs/{program_id}/rankings` | 兼容旧命名的排行榜包装 |
| `PUT` | `/programs/{program_id}` | 收藏、置顶、备注、标签、归档、auth_type |
| `DELETE` | `/programs/{program_id}` | 删除程序、积分历史和商品 |

`GET /programs` 的常用参数：`page`、`size`、`q`、`is_favorite`、`tag`、`status=active|archived|all`、`ql_status=all|enabled|disabled|unknown`、`sort=default|cron`、`kind=mini|app|all`。搜索会额外使用 `pypinyin` 做中文全拼/首字母匹配。

### 6.3 库存管理

`stock` router 的前缀是 `/api/v1/stock`：

| 方法 | 路径 | 作用 |
|---|---|---|
| `POST` | `/stock/product` | 手工创建/更新商品 |
| `GET` | `/stock/programs` | 按小程序汇总可见商品数/库存 |
| `GET` | `/stock/center` | 服务端分页库存中心；支持 `page/size/q/tag/status/price_mode/cash_max`，返回汇总和隐藏/下架数量 |
| `GET` | `/stock/programs/{program_id}/products` | 单程序分页商品 |
| `GET` | `/stock/search` | 全局商品搜索 |
| `GET` | `/stock/hidden` | 用户手动隐藏的商品 |
| `GET` | `/stock/off-shelf` | 系统检测下架的商品，按程序分组；支持 `page/size/q` 分页搜索 |
| `PUT` | `/stock/products/{id}/hide` | 手动隐藏 |
| `PUT` | `/stock/products/{id}/restore` | 取消手动隐藏 |
| `PUT` | `/stock/products/{id}/relist` | 取消系统下架标记 |

另有图片上传：`POST /api/v1/upload/image`，`multipart/form-data`，由 Bearer token 保护；图片保存为 `/static/uploads/<filename>`，若带 `program_id + product_id` 会更新商品本地图片路径。

### 6.4 QingLong 任务整理

| 方法 | 路径 | 作用 |
|---|---|---|
| `GET` | `/qinglong/crons` | 实时拉取 QingLong 任务、解析最早触发分钟 |
| `POST` | `/qinglong/crons/schedules` | 批量更新 cron；单次最多 500 个，更新后刷新本地镜像 |

批量更新前会先拉全量任务，因为 QingLong 的 `PUT /open/crons` 需要同时提交 `id/name/command/schedule`；实际 PUT 调用并发数为 8。

## 7. 后台集成

### 7.1 QingLong OpenAPI

`app/services/qinglong_open_service.py` 的流程：

1. `GET {base_url}/open/auth/token?client_id=&client_secret=`，按 base URL + client ID 缓存 token。
2. `GET {base_url}/open/crons?page=0&size=0` 获取任务列表。
3. 优先用 cron 名称与 `program_name` 规范化后精确匹配，再用 command basename，最后允许包含关系；匹配按分数从高到低贪心分配，一个 cron 不重复占用。
4. 把 `ql_cron_id/name/is_disabled/matched_at/command/schedule` 写入小程序缓存字段。

同步模式：

- `auto`：启动后后台线程先等待约 15 秒，随后按 `ql_auto_sync_minutes`（1–1440，默认 5）周期刷新；列表请求本身不等待。
- `blocking`：`GET /programs` 发现过期时在当前请求中等待同步。
- `manual`：后台线程和列表路径都不主动同步，只由“立即同步”触发。

多 worker 场景使用 `data/.qinglong_scheduler.lock` 文件锁和进程内 `_sync_inflight` 防止重复同步。SQLite 仍建议单 worker。

### 7.2 Bark

`app/services/bark_service.py` 启动一个每分钟检查的 daemon 线程：

- 默认服务器：`https://api.day.app`
- 默认推送时间：本地 Asia/Shanghai `20:00`
- 只统计未归档且当天没有积分/现金上报的小程序
- 推送成功后写入 `bark_last_push_at/status`，同一当地日期不会重复自动推送
- 手动测试可在自动推送关闭时执行，但仍需要 Device Key
- 多 worker 使用 `data/.bark_scheduler.lock` 保证只有一个调度进程

## 8. 前端页面与状态

Vue Router 使用 `createWebHistory('/app/')`，主要路由：

| 路由 | 页面 | 主要能力 |
|---|---|---|
| `/dashboard` | `DashboardPage.vue` | 总数卡片、近期更新、未上报列表 |
| `/programs` | `ProgramsPage.vue` | 小程序卡片、筛选、标签、备注、详情/库存弹窗、归档/删除 |
| `/apps` | `ProgramsPage.vue` | 同一组件，传 `kind=app`，仅显示 `auth_type=app` |
| `/programs/:programId` | `ProgramDetailPage.vue` | 独立详情页，加载详情与库存 |
| `/apps/:programId` | `ProgramDetailPage.vue` | APP 版本详情页 |
| `/favorites` | `FavoritesPage.vue` | 收藏列表 |
| `/users` | `UsersPage.vue` | 用户 CRUD、手机号/设备、SortableJS 拖拽排序、积分抽屉 |
| `/points` | `PointsPage.vue` | 账号总积分/现金、今日变化、搜索排序、未注册项目抽屉 |
| `/stock` | `StockPage.vue` | 商品画廊、标签/价格/库存/可兑换筛选、隐藏/下架抽屉 |
| `/qinglong-crons` | `QinglongCronsPage.vue` | 时间线、拥挤检测、单任务编辑、批量重排预览/应用 |
| `/settings` | `SettingsPage.vue` | 基础、青龙、Bark、数据库备份四个分区 |
| `/access-gate` | `AccessGatePage.vue` | 访问密钥输入，公开路由 |

前端关键行为：

- `api.js` 的 Axios baseURL 是 `/api/v1`；新登录流程依赖后端 HttpOnly Cookie，不把原始 access key 写入 localStorage。若旧版本残留 `site_access_key`，会暂时自动加 `X-Access-Key`，服务端成功迁移后前端清理它。
- `router.js` 对页面导航做 access-status 检查，缓存 30 秒；`api.js` 对受保护 API 的 401 清理会话并触发跳转；保护开启且密钥无效时跳 `/access-gate`。
- `ProgramsPage` 每页 20 条，用 `IntersectionObserver` 无限加载，并分别用 `sessionStorage` 保存小程序/APP 页面状态。
- `QinglongCronsPage` 的排除名单保存在 `localStorage` 的 `ql_crons_excluded_names`，只影响前端一键整理，不写后端。
- 青龙批量应用请求把超时提高到 300 秒；后端最多并发 8 个青龙 PUT。
- 主移动导航是 `App.vue` 自定义 `.mobile-nav-shell`，不要改回 Element Plus `el-drawer`，否则容易出现遮罩残留/点击被拦截。
- Vite 自动导入 Vue/Vue Router API 和 Element Plus 组件及样式；图标仍需从 `@element-plus/icons-vue` 显式导入。

## 9. 时间、鉴权与并发

### 9.1 时间

数据库历史字段多为 naive UTC（旧代码使用 `datetime.utcnow()`）。API 设置时间通过 `timeutil.iso_for_api()` 加 `Z`，前端设置页按 Asia/Shanghai 显示；Bark 推送时间和“今天是否上报”以 Asia/Shanghai 为业务日。

未来新增代码优先使用 `app/timeutil.py`：

- `now_local()`：中国时区 aware 当前时间
- `now_utc()`：UTC aware 当前时间
- `utcnow_naive()`：兼容现有数据库列的 naive UTC
- `local_today_str()`、`is_same_local_day()`：当地日期判断

现有代码仍混用 `datetime.now()`、`datetime.utcnow()`、固定 `+8h` 和 helper；涉及日期的新改动要避免继续扩大这种混用。

### 9.2 两套不同鉴权

1. Bearer `INGEST_TOKEN`：仅保护外部写入路由（积分/库存上报）和图片上传；暂时读取旧 `.env` 的 `API_TOKEN` 作为兼容别名。缺少、仍为 `default_token` 或少于 32 个字符时，应用启动失败。
2. UI access session：人类用户界面锁现在只在 `system_settings.access_key_hash` 保存 PBKDF2-HMAC-SHA256 哈希；旧数据库中的 `system_settings.access_key` 会在启动时一次性哈希并清空。登录后签发绑定该哈希的 8 小时签名 HttpOnly Cookie。`web` 和 `stock` router 当前统一挂 `require_ui_access()`，只豁免 `/access/status`、`/access/verify`；旧 `X-Access-Key` 仅用于迁移，前端收到受保护 API 的 401 会清理会话并回到访问页。访问成功/失败/限流事件写入 `access_audit_events`，不保存提交的密钥。

重要：数据库内 access key 已改为单向哈希，旧明文仅作为兼容迁移字段存在且启动迁移后清空；Cookie 会话使用哈希作为签名绑定材料。单进程失败限流已落地，多 worker/多实例仍需反向代理共享限流，审计保留策略和后台查看接口也仍可继续完善。

## 10. 运行与部署

### 本地开发

```bash
# 仓库根目录
python -m venv venv
venv\Scripts\activate              # Windows
pip install -r requirements.txt
python scripts/init_db.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 另一个终端，frontend/ 目录
npm install
npm run dev                         # http://127.0.0.1:5173/app/
```

Vite 将 `/api`、`/static` 代理到 `http://127.0.0.1:8000`。开发时无需让后端承担实时前端构建。

### 生产式本地运行

```bash
cd frontend
npm run build                       # 生成 dist 和大资源 .gz
cd ..
uvicorn app.main:app --host 0.0.0.0 --port 5711
```

`frontend/dist/index.html` 不存在时，`/`、`/app` 和 SPA fallback 会返回 503；生产启动前必须构建前端。

### Docker Compose

```bash
cd frontend && npm run build && cd ..
docker compose up -d --build
```

默认：`http://127.0.0.1:5711/` 或 `/app`。Compose 挂载：

- `./app` → `/app/app`
- `./data` → `/app/data`
- `./logs` → `/app/logs`
- `./static/uploads` → `/app/static/uploads`
- `./scripts` → `/app/scripts`
- `./frontend/dist` → `/app/frontend/dist`

容器默认 `TZ=Asia/Shanghai`、`UVICORN_WORKERS=1`，并把 `host.docker.internal` 映射到宿主机，青龙在宿主机时可配置类似 `http://host.docker.internal:5700`。

### systemd

`points-stock.service` 是 Linux 示例，路径仍是 `/root/wechat-points-stock`，需要按实际用户/路径修改。它直接启动 uvicorn，当前写的是 `--workers 2`；这与 Compose 的单 worker 推荐不一致，也不会经过 `start.sh` 的建库检查。生产部署时应明确统一启动方式和 worker 数。

## 11. 构建与开发约束

- 后端没有自动迁移框架；新增可空列必须同步 lazy migration helper。
- SQLite 默认单 worker；若必须多 worker，保留 WAL、busy timeout、调度文件锁和数据库恢复旁路锁。
- 前端不要在 `main.js` 全量注册 Element Plus，也不要导入 `element-plus/dist/index.css`；组件/样式由 Vite 插件按需处理。
- 新增重依赖时检查 `frontend/vite.config.js` 的 `manualChunks`，必要时加入拆包规则。
- 生成构建产物使用 `npm run build`，它会额外运行 `scripts/gzip-assets.mjs`；不要手写 `.gz`。
- 前端主导航保持自定义移动壳；图片预览的点击空白关闭逻辑在 `App.vue`。
- 删除程序会同时删除其积分历史和商品；删除账号会删除该账号积分历史，库存不受账号删除影响。
- 修改库存上报语义时同步更新 `docs/库存上报.md`、`scripts/api_template.py`、`app/schemas.py`、`app/services/qinglong_service.py` 和库存 UI。
- 改动 access-key 时同时检查后端 `web.py`、前端 `api.js`、`router.js` 和 `AccessGatePage.vue`。

## 12. 已发现的风险/偏差

这些不是本次修复项，只是后续工作时必须知道的事实。

1. **`API_TOKEN` 曾随 Git 跟踪的 `.env` 出现。** 当前 `main` 已不再跟踪 `.env`，且可达历史中的 `.env`、运行时数据库和 `venv/` 已清理；本机旧凭据已轮换为 `INGEST_TOKEN`，记忆文档不复述任何 token。其他已部署环境仍需按各自发布流程确认轮换。
2. **`INGEST_TOKEN` 仍保留旧 `API_TOKEN` 兼容读取。** 这是迁移窗口，不是永久双配置；后续文档、脚本统一后再删除别名。
3. **UI access 已完成第一阶段会话化和单进程限流。** 当前使用 8 小时签名 HttpOnly Cookie，旧 header 只用于迁移；SQLite 明文和持久化审计仍待处理，多 worker 场景需依赖反向代理共享限流。
4. **数据库恢复已加跨进程保护。** `app/maintenance.py` 使用数据库路径旁路锁，维护期间新 API 返回 503，恢复前 `wal_checkpoint(TRUNCATE)` 忙则中止；仍需完整调度暂停、在途事务排空和真实文件恢复/回滚集成测试，不要把 `os.replace` 视作已完成全部恢复治理。
5. **文档与当前 QingLong 列表行为有偏差。** README/CLAUDE 的部分描述说 `GET /programs` 会在自动模式触发非阻塞后台同步；当前 `handle_programs_list_sync()` 在 `auto` 模式明确不在列表路径触发，实际由启动的 scheduler 负责，`trigger_background_sync()` 虽存在但当前没有调用点。
6. **启动配置不完全统一。** Compose 推荐 1 worker；systemd 示例使用 2 worker，且绕过 `start.sh`/`entrypoint.sh` 的初始化和前端存在性检查。
7. **日期处理仍有历史混用。** `get_unreported_programs()` 等位置使用 `datetime.now()` 或固定 `+8h`，而其他位置使用 `timeutil`；部署环境改变时需要优先回归“今日未报”和设置时间显示。
8. **库存中心与下架抽屉已改成服务端分页。** 首屏不再自动请求下架明细，抽屉默认每页 50 条并可继续加载；后续仍需补 revision/ETag 和真实 p95 基准。
9. **健康检查已提供。** `/health/live` 只表示进程路由可用；`/health/ready` 执行 `SELECT 1`，Compose 已用它做容器 healthcheck。

## 13. 后续接手时的推荐阅读顺序

1. `CLAUDE.md`：项目约束和两个鉴权体系
2. `app/models.py`、`app/schemas.py`：数据字段与上报契约
3. `app/services/qinglong_service.py`：积分/库存写入和快照语义
4. `app/routers/web.py`：UI API 聚合逻辑
5. `app/routers/stock.py`、`frontend/src/views/StockPage.vue`：库存展示和隐藏/下架区分
6. `app/services/qinglong_open_service.py`、`frontend/src/views/QinglongCronsPage.vue`：青龙同步与任务整理
7. `frontend/src/views/ProgramsPage.vue`、`SettingsPage.vue`：主要交互和设置
8. `README.md`、`技术文档.md`、`docs/库存上报.md`：运行和外部脚本使用说明

常见改动定位：

- 上报字段/兼容旧脚本：`app/schemas.py` → `app/services/qinglong_service.py` → `scripts/api_template.py` → `docs/库存上报.md`
- 新 UI API：通常在 `app/routers/web.py`；如果是库存实体则看 `app/routers/stock.py`
- 新页面：`frontend/src/views/` → `frontend/src/router.js` → `frontend/src/App.vue` 导航
- 数据库字段：`app/models.py` + 对应 `ensure_*_columns()`，必要时补一次性迁移脚本
- 后台任务：`app/main.py` 启动入口 + 对应 service 的 scheduler/文件锁
