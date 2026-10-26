# Implementation record — three-case validation

## 实现与关键决策

1. **独立沙箱**
   - `docs/workflow-validation/benchmarks/runner.py` 为每个 case、每个重复和每个场景创建独立项目目录。
   - 每个实际步骤使用独立临时 `WF_HOME`，因此：
     - 不会读取或修改真实环境的控制面状态。
     - 不会污染当前 harness 任务 `Deliver three-case harness validation`。
   - `raw-run.tar.gz` 保存了最终临时 sandbox 的完整内容，确保 summary 可向下追溯到原始控制面文件和产物。

2. **对等基线**
   - `skills/static-step.md` 描述完整 Step 1-6 流程。
   - 该 prompt 同时声明文件产物和 `npm test` gate 要求，但没有物理控制面。
   - static 模式由确定性 honest/drift replay 驱动，报告中明确界定其不可外推到所有 agent。

3. **衡量口径**
   - Case A 记录上游 requirement 缺失时 harness 从 design 进入 implementation 的 `blocked`/active/done 状态。
   - Case B 记录真实 `npm test` 退出码、stdout、stderr、gate response、retry 数和最终 terminal 状态。
   - Case C 记录单流程 3 个 work order 的逐 turn 字节数与累积字节数，并将 3 次重复作为稳定性证据单独保存。

4. **证据**
   - 最终证据目录：`results/2026-10-22-final/`
   - Case visibility 目录：`case-a/`、`case-b/`、`case-c/`
   - 最终解读与 limitation：`docs/workflow-validation/REPORT.md`

5. **核心实现保护**
   - 未修改 `agent_workflow_harness/` 中任何核心实现。
   - 根级 `package.json` 仅作为当前 workflow command gate 的最小 `npm test` 转发器，指向 `python3 -m unittest discover -v`。
   - benchmark 自身也没有直接读写 `~/.workflow-harness/` 内部状态，而是使用真实 CLI。

## 测试结论

- Benchmark contract：
  - `python3 -m unittest discover -s docs/workflow-validation/benchmarks -v` 通过 2/2。
- 核心 control plane 回归：
  - `npm test` 通过 44/44，等价于根级仓库原有 Python 单元测试。
- 三组 case 最终运行均由真实 harness gate 驱动；没有通过编辑内部 JSON 或伪造响应取得结论。
