extends Node
## 游戏进程起来即通过。


const TIME_LIMIT_SECONDS := 5


func _ready() -> void:
	get_tree().create_timer(TIME_LIMIT_SECONDS).timeout.connect(func() -> void: get_tree().quit(1))
	get_tree().quit(0)
