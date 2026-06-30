# 乐不停（lebuting）— 产品需求文档（PRD）

| 项 | 内容 |
|---|---|
| 产品名 | 乐不停（lebuting） |
| 版本 | v1.0 |
| 日期 | 2026-06-30 |
| 状态 | 已实现模块可维护；记账模块为规划/原型阶段 |
| 技术栈 | uni-app x（App/H5）+ FastAPI + SQLite + Hermes Agent |
| 业务 API | `backend/`，端口 **8181**，前缀 `/api/{slug}` |
| Hermes | 端口 **8642**，OpenAI 兼容 `/v1/chat/completions` |

---

## 1. 背景与目标

### 1.1 背景

「乐不停」是个人生活助手 App，把日常高频但分散的需求收进一个入口：和 AI 对话、决定吃什么/做什么、记录消费。各模块独立 slug，共享同一套 App 壳与部署习惯，但数据与 API 隔离。

### 1.2 产品定位

- **App 首页**：多功能宫格入口，用户选一个模块进入。
- **已实现**：渣渣乐 Agent 对话、吃什么菜、做什么菜。
- **规划中**：记账（参考第三方 App 截图与自有 CSV 分析页，功能细节待迭代）。

### 1.3 产品目标

| 目标 | 说明 |
|------|------|
| 低摩擦决策 | 转盘 30 秒内完成「转 → 确认」闭环 |
| 可回顾 | 吃什么/做什么有记录与月度统计 |
| 可对话 | App 直连 Hermes，与微信 Bot 共用同一 Agent |
| 可记账（规划） | 日常记一笔 + 月度概览 + 图表分析 |

### 1.4 成功标准

- 首页可进入全部已上线模块，H5 与真机网络可达。
- 吃什么/做什么：候选 ≥ 2 且未全部排除时可转盘；记一笔后统计 +1。
- Agent：健康检查通过后可持续多轮对话。
- 记账（后续）：PRD + HTML 原型对齐参考 App；实现阶段另定 MVP 范围。

---

## 2. 用户与场景

**用户**：个人使用，单设备或多设备同网访问同一后端（局域网 IP，禁真机直连 `127.0.0.1`）。

| 场景 | 模块 | 行为 | 期望 |
|------|------|------|------|
| 打开 App | 首页 | 选模块 | 一眼看清四个入口 |
| 想找人聊 | Agent | 发消息 | 流式/非流式回复，连接状态可见 |
| 午饭纠结 | 吃什么菜 | 转盘 → 记一笔 | 几秒出结果，本月次数可见 |
| 在家做饭 | 做什么菜 | 同上 | 与外出就餐逻辑一致，文案区分「做/吃」 |
| 维护清单 | 吃什么/做什么 | 增删改候选、分类 | 名称唯一，分类可管理 |
| 今天不想某选项 | 吃什么/做什么 | 排除/恢复 | 仅从转盘池移除，不删候选 |
| 月底回顾 | 吃什么/做什么 | 看统计页 | 本月榜单 + 总次数 |
| 记消费（规划） | 记账 | 选分类输金额 | 首页看本月支出与预算 |
| 看钱花哪了（规划） | 记账 | 图表分析 | 趋势 + 分类占比 |
| 导入历史账单（规划） | 记账 | CSV 导入 | 兼容参考 App 导出格式 |

---

## 3. 系统架构

### 3.1 三条数据路径

```
┌─────────────┐     POST /v1/chat/completions      ┌──────────────┐
│  App 对话页  │ ─────────────────────────────────►│ Hermes :8642 │
└─────────────┘     Bearer VITE_HERMES_API_KEY     └──────────────┘

┌─────────────┐     GET/POST /api/{slug}/...       ┌──────────────┐
│  App 业务页  │ ─────────────────────────────────►│ FastAPI :8181│
└─────────────┘                                    │ SQLite       │
                                                   └──────────────┘

微信 Bot ──► Hermes Gateway ──► 同上 Agent + Skills
```

### 3.2 网络与代理

| 服务 | H5 代理 | App 直连 |
|------|---------|----------|
| Hermes | `/hermes-api` → `:8642` | `http://{VITE_HERMES_HOST}:8642` |
| 业务 API | `/biz-api` → `:8181` | `http://{VITE_BIZ_API_HOST}:8181` |

环境变量见 `.env.example`；改 `.env` 后 H5 重启，App 重编，Android 执行 `node scripts/sync-android-config.mjs`。

