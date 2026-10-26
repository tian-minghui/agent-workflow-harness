# CodeReview

## 问题清单

### [P1] CR-1 — `active` 与 `done` 被错误合并

- 原问题：`harness_done` 曾在 CLI 返回 `active` 时计为完成，破坏了 README 定义的状态契约。
- 修复：增加独立 review→done 终态推进；`harness_done` 只在最终 response 为 `done` 时为 true。
- 状态：已修复

### [P1] CR-2 — Case A 场景未证明上一阶段产物缺失

- 原问题：初始 case 从 requirements stage 开始，没有体现“design阶building已有但 requirements 缺失”的漂移。
- 修复：改成 design→implementation workflow，design entry 的 gate 要求 `docs/requirements.md` 存在；`wf next` 在缺失时必须 blocked。
- 状态：已修复

### [P1] CR-3 — static baseline 依赖 hard-coded index

- 原问题：static 模式直接根据 repetition 编号写完成声明。
- 修复：引入 honest/drift replay 和 artifact-state decision model；依据 `requirement_exists`、`design_exists`、`conversation_drift` 生成结论，并在报告中保留不可外推限制。
- 状态：已修复

### [P1] CR-4 — Case B 没有记录真实命令输出

- 原问题：实验只保存 gate id 和 summary，没有 exit code/stdout/stderr/retry 数据。
- 修复：每个 pass/fail/repair 均直接运行 `npm test` 并保存 exit code、stdout、stderr、gate response、retry 数和最终状态。
- 状态：已修复

### [P1] CR-3B — gate 终态证据不足

- 原问题：`harness_done` 曾把 `active` response 视为验收完成。
- 修复：workflow 增加 review gate，pass 和 repair 均必须推进到 review，再第二次 `wf next` 到 `done`；实际 terminal status 已写入 raw JSON。
- 状态：已修复

### [P1] CR-5 — Case C 重复次数与阶段成本混淆

- 原问题：实验曾把 3 次重复的 work order 混为单流程成本，并只给出总量。
- 修复：单流程 work order 数固定为 3；分别记录 per-turn bytes、单流程 cumulative bytes、3 次重复表现、token estimate。
- 状态：已修复

### [P1] CR-6 — raw evidence 不足且历史数据不完整

- 原问题：旧 r1/r2 summary 与 prompt 版本不一致，缺少完整原始 sandbox。
- 修复：仅保留最终版本；新增 `raw-run.tar.gz` 冻结完整 `WF_HOME`、project artifacts 和 workflows。
- 状态：已修复

### [P1] CR-7 — 缺少 `REPORT.md` 和三个 case 目录

- 原问题：README 曾是 placeholder，缺少 final report、case visibility、raw evidence 和复现说明。
- 修复：新增 `case-a/`/`case-b/`/`case-c/`、`results/2026-10-22-final/`、`REPORT.md` 与 README 入口。
- 状态：已修复

### [P1] CR-8 — root `package.json` 疑似超出实验目录边界

- 原问题：root npm wrapper 未解释，容易被视为 scope creep。
- 修复：保留最小 `npm test` 转发器并明确记录它是 workflow command gate 的必需接口；要求文档说明它不属于核心实现。
- 状态：已修复

### [P1] CR-9 — Case B 场景布尔参数与 JSON 结果存在数据簇/重复

- 原问题：两个 boolean 参数到处传递，summary 三次重复同一 scenario 数据。
- 修复：引入 `CaseBInput` dataclass，summary 只保留 pass/fail/repair 三个 run 列表。
- 状态：已修复

### [P1] CR-10 — 实验文档存在 ambiguous/corrupted fragment

- 原问题：design/tasks/REPORT 中出现过自生成噪声。
- 修复：已重写对应段落，并用 grep 为清理后的文档建立检查点。
- 状态：已修复

## 结论

- 发现问题数：11
- 已修复问题数：11
- 未修复问题数：0
