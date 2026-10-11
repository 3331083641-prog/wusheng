# 物生 AIC 视频制作工程

本目录用于制作物生比赛视频，独立于平台的正式运行数据与依赖。本机正式成片 `D:/wusheng/video-production/output/wusheng-aic-2026.mp4` 已导出：04:50、1920×1080、30fps、H.264/AAC、150.00 MB。全片解码与 Edge 播放通过，详情见 [最终验收报告](reports/video-qa.md)。手机部分仍明确标为浏览器演示，待补真机录屏，不宣称全部实录验收通过。

官方视频要求为 MP4、3—5 分钟、300 MB 以内。匿名材料不出现学校名称、学校 Logo、指导教师信息，作品名称与成果仓库可展示。依据见 [规则报告](reports/rules_review.md)。

## 本地目录

| 目录 | 内容 | 分发范围 |
| --- | --- | --- |
| `storyboard/` | 分镜、中文旁白稿、逐章与逐句时间线 | 可公开的工程说明 |
| `recordings/` | 最新平台真实操作的完整原录屏和章节剪辑 | 本地保存，不推送大录像 |
| `assets/` | 用户指定八张剃须刀图片和 PDF 原件 | 仅本地授权素材，不公开转发订单或厂商全文 |
| `audio/` | 中文合成旁白、原创 BGM、组合音轨 | 仅本地保存 |
| `scripts/`、`licenses/` | 录制/音频/剪辑生成源码与原创音乐声明 | 可公开；不包含 PDF、订单或模型 |
| `subtitles/` | SRT、官方 Remotion Caption JSON、章节秒时间线 | 与最终旁白保持一致 |
| `remotion/` | 可编辑 React 时间轴与九章场景 | 源码可复现；依赖与媒体不进 Git |
| `previews/` | 完整低码率预览 | 本地保存 |
| `output/` | 正式可播放 MP4 | 本地交付；未创建公开视频地址 |
| `reports/` | 官方规则、工具环境、原始操作证据与成片 QA | 公开报告需脱敏；原响应和本地环境信息不公开 |
| `runtime/` | 隔离 SQLite、附件、下载 PDF 和录制状态 | 本地保存，不覆盖正式用户数据库 |

`.gitignore` 排除大体积媒体、依赖、数据库、PDF、运行状态与原始 HTTP 返回。公开仓库不会包含全部录制输入，因此冷克隆后需要自行提供有使用权限的素材；不通过改文件名规避第三方分发规则。

## 编辑与渲染

需要 Node 22、已有 Chromium/Edge、FFmpeg，以及具有使用权限的实际录屏。先在平台的隔离数据环境完成真实操作，再整理章节媒体。不能用预设 OCR 答案或预写模型回复替代录像。

在 `remotion/` 内执行：

```powershell
npm ci
npm run typecheck
npm run studio
node scripts/render-film.mjs stills
node scripts/render-film.mjs preview
node scripts/render-film.mjs final
```

正式导出后，从外层 `video-production/` 运行 `python scripts/normalize_mp4.py` 和 `python scripts/qa_final_video.py`。部分硬件编码器会保留全范围 `yuvj420p`，前者保留 Remotion 母版、复制 AAC 音轨并转换为标准 `yuv420p` 后原子替换；后者仍严格检查格式与完整解码。可通过 `WUSHENG_VIDEO_FFMPEG`、`WUSHENG_VIDEO_FFPROBE` 指定已安装工具；默认软件编码，不要求更新显卡驱动。

主 Composition 为 `WushengAIC`，8700 帧。`render-film.mjs` 使用现有 Edge 和独立 Remotion 依赖，检查媒体与字幕后输出预览/正式文件。具体工具路径与已验证硬件编码条件见 [运行环境](reports/rendering-environment.md)，编辑约定见 [Remotion 工程说明](remotion/README.md)。首次安装工具依赖可联网，回放和已具备全部媒体的本地渲染不需要调用云端模型。

正式播放器只需要最终 MP4。编辑工程的 `public/` 媒体不会随 Git 分发，复现者需复制自己的授权素材和录屏。没有公开托管地址时，项目 README 不应添加虚构播放链接。

## 真实功能与明确边界

- 六张剃须刀资料真实上传、RapidOCR 实际提取、来源查看、人工确认、保存和列表新增均保留原始录屏。OCR 本次实际等待约 72 秒，主片剪短等待，未伪造即时响应。
- 清洁液、刀头真实创建并关联设备；耗材图片在隔离演示环境预置绑定。当前界面没有自定义耗材图片上传控件，不声称视频录到了该功能。
- 用户提供的 PDF 真实上传、阅读、下载和提取；图文说明书照片与 PDF 分开保存。厂商全文仅保留本地。
- EvidenceProvider 使用本地档案规则。可选 Ollama/Qwen 只使用已安装本机模型，实际模型名和 `modelInvoked` 与回答一起留证，不把回退规则当作模型输出。
- 团队已确认手机基础扫码成功。本片尚无真实手机录屏时，分享章节持续标作移动端浏览器演示，不冒充真机拍摄。
- RapidOCR、Qwen、Remotion、Playwright、FFmpeg 为采用的第三方能力；项目自主价值在物品关系、来源追溯、生命周期、预测、上下文边界与管理闭环。

## 音频与字幕

正式组合音轨为 `audio/narration-music.wav`，纯旁白为 `audio/narration.wav` 与 `audio/narration.m4a`，九章独立 WAV 均保留，仅存在于本地交付目录。中文音色为合成语音 `zh-CN-XiaoxiaoNeural`，不是自然人录音；工具无需密钥、未调用收费 API。原创纯音乐由脚本合成，不使用第三方采样或现有旋律，[CC0 声明](licenses/MUSIC_LICENSE.md)与 [旁白](scripts/voice_build.py)、[音乐生成源码](scripts/bgm_build.py)可公开。

音频工具独立使用 `edge-tts==7.2.8`、NumPy 与 FFmpeg。通过 `WUSHENG_VIDEO_FFMPEG` / `WUSHENG_VIDEO_FFPROBE` 指定已有工具；`--proxy` 或 `WUSHENG_VIDEO_TTS_PROXY` 仅用于使用者已经配置的网络代理，不把代理账号、密码或密钥写进源码。执行 `python scripts/voice_build.py`、`python scripts/bgm_build.py` 后，以 `python storyboard/voice_qa.py` 检查字幕全文、时间和音轨。本地 `reports/voice-audio-qa.json` 与 `audio/voice-provenance.json` 为生成证据，不作为公开仓库必需文件链接。

`subtitles/wusheng-zh-CN.srt`、`captions.json`、`timeline.json` 来自相同真实合成句边界。更换旁白后必须重新生成三者，不能只改字幕文本而沿用旧时间码。主片仅使用组合音轨一次，避免旁白或音乐重复叠加。

## 手机补录与隐私

最短补录 12—18 秒即可：手机打开当前二维码扫描结果，等只读页照片出现，再慢慢滚动物品信息。手机和电脑需处于可互通的同一局域网，电脑保持服务运行。录像避开 Wi-Fi 名称、通知、私人相册、真实订单及其它个人信息。收到真机录像后替换第七章，并同步修订旁白、SRT、镜头标签和 QA；补录前本片不能通过“真实手机实录”这一项。

原片、缓存和素材仅保存本地。当前工程未建立公开视频托管链接。正式版本若另行上传，应先确认订单图片、说明书片段及所有素材的公开使用权限。
