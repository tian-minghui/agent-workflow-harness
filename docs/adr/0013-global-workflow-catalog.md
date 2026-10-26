# Global workflow catalog

V1.1 will resolve workflow aliases through a global catalog owned by the control plane rather than through aliases stored in the project repository. The agent-facing start command will therefore accept an alias such as `frontend-delivery`; it will not expose or receive a workflow YAML path. Built-in and installed workflows live in the control-plane catalog, while project-specific alias overrides remain a future extension.

升级说明：除了单文件 YAML，别名也可以指向一个目录包。目录包必须包含 `workflow.yaml`，并且可以携带 `resources/` 运行资产。控制面在启动时把整个目录包复制进任务快照，保证运行期与源目录解耦。
