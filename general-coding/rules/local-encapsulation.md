# 约定：单函数内封装规则

## 规则

- 如果一段逻辑在当前函数内只调用一次，默认**不要封装**，直接内联到调用处。
- 如果一段逻辑仅被当前函数调用，但在该函数内会调用多次，默认提取为**局部闭包**。
- 仅在以下情况提升为类级方法：跨函数复用、需要独立测试、或明显提升可读性。

## 不符合（单次调用仍封装）

```csharp
int RollStepDelta() {
	return (int)(GD.Randi() % 36) + 12;
}
var stepDelta = RollStepDelta();
```

## 符合（单次调用直接内联）

```csharp
var stepDelta = (int)(GD.Randi() % 36) + 12;
```

## 符合（同函数多次调用提取闭包）

```csharp
void UpdateVision() {
	void ConfigureCardAsPreview(MChrCardBig card) {
		card.DeactivateButton();
		card.btnCard.MouseFilter = MouseFilterEnum.Ignore;
	}
	ConfigureCardAsPreview(cardA);
	ConfigureCardAsPreview(cardB);
}
```
