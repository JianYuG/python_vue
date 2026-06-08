# 地图采集系统

基于 Vue 3 + OpenLayers + FastAPI + PostGIS 的地图要素采集与管理平台。

## 项目结构

```
python_vue/
├── backend/                # 后端 (FastAPI)
│   ├── app/
│   │   ├── api/            # 路由模块
│   │   │   ├── auth.py         # 用户认证（注册/登录）
│   │   │   ├── feature.py      # 地图要素 CRUD
│   │   │   ├── attachment.py   # 要素附件管理
│   │   │   ├── xzqh.py         # 行政区划树接口
│   │   │   └── doorplate.py    # 门牌搜索接口
│   │   ├── core/           # 核心配置
│   │   │   ├── config.py       # 环境变量配置
│   │   │   ├── database.py     # 数据库连接
│   │   │   ├── security.py     # JWT/密码加密
│   │   │   └── result.py       # 统一响应格式
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   └── schemas/        # Pydantic 请求/响应模型
│   ├── uploads/            # 附件上传目录（git忽略）
│   ├── requirements.txt    # Python 依赖
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── frontend/               # 前端 (Vue 3 + Vite)
│   ├── src/
│   │   ├── api/            # 接口请求封装
│   │   ├── assets/         # 静态资源
│   │   ├── components/     # 组件
│   │   │   ├── MapControls.vue    # 地图控制（缩放/图层/编辑）
│   │   │   ├── DrawToolbar.vue    # 绘制工具栏
│   │   │   ├── FeatureFormDialog.vue  # 要素属性弹窗
│   │   │   ├── SearchPanel.vue    # 搜索面板
│   │   │   └── XzqhSelector.vue   # 行政区划选择器
│   │   ├── router/         # 路由
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── utils/          # 工具函数
│   │   └── views/          # 页面视图
│   ├── vite.config.js
│   └── package.json
│
└── .gitignore
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus + OpenLayers + Pinia |
| 后端 | FastAPI + SQLAlchemy 1.4 (async) + asyncpg |
| 数据库 | PostgreSQL + PostGIS |
| 认证 | JWT (PyJWT + bcrypt) |

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 18+
- PostgreSQL 12+ （需安装 PostGIS 扩展）

### 后端启动

```bash
cd backend

# 1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量（复制并修改）
cp .env.example .env

# 4. 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload
```

### 前端启动

```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev
```

浏览器访问 `http://localhost:5173`

## 环境变量

后端通过 `.env` 文件配置（不纳入版本控制），示例：

```env
# 数据库
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=postgres

# JWT
JWT_SECRET_KEY=your-random-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 调试
DEBUG=false
```

## 核心功能

- **地图浏览** — 天地图电子/影像底图切换，经纬度坐标实时显示
- **要素采集** — 支持点、线、面绘制，附带属性信息录入
- **要素编辑** — 选中要素后可修改几何（拖拽）和属性，支持删除
- **附件管理** — 要素支持上传图片/文档/PDF等附件，编辑时可回显和删除
- **行政区划** — 4 级区划级联选择（省/市/区县/乡镇），选择后地图自动定位
- **门牌搜索** — 基于 ST_DOORPLATE 表的千万级数据搜索，搜索结果在地图上渲染展示
- **用户认证** — 注册/登录，JWT Token 鉴权