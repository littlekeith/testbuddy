# 测试设计生成工作流

**触发关键词**：`生成测试设计`、`帮我做测试设计`、`测试设计`

**工作流简介**：基于需求分析，分两阶段完成完整测试设计——先生成测试框架（FEATURE/SCENE/TEST_POINT），再基于框架生成测试用例，最后整体落库 MeterSphere。

## 执行流程

### 第一阶段：需求与框架

**步骤 1：获取需求**

- 用户粘贴文本或给文件路径 → `get_requirement.py --text "..."` 或 `--file <路径>`（`references/tools/get_requirement.md`）。

**步骤 2：需求分析**

- 读取 `references/generators/issue-analyst.md`，按框架分析，写入 `.testbuddy/md/analysis.md`。
- 若该需求已分析过（文件存在且内容匹配），直接复用。

**步骤 3：生成测试框架**

- 读取 `references/generators/framework-generator.md`，生成 FEATURE/SCENE/TEST_POINT 节点 JSON 数组。
- 输出写入临时文件（如 `.testbuddy/designs/framework_draft.json`）。

**步骤 4：查重（可选）**

- 用 `ms_search.py modules`（`references/tools/ms_search.md`）检查目标父模块下是否存在同名模块，合并/去重节点。

### 第二阶段：用例与落库

**步骤 5：生成测试用例**

- 读取 `references/generators/case-generator.md`，以上一步框架节点（优先 TEST_POINT）为 ref_nodes 生成 CASE 节点，追加到设计 JSON（或独立文件）。

**步骤 6：落库（dry-run → 确认 → 执行）**

- `ms_design.py --design <draft.json> --name <需求名> --dry-run` 预览。
- 展示计划 → 用户确认 → 正式执行。
- 检查 `case_id` 与 `design_mapping.json`。

**步骤 7：收尾**

- `references/tools/open_design.md`：输出 MeterSphere 链接、根模块名、mapping 路径。

## 注意

- 一个需求一个根模块 `{需求名}_{yyyyMMdd}`；重复设计同一需求时 find-or-create 复用模块，不重复建树。
- 落库前必须 dry-run 并让用户确认。
