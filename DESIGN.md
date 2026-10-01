---
name: "物生 Wusheng"
description: "让每一件物品，都被好好对待"
colors:
  green: "#118b50"
  accent: "#16a361"
  green-hover: "#0a7743"
  green-active: "#087f46"
  green-soft: "#ecf8f1"
  green-status: "#09874b"
  canvas: "#f8faf9"
  surface: "#fff"
  text: "#17202a"
  muted: "#667085"
  line: "#e7ece9"
  field-text: "#344054"
  placeholder: "#75827b"
  nav-text: "#536078"
  nav-hover: "#f5f9f6"
  filter-neutral: "#eef2f1"
  filter-text: "#48556c"
  orange-soft: "#fff4eb"
  orange: "#e97720"
  blue-soft: "#edf4ff"
  blue: "#2b7bd6"
  purple-soft: "#f4efff"
  purple: "#8860dc"
  red-soft: "#ffeff0"
  red: "#d83e43"
  error-bg: "#fff1ef"
  error-text: "#ba3c31"
  notice-bg: "#fffaec"
  notice-text: "#83642c"
typography:
  display:
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif'
    fontSize: "clamp(34px, 3.15vw, 53px)"
    fontWeight: 750
    lineHeight: 1.4
    letterSpacing: "-0.025em"
  headline:
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif'
    fontSize: "40px"
    fontWeight: 750
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  section:
    fontSize: "27px"
    letterSpacing: "-0.02em"
  title:
    fontSize: "18px"
    fontWeight: 650
    lineHeight: 1.45
  description:
    fontSize: "15px"
    lineHeight: 1.75
  button:
    fontSize: "14px"
    fontWeight: 550
  field:
    fontSize: "13px"
  label:
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.2
rounded:
  field: "9px"
  icon-button: "10px"
  button: "11px"
  dropzone: "12px"
  navigation: "13px"
  card: "16px"
  icon-well: "18px"
  filter: "24px"
  hero-button: "28px"
  badge: "30px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  chart-gap: "18px"
  item-gap: "19px"
  lg: "20px"
  panel: "22px"
  xl: "24px"
  page: "32px"
components:
  button-primary:
    backgroundColor: "{colors.green}"
    textColor: "{colors.surface}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    padding: "12px 20px"
  button-primary-hover:
    backgroundColor: "{colors.green-hover}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.field-text}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    padding: "12px 20px"
  button-outline:
    backgroundColor: "#fcfefc"
    textColor: "{colors.green}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    padding: "12px 20px"
  button-soft:
    backgroundColor: "{colors.green-soft}"
    textColor: "{colors.green}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    padding: "12px 20px"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.field-text}"
    rounded: "{rounded.field}"
    padding: "10px 12px"
  navigation:
    textColor: "{colors.nav-text}"
    rounded: "{rounded.navigation}"
    padding: "0 21px"
    height: "52px"
  navigation-active:
    backgroundColor: "{colors.green-soft}"
    textColor: "{colors.green-active}"
  badge-green:
    backgroundColor: "{colors.green-soft}"
    textColor: "{colors.green-status}"
    typography: "{typography.label}"
    rounded: "{rounded.badge}"
    padding: "6px 12px"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.card}"
  filter:
    backgroundColor: "{colors.filter-neutral}"
    textColor: "{colors.filter-text}"
    rounded: "{rounded.filter}"
    padding: "9px 23px"
  filter-active:
    backgroundColor: "{colors.green}"
    textColor: "{colors.surface}"
  dropzone:
    backgroundColor: "#fbfdfb"
    rounded: "{rounded.dropzone}"
    padding: "28px 14px"
---

# Design System: 物生 Wusheng

## Overview

**Creative North Star: "让每一件物品，都被好好对待"**

自然、温暖、克制。白色内容面板与浅色画布承载家庭物品档案，自然绿标记行动和当前状态。植物照片、叶片标志与轻微绿色氛围出现在品牌区域，日常工作页面以内容和真实物品照片为中心。

