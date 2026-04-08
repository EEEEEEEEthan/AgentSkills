# 用 LINQ 收集下标再随机选一个

- 需要「列表里所有满足条件的索引」时：`Enumerable.Range(0, list.Count).Where(index => list[index] == 目标值).ToList()`（需 `using System.Linq`）。
- 从中随机取一个下标：`indices[rnd.Next(indices.Count)]`，再对原列表赋值或读取；`Count == 0` 时先跳过或分支。
- 比手写两次循环更直观；会分配中间 `List`，极热路径可改回单次扫描 + 第 k 个命中。
