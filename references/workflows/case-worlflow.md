# 用例生成工作流

**触发关键词**：`生成测试用例`、`生成用例`、`根据测试点生成用例`、`根据需求生成用例`

**工作流简介**：基于需求分析与参考节点（FEATURE/SCENE/TEST_POINT），生成全面的测试用例（正常、异常、边界、安全、性能等），并落库到 MeterSphere。

## 执行流程

**步骤 1：确认需求与会话**

- 用 `references/tools/get_requirement.md` 查看会话需求（`get_requirement.py` 不传参数）。
- 若无需求，请用户粘贴文本或给文件路径，再录入。
- 需求分析文档：读 `.testbuddy/md/analysis.md`；若不存在，先执行需求分析（见 `references/generators/issue-analyst.md`）。

**步骤 2：确认参考节点**

- 参考节点来自用户指定的设计范围，或通过 `references/tools/ms_search.md` 查询既有模块/用例。
- 节点信息包含：uid、name、kind（FEATURE/SCENE/TEST_POINT）、parent_uid。
- 如信息不完整，提示用户补充并终止流程。

**步骤 3：生成测试用例**

- 读取 `references/generators/case-generator.md`，按其规则执行用例生成。
- 输入：`ref_nodes`（参考节点数组，优先最细粒度 TEST_POINT/SCENE）+ `issue_analysis`（需求分析文档内容）。
- 输出要求：标准 JSON 数组，每个节点含 `uid/name/description/kind=CASE/parent_uid/instance{preconditions,priority,steps[{action,expected}]}`。**禁止 YAML、禁止注释**；把 JSON 写入临时文件（如 `.testbuddy/designs/cases_draft.json`）。

**步骤 4：转换与落库（dry-run → 确认 → 执行）**

- 先用 `ms_design.py --design <cases_draft.json> --dry-run` 预览要创建的模块/用例。
- 展示计划 → 用户确认 → 去掉 `--dry-run` 正式落库。
- 检查输出：`status: success`、每个用例的 `case_id`、`mapping_file`。

**步骤 5：收尾**

- 读取 `references/tools/open_design.md`，输出 MeterSphere 链接与根模块名，让用户点击打开。

## 注意

- 用例名称若带测试点前缀由 `ms_design` 自动加 `{测试点}::`，生成器不要手动加。
- 删除/修改类操作遵循 SKILL.md 全局约束（先 dry-run、不在真实业务树直接验证）。
