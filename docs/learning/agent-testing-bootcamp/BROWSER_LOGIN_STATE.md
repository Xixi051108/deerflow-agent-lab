# 浏览器登录态持久化与复用

2026-10-20实现，2026-10-21同步。仅处理第五阶段的浏览器登录态；不改变研究业务编排，不进入第六阶段。上一版阶段四／五及专项修复已单独推送为`e370ea3`。用户随后明确授权同步当前代码，本次提交包含登录态及已有官网／浏览器采集改动；下方10月20日“保留本地”的描述属于当时历史，不表示本次仍未纳入提交。真实网站联调与第五阶段业务验收仍待完成。

## 使用与启用

1. 部署时按 README 的 Agentic Browser 配置准备 Playwright 与 Chromium，开启原 `browser` 工具组。保持 `GATEWAY_WORKERS=1`，每个 `DEER_FLOW_HOME` 只运行一个 Gateway。需要区分不同人的部署必须启用 DeerFlow 用户认证；禁用认证时所有访问者属于同一本地用户。
2. 让部署加载本地新代码并刷新前端；本轮没有修改真实配置、安装浏览器、重启现有服务或使用用户真实账号。Windows 缺少 Playwright Chromium 时，可回退到本机 Chrome 的全新隔离实例；不连接个人浏览器目录。
3. 在已有聊天的 Browser 面板开启 Live，打开官网／必要电商页面。需要登录时由用户手动完成，包括短信、扫码、同意页及弹窗；勿把密码或验证码发送到聊天。标签选择器可切回原页面，点击页面后可输入、粘贴、使用中文输入法或拖动。
4. 等网站完成跳转且已进入正常页面，再点 **Remember login**。这是保存网站状态的授权，不是程序验证账号登录成功。保存成功后，新研究线程和服务正常关闭重开后的浏览器会恢复同一用户的状态。
5. **Forget all logins** 清除该用户全部网站的保存状态并关闭其所有当前浏览器；再次打开 Live 使用新浏览器。另一用户不受影响。会话被网站撤销或页面要求登录时，在 Live 重新登录并保存。

## 机制与边界

- 沿用 Playwright `storage_state(indexed_db=True)`／`new_context(storage_state=...)`，包含 Cookie、localStorage、IndexedDB；不保存输入框、整个浏览器目录、密码管理器、sessionStorage 或浏览器缓存。没有确认需要改用独立持久化浏览器目录。
- 私有文件：`DEER_FLOW_HOME/users/{user_id}/browser-auth/{SHA256(user_id)}/state.json`。额外摘要保证 Windows 上大小写不同的身份不落入同一状态文件；拒绝路径重定向。原型旧路径／无时间戳状态不自动迁移，需重新登录保存。
- 原子写入使用有界 JSON（1 MiB）、临时文件、flush/fsync/replace；临时文件使用操作系统私有权限，目录以 0700 创建。文件包含凭据，不能挂入 sandbox、发布为研究证据或纳入版本管理。不是加密保险箱；Windows ACL 没有单独作系统安全审计。
- 同一 Gateway 内锁定读取、比较 revision 和写入。清除保存新 revision 的空墓碑，先撤销活浏览器并阻止新会话进入，再清除文件和关闭浏览器；旧句柄不能重新打开或覆盖墓碑。取消请求等待磁盘操作结束。不同线程同时修改同一用户的状态时，旧版本会冲突并失效，需关闭再开启 Live；不自动合并两个网站快照。
- 用户点击 Remember 后，每 5 秒检查保存变化，浏览器快照及正常关闭也会保存；恢复的会话继续更新。相同状态不重复写盘；保存错误仅返回状态提示和异常类型，不打印异常内容。进程被强杀可能丢失最后约 5 秒未落盘的变化。
- 过滤已过期 Cookie；最长保留时间为最后一次实际保存后 30 天，达到上限写空墓碑。网站可以提前撤销会话，也可能用 opaque token，不存在通用的“验证所有网站登录成功”接口。密码框或常见登录路径仅是人工登录提示线索；遇到未识别的登录／验证码页，用户仍须在面板自行判断。损坏或不可读的文件使用干净浏览器并提示清除重登。
- 登录页不向模型返回元素／正文，不保存截图或采集为研究文本。普通表单快照不读取输入框 value；返回 URL 去掉用户信息、query 和 fragment，以免回调凭据泄漏。Live 只向已有线程的所有者传送画面；PUT／DELETE 只返回 saved 布尔值，WebSocket 登录状态只包含布尔值和固定提示码。网页自身把敏感内容显示在正常正文中的情况，不由通用页面检测完全解决。
- 只保存已经存在、归属一致的隔离浏览器，保存接口不能创建缺少网络防护的新会话。上下文重建重新绑定请求防护并阻止 service worker 绕开路由；OAuth 弹窗关闭后回到原上下文。CDP 模式仍沿用原显式信任开关，但不导入／导出本功能的状态。
- 不绕过验证码、反爬、站点访问限制或原 URL 防护。不承诺系统 WebAuthn、硬件密钥、客户端证书、浏览器扩展、OS 文件选择器等本机交互能在远程截图面板完成；这些流程需要站点支持的替代登录方式，否则记录访问限制。

