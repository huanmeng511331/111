# HSE 隐患上报与闭环管理演示系统

基于「上报 → 审核分派 → 整改 → 验收关闭」闭环的 HSE 隐患管理 Demo。
前端使用 Vue 3 + Vite + Element Plus，后端使用 FastAPI + SQLite，全部数据为本地模拟数据，
不接入生产系统，不含真实人员或敏感信息。

## 功能概览

- 隐患台账：按状态、等级、类型、关键字筛选，支持「只看超期」、分页与多字段排序。
- 隐患上报：表单校验（必填、长度、日期、附件 URL），提交后生成 `HSE-YYYYMMDD-NNNN` 编号。
- 隐患详情：展示上报信息、整改措施/结果、验收意见与状态流转记录，并按当前状态提供操作入口。
- 状态闭环：待审核 → 整改中 → 待验收 → 已关闭；验收可退回整改。
- 统计看板：状态/等级/类型分布、超期数量、关闭率、近 7 日上报趋势。
- 交互反馈：加载状态、空数据提示、成功/失败提示、按钮防重复提交。

## 技术栈

| 分层 | 选型 |
| --- | --- |
| 前端框架 | Vue 3（`<script setup>`） |
| 前端工程化 | Vite 6 |
| 组件库 | Element Plus |
| 请求 | axios（Vite 代理 `/api` → 后端） |
| 后端框架 | FastAPI |
| 数据库 | SQLite（`backend/demo.db`，首次启动自动创建并写入演示数据） |
| 接口风格 | JSON REST API，自动文档 `/docs` |

## 目录结构

```text
.
├── frontend/                  # Vue 3 + Vite + Element Plus
│   ├── src/
│   │   ├── api/               # axios 实例与隐患接口封装
│   │   ├── components/        # 状态/等级标签、分布图
│   │   ├── constants/         # 与后端一致的枚举与标签颜色
│   │   ├── router/            # 页面路由
│   │   ├── styles/            # 全局样式
│   │   ├── utils/             # 日期格式化
│   │   └── views/             # 台账、上报、详情、统计看板
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口、CORS、异常处理
│   │   ├── db.py              # SQLite 建表与演示数据
│   │   ├── errors.py          # 领域异常
│   │   ├── models/enums.py    # 类型/等级/状态与状态机
│   │   ├── routers/hazards.py # API 路由
│   │   ├── schemas/hazard.py  # 请求/响应模型与校验
│   │   └── services/          # 查询、状态流转、统计逻辑
│   ├── tests/test_hazards.py  # 闭环与校验测试
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── demo.db                # 首次启动后自动生成
└── README.md
```

## 环境要求

- Node.js ≥ 20（本机验证版本 20.18.1）与 npm ≥ 9
- Python ≥ 3.10（本机验证版本 3.12.3）
- 无需单独安装数据库服务，SQLite 由 Python 标准库提供

## 安装与启动

### 1. 启动后端（端口 8000）

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

首次启动会自动创建 `backend/demo.db` 并写入 12 条演示隐患（含待审核、整改中、待验收、已关闭与超期场景）。
如需重置演示数据，停止服务后删除 `backend/demo.db`，再次启动即可重新生成。

### 2. 启动前端（端口 5173）

```bash
cd frontend
npm install
npm run dev
```

### 3. 访问地址

- 前端页面：<http://localhost:5173>
- 后端接口文档：<http://localhost:8000/docs>
- 健康检查：<http://localhost:8000/api/health>

前端通过 Vite 代理把 `/api` 转发到 `http://localhost:8000`。如后端端口不同，请同步修改
`frontend/vite.config.js` 中的 `server.proxy['/api'].target`，或在启动前端时指定
`VITE_API_TARGET=http://localhost:8010 npm run dev`。

## 演示路径

1. 打开 <http://localhost:5173/hazards>，在台账中筛选「待审核」查看待处理隐患。
2. 点击「上报隐患」，上报一条「消防通道堆放杂物」的一般隐患（类型：消防安全，等级：一般，
   位置：1号厂房东侧消防通道，整改期限选择未来日期），提交后跳转详情页。
3. 在详情页「审核并分派责任人」中填写责任人（如：李强）与整改期限，点击「审核并分派」，
   状态变为「整改中」。
4. 在「提交整改措施与结果」中填写整改措施与「已清理并设置禁放标识」，提交后状态变为「待验收」。
5. 在「验收确认」中填写验收意见并点击「验收通过并关闭」，状态变为「已关闭」；
   也可点击「退回整改」验证退回路径。
6. 打开 <http://localhost:5173/dashboard> 查看状态、等级、类型分布与近 7 日趋势变化。

## API 一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/hazards` | 隐患列表，支持 `status`、`level`、`type`、`keyword`、`overdue`、`page`、`page_size`、`sort_by`、`sort_order` |
| POST | `/api/hazards` | 上报隐患 |
| GET | `/api/hazards/{id}` | 隐患详情（含状态流转记录） |
| PATCH | `/api/hazards/{id}/assign` | 审核并分派责任人 |
| PATCH | `/api/hazards/{id}/rectification` | 提交整改措施与整改结果 |
| PATCH | `/api/hazards/{id}/acceptance` | 验收并关闭或退回整改 |
| GET | `/api/hazards/statistics` | 统计数据 |
| GET | `/api/hazards/options` | 类型/等级/状态枚举 |

错误约定：参数校验失败返回 `422`；记录不存在返回 `404`；当前状态不允许该操作返回 `409`，
响应体为 `{"detail": "..."}`，前端直接提示。

## 状态规则

| 当前状态 | 可执行操作 | 下一状态 |
| --- | --- | --- |
| 待审核 | 审核并分派 | 整改中 |
| 整改中 | 提交整改 | 待验收 |
| 待验收 | 验收通过 | 已关闭 |
| 待验收 | 验收退回 | 整改中 |

状态流转在服务端校验，前端按钮仅作为入口，无法绕过状态机。

## 数据字段

`id`、`hazard_no`、`hazard_type`、`hazard_level`、`location`、`description`、`reporter`、
`owner`、`due_date`、`status`、`rectification_measure`、`rectification_result`、
`acceptance_comment`、`attachment_url`、`created_at`、`updated_at`；流转记录表
`hazard_logs` 保存动作、前后状态、操作人、意见与时间。

## 测试与构建

完整的自动化测试、API 冒烟测试与页面测试用例见 [TESTING.md](TESTING.md)。

```bash
# 后端测试（覆盖完整闭环、验收退回、非法流转、参数校验、筛选排序）
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest

# 后端启动后执行 API 冒烟测试（默认 http://localhost:8000）
python3 scripts/smoke_test.py

# 前端生产构建
cd frontend
npm run build
```

> 生产构建会打包 Element Plus 组件与样式，建议预留 2GB 以上可用内存；内存不足时
> `vite build` 可能被系统 OOM 终止，这不影响 `npm run dev` 的本机演示。

## AIWork 生成说明

- AIWork 依据需求文档生成了：前后端目录骨架、SQLite 表结构与演示数据、全部 8 个 API、
  状态机校验与统计逻辑、四个前端视图与公共组件、后端测试与本 README。
- 人工调整：需求选题与演示口径由需求方确认；如需调整字段、状态或界面文案，请在本节补充人工修改记录。
- 本 Demo 未实现登录认证、权限控制、文件上传与生产部署，相关能力不在本次范围内。

## 已知限制

- 附件仅保存图片 URL，不做文件上传与存储。
- SQLite 为单文件数据库，适合本机演示，不适合并发写入场景。
- 系统无鉴权，任何访问者都可执行分派、整改、验收操作，仅限本地演示使用。