### 3.3 模块约定

| 模块 | slug | API 前缀 | 数据表前缀 | 前端 | 客户端封装 | 主色 | 状态 |
|------|------|----------|------------|------|------------|------|------|
| 渣渣乐 Agent | `chat` | Hermes 直连 | — | `pages/chat/` | `utils/hermes.uts` | `#007aff` | ✅ 已实现 |
| 吃什么菜 | `eat-dish` | `/api/eat-dish` | `eat_dish_*` | `pages/eat-dish/` | `utils/eat-dish.uts` | `#ff6b35` | ✅ 已实现 |
| 做什么菜 | `cook-dish` | `/api/cook-dish` | `cook_dish_*` | `pages/cook-dish/` | `utils/cook-dish.uts` | `#34a853` | ✅ 已实现 |
| 记账 | `bill` | `/api/bill`（规划） | `bill_*`（规划） | `pages/bill/`（规划） | `utils/bill.uts`（规划） | `#e85d5d`（建议） | 📋 PRD+原型 |

**隔离原则**：各业务模块独立 router、表、utils；页面不硬编码 URL；统一响应 `{ code, message, data }`，HTTP 始终 200。

### 3.4 错误码（业务 API 共用）

| code | 含义 |
|------|------|
| `0` | 成功 |
| `404` | 资源不存在 |
| `1001` | 转盘池不足（< 2 条可选项） |
| `1002` | 名称重复 |
| `1003` | 参数校验失败 |
| `1004` | 分类仍被候选引用，无法删除 |
| `1005` | 转盘指定分类不存在或无候选 |

---

## 4. 信息架构

```
App 首页 pages/index
├── [渣渣乐 Agent]     pages/chat/chat
├── [吃什么菜]         pages/eat-dish/   （subpackage）
├── [做什么菜]         pages/cook-dish/  （subpackage）
└── [记账]             pages/bill/       （规划，subpackage）

吃什么菜 / 做什么菜（结构对称，文案不同）
├── 转盘 wheel（默认进入）
├── 候选 foods
├── 排除 excluded（今天不吃 / 今天不做）
├── 记录 records
├── 统计 stats
├── 候选编辑 food-edit
├── 分类 types
└── 分类编辑 type-edit

记账（规划，参考截图 my/bill/*.jpg）
├── 首页 home（本月概览、预算、账单列表）
├── 记一笔 add（分类网格 + 数字键盘）
├── 图表分析 charts（趋势 + 分类概况）
├── 分类管理 categories
└── （可选）导入 import、设置 settings
```

**术语（吃什么/做什么共用）**

| 说法 | 含义 |
|------|------|
| **候选** | 转盘可选项（店名/菜名 + 分类） |
| **排除** | 暂不参与转盘，候选仍保留 |
| **恢复** | 重新加入转盘池 |
| **记一笔** | 写入一条吃过/做过记录 |

---

## 5. 全局 UI 设计方向

> 后续统一样式页见 `my/html/`（步骤 2）；改页面时遵循 `.agents/skills/frontend-design/SKILL.md` 与 `uni-app-x` 样式约束。

| 项 | 规范 |
|----|------|
| 布局 | 浅灰底 `#f5f5f5` + 白卡片圆角，模块内 Tab 底栏 |
| 层级 | 标题 / 主数据 / 辅助说明 / 操作按钮 |
| 模块色 | 各模块主色见 §3.3，禁止随意混用 |
| 首页 | 模块卡片 + 左侧色条 + 简述 + 箭头 |
| 待优化 | 当前 UI 较朴素，步骤 2 做统一 HTML 原型后再落地 App |

---

## 6. 模块一：渣渣乐 Agent 对话

### 6.1 概述

App 内嵌聊天页，直连笔记本 Hermes 服务，与微信 Bot 共用 Agent 与 Skills。

### 6.2 功能需求

| ID | 功能 | 说明 | 状态 |
|----|------|------|------|
| CH-01 | 连接状态 | 进入页调用 `GET /health`，显示版本或离线 | ✅ |
| CH-02 | 多轮对话 | `POST /v1/chat/completions`，保留 history | ✅ |
| CH-03 | 发送消息 | 输入框 + 发送按钮，Enter 发送 | ✅ |
| CH-04 | 加载态 | 等待回复时显示「思考中...」 | ✅ |
| CH-05 | 重试连接 | 顶部「重试」按钮 | ✅ |
| CH-06 | 流式输出 | SSE 逐字显示 | ⬜ 未做 |

