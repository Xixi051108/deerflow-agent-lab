# 先体验原版页面，再理解链路

本轮目标：使用原有聊天界面、Gateway 和 DeepSeek，先建立真实运行基线。新增业务任务诊断工具在本机配置中未启用，尚未开始页面上的二次开发验收。

## 本机启动方式

Docker CLI 存在但 Linux 引擎当前不可用，因此使用项目已有的本机开发入口。Next.js 自带的 API rewrites 将 `/api/*` 和 `/api/langgraph/*` 转发到 Gateway，无需为这次体验额外安装 Nginx。

- 页面：<http://localhost:3000>
- Gateway：<http://127.0.0.1:8001>
- 健康检查：<http://127.0.0.1:8001/health/ready>
- 两个服务均只监听本机回环地址；保留原有认证。
- 模型：`deepseek-flash`，从已有根目录 `.env` 读取 `DEEPSEEK_API_KEY`，未复制或打印密钥。
- `config.yaml` 从模板生成并加入 DeepSeek 模型配置；`extensions_config.json` 为空的可用 MCP 配置，二者均不提交 Git。

前端锁定依赖已安装；后端已按 `backend/uv.lock` 安装。原版 Gateway 的 SQLite、checkpointer 和 readiness 检查已启动并通过。

## 第一次进入

打开页面后点击 Get Started；首次运行需要创建本地管理员账号，也可以直接打开 <http://localhost:3000/setup>。邮箱、密码和确认密码由用户在页面填写，不发送到聊天中。

账号创建后进入工作区，发送第一条简短问题：

> 请用两句话解释你能做什么。这次不要调用工具。

先验证模型能真实返回回答，再进行可观察的工具任务。不要把首页宣传案例或离线测试当作这次真实对话的结果。

## 下次如何启动

如果服务已运行，不要再启动一份。需要重新运行时，用两个普通 PowerShell 终端；保持火绒开启。

终端一：

```powershell
cd D:\deerflow-agent-lab\backend
$env:DEER_FLOW_PROJECT_ROOT = 'D:\deerflow-agent-lab'
$env:DEER_FLOW_CONFIG_PATH = 'D:\deerflow-agent-lab\config.yaml'
$env:DEER_FLOW_EXTENSIONS_CONFIG_PATH = 'D:\deerflow-agent-lab\extensions_config.json'
$env:DEER_FLOW_HOME = 'D:\deerflow-agent-lab\.deer-flow'
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -B -X utf8 -c "from dotenv import load_dotenv; load_dotenv('../.env', encoding='utf-8-sig'); import uvicorn; uvicorn.run('app.gateway.app:app', host='127.0.0.1', port=8001)"
```

终端二：

```powershell
cd D:\deerflow-agent-lab
python -B scripts/pnpm.py dev --hostname 127.0.0.1 --port 3000
```

普通终端启动的服务可分别按 Ctrl+C 停止。本次助手启动的后台进程与日志位于 `.deer-flow/local-dev/`，需要停止时核对 `services.json` 中的 PID 及实际进程，避免终止无关程序。

## 本次观察与界限

Gateway `/health`、`/health/ready` 均返回 200；用户已在页面自行创建账号，原有认证保留。第一条真实聊天已在浏览器确认显示模型回答：输入为“请用两句话中文介绍你能做什么。这次不要调用工具或子智能体。”，界面显示耗时 2 秒，输入 token 11535、输出 69，总计 11604；后台 run 状态为 success。

本次会话 thread_id 为 `309da99f-d672-4c8a-b2db-26a7d8d79083`，首条 run_id 为 `58505146-4490-4e19-93fd-00a901c0c0fe`。截图保存在被 Git 忽略的 `.deer-flow/local-dev/deerflow-first-chat.png`，运行日志同目录。模型直接连接检查另有 14 token 请求，它只验证连接，不能替代上述真实 Agent 聊天。

首轮页面编译比后续打开慢，不能把编译中的 Loading 误判为 Agent 推理。这次按要求没有调用工具；模型自我介绍所列的其他能力尚未逐一验证。

## 用这次真实请求理解链路

1. 聊天页面收集问题，前端通过 LangGraph SDK 提交请求。
2. Next.js 将 `/api/langgraph/...` 代理到 Gateway 的 `/api/...`；本机未使用 Nginx。
3. Gateway 创建 thread/run，RunManager 让本次 run 进入 running。
4. worker 调用主 Agent 工厂，装配模型、提示词、原有工具和中间件，再执行图。
5. 主 Agent 请求真实 DeepSeek；本次直接产生回答，无需工具。
6. 事件经 StreamBridge/SSE 返回，前端显示回答；run 进入 success，状态/消息持久化。

在这个无工具基线上，再选一次明确的只读文件任务，观察“模型提出工具调用→程序执行→工具结果回给模型→再次回答”的额外循环。不要一次研究全部中间件、记忆或子 Agent。

Gateway 初次在受限环境启动时继承了不可连接的代理地址，后已在具备网络访问的环境重启。首次日志中的 tiktoken 下载警告有字符数估算回退，不等于模型已失败；真实模型是否可用仍以实际对话为准。

Next.js 首次运行自动追加到 `frontend/AGENTS.md` 的框架提示已移除，避免将启动副作用混入二次开发改动。下次 `next dev` 可能再生成同类提示。
