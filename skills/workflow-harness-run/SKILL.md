---
name: workflow-harness-run
description: 当用户要使用 awh 工作流完成任务时使用，例如「使用awh工作流完成 xxx」；awh 是 agent-workflow-harness 的缩写。只通过 awh start / awh next 执行，不自报完成或跳步。
---

# AWH Workflow Harness 运行器

## 目的

把 `agent-workflow-harness`（缩写 `awh`）当作任务推进的唯一权威。你只负责执行当前阶段的工作指令，不得推断、选择或预测后续阶段。

## 安装

先检查 CLI 是否可用：

```bash
command -v awh
```

如果 `awh` 不存在，在仓库根目录本地安装：

```bash
uv tool install --force .
```

安装后重新检查：

```bash
awh --help
```

## 任务输入准入
AWH runner 不负责解释业务语义，也不替某个 workflow 预判结果。启动前只做一件事：确认用户输入是否已经足够形成任务标题和 workflow 选择。

- 外部链接、文件、ID、票据等材料，必须先解析到能明确本次任务要解决什么，以及“某个 workflow 是否适合接手”。
- 解析失败或内容明显不完整时，先披露缺口，不要只凭链接或 ID 启动 workflow。
- `https://...` 这类复杂指针不适合作为 `--var` 值；请转为短稳定 token（如 `doc_id=576489266`），或在 workflow 不要求时省略。
  
## 预检

选择命令前，先读取当前任务锚点：

```text
<repo>/.workflow-harness/task.json
```

如存在，用其中的 `title` 作为当前请求的语义锚点：

1. 用户请求是同一任务时，调用 `awh next`。
2. 明显是不同任务时，不要静默替换当前任务。只有用户明确要求继续当前任务才调用 `awh next`，否则报告当前标题并请用户确认；`awh next` 不会自动切换任务。
3. 锚点不存在时，不要尝试修复状态。按当前请求选择 workflow alias 并运行 `awh start`。
4. 若 `awh next` 返回 `No active workflow task`，按用户请求选择 workflow alias 启动新任务；CLI 不会自动 start。

新标题必须是一行自然英文，5–120 个字符，只包含 ASCII 字母、数字、空格和连字符，且至少包含一个字母或数字。描述用户要的结果而不是实现过程；不要传入 kebab-case 形式的目录名。复用已有标题时必须逐字原文使用。

## 命令协议

启动任务；`--var` 可重复，用于记录控制面可用的 token 输入。没有输入时必须省略：

```bash
awh start <workflow-alias> --task "<task-title>" [--var name=value]...
```

继续任务、验证当前 gate，并只在控制面批准时进入下一步：

```bash
awh next
```

人审通过时默认只记录决策，不要推进：

```bash
awh approve
```

如果用户明确要求“确认后一步推进”，可以使用显式一步命令；它等价于先 `awh approve` 再 `awh next`，不会绕过任何 gate：

```bash
awh approve --next
```

人审拒绝时必须记录用户意见：

```bash
awh reject --reason "<用户给出的具体拒绝/修改意见>"
```

## 输入规则

- 变量名使用小写 snake_case，值必须是单个非空 ASCII token（仅字母、数字、`.`、`_`、`-`、`/`）。
- `https://...` 不是合法 token，因为它含 `:`；请先读取原文，再传短稳定 ID（如 `doc_id=576489266`）或在 workflow 不要求时省略 `--var`。
- 变量可用于 `${name}` 模板替换；缺引用变量时 CLI 会返回 `error`，不要伪造值。
- `.workflow-harness/tasks/` 下的控制面 state/history 不可读写或修改；`.workflow-harness/task-artifacts/` 下的业务产物按当前阶段 instruction 和 gate 要求写入。
- 同一个变量不能在同一命令中重复。
- 续接同一个活跃任务时，`--var` 可以完全省略，或逐字重复创建时的输入；不得添加或改变输入。
- 若 `start` 返回 `conflict`，不要改写 `.workflow-harness` 状态，向用户确认当前任务和期望输入。

## 响应协议

解析 JSON 响应。任务级命令会返回 `task.id`、`task.title`、`task.step` 和 `task.artifactDir`；直接使用这些字段描述当前任务上下文，不要再读取 `.workflow-harness/tasks/` 下的控制面状态。只处理以下五种状态。

### `active`

1. 执行返回的 `instruction`。
2. 按照指令完成任务。
3. 完成工作后调用 `awh next`。

### `blocked`

当前任务推进被阻塞，尚未获得推进批准。

若 `check.reason` 以下列前缀开头，说明当前 gate 是人工确认 gate，不要自行推进：

- `HUMAN_REVIEW_PENDING`：请人审当前 evidence；用户确认后运行 `awh approve`，拒绝则运行 `awh reject --reason "..."`。
- `HUMAN_REVIEW_RECORDED`：已记录 approved。请继续运行 `awh next`。
- `HUMAN_REVIEW_REJECTED`：用户已拒绝；请根据 reason 修复 evidence 后再请求一次人审。
- `HUMAN_APPROVAL_STALE`：用户之前确认过的 evidence 已变化；请修改后重新请求人审。
- `HUMAN_REVIEW_UNCHANGED`：用户拒绝后 evidence 仍未变化；请先完成实质修改。

其他 blocked 原因：

1. 根据阻塞原因和当前阶段的 instruction 修复。
2. 再次调用 `awh next`。

blocked 响应中的 instruction 描述的是当前阶段的任务。

### `done`

停止 workflow 工作，报告完成即可。不要发明新的流程步骤。

### `conflict`

项目已有另一个活跃任务。不要切换或替换任务；报告当前任务标题并请用户确认。

### `error`

根据响应中的 `reason` 和可选 `hint` 选择安全的下一步。若原因是 `No active workflow task`，启动新任务；若提示任务锚点或控制面状态不匹配，报告给用户，不要手工改状态。若原因来自路由评估、输入解析或控制面日志，将它当作操作错误处理，不要把它当作当前阶段的 `blocked` 修复说明，更不要自行选择路由。

## 每次命令后的汇报

简要说明：

- 响应状态
- 当前任务标题
- gate 通过或失败
- 下一步执行的工作指令
- `done` 时明确报告完成

## 硬边界

- 不要自我宣布推进状态。
- 不要把 `start` 当作二次触发或推进命令。
- 不要推断候选路由、条件、未来阶段或图结构；控制面只会给出被选中阶段的工单。
- 不要读取或修改 `.workflow-harness/tasks/` 下的 `state.json`、`history.jsonl`。
- 不要把 `awh approve` 或 `awh reject` 当作推进命令；它们只记录人审结果。
- `done` 后不要继续。
