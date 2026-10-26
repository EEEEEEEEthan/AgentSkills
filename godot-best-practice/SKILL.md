---
name: godot-best-practice
description: Godot 最佳实践。编写、审查或改 Godot 项目时使用。
---

# Godot 开发

仍是同一个技能。先读本文件，再读与手头问题对应的一层；落到具体问题时再读该层里的条目。两层都要读完再动手，不要停在分类文件。

## 初始化godot工程

用仓库脚本下载并启动 Godot，版本写在 `project.godot` 的 `[engine_host]`。`.engine` 自己下载，不用先跑准备脚本。
[setup.md](setup.md)

## 引擎最佳实践

资源管理、tscn 结构、场景边界、节点生命周期与引擎行为。
[engine.md](engine.md)

## 编码最佳实践

GDScript 与 C# 的写法、属性桥接、场景内节点访问。
[coding.md](coding.md)

## 自动化测试最佳实践

冒烟、专项、时限，以及用 Python 出 debug 包再跑。
[testing.md](testing.md)

# 维护此文档

安装直接改 `setup.md`。引擎和编码：在 `engine.md` 或 `coding.md` 增加一句话摘要和 `entries/` 链接，并在 `entries/` 下新增详述。自动化测试直接改 `testing.md`。条目保持短小可检索，不扩成替代官方文档的教程。
