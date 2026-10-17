# deerflow-agent-lab 项目交接

## 项目目标

以字节跳动开源的 DeerFlow 为主要底座，通过源码学习和二次开发系统掌握 Agent 开发，并完成一个能够演示、部署、评测和写入简历的作品。

- 上游项目：https://github.com/bytedance/deer-flow
- 本项目仓库：https://github.com/Xixi051108/deerflow-agent-lab
- 本地目录：D:\deerflow-agent-lab
- 当前阶段：DeerFlow v2.1.0 源码快照已完整引入并核验，尚未安装 DeerFlow 依赖、构建或运行应用。详细证据见 docs/UPSTREAM.md。
- 具体应用场景和二次开发功能：在理解上游能力、完成原版复现后共同确定。

用户已有 Python 基础，主要目标是学习 Agent 开发。用户接受高难度，质量优先，选择架构、测试、维护和扩展能力扎实的实现。Docker 的使用与部署也是明确学习目标。

## 协作方式与约束

- 使用中文，助手带着开发；每步说明目标和必要原理，一起实现并检查实际输入输出，再逐步增加用户独立完成的部分。
- 编码前理解需求和已有实现，重要不确定问题先确认。
- 优先采用简单直接的实现，只修改当前任务所需内容，保留上游结构和风格，不顺手重构或添加功能。
- 修改后做相关验证并检查 diff，明确区分本机执行结果、上游 CI 记录和未验证事项。
- 模型供应商选择 DeepSeek，使用本地配置；不要求用户发送密钥，不在日志、文档、镜像或 Git 中暴露密钥，不自行充值或购买服务。
- 简历描述必须区分上游能力与个人贡献，使用实际代码、测试、对比实验和演示支撑，不虚构改进数字。
- 用户仓库为 origin。引入上游代码前先规划版本和目录，保留环境检查脚本与本地配置，按许可证保留上游声明。
- 当前未要求提交或推送代码；不得擅自提交或推送。

## 当前文件与仓库状态

- HANDOFF.md：项目目标、状态和后续步骤。
- docs/UPSTREAM.md：固定版本、源码引入结果、校验与拦截记录。
- backend/、frontend/、docker/、scripts/、skills/ 等：固定于上游 v2.1.0 提交 `345f08be00c8a9495079b732a39b46aa9af1584e` 的源码快照，保留原有布局与 MIT 许可证。
- main.py：DeepSeek API 连通性检查脚本，使用 urllib 和 python-dotenv，输出简短回答、结束原因与 token 用量。
- test_main.py：环境检查脚本的两项离线测试，覆盖密钥缺失时不发送请求，以及 HTTP 错误时不打印凭据或错误正文。
- requirements.txt：环境检查脚本依赖 python-dotenv==1.2.4；此文件尚不代表 DeerFlow 的依赖清单。
- .env：用户自行填写的本地 DeepSeek 配置，必须保留并保持忽略，不展示内容。
- .venv：环境检查脚本的虚拟环境，已在当前目录重建并安装记录的依赖，路径和 pip 启动器检查通过。
- .gitignore：已合并上游规则，继续忽略 .env、.venv/ 和 __pycache__/；额外忽略源码下载缓存 .source-import-v2.1.0/。
- Git 本地分支为 main，尚无提交；未暂存或上传代码。
- GitHub API 已核实当前仓库为 Xixi051108/deerflow-agent-lab。最后的 git ls-remote 复查遇到连接重置和网络超时，CLI 网络连通性待网络稳定后复核；未执行推送。
- GitHub 仓库名称和本地 origin 已统一为 deerflow-agent-lab；origin 为 https://github.com/Xixi051108/deerflow-agent-lab.git。此次通过固定提交归档引入源码快照，未修改 origin，未引入上游 Git 历史。

## 已完成的环境验证

检查日期：2026-10-16。以下是已实际执行的基础检查，不能代替 DeerFlow 的部署和功能验收。

- Windows 11 家庭版 64 位；Python 3.12.12，位于 D:\index\python.exe；Git 2.51.1.windows.1；宿主机 pip 26.0.1；uv 尚未安装。
- venv、ensurepip、SSL、SQLite 和 Python HTTP 标准库可用，项目虚拟环境已实际创建并安装 python-dotenv==1.2.4。
- Docker Desktop 4.95.0、Docker CLI/Engine 29.8.2、Compose v5.6.0；WSL 2 已配置；Docker 使用 Linux 引擎和 desktop-linux context。
- 官方 hello-world 镜像拉取与容器运行已通过；python:3.12-slim 容器运行与 D 盘目录只读挂载已通过，容器中 Python 为 3.12.15；临时容器通过 --rm 自动删除。
- DeepSeek 官方 API 真实简短请求已通过，使用 deepseek-flash；中文终端输出使用 Python 的 -X utf8 模式可正常显示。尚未验证 DeerFlow 内部的模型、工具或浏览器调用。
- 在 D:\deerflow-agent-lab 下重建 .venv 后，test_main.py 两项离线测试再次通过，pip check 通过，pip 启动器路径正确，本地 DeepSeek 配置存在性检查通过；该轮未发送新的模型请求。
- 项目迁移时已通过文件哈希确认 .env、main.py、test_main.py 和 requirements.txt 内容完整保留。
- 本机总内存约 15.69 GiB，源码引入前检查可用约 1.76 GiB；磁盘当时 C 盘可用约 42.59 GiB、D 盘约 69.96 GiB。Docker 引擎暂时无法连接，当前 PATH 未找到 make 或 uv，Git Bash 的实际入口为 `D:\git for windows\Git\bin\bash.exe`。部署前需重新检查资源与依赖。
- 本轮引入期间实际执行 `python -m unittest -v test_main`，2 项通过，当前检查脚本环境的 `pip check` 通过；未发送新的 DeepSeek 请求。

