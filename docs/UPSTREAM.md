# DeerFlow 源码引入方案

核对日期：2026-10-16。DeerFlow v2.1.0 源码快照已完整引入；此前被安全软件拦截的两个文件已恢复且内容校验通过。未安装 DeerFlow 依赖或启动服务。

## 固定版本

- 上游仓库：https://github.com/bytedance/deer-flow
- 选用正式发布版：[v2.1.0](https://github.com/bytedance/deer-flow/releases/tag/v2.1.0)，发布于 2026-09-24。
- 固定提交：`345f08be00c8a9495079b732a39b46aa9af1584e`。
- 标签对象：`f6e747be2486d3f75b0d66a8b17d8fb0ffd5f8ce`，已通过 GitHub API 解引用到上述提交。
- 选择理由：使用有明确发布边界的版本作为学习和复现基线，避免跟随持续变化的 main；正式发布不代表没有缺陷。
- 后续文档、配置模板和启动脚本以此提交为准，不混用 main 的说明。

该提交的上游 Unit Tests、E2E Tests、Replay E2E、Frontend Unit Tests、Lint Check、Backend Blocking IO 和 Skill Review CI 均显示 success。这是 GitHub Actions 的远程记录，不是本机验证结果。

## 目录与保留规则

将源码引入 `D:\deerflow-agent-lab` 根目录，保留上游 `backend/`、`frontend/`、`docker/`、`scripts/`、`skills/` 等相对位置，便于按官方文档运行和对照源码。

- 保留当前 `.git` 和 origin（用户仓库），不在目录中创建第二个 Git 仓库。
- 保留现有 `main.py`、`test_main.py`、`requirements.txt` 和 `HANDOFF.md`；它们属于环境准备阶段，不代表 DeerFlow 应用实现或依赖。
- 保留本地 `.env` 与 `.venv/`；导入前后用哈希校验原文件，密钥不输出、不写入文档、不上传。
- 合并上游 `.gitignore` 与本地忽略规则，保持 `.env`、`.venv/`、`__pycache__/` 被忽略；导入前检查同名文件，不直接覆盖。
- DeerFlow 后端环境与当前检查脚本的 `.venv` 分开管理，按上游锁文件安装。
- 保留上游 LICENSE 和版权声明；该版本采用 MIT License，复制和分发时须保留声明及许可文本。
- 引入源码不包含提交或推送操作。

## 源码引入结果

- 从 GitHub codeload 下载固定提交的归档，按 GitHub API 返回的完整 Git tree 逐文件核验。
- Git tree：`331bcaa14632b04aa7fb2d3187187a4cd9a01ba7`，共 2,964 个文件，API 返回未截断。
- 归档 SHA-256：`de309ec407d0b5b9ef1855a2cdcd97d9a9c2c95d0b0029cde6c79b9212518ffe`。
- 归档内全部文件的 Git blob 校验通过；`scripts/run-with-git-bash.cmd` 按上游 `.gitattributes` 的 CRLF 规则规范化后匹配。
- 本机 2,963 个上游文件的内容校验通过，另有 `.gitignore` 按计划合并本地忽略规则，全部 2,964 个文件已落地；完整性报告 `complete: true`，无缺失或内容不符项。
- 此前受防护拦截的两个文件现已恢复，并通过读取及 Git blob 校验：
  - `backend/packages/harness/deerflow/skills/skillscan/orchestrator.py`
  - `backend/tests/test_skillscan_native.py`
- 历史拦截：用户截图显示安全软件曾自动处理 `test_skillscan_native.py`，检测名称为 `HEUR:Trojan/Python.ReverseShell.f`。详情截图还显示临时解压目录中的 SkillScan 模块被删除，操作进程为运行 `import_source.py` 的 Python。用户按恢复弹窗勾选加入信任区并完成操作后，两个正式项目路径均可正常读取。
- 两个受影响文件在归档中的内容均匹配上游 Git blob。前者实现安全扫描，后者包含反向 Shell 检测测试；文件来源和测试用途已核实，但不能据此断言检测一定是误报。本轮未执行这些文件，也未改变防护设置。
- 下载缓存及 Git tree 清单保留在 `.source-import-v2.1.0/`，已加入 Git 忽略规则，供后续核验和恢复，避免重复下载。
- 现有 `.env`、`main.py`、`test_main.py`、`requirements.txt` 哈希校验通过；原 `.venv/` 保留。除合并忽略规则与更新交接文档外，未修改现有项目文件。
- 本机实际执行 `python -m unittest -v test_main`：2 项通过；当前检查脚本环境的 `pip check` 通过。未执行 DeerFlow 的测试、构建或服务启动。
- 当前为源码快照引入；本地 Git 分支仍为无提交的 main，未引入上游 Git 历史、暂存、提交或推送。

## 两个受影响文件的静态审查

2026-10-16，用户明确选择“先保留隔离，继续审查两个文件”。本轮仅从缓存归档读取文本、核对 Git blob 并分析语法树，未重新落地或执行这两个文件，未修改防护设置。

- 来源复核通过：`orchestrator.py` 的 Git blob 为 `be09e74aa5177731155b02a76f61da13f06d7ea8`；测试文件为 `5893d68580e6a82df69207ba6b5f7474b1aaa09c`；原始归档 SHA-256 仍匹配上文记录。
- 扫描模块的 `scan_skill_dir`（224–258 行）读取指定技能目录，`_scan_python`（357–434 行）解析语法树并生成发现，`_scan_shell`（437–453 行）匹配文本规则。模块中的危险调用名称用于识别被扫描代码，不是直接调用；在该文件的实际语法树调用节点中未发现命令执行、套接字连接或 HTTP 发送调用。
- 测试文件的反向 Shell 用例（584–597、1415–1429 行）把样例写入 pytest 临时目录，然后调用静态扫描器并断言其被阻止，未调用样例脚本。运行测试仍可能因写出这些样例而再次触发安全软件。
- 测试文件并非完全没有动态执行：`_runtime_client_receivers`（1162–1212 行）使用 `compile` 与 `exec` 执行仓库内固定的客户端绑定用例。它以 `_Recorder` 等模拟对象替换网络客户端；记录器仅保存接收者标签，未发送请求或保存请求参数。调用点与输入均来自当前文件固定用例。
- 上述辅助函数使用真实 `os` 对象，部分固定用例会在内存中读取进程环境变量；当前模拟客户端未将这些值外传。该辅助函数保留 Python 内置能力，不是适用于外部代码的安全沙箱，不能改为执行未经审查的输入。
- 测试中涉及模型调用的用例（641–672 行）替换为 `FakeModel`，其返回值为本地构造。当前审查未发现两个文件中的真实反连、系统命令执行或网络外传路径。
- 结论：这两个文件的来源与静态调用关系支持“安全扫描规则和测试样例触发启发式误报”的判断。该结论限于固定版本的这两个文件，不代表完整项目、依赖或运行时已通过安全审计。审查阶段按用户选择保持隔离，后续经用户授权恢复，当前状态见源码引入结果；未运行相关测试。

代码证据：[扫描逻辑](https://github.com/bytedance/deer-flow/blob/345f08be00c8a9495079b732a39b46aa9af1584e/backend/packages/harness/deerflow/skills/skillscan/orchestrator.py#L357-L434)、[反向 Shell 检测测试](https://github.com/bytedance/deer-flow/blob/345f08be00c8a9495079b732a39b46aa9af1584e/backend/tests/test_skillscan_native.py#L584-L597)、[使用模拟客户端的动态测试辅助函数](https://github.com/bytedance/deer-flow/blob/345f08be00c8a9495079b732a39b46aa9af1584e/backend/tests/test_skillscan_native.py#L1162-L1212)。

## 防护拦截处理记录（已解决）

2026-10-16，用户在了解审查结论与安全边界后明确要求“那导入吧”，已改变此前保留隔离的处理决定，无需再次询问是否允许补齐源码。

- 再次校验归档 SHA-256、完整 Git tree 及两个文件的 Git blob 后，尝试直接写入正式路径，早期回读仍返回 `OSError: [Errno 9] Bad file descriptor`。
- 用户在安全软件中完成恢复及加入信任区操作，针对以下正式项目路径：
  - `D:\deerflow-agent-lab\backend\packages\harness\deerflow\skills\skillscan\orchestrator.py`
  - `D:\deerflow-agent-lab\backend\tests\test_skillscan_native.py`
- 最终复查：两个文件分别为 62,356 和 71,559 字节，读取及上游内容校验通过；全部 2,964 项源码文件完整。前后端版本均为 2.1.0，本地配置与检查脚本哈希保持一致。
- 本轮重新执行 `python -m unittest -v test_main`，2 项通过；当前检查脚本环境的 `pip check` 通过。缓存归档保留；未执行 DeerFlow 应用测试、安装依赖或启动服务，助手未修改防护设置。

## 启动路径

选择 Docker 开发流程，并接入 DeepSeek 官方 API。当前不需要 Ollama。

固定版本的官方入口为 `make config`、`make docker-init`、`make docker-start`。这些命令尚未执行；前者需要保留已有配置，后两者分别涉及镜像准备和实际服务启动。

官方 Docker 开发起步建议：4 vCPU、8 GB RAM、25 GB 可用 SSD；推荐 8 vCPU、16 GB RAM。Compose 要求 v2.24+。Python 后端要求 >=3.12。

## 本轮本机只读检查

- 物理内存约 15.69 GiB，可用约 1.76 GiB；构建或启动前需要释放内存并重新检查。
- C 盘可用约 42.59 GiB，D 盘约 69.96 GiB。
- Docker Compose v5.6.0 可用；Docker CLI 无法连接 `dockerDesktopLinuxEngine` 命名管道，因此未取得有效引擎资源信息。
- 当前 PATH 未找到 `make` 或 `uv`；Git for Windows 的 Bash 存在于 `D:\git for windows\Git\bin\bash.exe`，PATH 中的 `bash` 则指向 Windows 系统入口，后续不能混用。
- Windows CIM 内存查询被拒绝访问，已改用只读的 `GlobalMemoryStatusEx` 查询；失败查询产生的零值无效。
- 现有仓库仍为 main，无提交；现有 `.env` 和 `.venv/` 的 Git 忽略规则有效。

## 下一步

1. 重新检查内存与磁盘资源，确认 Docker Desktop Linux 引擎可连接。
2. 检查 Git Bash 和官方启动入口所需工具，保留现有本地配置并按固定版本接入 DeepSeek。
3. 验证 Compose 配置，再构建和启动最小环境。
4. 执行最小任务，保存本机的实际结果和日志，作为后续改动基线。

## 核对来源

- [固定提交](https://github.com/bytedance/deer-flow/tree/345f08be00c8a9495079b732a39b46aa9af1584e)
- [许可证](https://github.com/bytedance/deer-flow/blob/345f08be00c8a9495079b732a39b46aa9af1584e/LICENSE)
- [README](https://github.com/bytedance/deer-flow/blob/345f08be00c8a9495079b732a39b46aa9af1584e/README.md)
- [Makefile](https://github.com/bytedance/deer-flow/blob/345f08be00c8a9495079b732a39b46aa9af1584e/Makefile)
- [后端依赖](https://github.com/bytedance/deer-flow/blob/345f08be00c8a9495079b732a39b46aa9af1584e/backend/pyproject.toml)
- [发布提交的 Unit Tests](https://github.com/bytedance/deer-flow/actions/runs/35961583088)
