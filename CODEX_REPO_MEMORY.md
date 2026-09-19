# `wechat-points-stock` 仓库记忆

> 供后续 Codex/开发者快速恢复上下文使用。本文档记录的是代码实际行为优先的结论；如果本文档、README、技术文档与代码不一致，以代码为准，并在修改时同步更新文档。

后续优化清单和实施顺序见 `docs/优化路线图.md`。

## 0. 快照信息

- 本次 CI 修复：真实后端 Playwright smoke 移除 Dashboard、Programs 和程序详情页不必要的全局 `networkidle` 等待，改用真实页面数据可见断言作为同步点，降低 GitHub runner 上后台请求/动态资源引起的时序波动；临时 SQLite Chromium smoke 已复现通过。
- 本次推进：OPT-015 第十二批将 QingLongCronsPage 的读取请求接入 `useAbortableRequest`；共享控制器继续覆盖新请求取消、卸载取消和过期响应保护，批量写请求不做静默取消。
- 本次推进：OPT-015 第十三批将 StockPage 的已隐藏/已下架列表读取接入独立 `useAbortableRequest`，关闭抽屉时取消在途读取并消除隐藏抽屉重复请求；OPT-017 第三十五批将 StockPage 纳入 Prettier 格式门禁。
- 本次推进：OPT-015 第十四批将 Programs/Apps 的视口宽度与弹窗尺寸迁移到共享 `useViewport`，移除页面自管 resize 监听；OPT-017 第三十六批将 ProgramsPage 纳入 Prettier 格式门禁。
- 本次推进：OPT-015 第十五批修复真实后端 smoke 的全局网络空闲等待依赖；OPT-017 第三十七批记录真实后端 smoke 同步策略收敛，页面数据断言和 mock/真实双路径回归继续保持通过。
- 本次推进：OPT-015 第十六批将 App 根布局的移动导航断点迁移到共享 `useViewport`，并用桌面加载后切换到 390px 的 Playwright smoke 覆盖动态断点更新；OPT-017 第三十八批记录该跨断点回归，保留 App 既有模板格式边界。
- 本次推进：OPT-015 第十七批新增 `useViewport` 生命周期组件测试，覆盖初始宽度、跨阈值 resize 和卸载清理；OPT-017 第三十九批将 Vitest 组件测试提升到 `49 passed`。
- 本次推进：OPT-014 第三十批将 `ProgramDetailPage.vue` 拆为 `ProgramDetailOverview.vue` 与 `ProgramDetailDataSections.vue`，父页收敛为 API/加载/路由编排；OPT-017 第四十一批新增对应组件测试，Vitest 提升到 `53 passed`。
- 本次推进：OPT-014 第三十一批新增共享 `date.js`，收口 Dashboard、Favorites、Programs、ProgramDetail、Points、Stock、Settings 和 Users 积分详情的 API 日期展示；OPT-015 第十八批让历史无时区时间按 UTC 转 Asia/Shanghai，并让 Points 今日判断复用本地日期 key；OPT-017 第四十二批新增日期工具单测，Node 测试提升到 `33 passed`。
- 本次推进：OPT-014 第三十二批为拆分后的程序详情页补充真实 mock 数据交互 smoke，覆盖概览、收藏/标签/备注、积分排行、库存商品和日期展示；OPT-017 第四十三批将三浏览器 mock smoke 从 `24 passed` 提升到 `27 passed`。
- 本次推进：OPT-014 第三十三批将 ProgramsPage 的列表/详情/库存读取收敛到共享 `useAbortableRequest`；OPT-015 第十九批补充关闭/重复打开/卸载取消边界；OPT-017 第四十四批新增列表卡片到详情/库存弹窗 smoke，三浏览器 mock smoke 提升到 `30 passed`。
- 本次推进：OPT-017 第四十批将 `ProgramDetailPage.vue` 完成首轮 Prettier 格式收敛，并把 `ProgramDetailPage.vue`、`FavoritesPage.vue`、`SettingsPage.vue` 纳入 `npm run format:check`；页面业务编排保持不变。