所有页面共享同一侧栏、工具栏、标题和卡片语言。桌面布局提供充分信息密度，窄屏通过重排与收起导航文字保留操作。以用户九张设计稿为视觉权威，最新文字约束确定无账户、头像、设置或商业模块。[九张稿逐页分析](docs/references/ui-analysis.md) 保留参考来源，本文记录当前实现。规范提取自 `frontend/src/styles.css`、`frontend/src/components/ui.tsx`、`frontend/src/components/AppShell.tsx` 与 `frontend/src/App.tsx`。

**Key Characteristics:**

- 自然绿与白色为主要视觉语言。
- 系统中文字体与简洁无衬线文字。
- 统一八项导航、圆角面板与轻阴影。
- 物品照片、状态文字和来源证据共同传达信息。
- 可见键盘焦点，遵循减弱动态偏好。

## Colors

前置 YAML 为颜色规范；本节说明用途，不建立第二套色值。

### Primary

- **自然绿**（`green`）：主要按钮、链接、图标、输入光标和选中筛选。`green-hover` 对应主要按钮悬停；`green-active` 对应当前导航文字。
- **明亮绿**（`accent`）：焦点轮廓与在线状态点。
- **浅绿**（`green-soft`）：当前导航、柔和按钮和正常状态底色；`green-status` 为正常状态文字。

### Neutral

- **浅色画布 / 白色面板**（`canvas` / `surface`）：区分工作区与内容表面，避免以重描边划分每张卡片。
- **深色正文 / 次级灰**（`text` / `muted`）：标题、数字与说明的层级；字段文字和占位文字分别使用 `field-text`、`placeholder`。
- **轻分隔线**（`line`）：字段、内部隔断、抽屉内容分区。
- **导航与筛选中性色**（`nav-text`、`nav-hover`、`filter-neutral`、`filter-text`）：降低未选中操作的视觉重量。

### Semantic accents

橙、蓝、紫、红及各自浅色背景用于状态、指标图标和图表分类。橙色传达维修或维护提醒，红色与错误色用于异常，紫色用于部分补给或 AI 提示；蓝色作为局部信息色。每个状态同时保留文字。错误面板与提示面板分别使用 `error-*`、`notice-*`，不得替代主要自然绿。

## Typography

全站采用前置字体栈。中文由系统可用字体呈现，Inter 未通过外部字体服务加载；字体名称在栈中只作为本机可用时的候选。组件继承同一字体，不引入独立装饰字体。

- **Display**：首页主标题使用响应式字号；较宽屏范围与字重见 `typography.display`。窄屏规则见 Layout。
- **Headline**：工作页一级标题使用 `typography.headline`。
- **Section / Title**：二级标题与三级标题分别使用 `typography.section`、`typography.title`；原临时规范的 28px / 19px 已按实现刷新。
- **Body**：段落行高为 1.75；页面说明为 `typography.description`，卡片和表单按密度采用 12–14px。首页简介行高 1.9、最大宽度 480px。
- **Label**：状态标签为 `typography.label`；次级小字默认 12px。指标数字使用等宽数字特性以保持对齐。

## Layout

桌面固定侧栏宽度 232px，工作区对应左偏移；工具栏高 72px。工具栏包含全局搜索、通知与本地状态，保持统一位置。普通页面最大宽度 1680px、内边距 32px；首页最大宽度 1800px。

指标卡使用 16px 间距，物品卡使用 19px 间距，图表使用 18px 间距。物品列表桌面四列，建档主区与表单为两列，助手主区加 330px 上下文栏，统计页采用 1fr / 1.18fr / 0.86fr 三列。抽屉实际宽度为 460px、最大宽度 100%，内部滚动。

响应式行为以 CSS 的实际断点为准：

- 1700px 以上：扩大首页留白、演示区域与卡片内边距。
- 1400px 以下：普通页内边距 27px，压缩卡片和统计区域；助手上下文栏降为 300px。
- 1150px 以下：侧栏 205px，物品三列，部分指标三列，统计两列；助手上下文栏 260px。
- 1000px 以下：统计侧栏取消固定第三列定位。
- 800px 以下：侧栏 70px，仅展示图标并保留可访问名称；工具栏 64px。首页、建档、助手和统计主区单列，物品两列。
- 480px 以下：普通页内边距 20px 14px，物品单列；首页功能入口和步骤单列，建档方式单列、建档步骤两列。首页标题使用 `clamp(25px, 7.7vw, 34px)`，动作允许换行，搜索容器可收缩。

