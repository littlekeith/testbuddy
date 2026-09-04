# ms_search —— 查询既有模块与用例

用于落库前查重、复用既有模块树，或回答"这个模块下有什么用例"。

## 用法

```shell
python <SKILL_DIR>/scripts/ms_search.py modules [--project <pid>] [--keyword <关键词>]
python <SKILL_DIR>/scripts/ms_search.py cases   [--project <pid>] [--module <模块uid>] [--keyword <关键词>] [--limit N]
python <SKILL_DIR>/scripts/ms_search.py get --id <case_id>
```

- `modules`：输出模块树（含 path 面包屑与 count 用例数）。
- `cases`：分页输出用例列表（name/num/id/moduleId）。
- `get --id`：单个用例详情（读-改-写场景使用）。

## 注意事项

- 只读接口，不产生写入。
- 生成 FEATURE/SCENE 前先用 `ms_search modules` 检查目标父模块下是否已存在同名模块，避免重复创建。