- 仓库：`https://github.com/daidaideya/wechat-points-stock`
- 本地路径：`D:\mycode\wechat-points-stock`
- 分支：`main`
- 快照提交：`0c9275e`（2026-09-19）
- 最新代码提交：`0c9275e`，ProgramsPage 列表/详情/库存读取已统一使用共享取消控制器，弹窗关闭和重复读取不会保留旧响应；API 日期解析、Asia/Shanghai 展示和本地日期判断仍由 `frontend/src/utils/date.js` 统一提供，程序详情页拆分后的整页数据链路和弹窗交互均有三浏览器 mock 回归。
- 最新修复：ProgramsPage 请求取消边界补齐，Users 页面窄内容区不再显示被裁切的宽表格；三浏览器 E2E smoke 当前为 `30 passed`。此前 QingLong 任务数据绑定、Stock 卡片布局和 Points 导航问题已保留在历史提交中。
- 工作区：OPT-014 已完成 Programs/Apps 指标展示组件、程序卡片第二十三批、详情弹窗、库存弹窗、Stock 商品卡片第五批、Qinglong 时间线行第六批、整理预览弹窗第二十批、Settings 分区导航第二十一批、Settings 共享卡片第二十二批、Users 积分详情弹窗第七批、移动卡片第八批、桌面表格第九批、编辑弹窗第十批、Settings 数据库备份/恢复区第十三批、基础设置区第十四批、青龙联动区第十五批、Bark 推送区第十六批、Dashboard 指标卡第二十四批、Points 账号展示卡第二十五批、Chromium/Firefox/WebKit 跨浏览器第十八批验证和真实后端 Chromium 第十九批验证，并完成八个主页面的首轮桌面视觉 smoke、Settings 四个查询分区 smoke 及 390px 移动导航 Playwright smoke；OPT-015 已完成主要页面错误边界第三批、Dashboard/Favorites/Points/Users 请求取消第四批、ProgramDetail/Settings 读取取消第五批、移动导航可访问性第六批、Settings 导入/刷新 pending 第七批、Settings 页面级写操作 busy 边界第八批、复杂弹窗可访问性第九批、ProgramFilterBar 筛选语义第十批和 Settings 分区导航语义第十一批、QingLong 读取取消第十二批和 Stock 抽屉读取取消第十三批、Programs 共享视口第十四批；OPT-016 已完成当前余额快照第一批和库存快照可信度第二批，库存上报支持完整性元数据并阻止不完整报告误下架；OPT-017 已完成共享层 Prettier 门禁第二批、Users 展示规则测试第三批、本地桌面手工 smoke 第四批、API mock Playwright/CI 第五批、Chromium/Firefox 双浏览器第六批、三浏览器第七批、依赖安全/许可证门禁第八批、真实后端数据 Playwright/CI 第九批、OpenAPI 前端声明生成/漂移门禁第十批、Vitest/Vue Test Utils 组件测试第十一批、UsersPage 格式收敛第十二批、ProgramFilterBar 组件测试第十三批、ProgramMetricStrip 快照告警测试第十四批、QinglongCronPlanDialog 整理预览测试/页面格式门禁第十五批、SettingsSectionNav 导航语义测试第十六批、SettingsSectionCard 共享投影测试第十七批、ProgramCard 程序卡片展示/事件测试第十八批、ProgramDetailDialog 详情弹窗展示/事件测试第十九批、ProgramStockDialog 库存弹窗展示/交互测试第二十批、UserPointsDialog 积分详情弹窗展示/交互测试第二十一批、StockProductCard 库存商品卡展示/交互测试第二十二批、UserMobileCard Users 移动卡片展示/交互测试第二十三批、UserEditDialog 用户编辑弹窗展示/交互测试第二十四批、UserDesktopTable Users 桌面表格展示/交互测试第二十五批、QinglongCronRow 青龙时间线行展示/交互测试第二十六批、四个 Settings 业务区段展示/字段/写操作/文件选择边界测试第二十七批、Dashboard 指标卡展示/激活事件测试第二十八批和 Points 账号卡展示/状态/指标/入口事件测试第二十九批；OPT-018 已完成代码生成的 OpenAPI 基线、CI 漂移检查、PR 模板、前端静态资源引用门禁和 FastAPI 升级后的 OpenAPI 基线同步第四批；OPT-016 的金额精度、标签/身份模型、QingLong 映射及路线图剩余项仍未闭环，后续继续按 `docs/优化路线图.md` 推进
- 后端静态检查：`python -m compileall -q app tests` 通过
- 本次推进：OPT-014 追加 Users 窄内容区响应式布局修复（第二十九批），OPT-017 追加 Users 卡片布局回归（第三十三批）；同时保留 QingLong 任务行数据绑定和 Stock 商品卡布局修复。
- 前端构建：已执行 `npm run build` 通过；构建会生成/刷新 `frontend/dist`
- 回归测试：Python 3.11 下 `py -3.11 -m pytest -q` 为 `112 passed`；前端 Node 测试 `npm test` 为 `33 passed`，Vitest 组件测试为 `53 passed`，Playwright mock Chromium + Firefox + WebKit smoke 共 `30 passed`，真实后端 Chromium smoke 共 `1 passed`，`npm run lint`、扩展后的 `npm run format:check`、`npm run check:resources`、`npm run build`、`py -3.11 scripts/export_openapi.py --check` 和 compileall 均通过；npm audit、pip-audit 和许可证检查继续通过。
- CI：后端 job 按 compileall → `scripts/export_openapi.py --check` → pytest 执行；前端 job 按 `npm ci` → `npm test` → `npm run test:components` → `npm run lint` → `npm run format:check` → `npm run check:api-types` → `npm run check:resources` → `npm run build` 执行；独立 `dependency-audit` job 执行 npm audit、pip-audit 和许可证检查；独立 `frontend-e2e` job 安装 Chromium + Firefox + WebKit 后执行 mock `npm run test:e2e`；独立 `frontend-real-e2e` job 使用临时 SQLite、seed 脚本和 FastAPI 后执行真实后端 Chromium smoke；secret scan 仍为独立 job
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
| `app/database.py` | SQLAlchemy engine/session；SQLite 开启 foreign keys、WAL、busy timeout、NORMAL synchronous |
| `app/models.py` | `SystemSettings`、`WechatAccount`、`MiniProgram`、`PointsHistory`、`CurrentPointBalance`、`Product`、`StockHistory` |
| `app/schemas.py` | 外部积分/现金上报与库存上报的 Pydantic 请求模型；包含字符串、finite/非负数值和批量上限约束 |
| `app/schemas_stock.py` | 库存管理 CRUD/分页响应模型及分页、排序、字段范围约束 |
| `app/dependencies.py` | Bearer 上报鉴权、UI `require_ui_access()` 统一访问保护、8 小时签名 HttpOnly Cookie 会话 |
| `app/access_control.py` | UI access-key 失败尝试的单进程 IP 限流：60 秒最多 5 次，随后锁定 5 分钟 |
| `app/routers/web.py` | 大部分 UI API：仪表盘、账号、积分、小程序、设置、备份、青龙定时；同步 I/O 路由使用普通 `def` 交给 FastAPI 线程池 |
| `app/routers/qinglong.py` | 外部脚本上报积分/现金、库存 |
| `app/routers/stock.py` | 库存中心、商品隐藏/恢复/下架恢复和商品 CRUD |
| `app/routers/images.py` | Bearer 保护的图片上传；校验常见栅格 MIME/文件头、尺寸和像素数，单文件默认不超过 10 MiB，失败时清理已写入文件 |
| `app/services/qinglong_service.py` | 账号解析、积分入库、库存快照 upsert/下架判断 |
| `app/services/qinglong_open_service.py` | QingLong OpenAPI token、任务列表、匹配、同步和定时器 |
| `app/services/bark_service.py` | 今日未上报小程序计算、Bark 推送和定时器 |
| `app/services/cleanup_service.py` | 设置单例、懒迁移、当前余额快照回填/upsert、积分/库存历史清理；历史 max_entries 裁剪使用数据库子查询 |
| `app/maintenance.py` | 数据库恢复期间的进程内维护态、跨进程旁路锁和在途数据库请求排空 |
| `app/timeutil.py` | Asia/Shanghai 与 UTC 转换辅助函数；Windows 缺少 IANA tzdata 时回退到固定 UTC+08:00 |
| `app/static_assets.py` | 优先返回 Vite 生成的 `.gz` 资源 |
| `frontend/src/App.vue` | 全局布局、桌面/移动导航、页面标题、图片预览关闭处理 |
| `frontend/src/router.js` | SPA 路由、访问保护路由守卫、30 秒 access-status 缓存、导航进度和库存 chunk 预加载 |
| `frontend/src/api.js` | Axios 实例，baseURL=`/api/v1`；新 UI 鉴权依赖 HttpOnly Cookie，旧 `site_access_key` 仅迁移时注入 `X-Access-Key` |
| `frontend/src/stockCache.js` | 库存中心第一页短 TTL 跨组件内存缓存与失效 |
| `frontend/src/composables/useViewport.js` | 统一响应式视口宽度和移动断点监听 |
| `frontend/src/utils/cron.js` | QingLong cron 解析、时间格式化、类型判断和新任务时间建议等无副作用纯函数 |
| `frontend/src/utils/cron.test.js` | QingLong cron 纯函数的 Node 内置单元测试 |
| `frontend/src/utils/date.js` | API 时间戳解析、Asia/Shanghai 展示和本地日期 key，兼容历史无时区 UTC 数据 |
| `frontend/src/utils/date.test.js` | 日期解析、格式化、空值回退和本地日期判断的 Node 内置单元测试 |
| `frontend/src/utils/product.js` | 商品金额/价格格式化、可兑换判断和阻断文案等共享纯函数 |
| `frontend/src/utils/product.test.js` | 商品共享纯函数的 Node 内置单元测试 |
| `frontend/src/utils/user.js` | 用户手机号兼容判断、微信号/昵称主标识和确定性头像展示函数 |
| `frontend/src/utils/user.test.js` | 用户身份展示规则和头像函数的 Node 内置单元测试 |
| `frontend/src/composables/useInfiniteScroll.js` | 统一 IntersectionObserver 无限滚动观察、提前加载和卸载清理 |
| `frontend/src/composables/useInfiniteScroll.test.js` | 无限滚动控制器的 Node 内置单元测试 |
| `frontend/src/composables/useStockFilters.js` | Stock 页筛选状态、参数构造、现金上限和重置逻辑 |
| `frontend/src/composables/useStockFilters.test.js` | Stock 页筛选 composable 的 Node 内置单元测试 |
| `frontend/src/composables/useProgramFilters.js` | Programs/Apps 页筛选状态、参数构造、活动筛选标签和重置逻辑 |
| `frontend/src/composables/useProgramFilters.test.js` | Programs/Apps 页筛选 composable 的 Node 内置单元测试 |
| `frontend/src/composables/useAccessSession.js` | 旧版 localStorage access key 的安全读取与清理边界 |
| `frontend/src/composables/useAccessSession.test.js` | 访问会话迁移边界的 Node 内置单元测试 |
| `frontend/src/composables/useAbortableRequest.js` | 页面请求取消、最新请求判定和卸载清理控制器 |
| `frontend/src/composables/useAbortableRequest.test.js` | 请求替换、取消和过期判定的 Node 内置单元测试 |
| `frontend/src/composables/usePageStateCache.js` | 带 schema 版本和 TTL 的 sessionStorage 页面状态缓存 |
| `frontend/src/composables/usePageStateCache.test.js` | 页面状态缓存版本、TTL 和失效行为的 Node 内置单元测试 |
| `frontend/src/components/ProgramFilterBar.vue` | Programs/Apps 页筛选栏展示与筛选事件派发 |
| `frontend/src/components/ProgramMetricStrip.vue` | Programs/Apps 卡片当前库存、最高积分/现金和库存变化指标展示；通过 `open-stock` 事件回到页面编排 |
| `frontend/src/components/ProgramCard.vue` | Programs/Apps 程序卡片展示、青龙状态、标签、指标和桌面/移动操作；通过显式事件回到页面编排 |
| `frontend/src/components/QinglongCronPlanDialog.vue` | QingLong 整理预览摘要、计划表格和单行/批量应用事件；父页保留确认与 API 编排 |
| `frontend/src/components/ProgramDetailDialog.vue` | Programs/Apps 详情弹窗展示、积分排行和响应式布局；通过 `open-stock` 事件回到页面编排 |
| `frontend/src/components/ProgramStockDialog.vue` | Programs/Apps 库存摘要、变化明细、在架商品表格和兑换状态展示；业务计算通过函数 props 注入 |
| `frontend/src/components/StockProductCard.vue` | Stock 页主库存列表的商品卡片展示；通过 `hide` 事件回到页面执行隐藏操作 |
| `frontend/src/components/QinglongCronRow.vue` | QingLong 时间线单行的状态标签、执行时间、cron 表达式和编辑/排除操作展示；通过 `edit`、`toggle-exclude` 事件回到页面编排 |
| `frontend/src/components/UserPointsDialog.vue` | Users 页积分详情的加载/空态、桌面表格、移动卡片和展示格式化；通过 `v-model` 接收弹窗状态 |
| `frontend/src/components/UserMobileCard.vue` | Users 页移动端用户卡片展示；通过 `edit`、`view-points`、`remove` 事件回到页面编排 |
| `frontend/src/components/UserDesktopTable.vue` | Users 页桌面表格列、排序句柄、身份展示和操作按钮；通过 `edit`、`view-points`、`remove` 事件回到页面编排 |
| `frontend/src/components/UserEditDialog.vue` | Users 页新增/编辑表单、取消和保存状态展示；通过 `v-model`、`update-field`、`save` 事件回到页面编排 |
| `frontend/src/utils/apiError.js` | Axios/API 错误载荷归一化、request ID 和取消请求识别 |
| `frontend/src/utils/apiError.test.js` | API 错误消息与取消请求解析的 Node 内置单元测试 |
| `frontend/eslint.config.js` | ESLint 9 + Vue flat config，覆盖前端 JS/Vue 源码 |
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

