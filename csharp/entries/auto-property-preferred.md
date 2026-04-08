# 自动属性优先

- **何时用**：成员只是保存状态，`get` / `set` 不做额外逻辑，也不需要兼容特殊命名的 backing field 时，直接写自动属性。
- **常见形式**：公开读写用 `public int Count { get; set; }`；仅允许类内写入用 `public State? Current { get; private set; }`。
- **何时不要用**：setter 里要联动其它状态、做校验、触发刷新，或 getter / setter 需要自定义逻辑时，再回到完整属性。
- **目的**：减少样板字段与直通访问器，让“这是一个纯状态”更直接。
