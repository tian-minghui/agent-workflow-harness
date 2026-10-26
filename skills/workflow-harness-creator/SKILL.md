---
name: workflow-harness-creator
description: 仅当用户明确要求创建或修改 awh / agent-workflow-harness workflow 包时使用（awh 为其缩写）；不随普通任务推进语言自动触发。
disable-model-invocation: true
---

# AWH Workflow Harness Creator

## 目的

把用户明确提供的流程设计转换为可运行的 source-backed workflow v2 包。

本 skill 只做 workflow 创作，不执行业务任务，不复写字写不出来的业务事实。无论输入是用户描述、既有 skill、既有 workflow、需求文档还是系统文档，都使用同一套创作协议；不要按输入来源拆成不同模式。

写作 schema 时先读 `docs/workflow-v2-authoring-guide.md`。方法论按需读取：

- `references/workflow-authoring-contract.md`：通用创作协议
- `references/artifact-typing.md`：按真实产物决定 md / json / state
- `references/gate-design-contract.md`：按阶段完成标准设计 gate
- `references/clarification-protocol.md`：遇到硬阻塞时先向用户澄清

## 触发边界

- 必须由用户显式请求创建或修改 workflow 包，例如“创建一个 workflow”。
- 用户只是在推进当前任务、提到 workflow 或请求 `awh next` 时，本 skill 不触发。
- current task 的 runner skill 负责任务执行，两个 skill 不互相替代。

## 目的地与授权

1. 默认输出到 `<project>/.agents/workflows/<alias>/`。
2. 只有用户明确要求跨项目复用时，才输出到 `~/.agents/workflows/<alias>/`。
3. 拒绝写入 built-in workflow catalog；请记录 reason 并建议通过产品 release 修改。
4. 新项目本地包可在这次显式请求中直接创建。
5. 已存在同名包时，先列出 alias、目的地以及将被创建或修改的每个文件，并等待用户批准；未获批准不得覆盖。

## 创作协议

无论输入来自哪里，先按以下顺序推进：

1. **收集证据**
   - 提取用户目标、流程步骤、产物、条件、人工动作和不确定点。
   - 有既有材料时以既有材料为证据；没有时显式标记 assumption / unclear。
2. **建立阶段契约**
   - 在写 workflow 之前先把流程整理成阶段矩阵：输入、输出、完成标准、适配 gate。
   - 阶段名必须保留真实业务语义，不要因为用户描述或已有 skill 就限死成同一种目录或产物。
3. **产物类型先行**
   - 按真实阶段语义选择 Markdown、JSON、YAML、状态或外部引用。
   - 不默认“每个阶段都生成 stage Markdown”。
4. **沿 contract 设计路由**
   - 先定真实业务主链路，再决定是否需要 condition producers、backedge 或 default。
   - 条件 producer 必须输出真实 scalar，不做模型自行推断。
5. **明确 gates**
   - file_exists 只放在真的是契约产物的文件上。
   - workflow_script 用于校验状态、schema 和真实链路。
   - human gate 只用于真实须由用户评阅或选择的阶段。
   - audit 不新增业务阶段，只作为终端前的 final validation。
6. **匹配子依赖**
   - 有可替换 skill/generator/provider 时，只保留驱动字段，不绑定默认实现或固定模板。
   - 不确定的路径和正文留空，不要硬造。
7. **再开始生成包**
   - 生成 `workflow.yaml` 时必须遵循 v2 schema。
   - guide 详细但只描述当前阶段；复杂方法写在 references。
8. **验证链条**
   - 必须运行 `awh validate <workflow-alias>`。
   - 若可能，至少加入一条真实 smoke path 或阶段级校验例子。
9. **必要时澄清**
   - 在生成包之前，若目标、阶段边界、产物形态、路由条件或 gate 标准仍不清，先发澄清卡。
   - 不要继续创建或修改 workflow。
   - 收到用户答案后，再返回创作流程，不要重复追问同一问题。

## 创作红线

- 不为阶段整齐硬造统一文件名。
- 不用空正文模板填充不存在的产物。
- 不为 JSON/状态阶段再生成假骨架 doc。
- 不为路径不确定的产物硬造目录。
- 不为已有 skill 强制“迁移成 workflow”。
- 不为还没用户描述的阶段补充新业务模型。
- 不为回退或不确定的步骤硬造默认过渡。
不走 `awh validate` 前不得宣称完成。

不修改 `.workflow-harness/`、`task.json` 或任何 active task state/history。

## 创作契约

- `workflow.yaml` 必须声明 `version: v2`，且不允许顶级 `transitions`。
- 每个非 terminal step 必须包含 `guide`、可选 `gates`，以及非空 `transitions`。
- 每个候选 transition 只能写 `to`，并只可选 `when: <condition_variable> == <literal>` 或 `default: true`。
- 条件变量使用小写 snake_case；literal 是 ASCII token；`true`/`false` 按 Boolean 比较，其他值按精确字符串比较。
- 需要运行时判断时，使用当前 step 的 `condition_producers`；同一个条件变量在全 workflow 至多只能有一个 producer。
- `workflow_script` producer 必须输出一行 scalar；`command` producer 只能表达 Boolean。
- 需要较重的有界检查时，写入顶级 `producer_timeout_seconds`（1–300）。
- producer script 和 package resource 必须留在 workflow 包内；project args 必须是安全的 project 相对路径。
- 模板变量只允许 `${workflowDir}`、`${taskDir}` 和 lowercase snake_case start input；替换范围是 guide、file path、command、human request/evidence/project arg，以及 producer command/project arg。
- 模型生成的业务产物默认使用 `${taskDir}/...`；源码、测试和配置仍写在项目原位置。
- gate 不要求一次性写出所有阶段信息；不存在的路径或用户还没提交的内容必须留空或显式标注 uncertain。
- closed-world graph 必须可从 entry 到每个 step，且每个非 terminal step 到 terminal 有静态可达路径；拒绝 self-loop / duplicate target / duplicate default。