CurrentPointBalance (wechat_id + program_id 唯一)
    └── 逻辑镜像 PointsHistory 的最新一行；不设历史外键，允许历史裁剪后保留当前状态

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
| `mini_programs` | `stock_snapshot_*` | 最近库存报告的 ID、时间、完整性、状态和商品数量；用于阻止不完整快照自动下架，并向 UI 暴露需复核状态 |
| `points_history` | `points` / `cash` | 账户余额历史；均可为 `NULL`，`NULL` 表示该次没有上报该维度，不等于 0 |
| `points_history` | `batch_id` | 一次积分上报请求生成一个 UUID，便于识别批次 |
| `current_point_balances` | `points` / `cash` | 每个账号/程序最新历史行的当前镜像；保持 `NULL` 维度语义，不参与趋势/审计替代 |
| `current_point_balances` | `last_report_time` / `history_id` | 以报告时间、历史主键组成稳定版本；晚到旧报告不能覆盖新快照 |
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
- `cleanup_service.py:ensure_current_balance_table`

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
6. 每个余额快照写入 `PointsHistory`，并在同一事务内 upsert `CurrentPointBalance`；`report.execution_time` 优先作为时间，否则用当前 UTC。快照以 `(report_time, history_id)` 稳定判断新旧。
7. 请求结束后按 `SystemSettings.max_log_entries` 与 `max_retention_days` 裁剪积分历史；裁剪失败只打印日志，不让上报失败，当前余额快照不随历史裁剪删除。

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
5. 只有非空、`snapshot_complete=true` 且 `expected_product_count`（如提供）与实际数量匹配的报告才按全量快照下架缺失商品；再次出现会自动恢复上架。
6. `snapshot_complete=false`、数量不匹配或 `products=[]` 时跳过下架检测，保留旧商品，并在响应和程序卡片中标记库存快照需复核；列出的商品仍会更新。
7. `snapshot_id` 可由脚本提供；未提供时服务端生成 ID。快照质量元数据写入 `mini_programs.stock_snapshot_*`，旧库通过 `ensure_mini_program_columns` 按需补列。
8. 上报结束后按同一套日志保留设置裁剪库存历史。

