# 视频制作运行环境

检查日期：2026-10-11。仅安装独立视频工程依赖；未修改物生正式依赖，未下载或升级模型，未修改 GPU 驱动。

| 项目 | 绝对路径或实测结果 |
| --- | --- |
| Node | `D:/Codex/tools/node22/node-v22.23.3-win-x64/node.exe`，22.23.3 |
| Remotion | `D:/wusheng/video-production/remotion/node_modules`，所有 Remotion 包均为 4.0.532 |
| FFmpeg/ffprobe | `D:/Codex/temp/day200-tools/ffmpeg-9.0.2-essentials_build/bin/`，9.0.2 |
| Remotion 内置 FFmpeg | `D:/wusheng/video-production/remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe`，n7.1 |
| 可复用旧 FFmpeg | `D:/Python code/.venv/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe`，7.1 |
| 浏览器 | `C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe`，154.0.4258.62；Remotion `openBrowser()` 实测成功 |
| Playwright 录制依赖 | `D:/Codex/cache/ms-playwright/ffmpeg-1011/ffmpeg-win64.exe`，新安装官方 1.3 MiB 录制依赖，不下载浏览器 |
| GPU | NVIDIA RTX 4060 Laptop，8188 MiB；驱动 566.24 |
| CPU/RAM | i7-14650HX，24 逻辑线程；16,944,848,896 字节内存 |

外部 FFmpeg 9.0.2 的 NVENC 实测失败：它要求 NVENC API 13.1，当前驱动提供 12.2。内置 n7.1 与旧 FFmpeg 7.1 的 NVENC 均实际编码 30 帧成功。因此 Remotion 可尝试硬件编码，外部 9.0.2 则使用 libx264；无需升级驱动。

## 命令示例

```powershell
$env:PATH='D:/Codex/tools/node22/node-v22.23.3-win-x64;' + $env:PATH
$env:PLAYWRIGHT_BROWSERS_PATH='D:/Codex/cache/ms-playwright'
```

Remotion 命令必须传入现有 Edge：

```powershell
npx remotion render src/index.ts WushengAIC ../output/wusheng-aic-2026.mp4 --browser-executable="C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --codec=h264 --audio-codec=aac --audio-bitrate=128k --video-bitrate=5M --hardware-acceleration=if-possible --concurrency=4
```

硬件编码参数不得同时设置 CRF。软件编码可用 `--hardware-acceleration=disable --crf=20`。290 秒、5 Mbps 视频及 128 kbps 音频的目标体积约 186 MB，最终必须读取实际文件验证，而不能按估算验收。

```powershell
& 'D:/Codex/temp/day200-tools/ffmpeg-9.0.2-essentials_build/bin/ffprobe.exe' -v error -show_format -show_streams -of json '../output/wusheng-aic-2026.mp4'
& 'D:/Codex/temp/day200-tools/ffmpeg-9.0.2-essentials_build/bin/ffmpeg.exe' -v error -i '../output/wusheng-aic-2026.mp4' -f null NUL
& 'D:/Codex/temp/day200-tools/ffmpeg-9.0.2-essentials_build/bin/ffmpeg.exe' -hide_banner -i '../output/wusheng-aic-2026.mp4' -af volumedetect -vn -sn -f null NUL
```

检测黑帧和静帧仅作为定位信号。片尾淡出、标题停留和真实等待可能合理；必须查看对应时段后判断。

```powershell
& 'D:/Codex/temp/day200-tools/ffmpeg-9.0.2-essentials_build/bin/ffmpeg.exe' -hide_banner -i '../output/wusheng-aic-2026.mp4' -vf 'blackdetect=d=0.3:pix_th=0.10,freezedetect=n=-50dB:d=3' -an -f null NUL
```

## Qwen

现有 Ollama 0.40.2 已在 `http://127.0.0.1:11434` 运行。已有 `qwen3.5:4b` 与 `qwen3-vl:4b-instruct-q4_K_M`，均未重新下载。后者直接问答 6.27 秒完成；通过当前项目 ProviderFactory 和现有物品 ContextBuilder 的实际调用 8.00 秒完成，返回 `modelInvoked=true`。

`qwen3.5:4b` 默认 thinking 在 160 token 试跑中只输出内部思考而没有最终 response，不能以该测试宣称成功。正式录像优先现有 Qwen3-VL 4B；记录实际模型名，并核对回答的证据边界。

模型端点 `/api/generate`，项目配置 `WUSHENG_AI_PROVIDER=ollama`、`WUSHENG_OLLAMA_MODEL=qwen3-vl:4b-instruct-q4_K_M`。项目默认规则 Provider 不需要任何密钥。只有 EvidenceProvider 找到当前物品来源时，现有 ProviderFactory 才实际调用模型；录像需核对 `modelInvoked` 字段。
