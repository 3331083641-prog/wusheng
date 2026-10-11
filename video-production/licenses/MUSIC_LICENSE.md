# 原创背景音乐与声音说明

本地 `audio/bgm.wav` 及 `audio/bgm-original-master.wav` 由 [音乐生成脚本](../scripts/bgm_build.py) 使用正弦波、包络与确定性和声独立合成，不使用外部录音、采样、第三方音乐或现有旋律。为物生比赛演示制作，D 大调、88 BPM、无歌词。原创音乐及生成脚本以 CC0 1.0 Universal（公共领域贡献）提供，可用于本视频及后续修改、公开传播，无需署名。

CC0 法律文本：https://creativecommons.org/publicdomain/zero/1.0/legalcode

旁白由 `edge-tts 7.2.8` 调用 Microsoft Edge Read Aloud 的 `zh-CN-XiaoxiaoNeural` 合成，是合成语音，不是真人录音、不模仿指定自然人。使用现有本机网络代理，无付费 API、无密钥。本地 `audio/voice-provenance.json` 保存实际引擎、语速与章节时长。edge-tts 工具采用 LGPL-3.0 许可证，工具依赖独立安装，不并入物生正式软件依赖。

`narration.wav` 为独立旁白，`bgm.wav` 为已压低音量的音乐床，`narration-music.wav` 为组合音轨。建议正式渲染使用组合音轨；如分别导入，请勿再次叠加组合音轨，避免声音重复。