因此脚本侧必须：每个小程序报全量在架商品、保持 `product_id` 稳定、没库存报 `stock: 0`、不要过滤掉积分加钱购商品。

商品是否当前可兑换由前端判断：库存大于 0、用户最高积分不低于 `points`，且当 `cash > 0` 时用户最高现金也不低于 `cash`。

## 6. API 速查

所有路径都基于 `/api/v1`，除非特别注明。访问保护开启且配置密钥时，`web` 与 `stock` router 的 UI API 统一检查签名 HttpOnly Cookie；旧 `X-Access-Key` 仅用于迁移兼容。只有 `/access/status`、`/access/verify` 作为访问入口豁免。

### 6.1 访问与设置

| 方法 | 路径 | 作用 |
|---|---|---|
| `GET` | `/access/status` | 返回访问保护是否开启、是否已认证 |
| `POST` | `/access/verify` | 验证访问密钥 |
| `GET` | `/access/audit-events` | 受 UI 鉴权保护的安全审计分页查询；包含 UI 访问和成功高风险操作，支持事件类型/IP 过滤，不返回密钥 |
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
| `GET` | `/stock/center` | 服务端分页库存中心；支持 `page/size/q/tag/status/price_mode/cash_max`，返回汇总和隐藏/下架数量；SQLite 使用触发器 revision 生成 ETag，支持 `If-None-Match` 304 |
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

