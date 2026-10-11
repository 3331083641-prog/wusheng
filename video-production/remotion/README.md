# 物生 AIC 正式视频可编辑工程

主 Composition 为 `WushengAIC`，1920×1080、30fps、8700 帧（4分50秒）。`WushengFilm` 为旧命令兼容别名。九个章节均有独立的 Sequence、文件与 Composition，可在 Studio 双击进入单章编辑。

本工程只包装真实软件录屏，不绘制替代业务结果。手机部分明确标作“移动端浏览器演示 · 待替换手机实录”；收到实机录像后应替换 `public/media/ch07-mobile.mp4` 并同步修改相关标签、旁白及 QA 报告。

使用已安装的 Node 22，在本目录运行：

```powershell
npm run studio
node scripts/render-film.mjs stills
node scripts/render-film.mjs preview
node scripts/render-film.mjs final
```

`render-film.mjs` 会先检查必需媒体及字幕，使用已有 Edge 与 Remotion 自带 FFmpeg，优先尝试已验证可用的本机硬件编码并允许软件回退，不下载模型、调用付费服务或更改显卡驱动。完整低码率预览输出到 `../previews/`，正式 MP4 输出到 `../output/`。实际时长、音画、编码、文件大小需继续运行 FFprobe 与逐段 QA。

字幕读取 `public/subtitles/captions.json`，使用官方 Caption 字段，整片绝对毫秒计时。SRT 与该 JSON 应来自同一旁白时间数据。界面底部保留独立字幕区域，避免挡住录屏。

主片只使用已经校准响度与渐入渐出的 `public/audio/narration-music.wav` 单一混音，不再对背景音乐重复衰减。单独旁白和音乐母版保留在外层 `audio/` 目录。

可选镜头数据 `public/media/focus.json` 格式：

```json
{"clips":{"ch03":[{"timeMs":1200,"x":0.56,"y":0.48,"kind":"click"}]}}
```

`x/y` 可用 0—1 归一化值或 1920×1080 像素。记录应来自真实鼠标；原录屏已经包含指针，所以后期指针默认关闭，仅用这些数据柔和推进镜头。缺少轨迹时保留轻微推进。不得写入虚假点击或业务响应。

字体复用 Windows Microsoft YaHei，无字体下载。颜色保持白、米白和自然绿色。动画全部由帧驱动，未使用 CSS animation 或 transition。

制作参考 Remotion create、markup、captions、render 的本地 Skill；Recordly / OpenScreen 仅参考鼠标焦点、轻柔缩放和镜头平移的方法，未复制其源码或光标素材。Remotion 使用其专有许可证，不是 MIT。详情见 `../reports/rules_review.md`。
