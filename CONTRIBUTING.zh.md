# 参与 mchat 开发

感谢你对 mchat 的关注与贡献！

## 如何贡献

### 报告问题

1. 先检查 [issue 列表](https://github.com/mchat-ai/mchat/issues)，避免重复。
2. 使用 bug report 模板。
3. 提供复现步骤、预期行为和环境信息。

### 提出功能建议

1. 先查看已有 issue 和讨论。
2. 提交 feature request，并说明动机和使用场景。
3. 保持开放，便于后续讨论和完善。

### 代码贡献

1. **Fork** 仓库。
2. 创建功能分支：`git checkout -b feature/your-feature`。
3. 编写代码和测试。
4. 确保测试通过：`make test`。
5. 运行 lint：`make lint`。
6. 使用清晰的提交信息，并遵循 [Conventional Commits](https://www.conventionalcommits.org/)。
7. 推送代码并发起 Pull Request。

### 开发环境

```bash
git clone https://github.com/mchat-ai/mchat.git
cd mchat
make install
make dev
```

### 代码风格

- **后端（Python）**：遵循 PEP 8，使用 `ruff` 进行格式化与检查。
- **前端（TypeScript）**：使用 ESLint + Prettier。
- **提交信息**：遵循 Conventional Commits 格式。

### 测试

- 所有新功能都应补测试。
- 确保现有测试通过。
- 后端：`pytest` + `pytest-asyncio`。
- 前端：`vitest`（计划中）。

### Pull Request 流程

1. 如有需要，同步更新文档。
2. 增加 CHANGELOG 条目。
3. 确保 CI 通过。
4. 请求维护者评审。
5. 审核通过后再 squash merge。

## 项目结构

完整架构请见 [docs/architecture.zh.md](docs/architecture.zh.md)。

## 许可

提交代码即表示你同意这些贡献将按 MIT License 发布。
