# ms_modules —— 功能用例模块树操作

## 用法

```shell
python <SKILL_DIR>/scripts/ms_modules.py list   [--project <pid>] [--flat]
python <SKILL_DIR>/scripts/ms_modules.py create --name <模块名> [--parent <模块uid|root>] [--project <pid>] [--dry-run]
python <SKILL_DIR>/scripts/ms_modules.py update --id <模块uid> --name <新名称> [--project <pid>] [--dry-run]
python <SKILL_DIR>/scripts/ms_modules.py delete --id <模块uid> [--project <pid>] [--dry-run] [--yes]
```

- `create` 幂等：目标父模块下已存在同名模块时直接返回已有模块，不重复创建。
- `update` 用于重命名模块（目标：模块 `module/update`）。

## ⚠️ 删除警告（强制阅读）

- 删除接口实为 `GET /functional/case/module/delete/{id}`，**收到 GET 即执行**，会**级联删除子模块与用例，且不进回收站**（见根目录 INCIDENT-notes.md）。
- 因此：删除前必须 `--dry-run` 展示影响范围；正式删除必须 `--yes`；只允许删除本 skill 创建的设计根模块或沙箱模块（`testbuddy-ms-SMOKE-*`）。
- 禁止用 GET 探测任何语义为删除/变更的接口。
