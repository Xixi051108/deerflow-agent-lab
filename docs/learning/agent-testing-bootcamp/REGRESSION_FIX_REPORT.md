# Windows 全量回归修复记录

日期：2026-10-19。环境：Windows、Python 3.12、本机已有 DeepSeek 配置。

## 验证范围与状态

覆盖后端默认离线测试集（排除 live 与严格 I/O 目录）、独立严格 I/O 全量、后端 Ruff 和前端 lint／类型检查。默认离线集使用仓库已有的两个时长分片，合起来覆盖完整集合；真实模型与真实网络研究不在本轮范围内。

| 检查 | 实际结果 |
| --- | --- |
| 本轮修复前严格 I/O 全量 | 18 failed / 127 passed / 1 skipped；其中两项超时测试额外暴露启动时序问题 |
| 首次默认离线全量 | 运行至约 45% 后，因安全软件连续告警主动停止；没有最终汇总 |
| 首次完整离线分片 1 | 21 failed / 8480 passed / 185 skipped，760.99 秒 |
| 首次完整离线分片 2 | 24 failed / 8491 passed / 173 skipped，793.29 秒 |
| 最终严格 I/O 全量 | **145 passed / 1 skipped**，19.09 秒 |
| 网页提取、MCP 与消息合并组合 | **85 passed**，47.46 秒 |
| 文档架、工具、回收站、路径隔离与相关严格检查 | **170 passed / 2 skipped**，69.78 秒；随后撤回缩短临时目录的试验方案，使用原临时路径复跑 |
| Ruff 目录排除回归 | **1 passed**，1.98 秒；补测试时先复现误扫生成文件，再修改配置 |
| 后端全局 Ruff | `ruff check .` 通过；`ruff format --check .` 显示 1521 个文件已格式化 |
| 前端检查 | ESLint 与 TypeScript 均通过，进程退出码 0 |
| 最终默认离线分片 1 | **8504 passed / 183 skipped**，684.45 秒，退出码 0 |
| 最终默认离线分片 2 | **8502 passed / 186 skipped**，692.34 秒，退出码 0 |

首次完整分片是在初批修复后执行的继续定位，不能当作零改动原版基线。首次两个分片共选中 17,362 项；新增 Ruff 回归后，最终共选中 **17,363 项：17,006 passed、357 skipped、0 failed**。每个进程另有相同的 6 项收集阶段跳过，已包含在各自汇总的 skipped 中，不能把两个汇总直接相加当成独立用例数。跳过涉及本机缺少 GNU Make、未配置 PostgreSQL／Redis／外部服务及平台不适用等条件；跳过项不计为验证通过。最终使用正常 pytest 临时目录，没有缩短路径规避失败。

## 问题、定位与处理

