# WeChat Points & Stock Monitor

一个用于管理微信账号、小程序积分、库存商品与同步日志的前后端分离项目。

当前架构为：

- 前端：`Vue 3` + `Vite` + `Element Plus`
- 后端：`FastAPI` + `SQLAlchemy` + `SQLite`
- 部署：本地运行或 `Docker Compose` 一体化部署

## 1. 项目能做什么

这个系统主要解决几类日常管理问题：

- 统一管理微信账号信息
- 查看每个账号的积分 / 现金明细
- 管理已接入的小程序列表（收藏、归档、标签、定时状态）
- 查看小程序详情、排行和库存状态（弹窗，可兑换商品高亮）
- 接收青龙脚本上报的积分 / 现金 / 库存
- 同步青龙面板定时任务启用/禁用与 cron 表达式
- Bark 定时推送今日未上报小程序
- 数据库备份导出 / 导入恢复
- 访问密钥保护与日志清理设置

如果你只想快速跑起来，可以直接看下面的“快速开始”。

## 2. 当前技术架构

### 前端

前端是一个单页应用（SPA），负责：

- 页面渲染
- 路由跳转
- 表单交互
- 数据请求
- 构建产物输出到 `frontend/dist`

相关文件：

- `frontend/src/main.js`
- `frontend/src/router.js`
- `frontend/src/App.vue`
- `frontend/vite.config.js`

### 后端

后端只负责 API、静态资源和前端构建产物托管，主要入口：

- `app/main.py`
- `app/routers/web.py`
- `app/routers/stock.py`
- `app/routers/qinglong.py`
- `app/routers/images.py`

后端行为可以简单理解为：

- `/api/...` 提供业务接口
- `/static/...` 提供上传等静态文件
- `/` 与 `/app` 返回前端 SPA 入口页面
- 前端刷新任意页面时，由后端回退到 `frontend/dist/index.html`

## 3. 页面与功能概览

当前前端页面由 `frontend/src/router.js` 统一管理，包含以下主要路由：

- `/dashboard`：仪表盘（微信号卡片跳转用户管理）
- `/programs`：小程序列表（主工作台）
- `/favorites`：重点关注列表
- `/programs/:programId`：小程序详情页（列表内也支持弹窗详情）
- `/users`：用户管理
- `/points`：积分总览（含现金汇总）
- `/stock`：库存管理
- `/settings`：系统设置（二级分区：基础 / 青龙 / Bark / 备份）

### 3.1 小程序列表重点能力

- 分段筛选：状态 / 收藏 / 青龙启停 / 排序（默认、按 cron 最早时间）
- 标签常显筛选 + 当前筛选摘要
- 卡片展示：青龙启停图标、cron 表达式、最高积分、最高现金（无数据时隐藏）
- 点击名称复制名称，点击 program_id 复制 ID
- 详情 / 库存均为当前页弹窗，不强制跳转
- 库存弹窗：可兑换商品高亮并置顶；今日库存变动默认折叠

### 3.2 系统设置分区

- 基础设置：日志清理、访问保护
- 青龙联动：OpenAPI 凭证、立即同步
- Bark 推送：开关、Device Key、推送时间、立即测试
- 数据备份：导出 `.db` / 导入恢复

## 4. API 概览

以下是当前项目中最常用的一组接口，便于快速理解系统能力。

### 仪表盘

- `GET /api/v1/dashboard`

### 小程序

- `GET /api/v1/programs`（支持 `q` / `status` / `ql_status` / `sort=default|cron`）
- `GET /api/v1/programs/favorites`
- `GET /api/v1/programs/unreported`
- `GET /api/v1/programs/{program_id}`
- `GET /api/v1/programs/{program_id}/stock`
- `GET /api/v1/programs/{program_id}/ranking`
- `PUT /api/v1/programs/{program_id}`
- `DELETE /api/v1/programs/{program_id}`

### 用户与积分

