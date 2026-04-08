# CanvasItem 共享材质时不要把 sampler2D 当作实例参数

## 结论

Godot 4 的 `instance uniform` 不支持纹理类型，所以 `sampler2D` 不能作为每实例参数来解决 CanvasItem 的共享材质问题。

## 常见误区

看到 `float`、`vec4` 能写成 `instance uniform` 后，容易顺手把：

```glsl
uniform sampler2D rim_texture;
```

改成：

```glsl
instance uniform sampler2D rim_texture;
```

这个方向不成立。

## 默认做法

如果目标是“多个 2D 节点共用同一个 `ShaderMaterial`，但每个节点又有不同贴图”，优先把差异贴图放到节点自带纹理通道，而不是放进材质参数。

## 可用路径

### 1. 用节点主纹理通道

主贴图本来就应优先走 `TEXTURE`。

### 2. 用 `CanvasTexture` 承载额外贴图

若 shader 还需要额外纹理，可考虑把它放到：

- `NORMAL_TEXTURE`
- `SPECULAR_SHININESS_TEXTURE`

然后在 shader 里采样对应内置 sampler。

### 3. 再考虑其他共享方案

如果节点通道不够，再考虑：

- atlas
- texture array
- 重新设计数据承载方式

## 适用例子

例如角色 rim 效果想共享同一份 `ShaderMaterial`，可以把角色主图放进 `CanvasTexture.DiffuseTexture`，把 rim 图放进 `CanvasTexture.SpecularTexture`，shader 直接采样 `SPECULAR_SHININESS_TEXTURE`。
