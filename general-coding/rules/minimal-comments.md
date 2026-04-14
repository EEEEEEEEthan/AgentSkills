# 约定：注释最小化

## 规则

- 完成任务时**不要**为解释「这段在做什么」而写注释；用清晰的命名、布尔/枚举条件与小的结构拆分表达意图。
- **不要**为本次改动的业务背景写块注释或行尾说明（例如「与精英相同」「第一二章」）；若条件复杂，用有意义的局部变量名（如 `grantEliteStyleVolitionRewards`）或提取谓词方法名。
- 仅在有硬性外部依据时保留**最短**注释，例如：第三方协议字段含义、必须满足的规范编号、非代码可读出的安全/并发假设。

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
