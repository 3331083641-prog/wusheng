# 首页品牌视觉替换验收

完成时间：2026-10-02。范围：首页指定文案、共享 Sidebar 的 Logo 与宣传卡片背景。未修改后端、SQLite、上传/PDF/耗材/AI 功能、字体、产品图或动画逻辑。

## 资源

- `frontend/public/assets/branding/wusheng-eco-ring-logo.png`：877×877 PNG，源图绿色范围检测后四边保留12px安全边距。去掉近白色底；无重采样，RGB逐像素与源图裁切区域一致。
- `frontend/public/assets/branding/wusheng-eco-ring-logo-master.png`：1254×1254原始高清Logo。
- `frontend/public/assets/branding/sidebar-natural-leaf-bg.png`：1122×1402植物原图，文件SHA256与用户提供原图一致。

## 本轮源代码变更

- `frontend/src/components/ui.tsx`：Sidebar Logo 使用新品牌图。
- `frontend/src/components/AppShell.tsx`：移除宣传卡片旧线稿叶子。
- `frontend/src/pages/Home.tsx`：删除 Hero 三项声明、演示状态标题、场景H2副标题、整个Footer文本栏。
- `frontend/src/styles.css`：Logo 36px contain；植物背景 cover/right bottom、约12%白色轻蒙层；清理被删除节点样式，略缩Hero底部间距。移动端Logo居中。

关键文件备份：`backups/home-branding-20261002-011623/`。

## 检查结果

1. Sidebar左上替换为绿色生态叶环Logo：通过。
2. 去掉大面积白边，完整保留圆环/叶片/右上圆点：通过。
3. Logo与品牌字样垂直居中：通过。
4. 36px容器、图案尺寸自然：通过。
5. 无白色方框、无边框/阴影/额外底板：通过。
6. Sidebar宣传卡片使用真实植物原图：通过。
7. 主叶片位于右下：通过。
8. 图片不遮挡标题、副标题、箭头：通过。
9. 宣传卡片旧线稿叶子已从DOM移除：通过。
10. Hero三项文字与对应图标整行删除：通过。
11. 真实档案·动态演示与前方绿点删除：通过。
12. 场景H2副标题删除，主标题保留：通过。
13. Footer左侧文字删除：通过。
14. Footer右侧Demo文字删除：通过。
15. Footer整个DOM与CSS删除，无空占位：通过。
16. 原有布局、Sidebar宽度、6张功能卡片尺寸保持，3张场景卡、4步流程与8项导航保留：通过；几何尺寸与变更前自动比对。
17. 1440×900：通过。
18. 1920×1080：通过；1366×768及390×844亦无水平溢出。
19. `npm run build`、`npm run lint`：通过。
20. 浏览器控制台错误0；失败HTTP/图片请求0：通过。

保留 Sidebar 的“本地优先 · 免费开放”、宣传卡片原有两行主标题和“陪伴，比拥有更长久。”。实际点击“查看功能”与宣传卡片箭头均正常导航。

自动浏览器检查：`browser-check.json`。源图与裁边记录：`assets.json`。本目录保留各尺寸页面、Logo与宣传卡片截图。
