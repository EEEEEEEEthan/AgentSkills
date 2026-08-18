# GDScript (Godot 4) 补充说明

## 优化检查清单

- [ ] gdscript有自己的引用计数，所以内部自己使用的信号可以不必disconnect
- [ ] 如果有信号connect/disconnect的要求，那他们必须成对出现，例如enter_tree和exit_tree。ready/exit_tree这种是不合理的，因为reparent会导致信号被断开。
- [ ] tscn的脚本(或者tscn下的builtin脚本),对节点的访问应该尽量用unique_name(而不是get_parent, get_node, get_child等),除非不得已