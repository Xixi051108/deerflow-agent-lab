# 第一课：把业务查询工具接入 DeerFlow

## 要解决的问题

DeerFlow 的模型并不知道你定义的业务任务状态。直接询问“任务 T1001 为什么失败”，回答可能缺乏事实依据。我们给它两个只读工具，使其可以先查询再回答；所有数据都是合成样例，不连接公司系统。

验收：T1001 查询到 failed/E_TIMEOUT，再查询到“上游请求超时”和排查建议；T9999 不存在、E_UNKNOWN 未收录时，工具返回 `found: false`，模型应说明证据不足。建议不能被说成已执行的修复。

## 第一步：只读一个测试

打开 `backend/tests/test_task_diagnosis_tools.py` 的 `test_failed_task_returns_synthetic_evidence`。它有三部分：导入工具、传入 `task_id`、断言预先定义的事实。预期来自合成数据需求，不是复制被测函数的计算结果。

在仓库根目录 PowerShell 中运行（要求已按 `backend/uv.lock` 安装后端环境）：

```powershell
cd D:\deerflow-agent-lab\backend
.\.venv\Scripts\python.exe -B -X utf8 -m pytest tests/test_task_diagnosis_tools.py::test_failed_task_returns_synthetic_evidence -q -p no:cacheprovider
```

`-B` 不写 `.pyc` 缓存，`-X utf8` 使中文日志可读。它们不关闭安全软件。关于本机的火绒告警，见 [问题案例 001](cases/001-skillscan-antivirus-alert.md)。

如果测试在 setup/teardown 报临时目录权限错误，先处理终端/执行环境权限；这不是工具返回值错误，不应修改断言来掩盖它。

## 第二步：理解新增代码

打开 `backend/packages/harness/deerflow/community/task_diagnosis/tools.py`：

1. `TaskStatusInput` 定义参数格式；非法路径、非字符串和多余参数被拒绝。
2. `@tool("query_task_status", ...)` 把函数包装成模型可选择的工具对象。
3. `run_file_io(...read_text, encoding="utf-8")` 在专用线程读取固定文件，不阻塞异步事件循环；模型不能指定文件路径。
4. `found` 区分有证据和无记录；`data_source` 提醒模型和读者这是合成数据。
5. 第二个工具只解释已查询到的错误码，返回 `suggested_action`，不执行操作。

对照 `tasks.json` 和 `errors.json`：T1002 是权限不足，T1003 成功，T1004 运行中，T1005 有未收录的错误码，T1006 失败但没有错误码。不要把所有非成功状态都解释为超时。

## 第三步：接入原有配置

在你自己的根目录 `config.yaml` 中，将下列条目分别合并进已有 `tool_groups`、`tools` 列表，避免重复同名项。不要替换整个配置，不要把密钥写进代码。若尚无配置，先按根目录 Quick Start 完成 `make config` 或等价配置步骤。

```yaml
tool_groups:
  # 保留已有组
  - name: task-diagnosis

tools:
  # 保留已有工具
  - name: query_task_status
    group: task-diagnosis
    use: deerflow.community.task_diagnosis.tools:query_task_status_tool
  - name: lookup_error_code
    group: task-diagnosis
    use: deerflow.community.task_diagnosis.tools:lookup_error_code_tool
```

模板 `config.example.yaml` 提供同样的注释项，默认不启用。使用 Custom Agent 时，其 `tool_groups` 白名单也需要包含 `task-diagnosis`。

重新启动 Gateway 并新建一段聊天，以避免沿用已创建的 Agent 图。继续使用原来的模型配置和 `.env`；工具本身不需要新密钥。当前改动没有替你生成或改写根目录 `config.yaml`，没有启动前端或发起真实模型请求。

在聊天中输入：

> 请使用 query_task_status 查询合成任务 T1001；若有错误码，再调用 lookup_error_code。根据工具结果解释原因，标明这是合成数据，不要声称已修复。

检查聊天中的两次工具调用及各自结果，再检查最终回答。不只看回答是否“像正确答案”。随后尝试 T9999、T1005、T1006，观察模型是否明确承认证据不足。真实模型可出现错误，这正是后续评测需要发现的问题。

## 第四步：区分三层测试

在 `backend/` 运行：

```powershell
.\.venv\Scripts\python.exe -B -X utf8 -m pytest tests/test_task_diagnosis_tools.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B -X utf8 -m pytest tests/blocking_io/test_task_diagnosis_tools.py -q -p no:cacheprovider
```

| 测试 | 真实部分 | 替身/未覆盖部分 |
| --- | --- | --- |
| 工具输入与结果 | 参数校验、JSON 读取、未知记录 | 没有模型决策 |
| 配置加载与分组 | `get_available_tools()`、真实动态导入及执行 | 没有 Gateway/UI |
| 主 Agent 集成 | `assemble_lead_agent()`、原有中间件和图、两个工具 | 只替换外部模型；脚本化决策不证明真实模型诊断质量 |
| 严格阻塞检测 | 工具异步执行和文件 I/O | 不测网络模型延迟 |

默认 CI 已收集 `backend/tests/` 和 `tests/blocking_io/`，这些测试自动进入现有流水线，无需为本课另造一套 CI。

## 第五步：你独立发现并解决一个问题

先不要扩展功能。在练习分支中将 T1001 的错误码误改为 E_PERMISSION，预测会失败的断言，再运行第一步的测试。记录输入、预期、实际、根因，恢复数据后再次运行。你的报告应注明这是人为注入的学习故障。

然后独立添加一条 cancelled 任务：先写预期，再改数据，验证不会被错误地归因为失败。最后闭卷说明：工具由谁选择、由谁执行、配置如何生效、哪些测试不能证明真实模型正确。

当前第一课完成的是工具与运行装配的参考实现。页面上的真实模型验证、本人独立变更、20 场景评测和求职材料仍需要按任务卡实际完成。