## 依据

- [microsoft/playwright 认证文档](https://github.com/microsoft/playwright/blob/main/docs/src/auth.md)：使用 storage state 创建新上下文；认证状态是敏感数据；sessionStorage 需另行处理。本轮不保存 sessionStorage。
- [browser-use/browser-use 浏览器配置](https://github.com/browser-use/browser-use/blob/main/browser_use/browser/profile.py)：区分 storage_state 与 user_data_dir，并提示混用冲突。仅参考配置边界，没有复制其自动化／反检测参数。

## 验证与失败记录

全部使用临时用户目录、合成 Cookie／Token／密码、受控页面；没有真实登录或真实账号调用。日志位于 `.deer-flow/local-dev/browser-login-verification/`，每轮独立文件，失败未覆盖。

| 场景 | 实际结果 |
| --- | --- |
| 网站刷新 Cookie 后保存并创建新浏览器 | red-refresh 先复现仍为 v1，green-refresh 修复；扩展测试覆盖 Cookie/localStorage/IndexedDB |
| Windows 大小写用户 ID、30 天过期 | red-expiry-isolation 2 failed；修复后通过 |
| 主动清除、旧句柄、新会话、请求取消 | red-forget 缺少清除事务；后续覆盖墓碑、并发保存、清除等待、取消排空及句柄失效 |
| 密码／验证码／回调 URL | red-login-privacy 先复现泄漏；后续模型快照、研究采集保护通过 |
| 上下文重建网络防护 | red-rebuild-guard 先复现 guard 未执行；修复重绑与 service worker 策略后通过 |
| 保存接口不能创建未配置会话 | 首轮替身错误先失败；修正后 red-remember-admission-valid 命中真实会话残留，修复为仅获取已有会话 |
| 新 Python 进程恢复、周期保存、正常关闭、Cookie 到期 | login-lifecycle 13 passed；后续专项继续扩展 |
| 面板标签／粘贴／中文／登录提示 | red-panel 缺失入口；第一次绿色轮仍有 IME 事件失败，修正原生 composition 监听后 16 项通过 |
| 开发前默认离线全集 | 17,208 passed／362 skipped／1 failed／9 deselected，1358.62 秒；失败为原取消关闭测试没有会话用户身份 |
| 开发前严格 I/O | 150 passed／1 skipped，34.80 秒 |
| 最新扩大专项 | final-browser-expanded：117 passed，28.22 秒；覆盖原浏览器、路由、取消和研究采集，后续关闭任务检查另行记录 |
| 开发后严格 I/O | after-blocking：150 passed／1 skipped，28.19 秒 |
| 前端完整静态检查 | 首轮2项无用类型断言错误，随后TypeScript发现2项测试类型错误；最终frontend-check-verified退出0 |

原取消关闭测试仅补齐真实用户身份，未删除任何原断言。真实浏览器测试使用本机新建的隔离 Chrome；不是 Chromium 安装包兼容性或真实网站登录成功证明。

用户追加的旧版推送独立验证：214 passed／1 failed（未改的真实浏览器测试缺少 Playwright Chromium），严格 I/O 150 passed／1 skipped，Ruff 通过；旧版未包含 Windows Chrome 回退。隔离副本执行触发火绒 `HEUR:Trojan/Python.ReverseShell.f`／`25B49D93CA5A73B8`，副本 SkillScan 源码被删除，用户截图确认；未恢复、关闭防护或加白名单。原工作区源码仍在。后续未改模块使用原目录，不再执行被删副本。不能据此判定误报。首次命令错路径、收集失败和浏览器二进制缺失均保留日志。

最终补验（不与上表重叠计数）：

- 默认离线两个分片均退出0：8,607 passed／187 skipped（855.01秒）和8,615 passed／181 skipped（808.29秒）。合计17,222 passed；每进程相同的6项收集跳过去重后362 skipped。分片在最后准入／日志小项完成前启动，最后代码另由下面串行专项验证，后加测试没有冒充已纳入此前全集。
- 关闭后台任务的red-live-close复现后修复；加入容量负例，final-browser-complete为119 passed。red-error-privacy随后复现后台异常原文泄漏，改为仅日志异常类型。并行时final-security-targeted出现3个失败后等待不退出，256.72秒核对并终止该测试树，未取得完整失败栈；单例通过，最终串行serial-browser-diagnosis为**120 passed／0 failed（20.83秒）**。根因未确定，不把此恢复描述为已修复某个环境问题。
- 完整严格I/O最终**151 passed／1 skipped（30.79秒）**，包含新的登录态文件I/O路径。前端浏览器最终**18 passed／0 failed**（6文件，frontend-browser-verified为3.639秒），包含指针单击／拖动与清除后不自动重连；完整ESLint／TypeScript的frontend-check-verified最终退出0。此前因仅读日志头误报过静态检查通过，取回退出码后发现beforeEach回调返回mock函数、HTMLElement缺少value两项类型错误；修复为void回调和HTMLTextAreaElement泛型，失败日志与更正保留。
- 指南首轮新增说明使继承链超限149字节；将细节下沉浏览器模块后**0 errors／4 warnings**，最长98,038字节。全局Ruff存在**原有**collection.py／middleware.py／tools.py三处超长行及上述三文件＋test_research_collection.py格式问题；未顺手修改无关研究代码。专项文件的Ruff／format和最终diff结果另见本轮收尾日志。

- 专项7个后端实现／测试文件的Ruff check及format检查均退出0。closeout.json核对17个原有无关tracked diff全部一致、61个文档链接有效、批准提交不含登录态／配置／AFC；暂存区为空。git diff --check通过。task-final.diff保存本任务相对起点的修改，包含新增文件。

## 2026-10-21 本次代码同步验证

用户明确授权将当前代码提交推送。只对待提交的4个研究文件应用Ruff格式整理；原有格式失败历史保留，本次全后端Ruff check／format均退出0（1546文件）。没有修改生产价格规则或扩展业务。

10月21日首轮发现跨日期测试夹具问题：范围固定10月20日，采集时间却取运行日，正确触发`unverified_price`。首轮定向151 passed／1 failed，严格I/O149 passed／2 failed／1 skipped；冻结frozen_reader夹具的采集时钟后原边界30 passed。最终定向179 passed（58.70秒），完整严格I/O151 passed／1 skipped（48.60秒）；前端浏览器18 passed，完整ESLint／TypeScript退出0。此次未重跑默认离线全集，前文全集数字仍是10月20日历史结果。

日志均为`push-20261021-*`，没有覆盖首轮失败。未使用真实账号、模型或重启现有服务；没有再复制整棵源码做隔离验证。本次提交包含现有官网正文／浏览器采集改动，但真实网页与小米15报价场景仍待联调验收，不能把合成测试通过当作业务闭环完成。
