# 外部对标调研：spec-kit workflow 与 aix devflow

> 调研对象：agent-workflow-harness v1.1。
> 对标来源：github/spec-kit workflow 引擎（源码级实测）、蚂蚁 aix devflow（`ASF-Service-Platform/workflows` 目录仓 schema + 标杆 workflow 实测）、同类开源项目扫描。
> 结论日期：2026-10-22。
> 语雀发布版：《[Agent Workflow Harness 外部对标：spec-kit workflow 与 aix devflow](https://yuque.antfin.com/tianminghui.tmh/pmrwqt/tfle4181yemz2sn0)》。

## 一、核心结论

1. **方向不是坐井观天**：「确定性控制面」是 2025-2026 行业主航道，方法论文撑充分（ThoughtWorks guides/sensors 分层、Anthropic effective harnesses、OpenAI Harness Engineering），外部同构项目密集涌现。
2. **概念也不新鲜**：「YAML 状态机 + 证据门禁 + 暂停恢复」的功能面，已被 github/spec-kit（142k ★）内置 workflow 引擎覆盖，且至少 5 个小型开源项目独立实现了同构思路。
3. **真正的分野在驱动模型**：外部模型互相构成镜像——我们是「agent 开车，控制面当裁判」；spec-kit 是「引擎开车，agent 是每步被拉起的无头子进程」；aix 是「引擎全派发 + worker 内再嵌套子代理」。
4. **差异化组合仍然成立**：agent-blind（模型看不到全图与未来步骤）+ 控制面物理隔离（`~/.workflow-harness/`，模型不可篡改）+ 事件溯源事实源（state 只是投影），未检索到完全对齐的外部实现。
5. **最大落地缺口**：v1 明确排除宿主 Hooks（[ADR-0006](../adr/0006-v1-scope-boundary.md)），当前属"自律性他律"；外部同类已普遍补上 PreToolUse/Stop 物理哨卡。

## 二、生态地图

| 层级 | 项目 | Stars | 一句话定位 |
|---|---|---|---|
| 同构小型 | [AxGord/claude-workflow](https://github.com/AxGord/claude-workflow) | 6 | YAML 状态机驱动 agent，引擎管状态、enforce guards |
| 同构小型 | Mondragondon/claude-code-hooks | 0 | Hook 强制的流程状态机，防自我修改、状态放 /tmp |
| 同构小型 | MohamedRamadanSalah/Agentic-Workflow | 0 | 确定性 Python controller + hooks，evidence-gated bug 修复 |
| 同构小型 | archmax-ai/harness | 3 | 一个 workflow.yaml 既描述又执行，但 own-the-loop |
| 头部主流 | github/spec-kit | 142k | SDD + 内置 workflow 引擎（run/resume/gate/overlay） |
| 头部主流 | ruvnet/ruflo (ex claude-flow) | 78k | "agent meta-harness"，重平台路线 |
| 头部主流 | Fission-AI/OpenSpec | 73k | spec-driven，artifact 契约 + validation enforcement |
| 头部主流 | bmad-code-org/BMAD-METHOD | 54k | Agile AI 全流程，但 enforcement 主要靠 prompt/checklist |
| 内部对标 | aix devflow（ASF-Service-Platform/workflows） | — | 平台化工作流目录仓：引擎 + 审批 + 复盘 + 发行 |

## 三、三种驱动模型对比

| 维度 | agent-workflow-harness | spec-kit workflow | aix devflow |
|---|---|---|---|
| Driver | agent 是 driver，主动调 `wf next` | 引擎是 driver，headless 拉起 agent 子进程 | 引擎是 driver，每个 phase 派发 worker |
| agent 参与方式 | 在场同一会话连续干活 | 每步全新 `claude -p` 子进程 | 每 phase 独立 worker，无用户通道（禁用 AskUserQuestion） |
| 阶段内联执行 | 支持（现状），未来可选 fork | 不支持 | 不支持（`agents:` 必填；`run:` 仅 solo/parallel/pipeline） |
| 人的位置 | 干活现场的同一会话 | 前置 inputs + gate 边界审批 | 话务台（启动/问进度）+ hitl gate 结构化问卷 |
| gate 含义 | 机器验真（file/command），blocked → 修复 → 重试 | 人工审批 pause（gate 步） | 四种门禁：file/command/hitl/llm |
| 状态存放 | `~/.workflow-harness/`（模型不可读写） | repo 内 `.specify/workflows/runs/`（模型可读写） | 引擎侧 + `aix run phase file put/get` 工件库 |
| 事实源 | append-only 事件日志，state 是投影 | state.json 直接写 | 引擎持有 |
| 失败路径 | v1 无（closed-world 单出边） | abort/failed 终态 + resume | `on: success/failed/maxExhausted`，可路由 recovery |
| 防绕过 | v1 缺失（待补宿主 hooks） | 天然免疫（driver 不是 agent） | 平台门禁审批 |

## 四、spec-kit workflow 驱动机制（源码级）

- 调起链：`specify workflow run` → Python 引擎按序执行 steps。
- `command` step = `subprocess.run(["claude", "-p", "<slash command>", "--output-format", "json"], cwd=repo)`，退出码供后续步骤引用（`{{ steps.specify.output.exit_code }}`）。
- 步骤间上下文只有三条接力棒：repo 文件（"repo as memory"）、captured stdout（字节上限、明文落盘、官方自警告 untrusted）、inputs（启动时一次性）。
- **澄清密集任务在引擎模式下失效**：`clarify` 命令是会话式循环（每次一个问题、等用户回答、最多 5 问），headless 子进程无人应答，"答案编码回 spec"断链。澄清只能前置到 inputs 或压缩成 gate 审批。

## 五、aix devflow 关键发现

1. **schema 与 spec-kit workflow 近乎同构**：`phases/on/gates/retry/when/inputs`，但更工程化：四种单键 gate（file/command/hitl/llm）、`retry: {max, fresh}`、`permission: read/edit/full/auto`、`budget`。
2. **每个 phase 必然派发 worker**：`agents:` 必填（backend: auto/cc/codex），`run: solo|parallel|pipeline` 全是派发拓扑；没有"主会话内联执行某阶段"的档位。worker 被 prompt 明文约束"无用户通道——禁用 AskUserQuestion"。
3. **两级隔离**：phase worker（prompt 以 `[orchestrator]` 开头，本身是引擎派的子会话）在 phase 内再 spawn 重活 subagent，纪律是"subagent 回摘要，不回原始 dump"。
4. **人的位置被压缩到 gate**：`hitl:` gate 是结构化问卷（options + onTimeout 默认动作 + timeoutSec），且 **HITL 选项直接驱动状态机转移**（`on: retry-execution: execution / revise-research: research / drop: __end__`）。设计哲学是"HITL 极简：happy path 零阻塞，唯一 HITL 在失败路径，超时自动降级"。
5. **跨阶段产物走控制面 CLI**：`aix run phase file put/get --run-id ${runId} --phase-index N`，与我们的 task-dir + 文件门禁思路同构。
6. **`retry.fresh: true` 的动机值得记录**："每轮起新 worker，对抗合理化自欺"——同一会话修复自己产物时容易为旧结论辩护。

## 六、为什么"选择性内联"是真实生态位（实测数据佐证）

三个交付 bot 的交互构成统计（2026-09-21）：

| Bot | 交互量 | 修正类 | 流程/门禁类 |
|---|---|---|---|
| 架构 Bot | 11 轮 | 4 次 | 7 次 |
| 后端 Bot | 5 turn（恢复期）；自动 run 0 交互 | 2 次 | 3 次 |
| 前端 Bot | 24 决策问题（18 次 AskUserQuestion） | 8 次 | 16 次 |

结论：门禁/推进类可被 hitl gate 结构化吸收；**修正类**（对方案/字段/环境的现场纠偏）错误成本最高、最依赖"上一轮对话还在场"，是引擎派发模型的结构性盲区，也是 in-session 仲裁模型的核心价值。规划的 `execution: main | forked` 混合档位（交互段内联、重活段隔离），是 spec-kit engine 与 aix 均未覆盖的形态。

## 七、下一版吸收清单

| 优先级 | 事项 | 依据 |
|---|---|---|
| P0（gap） | 宿主 Hook 适配层：stop-guard / pre-tool guard，防"agent 干脆不调控制面" | 外部同类标配；Anthropic 建议结构性防御 |
| P1 | failure escape：每步「单 success 出边 + 单 failure 出边」，closed-world 不破 | spec-to-pr 实证：integration failed → pr，pr failed → summarize |
| P2 | `hitl:` gate：结构化问卷 + verdict 作为转移源 + onTimeout 默认动作 | aix recovery 的成熟形态 |
| P2 | `retry: {max, fresh}` schema | aix：fresh=true 抗合理化自欺 |
| P2 | `execution: main \| forked`：阶段级执行档位；forked 时 work order 嵌 orchestrator 纪律块（禁主会话干重活、只读摘要） | spec-to-pr 的 CRITICAL 段是现成模板 |
| P3 | `wf report`：阶段耗时/重试次数/gate 卡点 | append-only 事件日志的免费红利（aix-reporter 对标） |
| 明确排除 | `llm:` gate（概率机器验概率机器） | 违反确定性第一柱，写拒绝 ADR |

## 八、定位收口

- **aix devflow** = 方法论的完整平台化：引擎 + 审批 + 复盘看板 + 目录仓发行，绑定内网平台；全派发模型，人只在 gate。
- **spec-kit workflow** = 开源生态位的可自动化 SDD 引擎：每步冷启动 headless，通用语义丰富（if/while/fan-out/overlay），但 state 在 repo 内可被模型读写。
- **agent-workflow-harness** = host-agnostic 的最小确定性内核：agent-blind + 控制面物理隔离 + 事件溯源，交互段内联是独有档位；补齐 Hook enforcement 后即具备差异化立足点。

## 附：主要来源

- 方法论原文：《驯服自主智能体》（山宇AI库）
- github/spec-kit：`docs/reference/workflows.md`、`src/specify_cli/workflows/step/command/__init__.py`、`src/specify_cli/integrations/base.py`（subprocess 驱动实证）
- ASF-Service-Platform/workflows：`README.md`（schema）、`workflows/business/content/spec-to-pr/workflow.yaml`、`workflows/infra/aix/rfc-driven-dev/workflow.yaml`
- 语雀《自定义 Devflow 最佳实践》（aixcoding/manual/devflow）
- 同类扫描：AxGord/claude-workflow、Mondragondon/claude-code-hooks、MohamedRamadanSalah/Agentic-Workflow、archmax-ai/harness、OpenSpec、BMAD-METHOD、ruflo