- `GET /api/v1/accounts`
- `GET /api/v1/accounts/{wechat_id}`
- `GET /api/v1/accounts/{wechat_id}/points_details`
- `PUT /api/v1/accounts/{wechat_id}`
- `PUT /api/v1/accounts/sort-order`
- `DELETE /api/v1/accounts/{wechat_id}`
- `DELETE /api/v1/accounts/{wechat_id}/programs/{program_id}`
- `GET /api/v1/points`

### 青龙上报

- `POST /api/v1/qinglong/report`（积分 / 现金）
- `POST /api/v1/stock-report`（库存）

积分上报 `points_data[]` 字段：

```json
{
  "program_id": "wx...",
  "program_name": "小程序名称",
  "current_points": 100,
  "current_cash": 1.25
}
```

说明：`current_points` 与 `current_cash` 至少传一个；只传积分的老脚本完全兼容。

### 设置

- `GET/POST /api/v1/settings/logs`
- `GET/POST /api/v1/settings/qinglong`
- `POST /api/v1/settings/qinglong/sync`
- `GET/POST /api/v1/settings/bark`
- `POST /api/v1/settings/bark/test`
- `GET /api/v1/settings/database/export`
- `POST /api/v1/settings/database/import`
- `GET /api/v1/access/status`
- `POST /api/v1/access/verify`

### 库存

- `GET /api/v1/stock/programs`
- `GET /api/v1/stock/programs/{program_id}/products`
- `GET /api/v1/stock/search`
- `POST /api/v1/stock/product`
- `POST /api/v1/stock-report`

## 5. 快速开始

## 5.1 环境要求

建议版本：

- Python `3.11+`
- Node.js `20+`
- npm `10+`

## 5.2 安装后端依赖

Windows：

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Linux / macOS：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 5.3 安装前端依赖

```bash
cd frontend
npm install
```

## 5.4 启动开发环境

先启动后端：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

再启动前端：

```bash
cd frontend
npm run dev
```

开发时访问：

- 前端开发地址：`http://127.0.0.1:5173/app/`
- 后端 API：`http://127.0.0.1:8000/api/v1/...`

开发说明：

- 前端开发服务器和后端 API 是分开运行的
- `frontend/vite.config.js` 已代理 `/api` 和 `/static`
- 如果只启动后端并访问 `8000`，看到的是构建后的前端，而不是 Vite 实时开发页面

## 6. 近期重要能力补充

- 积分上报支持小数与现金（`current_cash`）
- 青龙 OpenAPI 同步启停状态与 cron
- 小程序列表支持按 cron 最早时间排序
- Bark 定时推送未上报小程序
- 设置页分栏：基础 / 青龙 / Bark / 备份
- 数据库一键导出导入
- 移动端主导航改为自研侧栏，避免宽窄屏切换白框 / 按钮点不动

## 6. 生产运行

先构建前端：

```bash
cd frontend
npm run build
```

再启动后端：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

生产访问地址：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/app`

说明：

- 后端会自动托管 `frontend/dist`
- 前端页面刷新时会自动回退到 SPA 入口
- `/static` 继续由后端提供文件访问能力

## 7. Docker 部署

项目支持通过 `Dockerfile` 和 `docker-compose.yml` 进行一体化部署。

### 7.1 使用 Docker Compose

```bash
docker compose up -d --build
```

默认访问地址：

- `http://127.0.0.1:5711/`
- `http://127.0.0.1:5711/app`

### 7.2 数据持久化目录

默认挂载目录如下：

- `./data`
- `./logs`
- `./static/uploads`

这些目录会保留：

- 数据库文件
- 日志文件
- 上传文件

### 7.3 环境变量与启动参数

`docker-compose.yml` 默认读取 `.env`，并设置：

- `TZ=Asia/Shanghai`

启动脚本还支持以下参数：

- `HOST`
- `PORT`
- `UVICORN_WORKERS`

### 7.4 单独构建镜像

```bash
docker build -t wechat-points-stock .
```

## 8. 项目结构

