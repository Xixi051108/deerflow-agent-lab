# 本机验证记录

日期：2026-10-18。以下为本次开发的实际验证记录。此前的独立示例已移除；当前代码位于 DeerFlow 的 community 工具目录，通过原有装配入口验证。

## 已通过

在 `backend/` 使用后端锁定环境执行（不调用真实模型）：

```powershell
.\.venv\Scripts\python.exe -B -X utf8 -m pytest tests/test_task_diagnosis_tools.py tests/test_local_bash_tool_loading.py tests/test_lead_agent_model_resolution.py tests/blocking_io/test_task_diagnosis_tools.py -q --tb=short -p no:cacheprovider
```

结果：77 passed。覆盖新增工具输入/合成事实/未知记录、配置动态加载、分组过滤、真实主 Agent 装配与执行、异步文件读，以及相邻已有回归。外部模型使用替身；没有替换工具与编排。

新增 Python 文件的 Ruff 格式/静态检查通过；`git diff --check` 通过；学习文档的相对链接和合成 JSON 已校验。

## 广泛回归发现的问题

为避免重复淹没错误，以下在首个失败时停止，没有声称全量通过。命令需具备正常 pytest 临时目录权限；之前受限环境的 `WinError 5` 属于测试准备失败。

```powershell
.\.venv\Scripts\python.exe -B -X utf8 -m pytest -m "not live" --ignore=tests/blocking_io tests/ -q --tb=short -p no:cacheprovider --maxfail=1
.\.venv\Scripts\python.exe -B -X utf8 -m pytest tests/blocking_io -q --tb=short -p no:cacheprovider --maxfail=1
```

| 集合 | 实际结果 | 首个失败 |
| --- | --- | --- |
| 默认后端 | 1732 passed、30 skipped、3 deselected、1 failed；停止 | `test_bench_sandbox_provider.py::test_boxlite_shim_workaround_retries_after_fixing_permissions`：Windows 上 `st_mode & 0o111` 不成立 |
| 严格 blocking-I/O | 36 passed、1 failed；停止 | `test_channel_runtime_config_store.py::test_runtime_config_store_file_is_owner_only`：Windows 返回 mode 0666，断言要求 0600 |

两个失败均位于未修改的测试/功能，涉及 POSIX 权限位在 Windows 上的语义，需单独调查。尤其运行时凭据存储应检查实际访问控制，不能仅改断言或添加 skip 就声称安全问题解决。本次没有扩大范围改动这些模块。

火绒告警的证据、静态检查与 `-B` 临时处理见 [案例 001](cases/001-skillscan-antivirus-alert.md)。未关闭防护、未添加排除项、未修改扫描器。

## 尚未执行

- 真实模型的 20 场景质量评测、性能实验、远程 CI。
- 用户本人闭卷变更、故障复盘、简历填充或投递。

后续启动阶段已从模板创建根目录 `config.yaml` 并接入已有 DeepSeek 配置，同时创建空 MCP 的 `extensions_config.json`；均被 Git 忽略，新增业务工具保持关闭。用户已在页面创建账号；Gateway health/readiness 均返回 200；浏览器中第一条真实 DeepSeek Agent 回答已确认，后台 run 状态 success。本次没有调用工具，详见 [启动记录与实际链路](LOCAL_RUN.md)。

## 板块三验证补充（2026-10-19）

上文保留早期诊断历史。板块三已实现研究契约、不可变快照与原工具链读写；最终定向组合 **210 passed**（含本块 66 个新用例），开发后严格 I/O **146 passed / 1 skipped**，全局 Ruff check／format 通过。默认离线全集开发前后均通过，开发后选中 17,428 项，**17,071 passed / 357 skipped / 0 failed**；共同收集跳过另列，分母、红绿证据、环境失败和未验证边界统一见 [板块三测试报告](RESEARCH_DATA_TEST_REPORT.md)。

本轮未修改前端、未运行真实模型研究、未构建 Docker、未提交推送。旧的前端、真实模型和用户页面结果不能作为本轮重新验证。