### 6.3 页面

| 路径 | 标题 | 说明 |
|------|------|------|
| `pages/chat/chat` | 渣渣乐agent | 消息列表 + 输入栏 + 连接状态 |

### 6.4 接口（Hermes）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查，返回 `version` |
| POST | `/v1/chat/completions` | 对话，model=`hermes-agent`，Bearer 鉴权 |

### 6.5 验收

1. `.env` 配置正确时，状态栏显示「渣渣乐agent v{x}」。
2. 连续多轮问答上下文连贯。
3. 断网时禁用输入并提示，重试可恢复。

---

## 7. 模块二：吃什么菜（eat-dish）

### 7.1 概述

外出就餐决策：大转盘随机 + 候选管理 + 吃过记录与统计。

### 7.2 功能需求

| ID | 功能 | 说明 | 状态 |
|----|------|------|------|
| ED-01 | 随机转盘 | 后端 `POST /wheel/spin` 返回结果，池 ≥ 2 | ✅ |
| ED-02 | 转盘池预览 | 展示当前可参与随机的候选 | ✅ |
| ED-03 | 记一笔 | 转中后或手动写入 `eat_dish_records` | ✅ |
| ED-04 | 今天不吃 | `PATCH /foods/{id}/exclude`，仅移出转盘池 | ✅ |
| ED-05 | 候选 CRUD | 名称唯一，绑定分类 | ✅ |
| ED-06 | 分类管理 | 增删改，被引用时不可删 | ✅ |
| ED-07 | 吃过记录 | 时间线列表，可删 | ✅ |
| ED-08 | 本月统计 | 榜单：本月次数、总计、最近日期 | ✅ |
| ED-09 | 分类筛选转盘 | spin 可选 `type` 参数 | ✅ |
| ED-10 | 下拉刷新 | 各列表页 | ✅ |

### 7.3 页面

| 路径 | 标题 | Tab |
|------|------|-----|
| `pages/eat-dish/wheel` | 吃什么菜 | 转盘 |
| `pages/eat-dish/foods` | 吃饭候选 | 候选 |
| `pages/eat-dish/excluded` | 今天不吃 | 今天不吃 |
| `pages/eat-dish/records` | 吃过记录 | 记录 |
| `pages/eat-dish/stats` | 吃饭统计 | 统计 |
| `pages/eat-dish/food-edit` | 编辑吃饭候选 | — |
| `pages/eat-dish/types` | 吃饭分类 | — |
| `pages/eat-dish/type-edit` | 编辑吃饭分类 | — |

底栏组件：`components/eat-dish-tab-bar/eat-dish-tab-bar.uvue`

### 7.4 数据模型

```sql
CREATE TABLE eat_dish_types (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT NOT NULL UNIQUE,
  sort_order  INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL
);

CREATE TABLE eat_dish_foods (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT NOT NULL UNIQUE,
  type        TEXT NOT NULL,
  type_id     INTEGER REFERENCES eat_dish_types(id),
  excluded    INTEGER NOT NULL DEFAULT 0,
  note        TEXT NOT NULL DEFAULT '',
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);

CREATE TABLE eat_dish_records (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  food_id     INTEGER NOT NULL,
  food_name   TEXT NOT NULL,
  food_type   TEXT NOT NULL,
  eaten_at    TEXT NOT NULL,
  meal        TEXT,           -- lunch / dinner / snack 等，可自动推断
  source      TEXT NOT NULL DEFAULT 'wheel',
  note        TEXT NOT NULL DEFAULT '',
  FOREIGN KEY (food_id) REFERENCES eat_dish_foods(id)
);
```

**默认分类**：火锅、烧烤、面食、米饭、快餐、轻食、日料、韩餐、西餐、其他。

### 7.5 API

