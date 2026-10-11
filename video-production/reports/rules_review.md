# 2026 AIC「AI+开源」视频制作规则核对

核对日期：2026-10-11（Asia/Shanghai）。本文件只核对官方视频规则与制作工具，不审查用户指定图片或产品身份。

## 直接影响导出的规则

| 项目 | 本赛道官方附件结论 | 本片执行目标 |
|---|---|---|
| 时长 | 3—5 分钟 | 4 分 50 秒，290 秒 |
| 容器 | MP4 | MP4 |
| 最大文件大小 | 300 MB 以内 | 导出后检查真实字节数，目标留出余量 |
| 分辨率、帧率、编码 | 两份附件未另行指定 | 1920×1080、30fps、H.264、AAC，属于制作选择 |
| 内容 | 核心功能、操作流程、实现效果、开源改进或开放成果 | 以真实交互录屏为主体，架构动画辅助解释 |
| 匿名边界 | 评审材料不得出现学校名称、学校 LOGO、指导教师信息 | 保留作品名、物生 Logo、团队名、项目仓库；检查浏览器与桌面隐私 |

以上导出及内容要求见《竞赛规则》第 4 页；匿名边界见第 3 页。官方附件没有要求隐藏作品名、团队名或成果链接。

作品申报名称另有不超过 20 字的限制（第 4 页）。视频主标题可用“物生”，完整说明性副标题保留为“AI驱动的家庭物品全生命周期智能管理平台”；提交系统中的作品名称应另外控制长度。

原始通知和赛题均指向以下同一组附件，未混入其他赛道规则：

- [官方通知](https://www.aicomp.cn/notice/notice-3/4890.html)
- [官方赛题](https://www.aicomp.cn/tracks/tracks-5/4924.html)
- [《AIC·AI+开源竞赛规则及作品提交要求》原 PDF](https://www.aicomp.cn/wp-content/uploads/2026/08/%E9%99%84%E4%BB%B61_AIC%C2%B7AI%E5%BC%80%E6%BA%90%E7%AB%9E%E8%B5%9B%E8%A7%84%E5%88%99%E5%8F%8A%E4%BD%9C%E5%93%81%E6%8F%90%E4%BA%A4%E8%A6%81%E6%B1%820812.pdf)
- [《AIC·AI+开源技术报告参考大纲》原 PDF](https://www.aicomp.cn/wp-content/uploads/2026/08/%E9%99%84%E4%BB%B62_AIC%C2%B7AI%E5%BC%80%E6%BA%90%E6%8A%80%E6%9C%AF%E6%8A%A5%E5%91%8A%E5%8F%82%E8%80%83%E5%A4%A7%E7%BA%B2260812.pdf)

## 制作表达边界

《技术报告参考大纲》第 2—3 页要求说明真实需求、AI 作用、自主开发边界、可验证结果与开放价值；第 4 页要求披露 AI 辅助制作与第三方资源使用。视频因此应清楚区分项目业务实现、RapidOCR、Qwen、Remotion 等所采用的第三方能力，并保留原始录屏与实际运行日志。文件与素材只有在具备相应权利时才公开分发。完整厂商 PDF、本地模型权重、私人订单和凭据不随视频工程上传公开仓库。

规则允许模拟业务流程等方法完成验证，并不要求大模型训练或企业试点。软件的实际操作结果仍须真实发生；自动化浏览器手机视口不能写成真实手机实录。

两份本地原文件均 5 页，已完成文本提取，并渲染查看规则第 4 页及大纲第 4 页的布局与表格。保存于 `reports/rules/`，下载地址、大小与 SHA256 见 `source_manifest.json`。官方文本提取文件仅用于本地核对。

## 赛程补充

[2026-10-10 官方赛程调整通知](https://www.aicomp.cn/notice/notice-3/5435.html)仍列 AI+开源报名缴费与作品提交截止时间为 **2026-10-30 20:00**。该通知未另行改变视频时长、格式或大小规则。

## 开源录屏及动态效果参考

本次只研究镜头方法，不复制 Recordly / OpenScreen 源码或其光标美术素材。下列方法由视频工程独立实现，并在最终报告中按实际使用情况列工具。

| 项目 | 可借鉴方法 | 已读取的一手来源 | 许可边界 |
|---|---|---|---|
| Remotion | React 时间轴、帧驱动动画、交叉转场、音频与字幕合成 | [仓库](https://github.com/remotion-dev/remotion)、[TransitionSeries](https://www.remotion.dev/docs/transitions/transitionseries) | [专有 Remotion License](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md)，不是 MIT；个人、最多 3 名员工的营利组织、非营利组织等属于免费许可适用类别，按实际使用版本的许可执行 |
| Remotion Skills | create / markup / captions / render / studio 分工 | [官方 Skills 清单](https://github.com/remotion-dev/skills) | 属于制作工作流与知识参考；最终列出实际读取的 Skill，不把研究过当成已经使用 |
| Recordly | 依据点击、文本焦点和停留确定放大区；相邻重点间平滑平移；弹簧平滑光标与镜头 | [README](https://github.com/DougNix/recordly)、[zoomSuggestionUtils](https://github.com/DougNix/recordly/blob/main/src/components/video-editor/timeline/zoomSuggestionUtils.ts)、[zoomRegionUtils](https://github.com/DougNix/recordly/blob/main/src/components/video-editor/videoPlayback/zoomRegionUtils.ts)、[motionSmoothing](https://github.com/DougNix/recordly/blob/main/src/components/video-editor/videoPlayback/motionSmoothing.ts) | [MIT](https://github.com/DougNix/recordly/blob/main/LICENSE)，实际分发代码时须保留版权及许可声明；本次未复制 |
| OpenScreen | 光标追随放大、可调缓动与停留、编辑段落速度、窗口圆角及阴影、隐私区域处理 | [README](https://github.com/Aldazou/openscreen)、[视频播放模块](https://github.com/Aldazou/openscreen/tree/main/src/components/video-editor/videoPlayback) | [MIT](https://github.com/Aldazou/openscreen/blob/main/LICENSE)，本次仅参考交互方法，不使用附带角色图案光标 |

Recordly 树快照为 `405946a1c89f219c38fd69a11f68a1819a42caea`；OpenScreen 树快照为 `46e4cd7cc84c1d648dabce469a3d2138666cfa3f`。相关源码路径清单已保存，但未将上游源码复制进物生。

用于物生视频的具体镜头选择：关键点击后柔和推进，保留动作前后的完整上下文；字段确认和 AI 引用区域适度放大；相邻操作以平移和短交叉淡化衔接；等待可剪短，但不得伪造响应。鼠标轨迹和点击反馈应来自实际自动化操作的时间与坐标记录。
