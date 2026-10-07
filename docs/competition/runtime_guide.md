# 本地运行细节

主入口为 [README](../../README.md) 的 setup/start。以下是分开启动与高级配置，不要求比赛评委先阅读。

`setup.ps1` 显式使用 `https://pypi.org/simple`，避免继承机器上失效的 pip 镜像配置。需要自己的可信 HTTPS 镜像时，可传 `-PythonIndexUrl https://镜像地址/simple`；不关闭 TLS 校验。

## 普通启动与开发启动

`start.ps1` 先构建生产前端，然后以 `0.0.0.0:8000`、单进程、禁用代理请求头启动 FastAPI；电脑管理使用 `127.0.0.1:8000`。仅随机令牌只读档案和必要静态资源允许 LAN GET，所有远程管理 API 和写操作拒绝。按启动窗口的 Enter 停止本次服务。

`-NoBrowser` 不打开浏览器、保留后台服务，并输出本次服务 PID；`-Smoke` 完成检查后停止本次服务；`-Port 8001` 可调整单端口；`-Python` 可指定已安装依赖的 Python。均不会停止其他服务或修改防火墙。

开发 HMR 使用 `powershell -ExecutionPolicy Bypass -File .\scripts\start_dev.ps1`。也可以分开启动：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple -r backend/requirements-lock.txt
npm --prefix frontend ci
# 终端一
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
# 终端二
cd frontend
npm run dev
```

仅开发模式使用前端 5173、后端 8000。普通启动只使用 8000。启动脚本检测端口冲突，不终止不属于脚本的服务。测试脚本使用 5175/8002 和 tmp 内随机隔离目录。用户 data 不作为测试输入。

## 模型与上下文

默认 WUSHENG_AI_PROVIDER=evidence。可选 ollama，配置 WUSHENG_OLLAMA_URL、WUSHENG_OLLAMA_MODEL；另支持 openai-compatible，配置 WUSHENG_AI_BASE_URL、WUSHENG_AI_MODEL、WUSHENG_AI_API_KEY。只允许回环 HTTP，不自动加载 .env、不自动下载模型、不传原始附件到外部服务。

/health 显示 configuredProvider、activeProvider、fallbackReason。生成读取当前 Item 的有限文字证据，模型回答与结构化来源返回给 UI；来源是输入证据，不是逐句正确性保证。危险维修与无相关证据先由规则守卫处理。生成失败回退规则，仍可使用基本管理。

## 说明书、售后与恢复

PDF 文本层使用 pypdf。扫描识别用 pypdfium2 + RapidOCR，用户触发，最多 50 页、单页渲染最多 800 万像素。needs_ocr / ocr_processing / ocr_ready / ocr_failed / text_ready 状态写回数据库，失败保留原件。

售后 ZIP 包含中文 PDF 摘要、JSON 档案、原图和 SHA256 manifest，说明书可选，附件上限 250MB。完整备份包含 SQLite 与引用附件，ZIP 上限 300MB；恢复校验路径、哈希、Schema 与外键完整性，保存恢复前快照，失败回滚。旧附件保留供找回，不支持多 Uvicorn worker。

## LAN 与 PWA

start.ps1 默认提供安全 LAN 只读分享，start_lan.ps1 仅作为兼容转调入口。默认 8000，可传 -Port 8001。只读分享需同一局域网和运行中的服务，管理 API 限回环；不修改防火墙或安装 Windows Service。网络检测成功但无 LAN 地址时不影响本机管理；连接 Wi-Fi 后在 Drawer 点击重新检测。

PWA 只缓存静态 JS/CSS，不缓存用户档案/API/PDF。localhost 安全上下文可用，LAN HTTP 通常不能安装。浏览器通知由用户授权且需要浏览器开启；离线/关闭后请依赖导出的 ICS 和系统日历。
