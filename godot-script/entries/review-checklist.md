# Godot 脚本检查清单

编写或审查 GDScript 时可对照：

- [ ] 成员顺序是否为：字段 → 属性 → 方法？
- [ ] 导出属性的 setter 是否检查 `is_node_ready()`？
- [ ] 是否在 `_ready()` 中刷新所有导出属性？
- [ ] 是否使用 `@onready` 缓存所需节点引用？
- [ ] 子节点访问场景根时是否用 `owner` 而非 `get_parent()`？
- [ ] 是否避免对「必有」的 unique 节点做多余 null 检查？
- [ ] 刷新函数是否直接访问已缓存节点（无无意义 null 检查）？
- [ ] 节点引用是否有合适类型提示？
- [ ] 惰性加载资源是否采用「成员与 getter 同名」，且每项只判断自己的成员？
- [ ] `call_deferred` 是否使用 `&"method_name"`？
- [ ] 纯数据类在 setter 里发信号或副作用时，是否用显式 `_xxx` 后备字段 + getter/setter？
