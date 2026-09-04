# ms_cases —— 功能用例操作（列表/详情/转换/创建/编辑/删除）

## 用法

```shell
python <SKILL_DIR>/scripts/ms_cases.py list    [--module <模块uid>] [--keyword <kw>] [--limit N] [--project <pid>]
python <SKILL_DIR>/scripts/ms_cases.py get     --id <case_id> [--project <pid>]
python <SKILL_DIR>/scripts/ms_cases.py convert --case <case.json> --module <模块uid> [--project <pid>]
python <SKILL_DIR>/scripts/ms_cases.py create  --case <case.json> --module <模块uid> [--project <pid>] [--dry-run]
python <SKILL_DIR>/scripts/ms_cases.py edit    --id <case_id> --case <case.json> [--project <pid>] [--dry-run]
python <SKILL_DIR>/scripts/ms_cases.py delete  --id <case_id> [--project <pid>] [--dry-run] [--yes]
```

## 用例 JSON（生成器输出 → convert 字段转换）

生成器输出 schema：

```json
{
  "uid": "case-xxxxx",
  "name": "用户正常登录",
  "kind": "CASE",
  "parent_uid": "tp_001",
  "instance": {
    "preconditions": "用户已注册",
    "priority": "P1",
    "steps": [ {"action": "打开页面", "expected": "显示登录框"} ]
  }
}
```

`convert`/`create` 自动转换为 MeterSphere payload：

- `prerequisite` ← `preconditions`
- `priority` ← 模板 `functional_priority` customField（P0-P3）
- `steps` ← `[{num, desc, result}]`，`caseEditType: "STEP"`
- name / tags / projectId / moduleId / templateId / versionId 由脚本补充

## 删除注意

用例删除会进回收站（软删），仍属高风险操作：必须先 `--dry-run`，正式删除必须 `--yes`，且只针对本次设计创建或用例确诊过期的用例。
