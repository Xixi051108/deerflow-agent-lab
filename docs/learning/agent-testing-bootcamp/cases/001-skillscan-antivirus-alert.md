# 问题 001：火绒拦截 SkillScan 的 Python 字节码

日期：2026-10-18。类型：开发环境与防护兼容性问题；尚无证据将其判为业务缺陷或恶意代码执行事件。

## 发现与证据

用户提供的火绒记录：

- 威胁名：`HEUR:Trojan/Python.ReverseShell.f`；病毒 ID：`25B49D93CA5A73B8`。
- 文件：`backend/packages/harness/deerflow/skills/skillscan/__pycache__/orchestrator.cpython-312.pyc`。
- 操作结果：已处理，删除文件；记录的操作类型为“执行”。
- 操作进程：`D:\index\python.exe`，命令行为 `"D:\index\python.exe" -`，父进程为 PowerShell。

进程命令行只说明 Python 从标准输入接收脚本，不能仅凭它证明执行了反向 Shell；当前证据也不足以证明整台机器安全。

## 定位过程

1. 暂停广泛测试，未恢复或重新执行被删除的 `.pyc`。
2. 定位对应源码 `skills/skillscan/orchestrator.py`，`git diff HEAD` 无改动。
3. 源码 Git blob 为 `be09e74aa5177731155b02a76f61da13f06d7ea8`，与本地保存的上游 Git tree 清单匹配。该清单对应固定提交 `345f08be00c8a9495079b732a39b46aa9af1584e`，来源与先前校验见 `docs/UPSTREAM.md`。
4. 源码 SHA-256：`d7b084ceff7ed413e6c7c086b5b9e66330d46c7ba69d69a0f138f61b5b9002b9`。
5. 只进行源码与 AST 静态检查，未导入目标模块进行该项分析。反向 Shell 名称在检测规则中，未发现直接 `exec/eval/os.system` 或 `subprocess/socket/requests/httpx/urllib.request` 执行/网络调用。
6. 既有引入记录记载，此扫描模块和对应测试源码曾触发相同启发式告警。这支持“安全扫描规则可能误触发特征”的判断，不能单独证明误报。AST 检查也不覆盖全部依赖或其他代码行为。

## 最小处理与验证

保留防护及 SkillScan 检测逻辑，保持被删除缓存不恢复。在开发测试命令中使用 `python -B`，不生成可再生的字节码缓存；不关闭火绒、不添加排除项、不改写或混淆检测规则。

实际执行 `python -B -m pytest tests/test_task_diagnosis_tools.py::test_failed_task_returns_synthetic_evidence -q -p no:cacheprovider` 的等价最小测试通过；随后文件存在性检查为 `False`。后续两工具、配置装配和主 Agent 集成测试也已在 `-B` 模式通过。

这验证了“不依赖该 `.pyc` 也能继续最小开发测试”，没有验证火绒在所有场景不再告警。防护仍启用；若出现源码被删除、其他路径或不同威胁名，需要重新调查。厂商尚未确认误报，默认 Python 缓存模式尚未复测。

## 另一个独立问题

早先全量测试在受限执行环境中出现 pytest 临时目录 `WinError 5`。它发生在测试 setup/teardown，不能算工具断言失败。具备正常临时目录权限的执行环境下，新工具及集成测试通过。全量测试曾中断，不宣称全量通过。

## 学习验收

能解释：告警事实与根因假设的区别；源码来源核验与运行时安全的区别；缓存与源码的区别；为什么本次无需删除安全扫描模块；为什么使用环境处理方式不能宣称修复了恶意代码漏洞。