| 问题 | 原因与处理 | 验证重点 |
| --- | --- | --- |
| 文档架目录和 255 字节文件名无法写入 | 深层内容地址超过 Windows MAX_PATH；项目文件使用扩展路径，数据库 URL 保留普通路径。早期缩短测试目录／转换临时名的试验已撤回 | 真实上传、转换、读取、去重、回收站、越权和存储清理 |
| 普通上传的最长文件名及重名批次失败 | 同一系统路径上限影响原子硬链接；长目标转换为 Windows 扩展路径，保留原子不覆盖和路径检查，元数据返回实际文件路径 | 多文件批次、重名后缀、实际内容与安全路径检查 |
| 凭据配置的权限断言失败 | Windows 权限位不能表达 Unix `0600`；仅在 POSIX 断言该模式，Windows 继续验证保存、重新读取和 chmod 故障记录 | 不把权限位测试当作 Windows ACL 安全证明 |
| Lark 模拟 CLI 无法运行 | Windows 不直接执行 POSIX／Python shebang；卡片链路采用本机批处理替身，broker Python 替身显式交给解释器，shell 启动器通过已有 Git Bash 执行 | 参数、标准输入、退出码、凭据目录和禁止 shell 解释 |
| Studio 重启后没有状态文件 | Windows 的 `terminate()` 强制退出，跳过生命周期落盘；测试子进程使用独立进程组和 Ctrl+Break 正常退出 | 关闭服务后文件存在，重启后可读取历史版本 |
| 超时及后台工作测试不稳定 | 冷启动和配置读取不保证在 10 毫秒或 1 秒内完成；明确记忆失败策略，用事件协调工厂释放，并确保执行器退出 | 仍验证不阻塞事件循环、保留 TimeoutError 原因及冻结记忆 |
| MCP 重试时间断言偶发失败 | 同一 Windows 时钟刻度可覆盖整个失败轮询；断言至少延后 5 秒，允许恰好 5 秒 | 失败任务释放和最小重试间隔 |
| 消息合并性质测试输入生成过慢 | 首次 Unicode 字符集初始化触发 Hypothesis 的生成耗时健康检查；只调整两项语义测试的该检查，保留随机输入与全部等价性断言 | 顺序合并与批处理合并结果一致 |
| 本地 MCP 测试走外部代理 | 环境代理影响本地模拟服务器；仅在该测试中设置 loopback 的 NO_PROXY | 使用真实 HTTP 请求核对工具参数与请求头 |
| 网页提取丢失链接 | ReadabiliPy 的上游自动安装命令在 Windows 找不到 `npm.cmd`，缺少 JS 依赖后退化为纯文本提取；补装现有包声明的依赖 | 真实 Readability 提取器保留相对链接、图片和 document base |
| 扩展安装和配置升级找不到工具 | 仓库根虚拟环境中已有 uv，但不在测试进程 PATH；补齐进程环境。测试解释器路径区分 Scripts／bin，依赖声明使用正斜杠 | 真实临时扩展安装、升级、失败回滚及配置迁移 |
| 依赖同步测试受外部参数影响 | 验证同步的临时项目清除继承的 UV_NO_SYNC；配置升级测试则显式禁用真实后端环境同步 | 保留缺失扩展情况下的核心依赖安装验证 |
| live 策略的子进程无法初始化 | 最小环境删掉了 Windows 初始化 Winsock 所需的 SystemRoot；保留系统目录变量，继续隔离凭据 | 仅收集测试，验证 live 默认关闭及显式启用规则 |
| Make 检查找不到可执行文件 | 本机未安装 GNU Make；统一明确报告需要该工具的检查为 skipped | 这些检查未执行，不能记为通过 |
| Ruff 扫描到运行时技能副本 | `.deer-flow/skills_view` 是生成内容；Ruff 显式排除运行目录，并通过 CLI 回归测试锁定边界 | 后端源文件仍受 lint 和格式检查 |

## 安全软件告警与执行边界

本轮收到同一 `skillscan/__pycache__/orchestrator.cpython-312.pyc` 的多次启发式告警。源码包含静态扫描规则，与 Git 版本一致；这只能核对源码，不能对已删除的缓存作完整鉴定。已停止当时的全量测试并核对临时 Studio 子进程。后续使用 Python 标准的 `-B` 和 `PYTHONDONTWRITEBYTECODE=1`，不生成缓存；杀毒软件与 SkillScan 均保持开启。

ReadabiliPy 的依赖补装在现有虚拟环境内执行 `npm.cmd install --ignore-scripts --no-audit --no-fund`，安装 38 个包。未修改其上游 Python 源码。新建虚拟环境后需要重新完成此依赖准备，详见 `backend/tests/AGENTS.md`。

## 复现与证据

从 `backend/` 使用现有 `.venv/Scripts/python.exe`。测试进程设置 UTF-8、`PYTHONDONTWRITEBYTECODE=1`，将已安装 uv 加入 PATH；验证期间配置升级使用 `UV_NO_SYNC=1` 避免重同步当前后端环境，专测依赖同步的用例会清除此覆盖。

```text
python -B -m pytest tests/blocking_io -q --tb=short
python -B -m pytest -m "not live" --ignore=tests/blocking_io tests/ --splits 2 --group 1 --splitting-algorithm least_duration --durations-path=.test_durations -v --tb=short
python -B -m pytest -m "not live" --ignore=tests/blocking_io tests/ --splits 2 --group 2 --splitting-algorithm least_duration --durations-path=.test_durations -v --tb=short
ruff check .
ruff format --check .
```

前端从仓库根目录执行 `backend/.venv/Scripts/python.exe -B scripts/pnpm.py check`。这是直接执行 Make 目标对应的 pytest／Ruff 命令，没有声称调用本机不存在的 Make。

原始日志保存在忽略目录 `.deer-flow/local-dev/full-regression-fixes/`：

