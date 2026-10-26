extends Node
## 游戏 Autoload。读到 --test= 时加载该脚本并设为当前场景。


const TEST_ARGUMENT_PREFIX := "--test="


func _ready() -> void:
	var test_script_path := test_script_path_from_arguments()
	if test_script_path.is_empty():
		return
	# 主场景还在进树，这一帧不能同步换场景。
	call_deferred(&"_attach_test", test_script_path)


func _attach_test(test_script_path: String) -> void:
	var test_script := load(test_script_path) as GDScript
	var test_node: Node = test_script.new()
	get_tree().root.add_child(test_node)
	var previous := get_tree().current_scene
	get_tree().current_scene = test_node
	if previous != null and previous != test_node:
		previous.free()


func test_script_path_from_arguments() -> String:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with(TEST_ARGUMENT_PREFIX):
			return argument.trim_prefix(TEST_ARGUMENT_PREFIX)
	return ""