**前缀**：`/api/eat-dish`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/types` | 分类列表 |
| POST | `/types` | 新增分类 |
| PUT | `/types/{id}` | 更新分类（联动候选/记录中的 type 文本） |
| DELETE | `/types/{id}` | 删除分类 |
| GET | `/foods` | 候选列表，可选 `type`、`excluded` |
| POST | `/foods` | 新增候选 |
| GET | `/foods/{id}` | 详情 |
| PUT | `/foods/{id}` | 更新 |
| DELETE | `/foods/{id}` | 删除 |
| PATCH | `/foods/{id}/exclude` | `{ excluded: true/false }` |
| GET | `/wheel/pool` | 转盘池 |
| POST | `/wheel/spin` | 抽奖，body 可选 `{ type }` |
| GET | `/records` | 记录列表，可选 `month`、`food_id` |
| POST | `/records` | 新增记录 |
| DELETE | `/records/{id}` | 删除记录 |
| GET | `/stats/summary` | 本月摘要 + 榜单 |
| GET | `/stats/food/{id}` | 单候选统计 |

### 7.6 验收

1. 首页进入转盘，「成都你六姐 · 火锅」类一行展示。
2. 「今天不吃」后不进转盘，恢复后重新参与。
3. 「记一笔」后本月统计 +1。
4. H5 / 真机可访问全部接口。

---

## 8. 模块三：做什么菜（cook-dish）

### 8.1 概述

在家下厨决策，与「吃什么菜」同构：转盘 + 候选 + 排除 + 记录 + 统计。差异仅在文案、时间字段名、默认种子数据与主题色。

### 8.2 与 eat-dish 的差异对照

| 项 | eat-dish | cook-dish |
|----|----------|-----------|
| slug | `eat-dish` | `cook-dish` |
| 记录时间字段 | `eaten_at` | `cooked_at` |
| 排除文案 | 今天不吃 | 今天不做 |
| 记一笔文案 | 吃了 | 做了 |
| 默认分类 | 火锅、烧烤、面食… | 家常菜、快手菜、硬菜、汤羹… |
| 主色 | `#ff6b35` | `#34a853` |
| API 前缀 | `/api/eat-dish` | `/api/cook-dish` |
| 表前缀 | `eat_dish_*` | `cook_dish_*` |

### 8.3 功能需求

功能 ID 与 eat-dish 一一对应（ED-01～ED-10 → CD-01～CD-10），行为相同，替换上述差异项即可。**状态：全部 ✅ 已实现。**

### 8.4 页面

| 路径 | 标题 |
|------|------|
| `pages/cook-dish/wheel` | 做什么菜 |
| `pages/cook-dish/foods` | 做菜候选 |
| `pages/cook-dish/excluded` | 今天不做 |
| `pages/cook-dish/records` | 做过记录 |
| `pages/cook-dish/stats` | 做菜统计 |
| `pages/cook-dish/food-edit` | 编辑做菜候选 |
| `pages/cook-dish/types` | 做菜分类 |
| `pages/cook-dish/type-edit` | 编辑做菜分类 |

底栏：`components/cook-dish-tab-bar/cook-dish-tab-bar.uvue`

### 8.5 数据模型

与 §7.4 同构，表名改为 `cook_dish_types`、`cook_dish_foods`、`cook_dish_records`，记录表时间列为 `cooked_at`。

### 8.6 API

**前缀**：`/api/cook-dish`，路径与 §7.5 对称（`/records` 返回 `cooked_at`）。

### 8.7 验收

同 §7.6，替换为做菜语境。

---

## 9. 模块四：记账（bill）— 规划

> **当前阶段**：仅 PRD + HTML 原型（步骤 2 在 `my/html/` 落地）；后端与 App 实现暂缓，MVP 范围待产品确认。

### 9.1 概述

个人记账：记一笔、看首页概览、图表分析、分类管理。参考 App 截图见 `my/bill/`，历史数据样例见 `my/bill/20260111160124.csv`，桌面分析原型见 `my/bill/bill.html`。

### 9.2 参考 UI（截图映射）

| 截图 | 页面 | 核心元素 |
|------|------|----------|
| `首页.jpg` | 记账首页 | 本月支出/收入/结余；预算进度条；今日与近三日账单；底部「记一笔」FAB |
| `新增账单.jpg` | 记一笔 | Tab：支出/收入/转账/借贷；分类图标网格；备注；金额；账户/账本/时间；自定义数字键盘 |
| `图表分析1.jpg` | 图表分析 | 月度摘要卡；趋势图（支出/收入/结余切换，按天）；分类概况环形图 |
| `图表分析2.jpg` | 图表分析（下滚） | 分类列表（图标、占比、金额、可进详情） |
| `分类管理.jpg` | 分类管理 | 支出/收入 Tab；分类列表（图标、编辑、排序）；添加分类 |

### 9.3 外部数据格式（CSV 导入参考）

来源：`my/bill/20260111160124.csv`

