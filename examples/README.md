# Workflow 示例

这组示例刻意比“单步冒烟”更长，用来验证 agent 在多轮交互场景下是否能持续推进、反复修正，并被 command 门禁约束住。

## workflow-v2-starter

一个最小 v2 示例包，包含一个默认路由、一个条件路由、一个 step-local command producer 和一个显式回退边。规范写法见 `../docs/workflow-v2-authoring-guide.md`。

## frontend-delivery

> 本目录中的说明只用于展示和应用参考；真正的运行时 workflow 是内置 `agent_workflow_harness/workflows/<alias>/` 目录包，或项目/用户 `.agents/workflows/<alias>/` 目录包。

一条针对前端的完整交付流程：

```text
需求澄清 -> 方案设计 -> 任务拆分 -> 页面实现 -> 自动化测试 -> CodeReview -> 提PR -> 完成
```

重点验证：

- 多轮推进
- 阶段间权力边界
- 前端页面不是只做 UI，而是完整交付
- `npm test` 自动化测试通过后才能继续
- 每一步都有产物
- 每一步都带 `command` 校验

## meeting-summary

内置 workflow 目录：`agent_workflow_harness/workflows/meeting-summary/`。一条非编码的会议纪要流程：

```text
会前信息 -> 议题归纳 -> 结论提炼 -> 行动项分配 -> 风险梳理 -> 纪要归档 -> 完成
```

重点验证：

- 纯文档型工作
- 多轮整理
- 逐阶段产出文件
- 用 command 门禁检查关键信息是否存在

## 运行方式

任选一个前端需求，例如“实现一个可交互的网页小游戏”，直接用别名启动:

```bash
awh start frontend-delivery --task "Implement a frontend interaction"
```

在一个干净的前端项目里，完成后通常会得到:

```text
.workflow-harness/task-artifacts/<task-slug>-<task-id>/
  requirements.md
  design.md
  tasks.md
  implementation.md
  test-report.md
  code-review.md
  pr.md
src/...
tests/...
```

其中 `自动化测试` 阶段会强制执行:

```bash
npm test
```

`CodeReview` 阶段使用 `agent_workflow_harness/workflows/frontend-delivery/resources/` 中的结构化报告作为约定，并由同目录下的资源脚本执行校验：

```text
未修复问题数：0
```

同时要求每个 `### [P?]` 问题条目都写成：

```text
状态：已修复
```

只有测试通过、CodeReview 报告明确的未修复问题数为 0，流程才会继续进入 `提PR`。

继续推进:

```bash
awh next
```

每完成一个阶段的产物后，再调用 `awh next`。如果 gate 未满足，CLI 会返回 `blocked` 和当前修复指令；满足后才会进入下一阶段，直到 `done`。

所有内容类 command gate 都在失败时输出明确的 `reason`，而不是只提示 `Command failed with no output`。
