# get_requirement —— 获取/保存需求来源

需求来源只有两种：**用户粘贴文本**或**本地文件路径**。禁止联网获取需求。

## 用法

```shell
python <SKILL_DIR>/scripts/get_requirement.py --text "<需求文本>"
python <SKILL_DIR>/scripts/get_requirement.py --file <prd.md> [--name <需求名>]
python <SKILL_DIR>/scripts/get_requirement.py        # 不传参数：仅查看当前会话需求
```

- 禁止 `cd`；`--file` 使用相对工作区根目录的路径或绝对路径均可。
- 成功返回 `{"status":"success","requirement":{"text","name","source":"text|file","file"}}`，并写入会话 `.testbuddy/env/session.json`。
- `--text` 与 `--file` 互斥。

## 注意事项

- 文本较长时建议使用文件路径方式，或直接粘贴全部文本到 `--text`。
- 需求名 `name` 用于根模块命名 `{name}_{yyyyMMdd}`；不传时自动取文本首行或文件名。
- 会话将在工作区根目录（向上查找含 `.testbuddy` 的目录，找不到则取当前目录）下创建 `.testbuddy/env/session.json`。
