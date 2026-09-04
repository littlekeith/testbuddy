---
name: spec-issue-analyst
description: >
  需求分析（SPEC 版）工作流定义。
  Args:
      inputs: {
          requirement, # 需求对象：{name, text, source, file}
          可选：@file:分析引用文件路径
      }
---

## 目标

按 SPEC 框架对需求做要点化分析，输出测试点规格所需的输入。

**需求名称**：${requirement.name}

**需求详情**

```
${requirement.text}
```

## 工作流

1. **要点提取**：从需求中提取功能要点、业务规则、约束条件，按功能模块归类。
2. **问题澄清**：标注需求不明确点，能基于需求文本回答的直接给出答案，否则标记"待澄清"。
3. **规格输出**：以 Markdown 写入 `.testbuddy/md/spec_analysis.md`，供 tpoint-generator / spec-tpoint-generator 使用。

## 输出要求

✅ 输出写入 `.testbuddy/md/spec_analysis.md`
✅ 仅输出确认信息："SPEC 分析已完成，文档已保存至 .testbuddy/md/spec_analysis.md"
❌ 禁止在对话中重复输出分析内容
