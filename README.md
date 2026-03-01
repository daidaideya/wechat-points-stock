# WeChat Points & Stock Monitor (积分监控系统)

一个基于 FastAPI 和 SQLite 的轻量级积分与库存监控系统，专为树莓派等嵌入式环境设计。支持多用户、多小程序积分追踪，库存管理，以及可视化数据看板。

## 🌟 核心功能

### 1. 积分监控 (Points Monitor)
- **多维度视图**：
  - **按用户聚合**：查看每个微信用户的活跃小程序数量、各小程序积分详情。
  - **按小程序聚合**：查看特定小程序的积分排行榜（Top N 用户）。
- **实时状态**：
  - 自动区分“未注册”用户（0分）与活跃用户。
  - 支持折叠/展开用户详情，按需异步加载数据，优化性能。
- **管理操作**：
  - 支持删除单条积分记录。

### 2. 小程序管理 (Mini Program Management)
- **列表与搜索**：
  - 分页展示小程序列表（默认 21 条/页）。
  - **增强搜索**：支持**拼音全拼**（如 `jingdong`）、**首字母**（如 `jd`）及汉字/ID搜索。
- **授权类型管理**：
  - 支持三种授权模式切换：`Code` (默认), `Token`, `App`。
  - 在列表页直接通过下拉菜单快速切换类型。
- **置顶功能**：
  - 支持将常用小程序置顶（显示在列表最前）。
  - 可视化置顶状态（蓝色实心箭头 vs 灰色空心箭头）。

### 3. 库存管理 (Stock Management)
- **商品管理**：
  - 支持创建、编辑商品信息（名称、图片、积分、库存）。
  - **自动聚合**：库存后台按小程序维度聚合展示商品。
- **全局搜索**：
  - 支持在库存页面跨小程序搜索商品（按名称）。
- **API 集成**：
  - 提供青龙面板专用上报接口，支持自动创建商品和更新库存/价格。
  - 自动记录库存变更历史。

### 4. 数据看板 (Dashboard)
- 实时统计用户总数、小程序总数。
- 最近积分变动日志流。

## 🛠 技术栈

- **后端**：Python 3.11 + FastAPI
- **数据库**：SQLite + SQLAlchemy (ORM)
- **前端**：Jinja2 模板 + Bootstrap 5 + Vanilla JS
- **搜索增强**：`pypinyin` (用于中文拼音搜索)
- **部署目标**：Linux (Raspberry Pi / Debian / Ubuntu)

## 🚀 快速开始

### 1. 环境准备
确保已安装 Python 3.11+。

```bash
# 克隆仓库
git clone <repository-url>
cd wechat-points-stock

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库初始化
系统启动时会自动创建 `data/database.db`。如果需要应用最新的数据库迁移（如添加字段）：

```bash
# 示例：添加 auth_type 字段
python3 scripts/migrate_add_auth_type.py

# 示例：添加 sort_order 字段
python3 scripts/migrate_add_program_sort_order.py

# 示例：添加 phone 字段索引 (v1.1.1 Update)
python3 scripts/migrate_add_phone_index.py
```

### 3. 启动服务
```bash
# 开发模式（支持热重载）
python3 main.py
```
服务默认运行在 `http://0.0.0.0:8000`。

## 📂 项目结构

```
wechat-points-stock/
├── app/
│   ├── routers/        # API 路由 (web.py, qinglong.py, stock.py 等)
│   ├── models.py       # 数据库模型 (WechatAccount, MiniProgram, PointsHistory, Product...)
│   ├── database.py     # 数据库连接
│   └── config.py       # 配置项
├── templates/          # Jinja2 前端模板 (html)
├── static/             # 静态资源 (css, js, images)
├── scripts/            # 数据库迁移脚本
├── data/               # SQLite 数据库文件存储
├── main.py             # 程序入口
└── requirements.txt    # 依赖列表
```

## 🔌 API 概览

### 小程序 (Programs)
- `GET /api/v1/programs`: 分页获取小程序列表（支持 `q` 搜索参数）。
- `PUT /api/v1/programs/{id}`: 更新小程序信息（`auth_type`, `is_pinned`）。
- `DELETE /api/v1/programs/{id}`: 删除小程序及其所有数据。

### 用户 (Accounts)
- `GET /api/v1/accounts/{wechat_id}/points_details`: 获取特定用户的详细积分数据。
- `DELETE /api/v1/accounts/{wechat_id}`: 删除用户。

### 库存与商品 (Stock & Products)
- **管理接口**:
  - `POST /api/v1/stock/product`: 创建或更新商品信息（需提供 `program_id`, `product_name`）。
  - `GET /api/v1/stock/programs`: 获取包含商品统计的小程序列表。
  - `GET /api/v1/stock/programs/{program_id}/products`: 获取指定小程序的商品列表。
  - `GET /api/v1/stock/search`: 全局商品搜索（支持 `q` 参数）。
- **青龙上报接口**:
  - `POST /api/v1/stock-report`: 批量上报商品库存与积分信息。
    - Header: `Authorization: Bearer <API_TOKEN>`
    - Body: 
      ```json
      {
        "program_id": "wx...", 
        "products": [
           {"product_name": "...", "stock": 10, "points": 100, "image_url": "..."}
        ]
      }
      ```

## 🔄 更新日志

### v1.1.1 (2026-02-07)
- **API 兼容性与用户识别优化**：
  - 优化积分上报接口：支持自动识别手机号格式的 `wechat_id`。
  - **手机号绑定逻辑**：
    - 若上报的 `wechat_id` 为手机号且已在系统绑定微信账号，自动关联并使用该微信账号的昵称。
    - 若手机号未绑定，用户昵称自动设置为空，避免显示乱码或脚本默认名。
  - **向下兼容**：完全兼容原有手机号+密码登录的脚本，无需修改脚本代码。
  - **数据库优化**：为 `wechat_accounts` 表的 `phone` 字段添加索引，提升查询性能。

### v1.1.0 (2026-02-06)
- **库存管理模块增强**：
  - 新增商品图片的按需加载与模态框预览功能。
  - 优化小程序维度的折叠/展开视图。
  - 支持显示小程序下的“最高用户积分”。
  - 新增小程序删除功能，支持一键清理关联商品与积分记录。
  - 新增跳转至小程序积分详情页的快捷入口，并支持按积分从低到高排序。
  - **商品列表排序**：支持在库存页面直接按积分从低到高对商品进行排序（纯客户端实现，无跳转）。
  - **交互体验优化**：
    - 将管理操作按钮（排序/详情/删除）迁移至折叠面板内部，杜绝误触。
    - 优化按钮组层级，解决与下拉菜单的点击冲突。
    - 适配长文本显示，优化移动端布局。
  - 修复图片加载失败时的 404 错误与显示异常。

### v1.0.0 (Initial Release)
- 基础功能上线：用户管理、小程序管理、积分追踪。

## 📝 开发计划

- [x] 小程序列表分页与滚动加载
- [x] 小程序拼音搜索支持
- [x] 小程序授权类型切换 (Code/Token/App)
- [x] 小程序置顶功能
- [x] 库存管理模块 (API + 前端搜索 + 可视化优化)
- [ ] 移动端适配优化
