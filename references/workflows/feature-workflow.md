# 测试模块生成工作流

**触发关键词**：`生成测试模块`、`生成功能模块`、`识别测试模块`

**工作流简介**：基于需求分析结果，识别并生成 FEATURE（一级功能模块）节点。

## 执行流程

**步骤 1：确认需求**

- 查看会话需求与 `.testbuddy/md/analysis.md`（同其他工作流，缺则先补）。

**步骤 2：生成 FEATURE 节点**

- 读取 `references/generators/feature-generator.md`，按规则从需求分析中识别核心功能领域，输出 FEATURE 节点 JSON 数组（`kind=FEATURE`，`parent_uid` 可为空或需求根节点 uid）。
- 写入临时文件（如 `.testbuddy/designs/features_draft.json`）。

**步骤 3：查重**

- `ms_search.py modules` 检查根模块下是否已有同名一级模块；已存在则跳过或提示复用。

**步骤 4：落库（可选，配合整体设计）**

- 若用户要求立即落库：`ms_modules.py create --name <模块名> --parent <根模块uid|root> --dry-run` → 确认 → 正式创建。
- 若仅生成设计 JSON，则等待整体设计流程统一落库。

**步骤 5：收尾**

- 输出已生成模块清单、拟创建的模块层级，以及（如已落库）MeterSphere 链接（`references/tools/open_design.md`）。