| 列 | 说明 | 示例 |
|----|------|------|
| TID | 外部流水号 | `TID.1768112630422228148` |
| 金额 | 正数 | `109.47` |
| 分类 | 支出分类名 | 餐饮、交通、医疗… |
| 类型 | 交易类型 | 支出 / 收入 |
| 账户 | 付款账户（可为空） | — |
| 账本 | 账本名（可为空） | — |
| 日期 | `YYYY-MM-DD HH:mm:ss` | `2026-01-11 14:23:42` |
| 备注 | 自由文本 | 盒马超市 |

**样例中出现的支出分类**：餐饮、日用品、娱乐、交通、其他、医疗、水电煤、人情往来、住房。

### 9.4 功能需求（分级）

#### P0 — MVP（建议首版实现）

| ID | 功能 | 说明 |
|----|------|------|
| BL-01 | 记一笔（支出） | 选分类、金额、备注、时间，保存 |
| BL-02 | 账单列表 | 按日分组，首页展示本月汇总 + 近记录 |
| BL-03 | 删除/编辑账单 | 单条 CRUD |
| BL-04 | 分类管理（支出） | 默认分类 + 增删改排序 |
| BL-05 | 图表：分类占比 | 环形图 + 列表（当月） |
| BL-06 | 图表：支出趋势 | 按天折线（当月） |
| BL-07 | CSV 导入 | 兼容 §9.3 格式，TID 去重 |

#### P1 — 增强（参考截图完整体验）

| ID | 功能 | 说明 |
|----|------|------|
| BL-10 | 收入记账 | 记一笔 Tab 切换 |
| BL-11 | 本月预算 | 设置预算、进度条、剩余、日均 |
| BL-12 | 趋势切换 | 支出/收入/结余；粒度：按天/月 |
| BL-13 | 分类详情 | 从分类行点进该分类账单 |
| BL-14 | 搜索/筛选 | 首页搜索、图表页筛选 |
| BL-15 | 账户 / 账本 | 多账本、多账户（可先单账本） |

#### P2 — 暂缓

| ID | 功能 | 说明 |
|----|------|------|
| BL-20 | 转账 | 账户间划转 |
| BL-21 | 借贷 | 借入/借出 |
| BL-22 | 导出 | 导出 CSV |
| BL-23 | 桌面级分析 | `bill.html` 全年多图联动、排行分页（可作 Web 附属页） |

### 9.5 页面（规划）

| 路径 | 标题 | 说明 |
|------|------|------|
| `pages/bill/home` | 记账 | 首页概览 + 列表 |
| `pages/bill/add` | 记一笔 | 半屏/全屏表单 + 键盘 |
| `pages/bill/charts` | 图表分析 | 趋势 + 分类 |
| `pages/bill/categories` | 分类管理 | 支出/收入分类 |
| `pages/bill/category-edit` | 编辑分类 | 名称、图标 |
| `pages/bill/import` | 导入数据 | CSV 选择（P0 可放设置或首页入口） |

### 9.6 数据模型（草案）

```sql
-- 账本（首版可仅一条「默认账本」）
CREATE TABLE bill_ledgers (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT NOT NULL UNIQUE,
  is_default  INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL
);

-- 分类
CREATE TABLE bill_categories (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  ledger_id   INTEGER NOT NULL DEFAULT 1,
  name        TEXT NOT NULL,
  kind        TEXT NOT NULL,        -- expense | income
  icon        TEXT NOT NULL DEFAULT '',
  sort_order  INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL,
  UNIQUE(ledger_id, kind, name)
);

-- 账户（P1）
CREATE TABLE bill_accounts (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT NOT NULL UNIQUE,
  created_at  TEXT NOT NULL
);

-- 账单
CREATE TABLE bill_transactions (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  external_tid  TEXT UNIQUE,        -- CSV TID，导入去重
  ledger_id     INTEGER NOT NULL DEFAULT 1,
  category_id   INTEGER NOT NULL,
  category_name TEXT NOT NULL,      -- 冗余，便于历史展示
  kind          TEXT NOT NULL,      -- expense | income | transfer | loan
  amount        REAL NOT NULL,      -- 正数，展示时支出带符号
  account_id    INTEGER,
  account_name  TEXT NOT NULL DEFAULT '',
  occurred_at   TEXT NOT NULL,
  note          TEXT NOT NULL DEFAULT '',
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL,
  FOREIGN KEY (category_id) REFERENCES bill_categories(id)
);

-- 预算（P1）
CREATE TABLE bill_budgets (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  ledger_id   INTEGER NOT NULL,
  month       TEXT NOT NULL,        -- YYYY-MM
  amount      REAL NOT NULL,
  UNIQUE(ledger_id, month)
);
```

