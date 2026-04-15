# 惰性加载资源：与语义同名的 `var` + getter

## 原则

懒加载 `AudioStream` / `Resource` 时，用**一条**与语义对应的成员名（如 `var audio_stream_selection`），在 getter 里 `if not audio_stream_selection` 再加载并返回，与项目中 `audio_stream_beep` 一类写法一致。

## 正确示例

```gdscript
var audio_stream_selection: AudioStream:
	get:
		if not audio_stream_selection:
			audio_stream_selection = _load_audio_stream(&"res://audios/selection.wav")
		return audio_stream_selection
```
