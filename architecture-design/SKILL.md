---
name: architecture-design
description: >-
  只做系统/模块架构与骨架，不写业务逻辑。用户要求架构、接口拆分、类图落地为代码骨架、或明确说「按架构 skill」时使用。新增类用空壳；新增成员用未实现占位；删改需求用 TODO 注释标出而不改实现。
---

# 架构设计（只做架构）

## 角色边界

- **只做**：模块边界、依赖方向、类/接口拆分、文件与命名落点、空壳与占位。
- **不做**：业务逻辑、具体算法、真实数据流实现、调试与优化细节。

若用户同时要求「实现功能」，先把本 skill 范围内的骨架与 TODO 标完，再按普通编码流程补逻辑（本 skill 不替代实现）。

## 新增类

- 写出**空的**类定义：必要的 `class_name` / `extends` / 基类构造、分组注释可保留。
- **不填写**方法体与信号连接逻辑；可写 `pass` 或按下方「新增成员」规则占位。

## 新增字段 / 属性 / 方法

每个新增成员须有**空的或最小**定义，并在被调用时**主动报错「未实现」**，避免静默空实现。

**GDScript（示例，按项目习惯择一）：**

```gdscript
func do_something() -> void:
	push_error("未实现: MyClass.do_something")
```

需返回值时：在 `push_error` 后返回类型安全默认值（如 `null`/`0`/空数组），或统一用断言在调试期暴露：

```gdscript
func compute() -> int:
	assert(false, "未实现: MyClass.compute")
	return 0
```

**C#：**

```csharp
void DoSomething() {
	throw new System.NotImplementedException("未实现: MyClass.DoSomething");
}
```

属性同理：getter/setter 内 `push_error` / `NotImplementedException`。

## 需要删除 / 修改的现有代码

- **不要**直接删改行为或重命名贯穿全项目（除非用户明确要求执行重构）。
- 在应删改处加**注释**，格式统一为 **`TODO:`**（可带简要说明），例如：

```gdscript
# TODO: 移至 xxx 模块，由 yyy 依赖注入
```

```csharp
// TODO: 合并到 FooService，删除重复状态
```

## 产出检查

- [ ] 无「看起来像已完成」的假实现（除未实现占位与 TODO）。
- [ ] 新增成员均能从调用路径触发明确「未实现」或在 TODO 中标明后续工作。
- [ ] 改动面控制在架构任务范围，避免顺手改无关逻辑。

## 可选扩展

详细约定或项目内统一占位宏若存在，可放在同级 [conventions.md](conventions.md)（无则省略）。
