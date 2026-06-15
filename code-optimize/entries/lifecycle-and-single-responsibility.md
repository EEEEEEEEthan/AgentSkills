# 生命周期与职责边界

适用于：**宿主对象**维护一组**附着物**（技能、buff 驱动器、子模块等），附着物有**挂接 / 恢复 / 卸下**等生命周期，且存在**正常运行**与**从持久化状态重建**两条入口。

## 问题从哪来

宿主上的「变更」方法（`AddXxx`、`Attach`、`Register`）容易偷偷承担两件事：

1. **改集合**（列表里多一项）
2. **按当前全局模式做副作用**（是否在会话中、是否读档、要不要初始化）

第二种往往通过 `bool` 参数或读**全局单例 / 静态门面**实现。结果是：

- 调用方不知道默认参数下会发生什么
- 「首次进入」「会话中途新增」「从存档重建」多条路径行为纠缠
- 否定命名（`dontXxx`）与模式布尔（`isFromSave`）叠加，语义难追

## 原则

### 变更方法只做变更

`AddXxx` 只改宿主上的集合或引用；挂接后的初始化、恢复、释放由**知道当前上下文的编排层**在紧邻调用后显式触发。

不要再给 `AddXxx` 塞 `runInit`、`deferInit`、`restoreImmediate` 等参数——那只是把分支决策藏回方法签名。

### 互斥生命周期拆成独立入口

用 `OnAttach(ctx, isFromSave)` 在单方法里 `if (!isFromSave)` 跳过副作用，等于把两种语义绑在一处。

拆成语义明确的独立方法，例如：

- `Initialize(...)` — 正常运行下首次挂接或会话中途新增；可注册监听、写入默认状态、触发一次性副作用
- `Restore(...)` — 从持久化重建后挂接已存在；**默认空实现**，不重复施加已由存档还原的状态

二者**互斥**：对**同一次挂接**只应走其一；在 API 文档中写明，并在编排层保证不会连续调用两者。

`Release` / `Dispose` 等与上述正交，负责卸下时的清理。

### 模式判断留在编排层，不读全局单例

宿主或附着物内部不应查询「当前是否在 X 模式」。由**会话开始、读档完成、规则系统、调试入口**等编排代码决定调用 `Initialize` 还是 `Restore`。

### 子类扩展：override + base，不用 Post 钩子

基类若提供 `PostInitialize` 且仅被基类自身调一次，子类往往只需：

```csharp
public override void Initialize(Context ctx) {
    base.Initialize(ctx);
    // 本子类额外逻辑
}
```

多一层 `PostXxx` 钩子通常只增加跳转，不增加复用。

## 何时由谁调用

下表用泛化角色：**编排层**（会话/存档协调）、**宿主**（持集合的对象）、**处理器**（附着物上的行为对象）。

| 场景 | `AddXxx` 之后 | 说明 |
| --- | --- | --- |
| 会话外配置、菜单里预先挂上 | 通常不调用 | 等会话开始时编排层批量 `Initialize` |
| 会话开始，从配置实例化一批附着物 | 通常不调用 | 同上 |
| 会话进行中动态新增 | `Initialize` | 规则、效果、作弊入口等在 `AddXxx` 后立刻调用 |
| 读档：先反序列化宿主与附着物列表 | 通常不调用 | 等运行时状态（数值、子状态）还原完毕 |
| 读档：编排层收尾 | 批量 `Restore` | 在持久化字段已写回宿主**之后** |
| 读档过程中极少见的临时新增 | `Restore` | 与 `Initialize` 互斥 |
| 卸下 / 会话结束 | `Release` | 可由 `RemoveXxx` 或编排层统一触发 |

**Restore 与 Initialize 的边界：** 若某副作用对应的**持久化字段已在反序列化阶段写回**，`Restore` 不应再执行该副作用；`Initialize` 会重复施加，读档路径必须避免对同一挂接再调 `Initialize`。

## 反模式演进（抽象）

某次游戏业务重构中走过的典型阶段，可对照任意类似系统：

| 阶段 | 反模式 | 改法 |
| --- | --- | --- |
| 1 | `dontRunInitDuringSession` | 肯定命名；仍可能是过渡方案 |
| 2 | `AddXxx` 内查全局「是否在会话中」再 `Initialize` | 去掉耦合；编排层显式 `Initialize` / `Restore` |
| 3 | 构造 / `AddXxx` 上的 `deferInit` 参数 | 去掉；变更与生命周期彻底分离 |
| 4 | `Initialize(ctx, isFromSave)` | 拆为 `Initialize(ctx)` + `Restore(ctx)` |
| 5 | `PostInitialize` 钩子 | `override Initialize` → `base` 后追加 |

## 目标形态（示意）

```csharp
// 宿主 — 只维护集合
public void Attach(Attachment item) {
    if (!CanAttach()) return;
    _items.Add(item);
}

// 会话中规则系统动态添加
var item = CreateAttachment(...);
host.Attach(item);
item.Handler.Initialize(host);

// 读档收尾 — 持久化字段已还原之后
foreach (var (host, item) in AllAttached) {
    item.Handler.Restore(host);
}
```

## 审查时快速问

1. `AddXxx` / `Attach` 是否在查全局单例或模式 `bool`？
2. 同一次挂接会不会既 `Initialize` 又 `Restore`？
3. 读档路径会不会误走 `Initialize`，导致副作用或状态叠两层？
4. 子类扩展是否只需 `override` + `base`，却多了一层仅调用一次的 `PostXxx`？
