# 研究范围校验与确认约束：测试报告

日期：2026-10-19。工作区：`D:\deerflow-agent-lab`。范围：板块一独立业务规则。

## 结论

本次规则模块的定向组合验证 **95 passed**：93 个范围规则用例、1 个新增严格 blocking-I/O 用例、1 个已有 harness 依赖边界用例，耗时 6.05 秒，pytest 退出码 0。

Ruff 检查与格式检查通过。完整严格套件未全绿；默认离线套件的最终状态见下表，不能用定向验证代替全量回归通过。

这是离线程序规则验收，不证明聊天确认卡、ThreadState、真实检索、模型决策或最终报告已接通。运行上限只做声明与校验，尚未实际控制研究循环。

## 环境与实际执行

Windows，Python 3.12.12，pytest 9.0.3，Pydantic 2.13.3；使用既有 `backend/.venv`，未安装新依赖。运行前设置 `PYTHONUTF8=1`，Python 使用 `-B`。

下列命令均从 `backend` 目录执行，解释器为 `.\.venv\Scripts\python.exe`：

| 检查 | 实际结果 | 解释 |
| --- | --- | --- |
| `-B -m pytest tests/test_research_scope.py -q --tb=short` | 93 passed，5.62 秒 | 规则测试单独通过 |
| `-B -m pytest tests/blocking_io/test_research_scope.py -q --tb=short` | 1 passed，2.22 秒 | 沙箱外执行，保留真实严格检测器，未跳过检测 |
| `-B -m pytest tests/test_research_scope.py tests/blocking_io/test_research_scope.py tests/test_harness_boundary.py -q --tb=short` | 95 passed，6.05 秒 | 最终组合验证，沙箱外执行 |
| `ruff check packages/harness/deerflow/agents/research tests/test_research_scope.py tests/blocking_io/test_research_scope.py` | All checks passed | 只检查本次 Python 文件 |
| `ruff format --check`，同上路径 | 4 files already formatted | 含空的包标记文件 |
| `git diff --check` | 退出码 0 | 检查已跟踪文件的 diff；新增 Python 文件另由 Ruff 检查 |
| 执行 `RESEARCH_SCOPE.md` 中的 Python 示例 | Documentation workflow: passed | 实际构造确认摘要、确认放行、修改后再次阻止；不访问网络 |
| 默认离线全量：`-B -m pytest -m "not live" --ignore=tests/blocking_io tests/ -q --tb=short` | 600.02 秒保护超时，未完成；末次完整进度行为 51%，此前已出现多项失败 | `timed_out=true`，pytest 退出码未取得；没有最终统计，不能报告全量通过率 |
| 严格全量：`-B -m pytest tests/blocking_io -q --tb=short` | 16 failed，128 passed，1 skipped，20.41 秒 | 退出码 1；失败详情见下节 |
| 严格全量加 `--basetemp=D:/deerflow-agent-lab/.deer-flow/t` | 5 failed，139 passed，1 skipped，28.40 秒 | 使用预先确认不存在的仓库内短临时目录，仍未全绿 |
| 仅独立执行残留 5 个既有严格用例 | 5 failed，7 deselected，6.07 秒 | `Research module imported: False`，未导入研究模块也可复现 |
| 上传前联合验证：范围规则、合成诊断工具、两者严格 I/O 及 harness 边界 | 112 passed，11.36 秒 | 用户授权上传后执行；不改变上述全量回归未通过的结论 |

修改前的默认／严格基线均已启动，但在受限环境长期无新输出后中止，未取得完整结果。修改后在沙箱中重跑两套选择，均在 120 秒保护上限终止，属于“未完成”，不是通过率结果。不存在可用的完整修改前全绿基线，不能据此宣称全量回归无新增失败。

## 覆盖内容

| 规则组 | 用例数 | 主要覆盖 |
| --- | ---: | --- |
| 用户带练场景 | 2 | 保存模糊草案、缺少目标；补齐目标后继续指出候选边界缺失 |
| 购买预算 | 12 | 缺失／不限、精确小数、零和相等端点、上限／区间、负值、布尔值、非有限值与结构冲突 |
| 完整性、默认与字段类型 | 24 | 显式待定不被默认覆盖、市场与日期、价格口径、交付／来源／运行限制、未解决歧义、开放品类 |
| 候选边界 | 6 | 指定比较、允许发现、起始名单、数量不匹配、重复或互相排斥的对象 |
| 确认闭环 | 12 | 完整不等于已确认、摘要／快照、明确动作、研究／版本／请求绑定、拒绝、旧请求与有效重复确认 |
| 修改与状态可靠性 | 27 | 21 类实质变更、无变化／空白规范化、改回历史值、过期写入、非法替换、嵌套冻结、可信 JSON 恢复 |
| 辅助方法与完整离线流程 | 10 | 建议错误类型、指定对象无需重复品类、数字日期拒绝、身份缺失、冲突记录，以及完整范围变更再确认流程 |
| 新增严格 I/O | 1 | 事件循环内执行确认、摘要、JSON 恢复与无变化替换，无阻塞 I/O |