HTTP 连接治理：`get_token`、`list_crons`、`update_cron_schedule` 按调用线程复用带连接池的 `requests.Session`，超时分别保持 15/30/20 秒；adapter 设置 `max_retries=0`，不对会改变任务的 PUT 自动重试，避免副作用重复执行。scheduler 停止或应用 shutdown 时释放所有已登记的连接池，手动同步在关闭后会按需创建新 Session；异常信息会脱敏，不输出 Client Secret 或 Bearer token。

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
- Bark 外部请求按线程复用 `requests.Session` 连接池，超时 15 秒；明确关闭自动重试，避免重复通知，scheduler/shutdown 时释放连接池。

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
- `ProgramsPage` 每页 20 条，用 `IntersectionObserver` 无限加载；离开页面时分别保存小程序/APP 的筛选条件和滚动位置，`usePageStateCache` 以 schema 版本和 15 分钟 TTL 约束缓存，返回时重新请求列表。
- `useViewport()` 统一管理需要响应式更新的移动断点；青龙页使用 900px 断点，积分抽屉使用 768px 断点，组件卸载时会移除 resize 监听。
- `QinglongCronsPage` 的排除名单保存在 `localStorage` 的 `ql_crons_excluded_names`，只影响前端一键整理，不写后端。
- QingLong 新脚本时间建议由 `frontend/src/utils/cron.js` 计算：按当前脚本类型筛选，优先使用数字 ID 最大的启用任务作为基准，跳过排除名单和已占用分钟，并正确处理超过 60 分钟的小时进位；页面只负责 Vue 状态和交互编排。
- 前端 cron 纯函数通过 `npm test` 执行 Node 内置单测，CI 在 `npm run build` 前运行该测试。
- `ProgramsPage.vue` 与 `StockPage.vue` 共享 `frontend/src/utils/product.js` 的金额/商品价格格式化、可兑换判断和阻断文案；库存排序、筛选和接口状态仍由各自页面负责。
- 前端共享纯函数通过 `npm test` 执行 Node 内置单测，目前共 `9 passed`。
- `ProgramsPage.vue` 与 `StockPage.vue` 共享 `frontend/src/composables/useInfiniteScroll.js` 的 IntersectionObserver 生命周期；页面仍分别控制分页参数、请求状态和加载回调。
- 前端 Node 内置测试目前共 `11 passed`，其中包含无限滚动控制器的浏览器 API 模拟测试。
- `StockPage.vue` 通过 `frontend/src/composables/useStockFilters.js` 管理关键词、库存状态、标签、价格模式和现金上限；页面保留筛选后请求、缓存和结果展示。
- 前端 Node 内置测试目前共 `14 passed`，其中包含 Stock 筛选参数和状态切换测试。
- `ProgramsPage.vue` 与 `/apps` 共用 `frontend/src/composables/useProgramFilters.js` 管理搜索、状态、收藏、青龙状态、排序和标签筛选；页面保留 API 请求、分页、sessionStorage 恢复和归档/删除等业务编排。
- `ProgramFilterBar.vue` 负责 Programs/Apps 页筛选栏展示和事件派发；`ProgramsPage.vue` 保留筛选状态、请求、分页、缓存恢复和业务操作。
- `ProgramMetricStrip.vue` 负责 Programs/Apps 卡片的库存、最高积分/现金、库存变化和不完整库存快照告警格式化、可见性判断与 scoped 样式；`ProgramsPage.vue` 保留列表状态、请求和库存弹窗编排，组件通过 `open-stock` 事件触发查看库存。
- `ProgramCard.vue` 负责 Programs/Apps 程序卡片的名称/ID、青龙状态、标签、指标、备注和桌面/移动操作展示；`ProgramsPage.vue` 继续持有复制、标签、库存、详情、备注、收藏、归档和删除等业务副作用，卡片通过白名单事件回传。
- `ProgramDetailDialog.vue` 负责 Programs/Apps 详情弹窗的概要、标签/备注、积分排行、手机号/微信号和响应式展示；`ProgramsPage.vue` 保留详情 API 请求与数据状态，组件通过 `v-model` 和 `open-stock` 事件回传页面编排。
- `ProgramStockDialog.vue` 负责 Programs/Apps 库存摘要、变化明细、商品表格和移动端展示；`ProgramsPage.vue` 保留库存 API、排序/兑换业务计算与状态，组件通过 `v-model` 和 `update:change-expanded` 回传交互状态。
- `StockProductCard.vue` 负责 Stock 页标准化商品对象的图片、状态、价格、库存、最高积分和隐藏操作展示；`StockPage.vue` 保留请求、筛选、分页、商品标准化和隐藏 API，卡片通过 `hide` 事件回传。
- `QinglongCronRow.vue` 负责 QingLong 时间线单行的禁用/排除/间隔状态、执行时间、cron 表达式和操作按钮展示；`QinglongCronsPage.vue` 保留 API、筛选、排除名单、新脚本时间建议和批量整理编排，组件通过 `edit`、`toggle-exclude` 事件回传。
- `UserPointsDialog.vue` 负责 Users 页积分详情的加载态、空态、桌面/移动展示和积分/现金/日期格式化；`UsersPage.vue` 保留用户与积分详情 API、当前用户标题和弹窗状态编排，组件通过 `v-model` 接收可见性。
- `frontend/src/utils/user.js` 统一处理 Users 页手机号兼容、微信号/昵称主标识和确定性头像展示；`UserMobileCard.vue` 负责移动卡片展示与操作事件，`UsersPage.vue` 继续持有列表容器、桌面表格和 Sortable 拖拽保存。
- `UserDesktopTable.vue` 负责 Users 页桌面列、头像、排序句柄和操作按钮展示；`UsersPage.vue` 通过组件 ref 继续取得表格 DOM 给 Sortable 使用，并保留顺序持久化、失败回滚和移动端列表生命周期。
- `UserEditDialog.vue` 负责 Users 页新增/编辑表单展示和字段更新事件；`UsersPage.vue` 保留表单初始化、字段白名单更新、微信号非空校验、保存 API、刷新和错误提示。
- `SettingsDatabaseSection.vue` 负责 Settings 页数据库备份/恢复区段、导出按钮和文件选择器；文件选择器在派发文件事件后立即重置，`SettingsPage.vue` 保留确认、上传、pending、错误提示和成功刷新编排。
- `SettingsGeneralSection.vue` 负责 Settings 页日志清理、访问保护状态、访问密钥输入和保存按钮展示；字段变更通过白名单 `update-field` 事件回传，`SettingsPage.vue` 保留校验、保存 API、会话轮换和成功刷新编排。
- `SettingsQinglongSection.vue` 负责 Settings 页青龙地址、Client ID/Secret、同步方式、同步间隔、最近同步状态和操作按钮展示；字段变更通过白名单 `update-field` 事件回传，`SettingsPage.vue` 保留配置读取、保存/同步 API、校验、pending 和错误提示编排。
- `SettingsBarkSection.vue` 负责 Settings 页 Bark 启用状态、服务器、Device Key、推送时间、最近推送状态和操作按钮展示；字段变更通过白名单 `update-field` 事件回传，`SettingsPage.vue` 保留配置保存、测试推送、校验、pending 和错误提示编排。
- `SettingsSectionCard.vue` 负责四个 Settings 区段共用的卡片容器、标题和描述结构；区段通过默认 slot 投影各自表单，专属字段和事件仍由各区段自行负责。
- `SettingsSectionNav.vue` 负责 Settings 分区导航、响应式布局和 active/`aria-current` 语义；通过 `v-model` 回传分区选择，`SettingsPage.vue` 保留路由 query、busy 禁用和请求编排。
- `ProgramsPage.vue` 的列表、详情和库存读取统一复用 `useAbortableRequest`；快速筛选、重复打开、弹窗关闭和组件卸载会取消旧请求并丢弃过期响应，Stock 页已有同类请求保护。
- `frontend/src/utils/apiError.js` 统一处理 API 的 `message`、`detail`、Pydantic 列表错误、Axios/native abort、超时/网络分类和后端 request ID；访问页、设置页、青龙页、用户页、Programs、Favorites、Dashboard、Points、Stock 和 ProgramDetail 的主要 API 请求已使用该边界。
- `frontend/src/composables/useAbortableRequest.js` 为 Dashboard、Favorites、Points、Users 列表/积分详情、ProgramDetail 和 Settings 读取提供“新请求取消旧请求、卸载取消、过期响应不写状态”的控制器；取消不会弹出错误，也不会由旧请求覆盖 loading 状态，Settings 的写操作仍保持显式 pending。
- `SettingsPage.vue` 通过 `settingsBusy` 汇总读取、保存、同步、推送、导出和导入状态，并传给四个 Settings 区段；busy 期间锁定分区导航、刷新、表单控件和操作按钮，避免副作用请求并发覆盖状态。Playwright 有延迟保存 smoke 覆盖该边界。
- 前端 Node 内置测试目前共 `33 passed`，其中包含 Programs/Apps 筛选参数、访问会话、页面状态缓存版本/TTL、API 错误解析、AbortError、日期边界和 Users 身份展示规则测试。
- 2026-09-18 在临时 SQLite 数据库和随机本地 `INGEST_TOKEN` 上完成桌面浏览器 smoke：Dashboard、Programs、Apps、Users、Points、Stock、QingLong、Settings 均可加载主内容/空态；Users 新增用户空表单校验和 QingLong 未配置 OpenAPI 提示均符合预期，浏览器 console 无 error/warn。验证后服务已停止、临时数据库已删除。
- 2026-09-18 新增 `frontend/playwright.config.js` 与 `frontend/e2e/smoke.spec.js`：API mock 下覆盖上述八个主路由、Settings 四个查询分区、Users 空表单校验、Settings 写操作 busy 边界和 390px 移动导航开关，监听 console error/warn 与 pageerror；桌面主路由在跳转后等待 network idle，避免 Firefox 快速切换时的动态模块取消 warning；本地干净 `npm ci` 后 Chromium + Firefox + WebKit `npm run test:e2e` 为 `12 passed`，共享 Vite dev server 的 Playwright workers 固定为 1，CI 使用独立 job 安装三种浏览器。真实后端数据和生产鉴权流程仍未纳入该 smoke。
- 2026-09-19 新增 `scripts/seed_playwright_data.py` 与 `frontend/e2e/real-backend.spec.js`：使用临时 SQLite 和固定测试 `INGEST_TOKEN` 注入真实用户、程序、积分、库存数据，`REAL_BACKEND_E2E=1` 选择不 mock API 的真实后端用例；本地 FastAPI + Chromium `1 passed`，CI 由独立 `frontend-real-e2e` job 执行，未使用默认数据库或生产凭据，生产鉴权流程仍不在该 smoke 范围内。
- 2026-09-19 新增 `frontend/src/api.generated.d.ts`，由 `openapi-typescript@7.13.0` 从 `docs/openapi.json` 生成；`npm run generate:api-types` 刷新声明，`npm run check:api-types` 在 CI 中通过 Git diff 阻断契约漂移。Playwright 默认不复用旧 Vite 进程，许可证检查支持带括号的 SPDX `AND/OR` 表达式；本地 Chromium/Firefox/WebKit `12 passed`，新增依赖后的 npm audit 和许可证门禁通过。
- 2026-09-19 复杂弹窗可访问性批次为 ProgramDetail/ProgramStock/UserPoints/Dashboard 加入加载 live 状态和 `aria-busy`，库存变动折叠区加入 `aria-controls`/region，图片加入 `alt`，QingLong Cron 输入和整理预览加入可访问名称/live 状态；Users 编辑/积分弹窗在关闭动画后恢复触发控件焦点，Playwright 覆盖 dialog role、modal、标题、表单名称和 WebKit 焦点回收。
- 2026-09-19 新增 `frontend/vitest.config.js` 和 `ProgramMetricStrip.component.spec.js`，使用 Vitest `4.1.11`、Vue Test Utils `2.5.1` 与 happy-dom 覆盖共享指标组件的空渲染、格式化、事件和异常值；Playwright Vite readiness probe 改为等待动态 `ProgramsPage.vue` 模块并使用 `--force`，避免依赖安装后首个 Chromium 的 `504 Outdated Optimize Dep`。
- 2026-09-19 将 `frontend/src/views/UsersPage.vue` 完成首轮 Prettier 格式收敛，并将该大型页面纳入 `npm run format:check`；本批只调整格式，不改变用户列表、弹窗焦点恢复或请求编排，其他大型页面继续按 OPT-014 拆分边界逐页纳入。
- 2026-09-19 将 `ProgramFilterBar.vue` 的状态、收藏、青龙、排序和标签筛选区补为带中文名称的 `role=group`，互斥按钮补 `aria-pressed`，并新增组件测试覆盖状态和事件映射；Vitest 组件测试从 `3 passed` 增至 `5 passed`，官方 registry npm audit 为 `0 vulnerabilities`。
- 2026-09-19 库存上报新增 `snapshot_id`、`snapshot_complete` 和 `expected_product_count`；旧库按需增加 `mini_programs.stock_snapshot_*` 字段。只有完整且数量匹配的非空报告才自动下架缺失商品，部分/数量异常/空报告会保留旧商品并在程序卡片显示需复核；新增输入约束、完整/部分快照回归测试和 `ProgramMetricStrip` 组件告警测试，Vitest 组件测试达到 `6 passed`，后端全量达到 `112 passed`。
- 2026-09-19 将 `QinglongCronsPage.vue` 的整理预览弹窗提取为 `QinglongCronPlanDialog.vue`；组件只通过 `v-model`、`apply` 和 `apply-item` 事件回传，父页继续持有计划生成、确认、批量写入和刷新。新增组件测试后 Vitest 达到 `8 passed`，并将该大型页面纳入 `npm run format:check`。
- 2026-09-19 将 Settings 分区导航提取为 `SettingsSectionNav.vue`，保留父页路由 query、请求和 busy 边界；新增组件测试覆盖 active `aria-current`、选择事件和 disabled boundary，Vitest 达到 `10 passed`，路线图推进 OPT-014 第二十一批、OPT-015 第十一批和 OPT-017 第十六批。
- 2026-09-19 将四个 Settings 区段重复的卡片、标题和描述结构提取为 `SettingsSectionCard.vue`；新增共享投影测试，Vitest 达到 `11 passed`，路线图推进 OPT-014 第二十二批和 OPT-017 第十七批。
- 2026-09-19 将 Programs/Apps 列表卡片提取为 `ProgramCard.vue`；组件承载卡片展示、指标和桌面/移动操作，通过白名单事件回传父页业务边界。新增 `ProgramCard.component.spec.js` 覆盖展示和事件映射，Vitest 达到 `13 passed`，路线图推进 OPT-014 第二十三批和 OPT-017 第十八批。
- 2026-09-19 新增 `ProgramDetailDialog.component.spec.js`，覆盖详情摘要、标签/备注、加载态可访问性、关闭回传和库存入口事件顺序；Vitest 达到 `16 passed`，路线图推进 OPT-017 第十九批。
- 2026-09-19 新增 `ProgramStockDialog.component.spec.js`，覆盖库存摘要、变动列表展开语义、关闭回传和加载态可访问性；Vitest 达到 `19 passed`，路线图推进 OPT-017 第二十批。
- 2026-09-19 新增 `UserPointsDialog.component.spec.js`，覆盖积分/现金格式、空态、加载态、关闭回传和 `closed` 事件；Vitest 达到 `22 passed`，路线图推进 OPT-017 第二十一批。
- 2026-09-19 新增 `StockProductCard.component.spec.js`，覆盖图片回退、价格/库存展示、兑换状态和 `hide` 事件；Vitest 达到 `25 passed`，路线图推进 OPT-017 第二十二批。
- 2026-09-19 新增 `UserMobileCard.component.spec.js`，覆盖身份/手机号回退、微信号隐藏、计数、删除 loading 和操作事件；Vitest 达到 `28 passed`，路线图推进 OPT-017 第二十三批。
- 2026-09-19 新增 `UserEditDialog.component.spec.js`，覆盖编辑/新增模式、字段回传、保存 loading、取消和关闭事件；Vitest 达到 `31 passed`，路线图推进 OPT-017 第二十四批。
- 2026-09-19 新增 `UserDesktopTable.component.spec.js`，覆盖多行 slot 展示、身份回退、计数和逐行操作事件；Vitest 达到 `34 passed`，路线图推进 OPT-017 第二十五批。
- 2026-09-19 新增 `QinglongCronRow.component.spec.js`，覆盖禁用/排除/拥挤/稀疏状态、时间摘要和操作事件；Vitest 达到 `37 passed`，路线图推进 OPT-017 第二十六批。
- 2026-09-19 新增 `SettingsSections.component.spec.js`，覆盖四个 Settings 业务区段的状态、字段、保存/同步/测试操作和数据库文件选择边界；Vitest 达到 `42 passed`，路线图推进 OPT-017 第二十七批。
- 2026-09-19 将 Dashboard 指标卡提取为 `DashboardMetricCard.vue`，父页继续保留指标计算和路由/弹窗副作用；新增组件展示/激活事件测试并将 `DashboardPage.vue` 纳入格式门禁，Vitest 达到 `44 passed`，路线图推进 OPT-014 第二十四批和 OPT-017 第二十八批。
- 2026-09-19 将 Points 账号展示卡提取为 `PointsAccountCard.vue`，父页继续保留数据标准化、筛选排序、抽屉状态和请求编排；新增状态/指标/Top 小程序/入口事件测试并将 `PointsPage.vue` 纳入格式门禁，Vitest 达到 `47 passed`，路线图推进 OPT-014 第二十五批和 OPT-017 第二十九批。
- 2026-09-19 修复 `PointsPage.vue` 漏传 `PointsAccountCard` 的 `item` 导致真实积分页渲染崩溃的问题；自定义桌面/移动导航改为显式调用 `router-link` 的 `navigate`，补充 Points 双抽屉 E2E 和导航回归，三浏览器 smoke 达到 `15 passed`，代码修复提交为 `ed78de2`。
- 2026-09-19 修复 `StockProductCard.vue` 在窄桌面双列网格下固定横向布局造成的内容重叠；通过每卡片容器的 container query 切换上下结构，新增三浏览器库存布局回归，完整 smoke 达到 `18 passed`，代码提交为 `fb04c97`。
- 2026-09-19 修复 `QinglongCronsPage.vue` 漏传 `QinglongCronRow` 的 `cron` 属性导致任务名称、命令和时间显示为空的问题；新增三浏览器 API 数据回归，完整 smoke 达到 `21 passed`，代码提交为 `65c9ece`。
- 2026-09-19 修复 `UsersPage.vue` 窄桌面内容区仍使用宽表格导致右侧列被裁切的问题；通过用户列表卡片 container query 切换 `UserMobileCard`，新增三浏览器布局回归，完整 smoke 达到 `24 passed`，代码提交为 `4e0ec57`。
- 2026-09-19 将 `ProgramsPage.vue` 的列表/详情/库存读取统一到 `useAbortableRequest`，弹窗关闭和重复打开会取消旧请求；新增卡片到详情/库存弹窗数据 smoke，三浏览器 mock smoke 达到 `30 passed`，临时 SQLite 真实后端 Chromium smoke `1 passed`，代码提交为 `0c9275e`。
- 2026-09-18 新增 `scripts/export_openapi.py` 与 `docs/openapi.json`；脚本从 FastAPI `app.openapi()` 生成排序稳定的 39-path API 基线，`--check` 用于 CI 漂移阻断，不启动数据库或后台调度器。
- 2026-09-19 将 FastAPI 升级到 `0.141.1` 后重新生成 `docs/openapi.json`；文件上传和校验错误 schema 的变化已通过 `scripts/export_openapi.py --check` 固化，避免依赖升级造成 API 基线漂移。
- `frontend/package.json` 提供 `npm test`、`npm run test:components`、`npm run test:e2e`、`npm run lint`、`npm run format:check`、`npm run generate:api-types`、`npm run check:api-types` 和 `npm run build`；ESLint/Prettier/Vitest/Playwright 配置与用例格式检查已接入 CI，现有代码基线通过 lint 和格式门禁。
- `npm run format:check` 当前覆盖共享层、组件、E2E、composable/utils，以及已完成首轮格式收敛的 `UsersPage.vue` 和 `QinglongCronsPage.vue`；其他大型页面继续随稳定拆分边界逐页纳入。
- 已删除确认无引用的 Vite 初始 `HelloWorld.vue`、`vite.svg` 和 `vue.svg`，入口页不再引用模板 favicon。
- README、CLAUDE、技术文档和 `points-stock.service` 已与当前 scheduler-only 青龙同步、显式导入约定、路由/API 入口及 SQLite 单 worker 默认值对齐。
- `scripts/export_openapi.py` 从 FastAPI `app.openapi()` 生成排序稳定的 `docs/openapi.json`；`--check` 在 CI 中阻断路由/参数/schema 漂移，导入 app 不启动数据库或后台调度器。
- `frontend/scripts/check-frontend-resources.mjs` 由 `npm run check:resources` 执行，扫描 `public`/`src/assets` 静态资源引用并阻断 Vite starter 资源回归；当前仓库没有这些静态资源，因此门禁报告扫描 `0` 项。动态路由、自动注册 Vue 组件和构建产物不纳入该检查。
- `scripts/check_dependency_licenses.py` 递归检查 `requirements-dev.txt` 的 Python 依赖闭包和已安装 npm 包的许可证；未知或不在允许清单内的许可证会失败退出，带括号的 SPDX `AND/OR` 表达式会拆成独立许可证检查，允许清单明确包含 `BlueOak-1.0.0`。本地检查 35 个 Python 包和 335 个 npm 包通过。
- 2026-09-19 依赖安全批次升级了有公告的 Axios/Vite 传递树，以及 FastAPI、Starlette、python-multipart、Jinja2、python-dotenv、Requests 和 pytest；本地 `npm audit --audit-level=high` 为 `0 vulnerabilities`，`pip-audit --strict` 为 `No known vulnerabilities found`。
- `.github/pull_request_template.md` 固化测试、迁移/旧库兼容、API/OpenAPI/上报模板、移动端、敏感文件和路线图/记忆同步清单。
- 全局导航进度/骨架由 `App.vue` 提供；`router.js` 在仪表盘空闲或库存菜单 hover/focus 时预加载库存 chunk。预加载失败会清理 promise，不能因此绕过访问保护。
- 青龙批量应用请求把超时提高到 300 秒；后端最多并发 8 个青龙 PUT。
- 主移动导航是 `App.vue` 自定义 `.mobile-nav-shell`，不要改回 Element Plus `el-drawer`，否则容易出现遮罩残留/点击被拦截。
- `App.vue` 移动导航按钮带 `aria-expanded`/`aria-controls`，面板带 dialog label；打开后首焦点进入导航，Tab/Shift+Tab 循环，Escape/关闭后焦点回到打开按钮，相关行为由 Playwright smoke 断言。
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

