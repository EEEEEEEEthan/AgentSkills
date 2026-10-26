extends Node
## 游戏 Autoload。读到 --test= 时把该脚本挂到本节点下。


const TEST_ARGUMENT_PREFIX := "--test="


func _ready() -> void:
	var test_script_path := argument_value(TEST_ARGUMENT_PREFIX)
	if test_script_path.is_empty():
		return
	var test_script := load(test_script_path) as GDScript
	var test_node := test_script.new() as Node
	add_child(test_node)


func argument_value(prefix: String) -> String:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with(prefix):
			return argument.trim_prefix(prefix)
	return ""
