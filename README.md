# Agent Workflow Harness

Agent Workflow Harness（AWH）是一个面向 AI coding agent 的确定性工作流控制面。它不依赖模型记住完整流程，而是用 YAML 状态机定义步骤，用 CLI 保存权威状态，用 gate 决定任务能否进入下一个阶段。模型每次只收到当前阶段的工单，并按工单执行。

## 解决什么问题

多步骤任务中的 agent 常见问题并不是“不会做”，而是执行过程不可控：

- 目标漂移：中间上下文越多，最初的目标和约束越容易被淡化。
- 自称完成：模型可以生成一本正经的“已完成”说明，但没有客观证据。
- 跳过关键步骤：测试、评审、人工确认等流程可能被模型当作可选动作。
- 状态不可靠：没有权威状态时，模型容易把“想做”当作“已经做过”。
- 依赖 prompt 自觉：自然语言约束只能影响模型行为，不能真正决定任务状态。

AWH 的答案是把这三件事拆开：

- **流程**：由 YAML 状态机声明，而不是靠模型临时规划。
- **状态**：由 CLI 持有，而不是放在对话上下文里。
- **执行**：由 agent 按当前阶段工单完成，不自行判断全局进度。

## 为什么这更接近大模型机制

大模型对输入是概率性的，而长对话中的注意力分布并不均匀。较早注入的全局规则，随着后续代码、工具输出和上下文不断堆叠，很容易被稀释。相比之下，越靠近当前生成位置的内容，通常对下一步行为影响越大。传统 skill 一次性把完整流程、全部规则和所有阶段塞给模型，随着任务推进，早期步骤容易被模型遗忘，后续自生成内容也会反过来强化错误方向。

AWH 采用的运行方式更贴近 agent 上下文工程：

- **最小上下文**：agent 每次只看到当前 step 的工单，不暴露完整 workflow。
- **最新指令优先**：每次 `awh next` 都重新把当前阶段的核心指令送回模型，让最重要的工作要求保持在高影响位置。
- **状态外置**：完整状态保存在控制面文件中，长期任务不依赖模型的短期记忆。
- **客观 gate**：文件、命令、脚本输出和人审结果共同决定能否进入下一步，而不是让模型给自己打分。

这套设计相当于把“计划、推进、验收”交给确定性控制面，把“具体生产”交给模型。AWH 也不是要替代 skill；skill 继续承载方法论、经验和具体工作方法，而 workflow 负责阶段顺序、状态推进和客观验收。

## 两种用法

### 通过 Skill 使用（自然语言方式）

这是更自然的入口，适合让 agent 帮你创作 workflow、改造既有 skill，或直接按某个 workflow 推进任务。

#### 创作 workflow

使用 `workflow-harness-creator` skill，明确请求它创建或修改一个 AWH workflow。你可以提供：

- 一段流程描述
- 一份现有 skill
- 一份已有 workflow
- 一份需求文档或系统设计文档

creator skill 的职责不是复制模板，而是：

1. 读取输入，推导真实流程、阶段、产物和人工决策点。
2. 先建立阶段契约：输入、输出、完成标准、适配 gate。
3. 以真实产物决定文件类型，避免为了流程好看硬造统一目录。
4. 生成源码 backed 的 workflow 包，并在必要时同步配套 references 或 scripts。
5. 运行 `awh validate`，只有 valid 才算完成。

如果要改造历史 skill，creator 会先提炼原 skill 的意图、行为边界、产物和依赖，再把它重构为“阶段 + gate + 路由”的 AWH workflow。它不会为了迁移而虚构阶段，也不会把原本不确定的路径硬填成占位产物。

#### 执行任务

使用 `workflow-harness-run` skill。当你明确说“使用 awh 工作流完成 xxx”时，它会接手任务推进协议：

1. 先读取当前项目的活跃任务锚点。
2. 判断本次请求是继续当前任务，还是需要用户确认任务切换。
3. 选择对应的 `awh start` 或 `awh next` 命令。
4. 只执行返回的当前阶段工单，不预测、不修改、不伪造后续阶段。
5. 遇到 gate 或 state 错误时，如实汇报原因并按协议处理。

runner skill 不负责业务事实判断。真正的业务方法、阶段边界、验收标准和人工确认点都由 workflow 及其 references 定义。

### 通过 CLI 使用（偏编程式）

这是偏编程式的用法，适合已经拥有 workflow、希望亲自检查或驱动每一步的用户。

#### 安装

从 GitHub 克隆仓库后在项目根目录安装：

```bash
git clone https://github.com/tian-minghui/agent-workflow-harness.git
cd agent-workflow-harness
uv tool install --force .
```

#### 检查可用性

```bash
awh --help
```

#### 校验 workflow

```bash
awh validate <workflow-alias>
```

`validate` 是无副作用命令，只检查 workflow 是否符合 v2 契约，不创建任务、不修改状态。

#### 启动任务

```bash
awh start <workflow-alias> --task "<task-title>" [--var name=value]...
```

`start` 会创建一个项目级任务，并返回第一个阶段的工单。它不推进 step，也不会自动重试加载上下文。

