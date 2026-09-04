# SPEC（测试点规格）生成工作流

**触发关键词**：`生成 spec`、`开启 spec 工作流`、`spec`

**工作流简介**：对需求中的核心功能点做规格化拆解（SPEC），输出结构化测试点规格，供后续用例生成引用。

## 执行流程

**步骤 1：确认需求**

- 查看会话需求与 `.testbuddy/md/analysis.md`；缺则先补。

**步骤 2：生成 SPEC/测试点**

- 读取 `references/generators/tpoint-generator.md` 与 `references/generators/spec/spec-tpoint-generator.md`，按规则把需求的功能点拆解为 TEST_POINT 节点（规格化描述：输入、操作、期望）。
- 输出 TEST_POINT 节点 JSON，写入 `.testbuddy/designs/spec_draft.json`。

**步骤 3：落到设计树**

- 将 TEST_POINT 节点并入设计 JSON（挂在对应 SCENE 下），或直接由 `ms_design.py` 落库（TEST_POINT 表现为用例名前缀）。

**步骤 4：收尾**

- 输出规格清单与（如已落库）MeterSphere 链接（`references/tools/open_design.md`）。
