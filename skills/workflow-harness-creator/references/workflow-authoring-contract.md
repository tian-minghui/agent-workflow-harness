# Workflow Authoring Contract

## 定位

本协议用于把任意流程输入转成 source-backed workflow v2 包。

适用输入可以是：

- 用户描述的流程
- 既有 skill
- 既有 workflow
- 需求文档或系统文档
- 混合材料

协议核心不是按输入来源分流，而是提取共同原则。

## 通用原则

1. **一个目标，一条状态链**
   - 一个 workflow 只承载一个清晰目标。
   - 不因输入来源不同创建不同模型。
   - 若目标复杂，先拆成阶段，而不是拆成另一个运行时。

2. **Contract first**
   - `workflow.yaml` 前先确定每个阶段的输入、输出、完成标准和路由。
   - gate 必须对应阶段真实产物，而不是“常用文件名”。
   - 生成文件之前必须知道这个文件用于什么、何时算完成、如何被校验。

3. **Evidence first**
   - 用户提供 skill、既有文档或系统资料时，把这些当作证据，不当作创作模式。
   - 只有用户描述时，先整理目标、阶段和边界；不确定处显式标记 assumption / unclear，不要直接落文件。
   - 所有推论都必须要有明确来源：用户描述、源文档、可见实现或既定契约。

4. **Clarify before authoring**

   在写 `workflow.yaml` 之前，如果目标、阶段边界、产物形态、路由条件或 gate 标准仍不清，先按 `clarification-protocol.md` 向用户澄清；不要默默估计后继续生成文件。

5. **No fabricated output**
   - 不为了“阶段完整”而生成空洞文档。
   - 不默认每个阶段都是一份 stage Markdown。
   - 不为不知道的内容编正文章节。
   - 不为路径不确定的产物硬编码目录。
   - 不为可替换生成器绑定固定模板。

6. **Package is the product**
   - workflow 的产出不是长文档，而是可运行包：`workflow.yaml`、references、scripts、templates。
   - guide 表达当前阶段工作；不为模型复述完整图。
   - 复杂方法论下沉到 references，不堆进 SKILL.md。

## 通用流程

### 1. 收集证据

先收集可用的材料，不因来源分模式。记录：

- 用户目标
- 输入来源
- 阶段边界
- 关键动作
- 明确产物
- 条件分支
- 需要人工确认的点
- 不确定项

### 2. 建立阶段契约

按表格拆解：

| 阶段 | 输入 | 输出 | 完成标准 | Gate |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

阶段名应继承输入材料里的真实业务语义，不要为了整齐重命名成 `step1`。

### 3. 归类产物

先看阶段真实产生什么，再决定文件类型：JSON、YAML、Markdown、状态文件、外部指针。

不要用“每个阶段一份 Markdown”作为默认。

### 4. 设计路由和 gates

根据完成标准设计：

- file gate：只用于确认某一文件是阶段契约
- workflow_script gate：校验 schema、状态和链路
- condition_producers：表达真实条件分支
- human gate：只用于人需要看内容并确认的阶段
- audit gate：用于终端前的链路复核

### 5. 生成包

再开始写包；不要在证据不足时直接着手写 YAML。

### 6. 验签

至少跑 `awh validate`，必要时补充 stage-level smoke test。

## 通用反模式

- 为了完成度硬造说明文档
- 用通用 section 名称（范围/主体/结论）替代真实业务内容
- 把状态阶段硬造成 Markdown
- 把 gate 覆盖不了的事实说成已完成
- 绑定默认生成器，却不提供替换字段
- 在同一 workflow 中混用多种文档模型
- 为了“统一”而丢失原流程语义
- 拆出不属于流程的额外业务 stage

## 完成判定

一个 workflow 创作任务只有在满足下面条件才算完成：

1. 阶段路径真实、可解释
2. 每阶段产物形态明确
3. 每条路由有真实语义
4. 每个非空 gate 都可执行
5. 人工 gate 只挂在真实审查阶段
6. 没有虚构路径、虚构模板或占位正文
7. `awh validate` 返回 valid
8. 如果可能，至少通过一次 smoke path
