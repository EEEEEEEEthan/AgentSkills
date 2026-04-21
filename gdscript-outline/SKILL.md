---
name: gdscript-outline
description: 用轻量扫描从 .gd 提取大纲（父类、class_name、字段/属性/方法，含类型与 static）。在需要了解 GDScript 结构时先运行 ~/.cursor/skills/gdscript-outline/scripts/gdscript_outline.py 再决定是否通读全文。
---

# GDScript 大纲（gdscript-outline）

## 何时用

- 快速了解某 `.gd` 的父类、类名与成员列表，**再决定**是否打开完整文件。
- Agent/人类做检索、对比、评审前的**第一层**信息。

## 脚本位置与用法

脚本在**用户全局**技能目录：`~/.cursor/skills/gdscript-outline/scripts/gdscript_outline.py`（Windows 即 `%USERPROFILE%\.cursor\skills\gdscript-outline\scripts\gdscript_outline.py`）。

```bash
python ~/.cursor/skills/gdscript-outline/scripts/gdscript_outline.py <文件.gd>
```