- `before-blocking.log`、`before-offline.log`：本轮开始时的复现与中止位置。
- `after-shard-1.log`、`after-shard-2.log`：首次完整遍历中的具体失败。
- `long-filename-red.log`、`shelf-long-path-green.log`：文档文件名失败及实际文件回归。
- `permissions-lark-green.log`、`remaining-isolation-red.log`、`remaining-isolation-green.log`：平台适配及重启失败定位。
- `extraction-mcp-delta-green.log`、`ruff-config-red-host.log`、`ruff-config-green.log`：提取器、性质测试与 Ruff 红绿证据。
- `final-blocking.log`、`final-shard-1.log`、`final-shard-2.log`、`frontend-check-host.log`：最终检查结果。

日志中的环境准备错误、保护性中止和未执行检查均不计为通过。真实研究质量、运行预算停止、报告与研究面板仍属于后续板块。

## 远程 agent-guidance 失败修复（2026-10-19）

推送 `377b726` 后，GitHub 的后端／前端 lint 通过，agent-guidance 失败。按相同提交区间本地复现得到 **4 errors / 8 warnings**；截图中的 5 errors 还包含作业退出 1 的汇总注解，不代表五条指南超限。原测试只约束每个文件大小，没有约束真实仓库的继承链总大小；本轮新增 1 项真实仓库链路回归。

| 测试用例 | 预期结果 | 实际结果 |
| --- | --- | --- |
| 原推送区间的指南检查 | 超过 98,304 字节硬上限应失败并指出继承链 | 复现退出 1；middleware 106,123、runtime 100,456、sandbox 99,512、subagents 99,142 字节，4 条 AG002 错误 |
| 新增真实仓库继承链回归，修复前 | 检出逐文件合法但继承链超限 | 1 failed / 12 deselected，精确列出上述四条继承链 |
| 迁移详细说明后的工作区检查 | 全部链低于硬上限，软警告如实保留 | 退出 0，28 份 AGENTS.md、0 errors / 4 warnings；最长链为 96,278 字节 |
| 完整指南测试 | 单文件、继承链、历史预算及指南目录约定均通过 | 宿主正常临时目录 **13 passed**，1.72 秒 |
| 内容保留与链接检查 | 移出的说明原文保留，链接可定位 | 运行机制及基准说明与原提交逐段相同，仅调整相对链接／标题；两份文档的本地链接均存在 |
| 修改测试的 Ruff 与 diff | 无 lint、格式或空白错误 | Ruff check 通过，1 file already formatted；git diff --check 通过 |

| 复现 | 红灯原因 | 怎么修改 | 修改后 | 日志 |
| --- | --- | --- | --- | --- |
| 原 CI 区间退出 1；新增仓库链测试失败 | 后端总指南的详细运行说明被所有子指南继承，新增研究说明使四条继承链增长并超硬上限；原仓库测试只查单文件 | 将运行机制与基准规则原文移入 backend/docs/DEVELOPMENT_INVARIANTS.md，总指南保留入口和关键约束；新增真实仓库链总预算测试；不改阈值、豁免或工作流 | 总指南由 30,622 降为 20,777 字节；最长链减少 9,845 字节；检查 0 errors，13 项测试通过 | ci-red.log、chain-red.log → worktree-green.log、tests-green-host.log |

环境失败单列：首次完整指南测试在沙箱中为 **10 passed / 3 errors**，三项均在 pytest 正常临时目录创建阶段失败，尚未执行用例主体。保持相同测试并在宿主正常临时目录复跑得到上述 13 passed；不把准备失败计为通过。日志：tests-green.log → tests-green-host.log。

日志目录：`.deer-flow/local-dev/agent-guidance-verification/`（本地忽略）。所有 Python 进程禁写字节码。实际命令：

```text
python -B scripts/check_agent_guidance.py --before 609e88c --after 377b726 --github-annotations
python -B -m pytest tests/test_agent_guidance_check.py -k effective_guidance_chains -q --tb=short
python -B scripts/check_agent_guidance.py --github-annotations
python -B -m pytest tests/test_agent_guidance_check.py -q --tb=short
python -B -m ruff check tests/test_agent_guidance_check.py
python -B -m ruff format --check tests/test_agent_guidance_check.py
git diff --check
```

检查脚本从仓库根运行，pytest／Ruff 从 backend 运行；使用既有 backend 虚拟环境。本轮没有修改业务代码、重跑默认离线全集或严格 I/O 全集；前述全集结果仍属于历史。远程 CI 状态需在推送本次修复后另行核对，本地通过不能代替远程作业结果。
