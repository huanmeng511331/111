# HSE 隐患闭环 Demo 测试流程

本文档给出从环境准备到完整业务闭环的测试步骤。所有命令均在项目根目录的
`backend/`、`frontend/` 子目录中执行，默认前端 5173、后端 8000。

## 1. 环境准备

```bash
# 后端依赖
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# 前端依赖
cd ../frontend
npm install
```

预期：两条安装命令均成功退出；无需单独安装数据库服务。

## 2. 启动服务

终端 A（后端）：

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

首次启动自动创建 `backend/demo.db` 并写入 12 条演示隐患。若需重置数据，停止服务后删除
`backend/demo.db` 再启动。

终端 B（前端）：

```bash
cd frontend
npm run dev
```

访问检查：

| 地址 | 预期 |
| --- | --- |
| <http://localhost:5173> | 自动跳转 `/hazards`，台账页显示 12 条数据 |
| <http://localhost:8000/docs> | Swagger 文档可打开，包含 8 个隐患接口 |
| <http://localhost:8000/api/health> | 返回 `{"status":"ok"}` |

若 8000 或 5173 被占用，可改用其他端口，并通过 `VITE_API_TARGET` 指定后端地址：

```bash
uvicorn app.main:app --port 8010
VITE_API_TARGET=http://localhost:8010 npm run dev -- --port 15173
```

## 3. 自动化测试（后端接口）

```bash
cd backend
source .venv/bin/activate
pytest
```

预期输出：`8 passed`。测试在临时数据库中执行，不会污染 `demo.db`，覆盖：

| 用例 | 覆盖点 |
| --- | --- |
| `test_seed_data_available` | 演示数据初始化、编号格式 |
| `test_options_endpoint` | 类型/等级/状态枚举接口 |
| `test_full_business_flow` | 上报 → 分派 → 整改 → 验收关闭 全链路与流转记录 |
| `test_acceptance_reject_returns_to_rectifying` | 验收退回回到整改中 |
| `test_invalid_transition_conflict` | 跳过整改直接验收返回 409 |
| `test_missing_hazard_returns_404` | 不存在记录返回 404 |
| `test_validation_errors` | 必填、枚举、过期日期、非法附件 URL、分页参数返回 422 |
| `test_filters_search_and_sorting` | 状态/等级/类型筛选、关键字、排序、超期筛选 |

## 4. API 冒烟测试（针对运行中的服务）

先启动后端，再执行：

```bash
python3 scripts/smoke_test.py
# 非默认端口：
python3 scripts/smoke_test.py --base-url http://localhost:8010
```

预期输出 12 个步骤全部通过，最后一行：

```text
冒烟测试全部通过（本次新增一条演示隐患并已关闭，可作为演示数据保留）。
```

脚本依次校验：健康检查、列表、枚举、上报、分派、整改、验收关闭、重复验收 409、
详情、404、422、统计 7 天趋势。任一步失败均以非 0 退出并打印失败原因。

手工调用接口（可选）：

```bash
curl http://localhost:8000/api/hazards?status=整改中\&level=重大
curl -X POST http://localhost:8000/api/hazards \
  -H 'Content-Type: application/json' \
  -d '{"hazard_type":"消防安全","hazard_level":"一般","location":"1号厂房东侧消防通道","description":"消防通道堆放杂物，影响应急疏散。","reporter":"张伟","due_date":"2026-12-31"}'
```

## 5. 前端页面测试用例

启动前端后按顺序执行，重点检查加载态、空数据、校验提示与成功/失败提示。

| 编号 | 页面 | 操作步骤 | 预期结果 |
| --- | --- | --- | --- |
| TC-01 | 隐患台账 | 打开 `/hazards` | 表格加载后显示 12 条，含编号、类型、等级、位置、责任人、整改期限、状态、上报时间 |
| TC-02 | 隐患台账 | 依次筛选状态「整改中」、等级「重大」、类型「消防安全」，输入关键字后查询 | 列表按条件收敛；无匹配时显示「暂无符合条件的隐患」空状态 |
| TC-03 | 隐患台账 | 勾选「只看超期」 | 仅保留未关闭且整改期限早于今天的记录，期限列显示红色「超期」标签 |
| TC-04 | 隐患台账 | 点击「整改期限」「上报时间」表头排序，切换分页 | 数据顺序变化且分页生效，无报错 |
| TC-05 | 上报隐患 | 直接点击「提交上报」 | 各必填项出现中文校验提示，请求不发出 |
| TC-06 | 上报隐患 | 填写非法附件地址、选择过去日期 | 附件提示需 http(s) 开头；日期选择器禁止选择过去日期 |
| TC-07 | 上报隐患 | 填写合法信息提交 | 提示「隐患 HSE-… 上报成功」，跳转详情页，状态为「待审核」 |
| TC-08 | 隐患详情 | 待审核记录中填写责任人、期限并分派 | 状态变为「整改中」，责任人回显，流转记录新增「审核并分派」 |
| TC-09 | 隐患详情 | 填写整改措施与完成情况并提交 | 状态变为「待验收」，整改信息展示在「整改与验收」区块 |
| TC-10 | 隐患详情 | 验收通过；对另一条记录验收退回 | 通过后状态「已关闭」，退回后回到「整改中」并记录验收意见 |
| TC-11 | 隐患详情 | 直接访问 `/hazards/999999` | 显示错误提示「未找到 id 为 999999 的隐患记录」，页面不白屏 |
| TC-12 | 统计看板 | 打开 `/dashboard` 并点击「刷新数据」 | 统计卡片、状态/等级/类型分布、近 7 日趋势与台账数据一致；关闭一条隐患后数量增加 |
| TC-13 | 全局 | 关闭后端后刷新任意页面 | 页面提示「无法连接后端服务，请确认 http://localhost:8000 已启动」 |

## 6. 完整业务链路验收（对应需求 6.7）

1. 打开 `/hazards/new`，上报「消防通道堆放杂物」一般隐患（类型消防安全、位置 1 号厂房东侧消防通道、期限选未来日期）。
2. 详情页分派责任人「李强」，期限保持不变，确认状态变为「整改中」。
3. 以责任人身份提交整改措施与「已清理并设置禁放标识」，确认状态变为「待验收」。
4. 以安全管理员身份填写验收意见并「验收通过并关闭」，确认状态变为「已关闭」并出现在流转记录最后一条。
5. 打开 `/dashboard`，确认「已关闭」数量 +1，关闭率与近 7 日趋势同步更新。

## 7. 构建检查（可选）

```bash
cd frontend
npm run build
```

需要约 2GB 以上可用内存；内存不足时构建可能被系统 OOM 终止，此时以 `npm run dev` 的页面验证为准。

## 8. 验收标准

- `pytest` 全部通过，`scripts/smoke_test.py` 全部通过。
- 四个页面均无控制台报错，加载、空数据、成功/失败提示可见。
- 状态只能按「待审核 → 整改中 → 待验收 → 已关闭/退回整改」流转，非法流转被后端 409 拒绝。
- 统计数据与台账筛选结果一致，超期判断与整改期限一致。
- 所有演示数据均为虚构信息，不含真实人员或敏感数据。