## 源码引入验证与已解决的防护拦截

- 已下载并核验固定提交的 2,964 个上游文件。归档内容全部通过 Git blob 校验；其中 Windows `.cmd` 脚本按官方换行规则规范化后匹配。
- 最终核验：本机 2,963 个上游文件内容匹配，加上按计划合并本地规则的 `.gitignore`，全部 2,964 个文件完整落地；现有 `.env` 和检查脚本的内容哈希保持一致，前后端版本均为 2.1.0。
- `backend/packages/harness/deerflow/skills/skillscan/orchestrator.py` 与 `backend/tests/test_skillscan_native.py` 此前被本机安全软件以 `HEUR:Trojan/Python.ReverseShell.f` 拦截，回读报 `Bad file descriptor`。用户通过恢复弹窗勾选“将恢复的文件加入信任区”并完成操作后，两个正式项目路径已可正常读取且内容匹配上游。
- 两个文件的归档内容均匹配官方固定提交；分别用于安全扫描与扫描测试，包含反向 Shell 特征相关逻辑或测试样例。尚不能断言一定是误报，未执行这些文件、关闭防护或设置排除项。
- 下载缓存 `.source-import-v2.1.0/` 保留原始归档、Git tree 清单和最终 `verification.json`，已忽略；报告 `complete: true`，缺失和内容不符项为空。
- 用户曾选择“先保留隔离，继续审查两个文件”。静态审查已完成，来源复核通过，实际调用关系支持启发式误报判断，未发现这两个文件中的真实反连、命令执行或网络外传路径。测试辅助函数包含执行固定用例的 `exec`，客户端为模拟对象，但会读取真实进程环境；不是通用代码沙箱。证据与局限详见 docs/UPSTREAM.md 的静态审查章节。
- 用户已明确授权补齐两个文件，完整性核验现已通过，无需再等待恢复或询问导入授权。防护设置由用户操作，助手未更改防护设置，未运行这两个文件或其测试。注意恢复缓存中的临时路径不等于恢复正式项目路径。
- 完整导入后重新执行现有 `test_main` 的 2 项离线测试及检查脚本环境的 `pip check`，均通过；未执行 DeerFlow 自身的测试或应用启动。

## DeerFlow 已核实的信息

- 已线上查阅官方 README、后端依赖声明、部分测试目录和 CI；尚未在本机安装、构建或执行 DeerFlow。
- 官方文档提供 DeepSeek 配置、Docker/Compose、沙箱及开发说明，后端要求 Python >=3.12。
- 官方 Docker 开发起步建议为 4 vCPU、8 GB RAM、25 GB SSD，推荐 8 vCPU、16 GB RAM；当前本机可用内存需在部署前重新安排。
- 查询时主分支提交 ec07de9618b4194533fea3d8bf8a2e4fbcca5385 的 Unit Tests、E2E、Replay E2E、Frontend Unit Tests 和 Lint Check 显示 success。这属于上游 CI 观察，不是本机测试结果。
- 后续部署文档以固定版本为准：https://github.com/bytedance/deer-flow/blob/345f08be00c8a9495079b732a39b46aa9af1584e/README.md

## 下一步

1. 当前工作区已是 D:\deerflow-agent-lab；源码完整性已通过。读取本文件及 docs/UPSTREAM.md，进入部署准备阶段。
2. 继续保留本地环境配置与上游结构，复查 Docker 引擎、内存和 Git Bash/启动工具。
3. 重新检查可用内存和部署依赖，按目标版本官方流程接入 DeepSeek，运行原项目最小任务并记录基线。
4. 沿真实调用链学习：用户输入 → 任务编排/Agent 循环 → 模型调用 → 工具执行 → 上下文和状态管理 → 停止与成果输出。
5. 根据上游现有能力共同确定一个具体应用场景及 2–3 项有价值的改进，结合源码做小步开发；RAG、多 Agent、MCP 和浏览器按实际需要选用。
6. 建立固定评测任务，记录改动前后的完成率、结果质量、耗时、token 或恢复行为，保留真实结果。
7. 在开发中掌握 Dockerfile、镜像与容器、环境变量、挂载和持久化、端口、Compose、日志与故障排查；形成可复现部署、架构与改动说明、演示和简历描述。

## 环境检查命令

在项目目录执行：

    .\.venv\Scripts\python.exe -X utf8 main.py
    .\.venv\Scripts\python.exe -m unittest -v test_main
    .\.venv\Scripts\python.exe -m pip check

第一条命令会发送真实 DeepSeek API 请求，后两条为本地离线检查。DeerFlow 的实际启动与测试命令应以选定版本的官方文档为准。
