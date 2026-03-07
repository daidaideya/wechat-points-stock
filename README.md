# WeChat Points & Stock Monitor（积分监控系统）

当前项目已切换为 **[`Vue 3`](frontend/package.json) + [`Vite`](frontend/vite.config.js) + [`Element Plus`](frontend/package.json) 前端 SPA** 与 **[`FastAPI`](app/main.py) 后端 API** 的前后端分离模式。

- 前端负责全部页面渲染、路由与交互；
- 后端仅负责 API、静态资源分发、前端构建产物托管与路由兜底；
- 旧的 Jinja2 模板页面方案已停止使用，不再作为运行入口。

## 技术栈

- 后端：Python 3.11+、[`FastAPI`](app/main.py)、SQLAlchemy、SQLite
- 前端：[`Vue 3`](frontend/package.json)、[`Vite`](frontend/vite.config.js)、[`Element Plus`](frontend/package.json)、Axios、[`Vue Router`](frontend/src/router.js)
- 搜索增强：`pypinyin`
- 部署方式：[`Docker`](Dockerfile)、[`Docker Compose`](docker-compose.yml)

## 当前页面结构

SPA 路由已统一由 [`frontend/src/router.js`](frontend/src/router.js) 管理，包含：

- [`/dashboard`](frontend/src/views/DashboardPage.vue)
- [`/programs`](frontend/src/views/ProgramsPage.vue)
- [`/favorites`](frontend/src/views/FavoritesPage.vue)
- [`/programs/:programId`](frontend/src/views/ProgramDetailPage.vue)
- [`/users`](frontend/src/views/UsersPage.vue)
- [`/points`](frontend/src/views/PointsPage.vue)
- [`/stock`](frontend/src/views/StockPage.vue)
- [`/settings`](frontend/src/views/SettingsPage.vue)

## 后端 API 概览

主要 API 由 [`app/routers/web.py`](app/routers/web.py) 与 [`app/routers/stock.py`](app/routers/stock.py) 提供。

### 仪表盘
- `GET /api/v1/dashboard`

### 小程序
- `GET /api/v1/programs`
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

### 设置
- `GET /api/v1/settings/logs`
- `POST /api/v1/settings/logs`

### 库存
- `GET /api/v1/stock/programs`
- `GET /api/v1/stock/programs/{program_id}/products`
- `GET /api/v1/stock/search`
- `POST /api/v1/stock/product`
- `POST /api/v1/stock-report`

## 开发运行

### 1. 安装后端依赖
Windows：

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Linux/macOS：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 启动开发环境
先启动后端：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

再启动前端：

```bash
cd frontend
npm run dev
```

访问地址：
- 前端开发服务器：`http://127.0.0.1:5173/app/`
- 后端 API：`http://127.0.0.1:8000/api/v1/...`

说明：[`frontend/vite.config.js`](frontend/vite.config.js) 已代理 `/api` 与 `/static` 到后端。

## 生产运行

### 1. 构建前端

```bash
cd frontend
npm run build
```

### 2. 启动后端

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

生产访问地址：
- SPA 入口：`http://127.0.0.1:8000/`
- 兼容入口：`http://127.0.0.1:8000/app`

后端入口与前端回退逻辑位于 [`app/main.py`](app/main.py) ：
- 根路径 `/` 返回 [`frontend/dist/index.html`](frontend/dist/index.html)
- 任意非 API 前端路由刷新时自动回退到 SPA 入口
- `/static` 继续由后端分发上传图片等静态文件

## Docker 部署

当前项目已支持通过 [`Dockerfile`](Dockerfile) 进行前后端一体化构建：

- 第一阶段使用 `Node 20` 构建 [`frontend/dist`](frontend/dist)
- 第二阶段使用 `Python 3.11` 安装后端依赖并运行 [`FastAPI`](app/main.py)
- 容器启动时由 [`entrypoint.sh`](entrypoint.sh) 自动检查数据库、初始化目录并启动服务

### 1. 使用 Docker Compose 启动

```bash
docker compose up -d --build
```

启动后默认访问：

- `http://127.0.0.1:5711/`
- `http://127.0.0.1:5711/app`

### 2. 持久化目录

[`docker-compose.yml`](docker-compose.yml) 已默认挂载以下目录：

- [`./data`](data)
- [`./logs`](logs)
- [`./static/uploads`](static/uploads)

这样容器重建后，数据库、日志和上传文件仍会保留在宿主机。

### 3. 环境变量

[`docker-compose.yml`](docker-compose.yml) 默认加载 [`.env`](.env) 文件，并设置：

- `TZ=Asia/Shanghai`

[`entrypoint.sh`](entrypoint.sh) 还支持以下可选启动参数：

- `HOST`
- `PORT`
- `UVICORN_WORKERS`

### 4. 单独构建镜像

```bash
docker build -t wechat-points-stock .
```

### 5. 单独运行容器

```bash
docker run -d \
  --name wechat-points-stock \
  -p 5711:5711 \
  --env-file .env \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  -v ./static/uploads:/app/static/uploads \
  wechat-points-stock
```

### 6. 部署注意事项

- 首次启动时若 [`data/database.db`](data/database.db) 不存在，[`scripts/init_db.py`](scripts/init_db.py) 会自动初始化数据库
- 若前端构建产物缺失，[`entrypoint.sh`](entrypoint.sh) 会直接退出，避免容器启动后页面不可访问
- 当前服务由 `uvicorn` 直接启动，默认监听 `5711` 端口
- 如果服务器已有反向代理，可将 Nginx / 宝塔 / 1Panel 转发到 `5711`

## 项目结构

```text
wechat-points-stock/
├── app/
│   ├── main.py
│   ├── models.py
│   └── routers/
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   ├── App.vue
│   │   ├── api.js
│   │   ├── main.js
│   │   └── router.js
│   ├── dist/
│   ├── package.json
│   └── vite.config.js
├── static/
├── templates/            # 历史模板目录，已废弃
├── data/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 迁移说明

本轮改造重点：

- 将原服务端页面能力从 [`app/routers/web.py`](app/routers/web.py) 中剥离，仅保留 API
- 将库存 HTML 视图从 [`app/routers/stock.py`](app/routers/stock.py) 中剥离，仅保留 API
- 将全站主要页面迁移到 [`frontend/src/views`](frontend/src/views)
- 由 [`frontend/src/App.vue`](frontend/src/App.vue) 提供统一布局
- 由 [`app/main.py`](app/main.py) 托管 SPA 入口并处理前端路由刷新回退
- 增加基于 [`Dockerfile`](Dockerfile) 与 [`docker-compose.yml`](docker-compose.yml) 的一体化容器部署方式

## 已知说明

- 当前构建可通过，但 [`Vite`](frontend/vite.config.js) 仍提示前端主包较大，主要来自 [`Element Plus`](frontend/package.json) 与当前全量打包；后续可继续通过路由懒加载与手动拆包优化。
- [`templates/`](templates/) 目录目前已不再作为运行入口使用，如需彻底物理删除，可在确认无历史回滚需求后清理。
- 如需生产级高并发部署，可在容器前增加 Nginx，并按实际服务器配置调整 [`UVICORN_WORKERS`](entrypoint.sh) 。