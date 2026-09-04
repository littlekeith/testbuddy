# open_design —— 输出 MeterSphere 页面链接

本 skill 不内置浏览器自动打开能力（Codex 无网页预览工具）：**只输出可点击链接文本，由用户自行点击打开**。

## 做法

在 ms_design 落库成功、或用户要求打开页面时：

1. 从最近一次 `ms_design.py` 输出（或 `design_mapping.json` 的 `project_id`）取 `BASE_URL`（默认 `http://10.10.8.52:8081`）与项目 ID。
2. 输出文本：

```text
请在浏览器打开 MeterSphere 查看用例：
<BASE_URL>
项目 ID：<project_id>
根模块：<root_module_name>（uid=<root_module_uid>）
设计映射文件：<mapping_file>
```

3. 不要尝试用任何工具自动打开浏览器。
