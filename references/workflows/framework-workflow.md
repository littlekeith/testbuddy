# 测试框架生成工作流

**触发关键词**：`生成测试框架`、`生成框架`、`创建测试框架`

**工作流简介**：基于需求分析，生成完整的 FEATURE → SCENE → TEST_POINT 三层测试框架节点树。

## 执行流程

**步骤 1：确认需求与会话**

- 查看会话需求（`get_requirement.py`）与 `.testbuddy/md/analysis.md`；缺则先补需求分析与录入。

**步骤 2：生成框架**

- 读取 `references/generators/framework-generator.md`，按规则输出节点树 JSON：
  - FEATURE（一级）→ SCENE（二级）→ TEST_POINT（挂 SCENE/FEATURE 下）
  - 每个节点 `uid/name/description/kind/parent_uid/instance`
- 写入临时文件（如 `.testbuddy/designs/framework_draft.json`）。

**步骤 3：查重与精修**

- `ms_search.py modules` 对照既有模块树，消除重复 FEATURE/SCENE 命名。

**步骤 4：落库**

- 若与用例一起落库：交给 `design-workflow` 的 `ms_design --dry-run → 确认 → 执行`。
- 若只生成框架：`ms_design.py --design <framework_draft.json> --name <需求名> --dry-run` 预览模块树，确认后落库。

**步骤 5：收尾**

- `references/tools/open_design.md`：输出 MeterSphere 链接、根模块名。

## 注意

- 框架只包含模块树；用例生成见 `case-workflow`。两层模块映射保持 FEATURE→一级、SCENE→二级。
