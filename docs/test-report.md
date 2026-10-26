# Test report — three-case validation

## 测试范围与方法

本实验使用：

```bash
python -m unittest discover -s docs/workflow-validation/benchmarks -v
python -m unittest discover -v
```

本次任务将 `npm test` 作为 workflow command gate。原仓库没有根级 `package.json`，首次 gate 被真实阻断；随后新增最小 `package.json`，将 `npm test` 转发到 `python3 -m unittest discover -v`，gate 才通过。Benchmark 自身由 `python -m unittest discover -s docs/workflow-validation/benchmarks -v` 覆盖。

## Benchmark 测试结果

`docs/workflow-validation/benchmarks/test_run_cases.py`

- 建立的测试独立运行点：2 个
- 最终结果：2 passed
- 覆盖面：
  - 静态 skill 必须包含完整 Step 1-6 与 `npm test` gate 语言。
  - 三个 case 均可真实生成 summary 和最终 REPORT。
  - Case A harness 不得缺挡前置产物，static 模式须能展示 agent 自我声明风险。
  - Case B harness 在实际 command gate 失败时不得转为 done。
  - Case C harness 累积输入需小于 static 全量 prompt。
  - 总结论必须给出 `demonstrated` 或 `not demonstrated`，不能自定义无法解析的结论。

## 核心回归结果

`npm test`

- 原有覆盖面：44 个测试，包含 agent-blind engine、command gate、workflow bundle、task identity 和 gate failure 输出。

- 结果：44/44 passed。

## 核心实现保护

本次实验新增文件均位于 `docs/` 和 `docs/workflow-validation/`，未修改 `agent_workflow_harness/` 内任何核心文件。

静态 skill prompt 中包含 `npm test`，因为它是测试要求的通用门禁语言；本 benchmark 实际使用等价的本地 Python command gate (`python3 check.py`) 作为 `npm test` 对应命令，并在 runner 中显式保留该映射。

最终 benchmark 结果已冻结在 `docs/workflow-validation/results/2026-10-22-final/`。

## 失败与边界

- 首次 `npm test` gate 按预期失败，原因是根级 `package.json` 缺少 `test` script；该失败已记录为 gate enforcement 证据。
- 补齐 `package.json` 后重跑，`npm test` 通过 44/44，与根级 `python3 -m unittest discover -v` 结果一致。
- 没有引入核心实现变更。
- `runner.py` 通过真实 CLI 获得异常状态；没有直接读写控制面内部状态。