```text
wechat-points-stock/
├── app/                     # FastAPI 后端
│   ├── main.py
│   └── routers/
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── views/
│   │   ├── App.vue
│   │   ├── api.js
│   │   ├── main.js
│   │   └── router.js
│   ├── dist/
│   ├── package.json
│   └── vite.config.js
├── data/                    # SQLite 数据库
├── logs/                    # 运行日志
├── static/uploads/          # 上传资源
├── scripts/                 # 初始化或辅助脚本
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 9. 前端构建优化说明

本项目目前已经完成以下几类前端构建优化。

### 9.1 路由懒加载

`frontend/src/router.js` 中的页面组件已改为按路由动态加载：

- 首屏不再一次性把所有页面代码都打进主包
- 进入某个页面时，才加载对应页面代码
- 对页面较多的后台系统，这种优化通常最直接有效

### 9.2 自动按需引入组件与样式

当前已接入基于 Vite 的自动按需引入方案：

- 自动导入常用 Vue / Vue Router API
- 自动注册实际用到的 Element Plus 组件
- 自动按需引入对应组件样式
- 移除了 `main.js` 中的 Element Plus 全量注册与全量样式引入

这样做的好处是：

- 避免把未使用组件一起打包
- 避免继续依赖 `element-plus/dist/index.css` 全量样式
- 更适合页面型后台项目逐步扩展

### 9.3 手动拆包

`frontend/vite.config.js` 中已为常见大依赖增加手动拆包策略：

- `element-plus`
- `@element-plus/icons-vue`
- `vue`
- `vue-router`
- `axios`

这样做的作用是：

- 降低主入口 chunk 体积
- 让依赖缓存更稳定
- 构建分析时更容易定位大包来源

### 9.4 图标使用收敛

项目继续保留 `@element-plus/icons-vue`，但改为仅按文件导入实际使用的图标，避免无意义扩散使用范围。

如果后续继续压缩体积，建议优先：

- 保持页面内只引入实际使用的图标
- 避免在公共入口统一注册整套图标
- 对重复但价值不高的装饰性图标做进一步精简

### 9.5 构建分析工具

已引入构建分析工具，可在前端目录运行：

```bash
npm run analyze
```

构建完成后会生成：

- `frontend/dist/stats.html`

打开这个文件即可直观看到各个 chunk、依赖包与体积分布，便于继续判断：

- 哪个页面 chunk 偏大
- `Element Plus` 占比是否过高
- 图标、路由、请求库是否拆分合理

### 9.6 仍需注意的点

虽然目前已经完成懒加载、按需引入、手动拆包与构建分析支持，但如果页面继续增长，仍建议持续关注：

- `Element Plus` 仍然可能是主要体积来源之一
- 样式体积仍可能随着页面组件增多而上升
- 某些公共页面若引入过多组件，仍可能形成较大的页面 chunk

## 10. 说明与注意事项

- 当前项目的主要运行入口已经是 Vue SPA + FastAPI API
- 系统设置中已支持“访问密钥保护”开关
- 当访问保护开启且已设置访问密钥后，进入系统需要先输入密钥才能访问页面与接口
- 访问密钥默认为空，需在“系统设置”页面中手动设置
- 本地数据库默认位于 `data/database.db`
- 如首次启动数据库不存在，初始化脚本会负责创建基础结构
- 旧数据库会在首次读取系统设置时自动补齐新增字段

## 11. 常用命令速查

安装后端依赖：

```bash
pip install -r requirements.txt
```

安装前端依赖：

```bash
cd frontend && npm install
```

启动后端开发：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动前端开发：

```bash
cd frontend && npm run dev
```

构建前端：

```bash
cd frontend && npm run build
```

Docker 启动：

```bash
docker compose up -d --build
```

---

如果你准备继续迭代这个项目，建议优先查看：

- `app/main.py`
- `frontend/src/router.js`
- `frontend/src/views/`
- `frontend/vite.config.js`

