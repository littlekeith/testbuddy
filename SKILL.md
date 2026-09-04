---
name: testbuddy-design
description: 基于需求文本或文件生成 MeterSphere 功能测试设计并落库。当用户要求根据 PRD/接口文档/功能描述/粘贴文本生成测试框架、功能模块、测试场景、测试点、测试用例，或把需求转换为 MeterSphere 用例树（FEATURE 一级模块、SCENE 二级模块、用例写入模块）时使用。不要用于纯查询类任务（查询 MeterSphere 数据请用 metersphere skill）。
---

# testbuddy-design：需求 → MeterSphere 测试设计

## 定位

把需求（粘贴文本或本地文件）转化为 MeterSphere 功能测试设计并落库：

| 设计元素  | MeterSphere 落库方式                              |
| --------- | ------------------------------------------------- |
| FEATURE   | 一级模块（挂在根模块下）                          |
| SCENE     | 二级模块（挂在所属 FEATURE 模块下）               |
| TEST_POINT| 不建模块，作为其下用例名称前缀 `{测试点}::`       |
| CASE      | 功能用例（写入最近 SCENE/FEATURE/根模块），tags=[FEATURE名, SCENE名] |

落库根模块命名：`{需求名}_{yyyyMMdd}`，与需求一一对应。

## 工具

所有脚本位于 `<SKILL_DIR>/scripts/`（`<SKILL_DIR>` 为本 skill 安装目录），执行时**禁止 `cd` 切换目录**，在工作区根目录直接用绝对/相对脚本路径调用：

| 脚本                 | 用途                                                     |
| -------------------- | -------------------------------------------------------- |
| `get_requirement.py` | 录入需求（--text / --file），读写会话 `.testbuddy/env/session.json` |
| `ms_design.py`       | 把设计 JSON 落库为模块树 + 用例，维护 design_mapping     |
| `ms_search.py`       | 查询既有模块/用例，供复用与去重                         |
| `ms_modules.py`      | 模块树 list/create/update/delete（delete 高风险）        |
| `ms_cases.py`        | 用例 list/get/convert/create/edit/delete（delete 高风险）|
| `ms_session.py`      | 会话读写（脚本内部使用，一般不需直接调用）              |

详细说明见 `references/tools/`；生成器与工作流见 `references/generators/`、`references/workflows/`。

## 配置

- 脚本自动读取 `<SKILL_DIR>/.env`（load_dotenv），外部环境变量优先覆盖。
- 必需：`METERSPHERE_BASE_URL`、`METERSPHERE_ACCESS_KEY`、`METERSPHERE_SECRET_KEY`。
- 可选：`METERSPHERE_PROJECT_ID`、`METERSPHERE_ORGANIZATION_ID`（缺省时用会话或交互指定）。
- `.env` 含真实密钥，属于本机敏感文件，不随 skill 分发。

## 全局约束（严格遵守）

1. **禁止 `cd`**：所有 Python 脚本从工作区根目录直接以完整路径执行，例如 `python <SKILL_DIR>/scripts/ms_design.py --design ...`。
2. **需求来源只能是用户粘贴文本或本地文件**：通过 `get_requirement.py` 录入；不要尝试联网抓取需求。
3. **变更类操作先 dry-run**：ms_design / ms_modules / ms_cases 的写操作必须先 `--dry-run` 预览，再与用户确认后正式执行。
4. **删除高风险**：模块删除 `GET /functional/case/module/delete/{id}` 会**级联删除子模块与用例且不进回收站**（详见根目录 INCIDENT-notes.md）。delete 必须显式 `--yes`，且只在确认目标属于本次设计创建的模块/用例时执行。
5. **不在真实业务树上直接验证**：新建模块一律落在本次设计的根模块 `{需求名}_{yyyyMMdd}` 之下。
6. 输出 JSON 状态以 `status: success/error` 为准；`status: error` 时原样展示 `msg` 并终止后续步骤。

## 执行流程（必须按序）

1. **获取需求**：用户粘贴文本或给出文件路径 → 运行 `get_requirement.py --text "..."` 或 `--file <路径>`，写入会话。
2. **需求分析**：读取 `references/generators/issue-analyst.md`，按其中框架分析需求，把结果写入 `.testbuddy/md/analysis.md`（会话如有历史分析可复用）。
3. **生成设计树 JSON**：按需读取 `references/generators/framework-generator.md` / `feature-generator.md` / `scene-generator.md` / `tpoint-generator.md` / `case-generator.md`，生成标准节点 JSON 数组（FEATURE → SCENE → CASE，TEST_POINT 挂在 SCENE/FEATURE 下），写入临时文件（如 `.testbuddy/designs/draft.json`）。
4. **落库**：运行 `ms_design.py --design <draft.json> [--name <需求名>] --dry-run` 预览计划；向用户确认后去掉 `--dry-run` 正式执行。检查输出：模块树、用例 case_id、mapping 文件。
5. **收尾**：读取 `references/tools/open_design.md`，输出 MeterSphere 页面链接让用户点击打开；汇报创建的模块数、用例数及 `design_mapping.json` 路径。

## 触发词

`生成测试设计`、`生成测试用例`、`生成测试框架`、`生成功能模块/场景/测试点`、`根据需求生成用例`、`把需求落到 MeterSphere`、`把 XX 需求写成用例并入库`。