合计为 **94 个本模块用例**；最终组合结果额外包含 1 个已有 harness 边界测试。各轮重复执行的 passed 数不能累计成独立用例数。

## 发现、定位与修复

1. 首轮测试出现 `ModuleNotFoundError`，说明模块尚不存在；新增基础模型与完整性接口后，结果为 `1 passed`。
2. 第二轮测试出现 `1 failed, 1 passed`：`issues=()` 导致过早返回可请求确认。补充候选发现权限与数量检查后，结果为 `2 passed`，并经重新运行核实。
3. 后续按范围／确认／修改的公开接口先加入测试，分别观察缺少预算字段、`with_defaults`、候选名单、确认接口与 `revise_scope` 的失败，再实现对应能力。预算阶段实际观察 4 failed / 8 passed，随后整组通过；不能把最初因额外字段被拒绝而通过的负例当作预算规则已经实现。
4. 最后边界检查实际出现 5 failed / 2 passed：错误建议类型被 `list(...)` 拆解、`None` 引发 TypeError、指定对象仍被要求补品类、数字 0 被当作日期时间戳。修复方式为先验证调用方输入、让明确名单满足对象条件、拒绝数字日期；回归至 93 passed。
5. Ruff 首次发现两个导入排序问题，已仅在改动文件中修复并完成最终检查。

## 全量回归限制与失败分析

### 受限环境中的异步初始化

新增严格用例最初停在 pytest fixture setup，而非业务函数。实际 faulthandler 栈位于：

`socket.accept → _fallback_socketpair → asyncio.proactor_events._make_self_pipe → pytest_asyncio fixture`

在沙箱外重跑同一新增用例，严格检测器保持开启，得到 1 passed；最终组合验证也通过。不能将沙箱中卡住或中止的运行记为通过。

### 完整严格套件

初次沙箱外全量为 16 failed / 128 passed / 1 skipped：

- 3 项 `test_channel_runtime_config_store.py` 权限断言：Windows 返回模式 `438`（`0o666`），测试期待 `384`（`0o600`）。
- 1 项 `test_integrations_router.py`：缺少 `lark-cli`，得到 HTTP 404。
- 12 项项目文档／回收站测试：默认临时目录下出现 WinError 206 等路径错误。

使用较短临时目录后，11 项原路径失败通过；剩余 5 项为上述 3 项权限、1 项 Lark CLI，以及 `test_conversion_publish_path_dispatches_off_the_loop`。最后一项在转换临时文件写入时出现 FileNotFoundError，随后断言缺少 `content`；不能仅凭这个结果断言已确定所有路径问题的根因。

这 5 项另行独立执行，结果 5 failed / 7 deselected，并检查到 `Research module imported: False`，说明不依赖本次研究模块的导入也能复现。它们位于本次未修改模块；本次不调整平台权限策略、不安装 Lark CLI、不修改转换逻辑、不跳过失败用例，也不声称已修复这些问题。

### 默认离线全量

沙箱外运行在 600.02 秒达到本次验证的外部保护上限，最后一个完整进度行为 51%，没有 pytest 最终汇总。运行中已观察到多项 `F`，但超时前没有打印具体失败详情，不能把这些失败一概归因于平台或声称与本次改动无关。需在后续独立回归中完成定位。

超时元数据保存在 `after-offline-host.json`，其中 `timed_out=true`、`exit_code=null`。外层日志脚本成功保存元数据，不代表 pytest 通过。这是测试执行的保护上限，不是研究 Agent 的产品默认预算。

原始运行日志保存在忽略目录 `.deer-flow/local-dev/research-scope-verification/`：`baseline-*.log`、`after-offline.log/.json`、`after-blocking.log/.json`、`after-offline-host.log/.json`、`after-blocking-host.log/.json`、`after-blocking-short-temp.log`、`unrelated-failures-isolated.log`。报告列出的定向验证还可从本次工具执行记录核对；本地日志不作为需提交的功能文件。

## 未覆盖与下一步

- 未接真实用户回答、认证、ThreadState/checkpoint、HTTP/SSE 或 UI。JSON 恢复只证明序列化与范围绑定一致。
- `ResearchScopeSession` 只可读取可信应用状态；外部伪造的一整套互相匹配的状态不能由此模块鉴权。模型不能自行创建确认记录。
- `expected_version` 是快照版本检查，不是数据库原子并发控制；下一块需要在写入边界实现。
- 不判断自由文本约束的任意语义矛盾，不验证市场上必然有合适候选，不评价真实模型研究质量。
- 时间和工具调用数是声明值；尚未接入实际消耗控制。测试中的 120 秒／6 次等数值是合成样例，不是产品默认值。
- 下一块接入确认卡、可信回答、线程持久化和真实研究动作拦截后，再做编排与端到端验收。

未构建 Docker；提交与推送状态以实际 Git 记录为准。
