# 测试点生成工作流

**触发关键词**：`生成测试点`、`创建测试点`、`根据模块生成测试点`

**工作流简介**：根据 FEATURE/SCENE 模块生成对应的 TEST_POINT 测试点节点，覆盖正常/异常/边界等维度。

## 执行流程

**步骤 1：确认模块范围**

- 用 `ms_search.py modules`（`references/tools/ms_search.md`）或用户指定，确定要生成测试点的模块（FEATURE/SCENE）列表。

**步骤 2：生成测试点**

- 读取 `references/generators/tpoint-generator.md`，按规则为每个模块生成 TEST_POINT 节点（`kind=TEST_POINT`，`parent_uid` 指向所属模块节点）。
- 写入临时文件（如 `.testbuddy/designs/tpoints_draft.json`）。

**步骤 3：并入设计树**

- 把 TEST_POINT 节点并入设计 JSON（作为 SCENE/FEATURE 子节点），等待整体落库；或先 `ms_design.py --dry-run` 预览。

**步骤 4：收尾**

- 输出测试点清单、（如已落库）MeterSphere 链接（`references/tools/open_design.md`）。
- 提示用户可继续触发 `用例生成` 工作流基于测试点生成 CASE。
