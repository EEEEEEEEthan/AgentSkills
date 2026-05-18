# 约定：少量且可维护的注释

## 规则

- 完成任务时**不要**为解释「这段在做什么」而写注释；用清晰的命名、布尔/枚举条件与小的结构拆分表达意图。
- 允许保留**少量**注释，但注释必须可长期维护：只写“为什么/约束/外部假设”，不写可从代码直接读出的事实。
- **不要**为本次改动的业务背景写块注释或行尾说明（例如「与精英相同」「第一二章」）；若条件复杂，用有意义的局部变量名（如 `grantEliteStyleVolitionRewards`）或提取谓词方法名。
- 注释中**不得出现具体数值**（例如：时间/范围/章节/阈值/倍率等具体数字）。若需要表达数值含义，把数值体现在代码里的常量/枚举/配置名上，注释只说明意图与约束。
- 仅在有硬性外部依据且“离开注释就会误用”时保留**最短**注释，例如：第三方协议字段含义、非代码可读出的安全/并发假设（外部依据用命名或链接表达，避免在注释中写具体数值）。

## 不符合

```csharp
// 精英战与第一、二章 Boss 战发放与精英相同的意志三选一奖励
if (elite || bossEarlyChapters) { ... }
```

## 符合

```csharp
var grantEliteStyleVolitionRewards =
	fight.tier == EnemyGroupConfig.Tier.Elite
	|| (fight.tier == EnemyGroupConfig.Tier.Boss && fight.mapLayer is >= 0 and <= 1);
if (grantEliteStyleVolitionRewards) { ... }
```
