# 参与贡献

欢迎提交问题和改进。请先描述可复现的问题、预期行为和运行环境；涉及本地数据库、图片或 PDF 时，请使用合成测试资料，不要附带真实个人文件或密钥。

## 本地开发

请参照 [README 快速开始](README.md#快速开始windows)安装锁定依赖。提交前运行：

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
cd frontend
npm run build
npm run lint
npm test
```

UI 测试需要本地前后端和 Microsoft Edge。不要提交 `data/` 中的 SQLite、用户图片、PDF、票据、日志或备份。新增外部依赖、模型、数据集或媒体时，请更新 `THIRD_PARTY.md` 并保留相应许可。

## 设计边界

维持 Local First 默认行为。未经用户明确同意，不要把本地附件或档案发送到外部服务。AI/OCR 输出应能检查和人工修改；没有证据时不要编造数据。