**默认支出分类（与 CSV/参考 App 对齐）**：餐饮、日用品、娱乐、交通、住房、水电煤、医疗、人情往来、其他。

### 9.7 API（草案）

**前缀**：`/api/bill`（未实现）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/summary` | 本月支出/收入/结余/笔数 |
| GET | `/transactions` | 列表，`month`、`day`、`category_id` |
| POST | `/transactions` | 记一笔 |
| PUT | `/transactions/{id}` | 编辑 |
| DELETE | `/transactions/{id}` | 删除 |
| GET | `/categories` | 分类，`kind=expense|income` |
| POST/PUT/DELETE | `/categories/...` | 分类 CRUD |
| GET | `/stats/trend` | 趋势，`kind`、`granularity=day|month` |
| GET | `/stats/category` | 分类占比 |
| POST | `/import/csv` | CSV 导入 |
| GET/PUT | `/budgets/{month}` | 预算（P1） |

### 9.8 与 bill.html 的关系

`my/bill/bill.html` 为**桌面宽屏分析工具**（Chart.js），能力包括：

- 本地选择 CSV 解析
- 按年、按月区间筛选
- 支出趋势（日/月/年）
- 各分类柱状图、占比饼图、年度多线对比
- 单笔支出排行（备注模糊搜、分页）

App 内图表分析（P0/P1）取其中**移动端必要子集**；复杂联动分析可保留为 H5 附属页或后续 Web 模块，不阻塞 App MVP。

### 9.9 验收（实现阶段再测）

1. 记一笔后首页本月支出更新。
2. 导入 CSV 后数据与 `bill.html` 同文件统计一致（抽样核对）。
3. 图表页分类占比与参考截图结构一致。
4. 分类管理可增删改，默认分类齐全。

---

## 10. App 对接约定

| 项 | 说明 |
|----|------|
| 页面 → 网络 | 只调 `utils/*.uts`，禁止硬编码 host |
| 业务响应 | `code === 0` 取 `data`；否则 `message` toast |
| 分包 | `eat-dish`、`cook-dish` 已在 `pages.json`；`bill` 待加 |
| 首页入口 | `pages/index/index.uvue` 增加记账卡片（实现后） |
| UI 改版 | 步骤 2 统一 HTML 原型 → 步骤 3/4 按模块落地 |

---

## 11. 开发路线图（与本次重构对齐）

| 步骤 | 内容 | 状态 |
|------|------|------|
| 1 | 整理完善本 PRD | ✅ 本文档 |
| 2 | 统一 UI 前端 HTML 原型 `my/html/` | 待做 |
| 3 | 实现除记账外的前端（含 UI 改版） | 待做 |
| 4 | 实现除记账外的后端（Hermes 已有，业务 API 已有） | 待做 |
| 5 | 记账：先 PRD + HTML 原型，功能实现不急 | 进行中 |

---

## 12. 新模块 Checklist（记账上线时）

1. 定 slug `bill` → `backend/app/bill/` + `bill_*` 表
2. `utils/bill.uts` 封装 API
3. `pages/bill/` 页面 + `pages.json` subPackage
4. `pages/index` 添加入口
5. PRD §9 MVP 范围评审 → 实现 → 验收 §9.9

---

## 附录 A：已实现文件索引

| 类型 | 路径 |
|------|------|
| 首页 | `pages/index/index.uvue` |
| Agent | `pages/chat/chat.uvue`、`utils/hermes.uts` |
| 吃什么菜 | `pages/eat-dish/`、`utils/eat-dish.uts`、`backend/app/eat_dish/` |
| 做什么菜 | `pages/cook-dish/`、`utils/cook-dish.uts`、`backend/app/cook_dish/` |
| 后端入口 | `backend/main.py` |
| 数据库 | `backend/data/lebuting.db` |
| 记账参考 | `my/bill/*.jpg`、`my/bill/20260111160124.csv`、`my/bill/bill.html` |
| 设计技能 | `.agents/skills/frontend-design/SKILL.md` |

## 附录 B：文档历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.3 | 2026-06-28 | 仅「吃什么菜」模块 PRD |
| v1.0 | 2026-06-30 | 扩展为 lebuting 全 App PRD，含四模块与记账规划 |
