# ms_design —— 设计 JSON 落库 MeterSphere

把生成器输出的设计 JSON（FEATURE/SCENE/TEST_POINT/CASE 节点树）落库为 MeterSphere 模块树与功能用例：

- FEATURE → 一级模块
- SCENE → 二级模块
- TEST_POINT → 用例名前缀 `{测试点}::`
- CASE → 功能用例（写入最近 SCENE/FEATURE/根模块），tags=[FEATURE 名, SCENE 名]

根模块命名 `{设计名}_{yyyyMMdd}`，默认挂在 `root` 下；`--parent` 可指定其他模块 uid。

## 用法

```shell
python <SKILL_DIR>/scripts/ms_design.py --design <design.json> [--name <设计名>] [--parent <模块uid|root>] [--project <pid>] [--dry-run]
```

- `--dry-run`：只输出将要创建的模块/用例清单，不产生任何写入。
- 成功输出：
  - `root_module_uid / root_module_name`
  - `cases[]`：每个用例 `case_id/case_name/module_uid/status`
  - `design_id` 与 `mapping_file`：`.testbuddy/designs/{design_id}/design_mapping.json`（node_uid↔module_uid、case_uid↔case_id/num/module_uid）
  - `url`：MeterSphere 基址（收尾输出链接用时）
- 设计 JSON 节点字段：`uid / name / kind(FEATURE|SCENE|TEST_POINT|CASE) / parent_uid / instance`。
  - CASE 的 `instance`：`{"preconditions": "...", "priority": "P0|P1|P2|P3", "steps": [{"action": "...", "expected": "..."}]}`
  - 支持 `.json`、或 markdown 内 ```json``` 代码块文件。

**流程要求**：先 `--dry-run` 展示计划 → 用户确认 → 正式执行；检查输出 `status: success`。
