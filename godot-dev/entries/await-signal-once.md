# 单次信号优先用 `await`

## 问题

只为「等某信号触发一次再往下写」而 `signal.connect(_on_xxx)`，多一个具名回调，跳转阅读成本高。

## 正确做法

在同一条控制流里直接挂起，再继续：

```gdscript
func _ready() -> void:
	set_process(false)
	await %ChildComponent.finished
	_begin_hold_phase()
```

## 仍用 `connect` 的情况

- 同一信号要响应多次，或要在运行时动态增删监听。
- 需要 `CONNECT_ONE_SHOT` 以外组合（如 `CONNECT_DEFERRED`）且不适合改成顺序 `await`。
- 监听对象不是当前脚本的线性流程（例如全局总线、多订阅者）。

## 为什么重要

线性代码更易读；减少仅服务一次的 `_on_*` 方法。注意：含 `await` 的函数在挂起点会让出执行，仍须保证与 `call_deferred`、`setup_*` 等同帧初始化的顺序正确。
