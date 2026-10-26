# Workflow Gate Design Contract

## Gate 的唯一职责

回答一个客观问题：

> 这个阶段的真实完成条件，能否被机器或人工证明？

因此 gate 应该来自阶段契约，而不是来自一致的文件名模型。

## Gate 类型选择

| 完成条件 | 推荐 gate |
|---|---|
| 必须存在某个真实文件 | `file_exists` |
| 必须验证 JSON / YAML / Markdown 结构 | `workflow_script` |
| 必须校验多状态、跨阶段一致性 | `workflow_script` audit |
| 需要某人阅读内容并确认 | `human` |
| 需要等待当前任务状态 | `human` |
| 只有进入下一阶段才检查状态 | step-local `condition_producers` |

## 设计顺序

1. 先确定阶段完成标准
2. 再决定由谁证明
3. 再决定 gate 类型
4. 再决定文件路径

不要先选 gate 再编产物。

## `file_exists` 适用边界

适合：

- 该文件本身就是阶段产物
- 文件名和路径是明确契约
- 只需要证明产物存在

不适合：

- 只希望“有东西就行”
- 文件内容没有意义
- 目录、模板或说明文档没有被任何下游消费

## `workflow_script` 适用边界

适合：

- 校验 schema
- 校验状态字段
- 校验多个文件之间的关系
- 校验证据链
- 校验实际输出文件是否齐全

不建议：

- 只检查文件存在
- 让脚本自己去创建或修改状态
- 做不可逆操作

## `human` 适用边界

只用于需要真实人工审阅的阶段，例如：

- 对外交付文档
- 影响方案定稿的评审
- 需要用户选择或确认的关键产物

不需要用于纯状态阶段。

## `condition_producers` 适用边界

当阶段内部或上游能明确生成一个 scalar，例如：

- `needs_review == true`
- `entry_mode == new`
- `has_contract == false`

才使用 `condition_producers`。

不确定时先补充显式输入，不把模型自推结果写成事实。

## Audit stage

链路完整性应在终端前作为 gate 校验，不建议拆成独立业务阶段。

常见 audit 内容：

- 同一 runId 是否一致
- 相邻阶段 digest 是否一致
- Bot / spec / work item 是否一一对应
- 机器声明与真实文件是否一致

## 通用禁止项

- 为每个 step 添加 file_exists，但不知道文件内容
- 为每个 stage 添加 human gate
- 用一个 gate 覆盖所有语义
- 把“能不能执行”强行当错“是否正确”
- 为了规避 gate 失败而生成占位文件
