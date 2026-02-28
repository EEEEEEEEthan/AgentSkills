---
name: git-create-branch
description: 解析 source/target 并安全创建 Git 分支，处理模糊 source、非法 target 字符和重名冲突，然后切换并设置默认 push 上游。用于用户要求新建分支、切换分支、或“从某分支拉出新分支”时。
---

# Git Create Branch

## 目标

在不误判 source 的前提下，创建合法且不冲突的 target 分支，并完成切换与上游绑定。

## 术语

- `source`：新分支的起点（本地分支或远程分支）。
- `target`：用户想创建的新分支名（可能包含非法字符或与现有分支重名）。

## 必须遵守

1. 如果 `source` 不明确，必须先向用户确认。
2. 必须同时检查本地和远程分支，按“精确 > 前缀 > 包含”匹配 `source`。
3. `target` 非法时要自动清洗，尽量保留原语义；中文字符合法，必须保留。
4. 若本地或远程已存在同名 `target`，必须自动改名避让。
5. 创建并切换后，必须执行可让默认 `git push` 直接推到该分支的指令。

## 标准流程

### 1) 收集输入

- 读取用户给的 `source` 和 `target`。
- 若 `source` 缺失或表达不清（如“从主干拉一个分支”但未说明主干是 `main`/`master`/其他），先提问确认，再继续。

### 2) 列举并匹配 source

先更新远程引用：

```bash
git fetch --all --prune
```

列举分支：

```bash
git branch --format="%(refname:short)"
git branch -r --format="%(refname:short)"
```

匹配策略：

1. 精确匹配（优先）：`source` 与分支全名一致。
2. 前缀匹配：分支名以 `source` 开头。
3. 包含匹配：分支名包含 `source`。

判定规则：

- 0 个候选：告知未找到，并请用户重新给 `source`。
- 1 个候选：使用该候选。
- 多个候选（含“本地和远程同名都存在”）：必须让用户明确指定一个。

### 3) 清洗并校验 target

对 `target` 执行以下处理（中文保留）：

1. 去掉首尾空白。
2. 把空白字符替换为 `-`（例如 `修复 天气` -> `修复-天气`）。
3. 将 Git ref 禁止字符替换为 `-`：`~ ^ : ? * [ \` 及控制字符。
4. 将连续的 `/` 压缩为单个 `/`。
5. 去掉首尾的 `/` 与 `.`。
6. 将 `..` 与 `@{` 替换为 `-`。
7. 若以 `.lock` 结尾，改为 `-lock`。

然后校验：

```bash
git check-ref-format --branch "<sanitized_target>"
```

- 校验失败：继续最小化修正；仍失败则向用户确认最终命名。

### 4) 处理重名冲突（本地 + 远程）

检查候选名是否已存在：

```bash
git show-ref --verify --quiet "refs/heads/<name>"
git ls-remote --exit-code --heads origin "<name>"
```

若任一存在，追加后缀直到可用：

- `<name>-1`
- `<name>-2`
- `<name>-3`

最终得到 `final_target`（保证本地和远程都不重名）。

### 5) 创建并切换分支

用解析后的 `resolved_source` 作为起点：

```bash
git switch -c "<final_target>" "<resolved_source>"
```

说明：

- 若 `resolved_source` 是远程分支，使用 `origin/<branch>` 作为起点即可。

### 6) 设置默认 push 上游（必须执行）

```bash
git push -u origin "<final_target>"
```

执行后，后续在该分支直接 `git push` 即可默认推送到 `origin/<final_target>`。

## 对用户的回报格式

按以下要点简洁反馈：

- 解析后的 `source`（以及是否经过确认）。
- 用户输入的 `target` 与清洗后的结果。
- 若发生重名，给出最终改名结果。
- 已执行：创建、切换、`git push -u`。

## 快速示例

用户输入：

- `source`: `0.4-bug-在游戏窗口不显示时`
- `target`: `ethan/修复 天气系统bug`

可能输出：

- 匹配到 `source`: `ethan/0.4-bug-在游戏窗口不显示时-鼠标移动也会触发装弹切换的逻辑-可以听见音效`
- 清洗后 `target`: `ethan/修复-天气系统bug`
- 若重名则改为：`ethan/修复-天气系统bug-1`
- 已执行 `git switch -c ...` 与 `git push -u origin ...`