重要：数据库内 access key 已改为单向哈希，旧明文仅作为兼容迁移字段存在且启动迁移后清空；Cookie 会话使用哈希作为签名绑定材料。生产 Docker 当前是单 worker，单进程失败限流覆盖当前实例；UI 审计已支持低频保留和受保护分页查询，成功的设置修改、数据库导入、账号/程序删除和批量 QingLong cron 更新也会记录无凭据事件。只有未来启用多 worker/多实例时才需要反向代理共享限流；失败/拒绝类高风险事件、指标和统一 JSON 日志仍待完善。

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

容器默认 `TZ=Asia/Shanghai`、`UVICORN_WORKERS=1`，并把 `host.docker.internal` 映射到宿主机，青龙在宿主机时可配置类似 `http://host.docker.internal:5700`。当前实际生产部署是 Docker Compose 单 worker；本轮测试/工作区的代码和配置尚未迁移到生产容器。

### systemd

`points-stock.service` 是 Linux 示例，路径仍是 `/root/wechat-points-stock`，需要按实际用户/路径修改。它直接启动 uvicorn，当前写的是 `--workers 2`；这与 Compose 的单 worker 推荐不一致，也不会经过 `start.sh` 的建库检查。当前生产 Docker 已明确使用单 worker；systemd 的 `--workers 2` 只是仓库中的历史示例，不代表当前生产部署。若未来切换 systemd 或扩容，需重新评估 SQLite 与共享限流。

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
3. **UI access 已完成第一阶段会话化、单进程限流和基础审计治理。** 当前使用 8 小时签名 HttpOnly Cookie，旧 header 只用于迁移；UI 审计按默认 90 天/10,000 条低频清理，并由受保护 API 分页查询；成功的配置修改、数据库导入、账号/程序删除和批量 QingLong cron 更新共用同一审计表。当前生产 Docker 是单 worker，不存在跨 worker 限流分散问题；未来扩容才需依赖反向代理共享限流，失败/拒绝类高风险事件、指标和统一 JSON 日志仍待补。
4. **数据库恢复已加跨进程保护。** `app/maintenance.py` 使用数据库路径旁路锁，维护期间新 API 返回 503，并等待当前进程的 API/Bark/QingLong 数据库任务退出；恢复前 `wal_checkpoint(TRUNCATE)` 忙则中止，其他 worker 的在途事务由 checkpoint 兜底。真实文件恢复/回滚集成测试和更完整的调度暂停仍待补齐，不要把 `os.replace` 视作已完成全部恢复治理。
5. **文档与当前 QingLong 列表行为有偏差。** README/CLAUDE 的部分描述说 `GET /programs` 会在自动模式触发非阻塞后台同步；当前 `handle_programs_list_sync()` 在 `auto` 模式明确不在列表路径触发，实际由启动的 scheduler 负责，`trigger_background_sync()` 虽存在但当前没有调用点。
6. **启动配置不完全统一。** Compose 推荐 1 worker；systemd 示例使用 2 worker，且绕过 `start.sh`/`entrypoint.sh` 的初始化和前端存在性检查。
7. **业务日期已收口，存储时间仍需持续审计。** `web.py` 的未上报、库存变化和积分变化路径已统一通过 `timeutil` 按 Asia/Shanghai 判断，历史 naive 值按 UTC 解释；模型/清理服务保留 `utcnow()` 作为 naive UTC 写入，API 时间字段和无时区上报输入仍需逐项审计。
8. **库存中心与下架抽屉已改成服务端分页。** 首屏不再自动请求下架明细，抽屉默认每页 50 条并可继续加载；全局导航骨架、进度反馈和库存 chunk 预加载已补；SQLite 通过 `stock_center_revision` 及商品、积分历史、小程序、库存历史触发器支持 ETag/304，后续仍需真实 p95 基准和虚拟网格。revision 表/触发器目前兼容旧库按需建立，正式迁移器仍待统一。
9. **健康检查已提供。** `/health/live` 只表示进程路由可用；`/health/ready` 执行 `SELECT 1`，Compose 已用它做容器 healthcheck。
10. **上报与库存 CRUD 已补第一层输入约束。** Pydantic schema 现在拒绝空白/超长字段、负库存/积分/现金、NaN/Infinity、非整数计数和超大批量；合法数字字符串继续兼容。图片上传还会校验 PNG/JPEG/GIF/WebP 尺寸，限制为 25 MP，并在尺寸校验失败时清理已写入文件；请求体/代理统一上限、批量配置化和校验审计仍待补。
11. **SQLite 连接已开启外键约束。** `app/database.py` 对每个 SQLite 连接执行 `PRAGMA foreign_keys=ON`，现有 `PointsHistory` 账号/程序外键有回归测试；正式迁移、旧库孤儿清理、StockHistory 外键和级联策略仍待设计。
12. **历史裁剪和积分摘要查询已避免大规模 Python 物化。** `cleanup_service.py` 用数据库子查询按时间和 `id` 稳定裁剪积分/库存历史，并保持调用方事务边界；`web.py` 的账号/积分摘要用窗口查询取每个组合的最新记录和本地业务日前基线；`current_point_balances` 已承接程序卡片、仪表盘、库存最高余额和最近上报时间聚合。程序排行/明细仍读历史，快照与历史的真实规模 p95 基准仍待补。
13. **Bark/QingLong HTTP 连接治理已补。** 两个服务都按线程复用带连接池的 `requests.Session`，scheduler/shutdown 时释放；通知与 QingLong PUT 均关闭自动重试，避免重复副作用。仅对明确幂等的 QingLong GET 设计有限重试/退避仍是后续项。

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
