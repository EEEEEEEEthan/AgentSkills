extends Control
## 纪录片式的红圈标注：把观众的注意力指到画面上那一点。


func _ready() -> void:
	resized.connect(queue_redraw)


func _draw() -> void:
	var center := size * Vector2(0.5, 0.45)
	var radius := minf(size.x, size.y) * 0.34
	draw_arc(center, radius, 0.0, TAU, 64, Color(1.0, 0.28, 0.24, 0.95), 7.0, true)
	draw_arc(center, radius + 7.0, 0.0, TAU, 64, Color(0.0, 0.0, 0.0, 0.35), 3.0, true)
