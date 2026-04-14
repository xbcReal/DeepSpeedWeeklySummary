# DeepSpeed Weekly Summary

🚀 **DeepSpeed 仓库周报自动生成工具**

自动追踪 [microsoft/DeepSpeed](https://github.com/microsoft/DeepSpeed) 仓库的每周更新，生成美观的 HTML 周报。

## 特性

- 📊 **自动统计**: PR 数量、合并数量、Commit 数量、新特性数量
- 🏷️ **智能分类**: 根据 PR 标题自动分类（Feature/Bugfix/Performance/Docs 等）
- 🎨 **精美界面**: 深色主题，响应式设计
- 🤖 **AI 生成**: 使用 Qoder Worker 自动生成周报内容
- 📱 **自动跳转**: 首页自动跳转到最新周报

## 目录结构

```
.
├── index.html              # 主页，自动跳转到最新周报
├── update_index.py         # 周报生成脚本（备用）
├── ds-summary/             # 周报文件目录
│   └── ds-weekly-report-YYYY-MM-DD.html
└── README.md
```

## 生成方式

本项目使用 **Qoder Worker** 自动生成周报：

1. Qoder Worker 定时任务每周自动收集 DeepSpeed 仓库更新
2. 生成 HTML 格式的周报并保存到 `ds-summary/` 目录
3. 自动提交并推送到 GitHub
4. GitHub Pages 自动部署更新

### 备用：本地生成

如需手动生成本地周报：

```bash
pip install requests beautifulsoup4
python update_index.py
```

## 周报内容

每份周报包含：

- **统计概览**: 新增 PR、合并 PR、Commits、新特性数量
- **本周亮点**: 重要更新摘要
- **新增 PR**: 本周创建的 PR 列表（含状态标签）
- **已合并 PR**: 本周合并的 PR 列表
- **重要 Commits**: 关键提交记录

## PR 分类规则

| 标签 | 关键词 |
|------|--------|
| Feature | feature, add, support, implement, new |
| Bugfix | fix, bug, hotfix, patch |
| Performance | perf, performance, speed, optimize |
| Documentation | doc, readme, documentation, tutorial |
| Test | test, testing, unittest, pytest |
| CI/CD | ci, github action, workflow, build |
| Refactor | refactor, cleanup, restructure |

## 许可证

MIT License - 参考 [TransformerEngineWeeklySummary](https://github.com/leonardozcm/TransformerEngineWeeklySummary) 项目实现

## 致谢

- 样式设计参考 [TransformerEngineWeeklySummary](https://github.com/leonardozcm/TransformerEngineWeeklySummary)
- 数据来源 [microsoft/DeepSpeed](https://github.com/microsoft/DeepSpeed)
