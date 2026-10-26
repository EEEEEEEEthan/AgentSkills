# 能进场景就进场景

## 约定

结构、引用、信号连接，能在 `.tscn` 里声明的就写进场景。运行时脚本只做场景表达不了的行为：输入、分支、生成数量不固定的实例、跨场景通讯。

同一 `.tscn` 内两端都在的信号，用检视器写入 `[connection]`，见 [scene-signals-inspector.md](scene-signals-inspector.md)。资源引用走 `@export` 进场景，见 [avoid-preload.md](avoid-preload.md)。脚本挂在哪个节点上，在场景里声明，见 [avoid-set-script.md](avoid-set-script.md)。

## 不推荐

用 `_ready()` 搭本来可以摆在场景里的节点、改本来可以在检视器里设的属性、或 `connect()` 本来固定的信号。

## 例外

- 节点数量或类型要到运行时才知道
- 连接目标依赖当次分支
- 占位符按规则实例化（见 instance-placeholder 条目）