## Elevation & Depth

深度由白色面板、浅色画布和低对比绿色阴影共同表达。共享卡片阴影以 CSS 变量 `--shadow` 为准，搜索下拉、抽屉、Toast 和首页产品演示具有各自的浮层阴影，完整值保存在 `.impeccable/design.json`。首页植物和渐变属于品牌氛围；工作页面保持清晰内容层级。

交互具有轻微运动：按钮与物品卡悬停抬升，页面以 220ms 淡入、轻移；抽屉以 250ms 从右进入。全站尊重 `prefers-reduced-motion`，Framer Motion 采用用户偏好，CSS 将动画与过渡压缩并关闭重复动画。

## Shapes

表面以轻圆角组织内容，角色半径以 YAML 为准：共享卡片 16px、按钮 11px、字段 9px、导航 13px。标签和筛选采用胶囊形；首页 CTA 使用更圆的 28px 角。图片裁切到容器，物品卡将图像与文字收在同一轮廓内。

字段和次级动作有细描边，主面板依赖底色与阴影；上传区域以虚线提示可拖放。叶片图形作为品牌标志，不延伸为所有组件的轮廓。

## Components

### Buttons

主要动作清晰，次级动作温和。四种变体为主要、白色次级、绿色描边与浅绿柔和按钮，共享最小高度 44px、图文间距 9px。按钮悬停上移 1px、过渡 180ms；主要按钮同时加深底色。禁用时不响应操作并以 0.5 透明度呈现。焦点使用 2px `accent` 轮廓、3px 外偏移。

### Chips

状态标签显示文字与语义色，不作为交互按钮。筛选按钮以中性底色显示未选中状态，以实心自然绿显示当前状态；筛选列表可换行。标签与筛选半径、内边距分别由 `badge-green`、`filter` 定义。

### Cards / Containers

共享白色圆角与轻阴影；指标卡通常内边距 20px、最小高度 105px，图表面板通常内边距 22px。物品卡图片长宽比默认 1.65，信息区内边距 15px 17px 16px，标题与品牌型号单行截断。悬停时卡片上移 3px、图片放大到 1.03。无图时显示照片占位与提示文字。

### Inputs / Fields

白色字段、细边框与绿色焦点边；字段的外轮廓遵循统一可见焦点规则。表单字段带文字标签，建档字段字号 13px、内边距 9px 10px，低置信度候选另附暖色提示与来源。全局搜索的焦点显示在整个容器；占位文字不代替可访问名称。

### Navigation

八项顺序固定为：首页、我的物品、添加物品、提醒中心、耗材管理、维修记录、AI 助手、数据统计。默认图标 21px、文字继承系统字体；活动项采用浅绿背景、绿色文字和加粗，悬停采用更轻的绿底。物品详情归属“我的物品”，建档单独归属“添加物品”。窄屏显示图标，同时保留标题与可访问名称。

### Upload and recognition

上传区最小高度 280px，拖入文件后虚线与底色转绿。扫描提示只在处理期间出现。识别候选与字段来源、置信度一起呈现，低置信度采用暖色，保留人工修改与确认。

### Drawers and feedback

抽屉包含标题与可访问关闭按钮，遮罩点击、Escape 和关闭按钮都可退出；打开时限制背景滚动、约束键盘焦点，关闭后还原焦点。Toast 使用深绿底与状态语义，空态保留具体文字和下一步操作，加载态使用圆角骨架。

## Do's and Don'ts

### Do:

- Do 保持自然绿、白色面板和浅色画布的统一视觉语言。
- Do 复用八项侧栏、工具栏和共享组件，遵守实际响应式重排。
- Do 用状态文字、标签和来源证据共同表达信息。
- Do 保留可见键盘焦点、表单标签和减弱动态支持。

### Don't:

- Don't 加入账户、头像、设置或商业推广模块。
- Don't 将蓝色信息点扩展为蓝色大屏或替代自然绿主色。
- Don't 以占位文字替代字段标签，或只以颜色传达状态。
- Don't 采用无依据的准确率、统计数或来源装饰来制造可信感。