任务标题必须是一行自然英文，长度 5–120 个字符，只能包含 ASCII 字母、数字、空格和连字符，且至少包含一个字母或数字。

`--var` 只用于记录 token 型路由输入：变量名使用小写 snake_case，值是单个非空 token。它不是自由文本输入，也不用于传递复杂链接或文档内容。

#### 继续推进

```bash
awh next
```

`next` 会按以下顺序验证当前 step 的完成标准：

1. file gate：检查要求状态的真实文件或目录。
2. command gate：在指定运行环境中执行命令。
3. workflow script gate：执行工作包内的确定校验脚本。
4. human gate：要求有明确的人工确认或拒绝记录。

全部通过后，`next` 才会按 workflow 声明的条件路由进入下一个阶段；否则返回 `blocked`，并跟随一个可执行的修复指令。

#### 人工确认

```bash
awh approve
awh reject --reason "<reason>"
```

`approve` 和 `reject` 只记录人工决策，不推进任务。

```bash
awh approve --next
```

这是显式的一步式命令，等价于先 `awh approve`，再尝试 `awh next`。它不会绕过任何 gate。

#### 响应协议

所有命令都会返回稳定的 JSON 状态：

- `active`：继续执行当前指令。
- `blocked`：当前 gate 未满足，需要按返回原因修复。
- `done`：任务完成，停止推进。
- `conflict`：项目已有另一个活跃任务。
- `error`：命令、状态或流程评估出错。

`next` 只继续当前活跃任务，不接收别名、标题或任务选择参数。也没有 `awh status` 命令；项目本地的运行状态文件就是诊断接口。

`start` / `next` 等任务命令还会返回 `task.id`、`task.title`、`task.step`、`task.artifactDir`，这些字段就是权威任务上下文。

## Workflow 包

一个 workflow alias 对应一个源码目录，至少包含 `workflow.yaml`：

```text
<workflow-alias>/
  workflow.yaml
  references/   # 可选，详细方法或文档
  scripts/      # 可选，workflow gate 或条件 producer 使用
  templates/    # 可选，产物模板
```

查找顺序：

1. `<project>/.agents/workflows/<alias>/`
2. `~/.agents/workflows/<alias>/`
3. 内置 `agent_workflow_harness/workflows/<alias>/`

AWH 不复制 workflow 包。任务启动时，它会记录源包路径和 `workflow.yaml` 的 SHA-256 指纹；运行期间如果 `workflow.yaml` 指纹变化，CLI 会返回 `error`。

`guide`、gate、human request 和条件 producer 都可以使用有限模板变量：

- `${workflowDir}`：workflow 源包目录
- `${taskDir}`：当前任务的业务产物目录
- `${name}`：`awh start --var name=value` 提交的 token 输入

`workflow.yaml` 使用 v2 schema，整体形如：

```yaml
version: v2
entry: draft
terminal: done
producer_timeout_seconds: 30

steps:
  draft:
    title: Draft
    guide: Draft a concise requirement note.
    gates:
      - id: draft_file
        type: file_exists
        path: ${taskDir}/draft.md
    transitions:
      - to: review
        default: true

  review:
    title: Review
    guide: Decide whether the draft needs another pass.
    condition_producers:
      needs_revisit:
        type: command
        command: "grep -q 'revisit' ${taskDir}/draft.md"
    transitions:
      - to: draft
        when: needs_revisit == true
      - to: done
        default: true

  done:
    title: Done
    guide: null
```

## 核心概念

- **Workflow**：YAML 定义的封闭状态机，包含步骤、路由、gate 和人工决策。
- **Task**：一次目标明确的执行实例，由 task title 和输入变量标识。
- **Step / Work order**：workflow 中的一个阶段；agent 每次只看到当前阶段的工单。
- **Gate**：客观完成标准，常见类型包括文件存在、命令、脚本和人工确认。
- **Human gate**：要求真实人审的 gate，用于把关键决策权交回给用户。
- **Route / Transition**：从一个 step 进入另一个 step 的可验证路径，由条件或 default 明确声明。
- **Runtime state**：CLI 持有的权威运行状态，模型可读但不可写。

## 状态与审计

`awh start` 会建立项目内的 `.workflow-harness/` 目录，用于保存活跃任务、权威状态、历史审计记录和任务产物。

```text
.workflow-harness/
  task.json
  task-artifacts/
  tasks/
```

其中：

- `task.json` 是活跃任务锚点，用于判断当前请求是否属于同一个任务。
- `tasks/<task-id>/state.json` 是权威状态，描述当前 step、输入、路由事实和 visited steps。
- `tasks/<task-id>/history.jsonl` 是 append-only 审计日志，记录有意义的推进结果。
- `task-artifacts/` 是任务业务产物目录，由 workflow guide 使用。

这些状态对模型可读，但 **不可由 agent 写入**。CLI 是控制面状态的唯一写入者。缺少或损坏的状态会被当作 `error` 处理，不会被自动修复或伪造。

## 进一步参考

- [Workflow v2 authoring guide](docs/workflow-v2-authoring-guide.md)
- [Domain Glossary](CONTEXT.md)
- [Architecture Decisions](docs/adr/)
- [Workflow Examples](examples/README.md)
