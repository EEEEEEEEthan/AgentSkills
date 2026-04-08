# 扩展成员（C# 14+，条件允许时）

- **语法**：在 `static` 容器类里用 `extension (T receiver) { … }` 声明实例扩展；块内成员直接写 `public int M(…)` / `public bool P => …`，不再写 `this T` 形参。调用方式与旧扩展方法相同（`x.M()`、`x.P`）。
- **何时用**：工程 `LangVersion`、SDK/Roslyn 已支持扩展成员时，新增或迁移扩展优先用该写法；与老 `this T` 扩展二进制/源码可互操作，可逐步替换。
- **属性优先**：扩展逻辑**不依赖除接收者外的参数**时，写成**只读属性**（`public bool Foo => …`），不要写成无参方法 `Foo()`；仍有额外参数时保留方法（如 `GetPrice(rate)`）。
