extends Node
## 游戏进程起来即通过。时间上限由 .engine_test.py 统一管，测试脚本不自己写。


func _ready() -> void:
	get_tree().quit(0)
