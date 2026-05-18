# Contributing to mchat

Thank you for your interest in contributing to mchat! 🎉

## How to Contribute

### Reporting Bugs

1. Check the [issue tracker](https://github.com/mchat-ai/mchat/issues) to avoid duplicates
2. Use the bug report template
3. Include steps to reproduce, expected behavior, and environment details

### Suggesting Features

1. Check existing issues and discussions
2. Open a feature request with clear motivation and use case
3. Be open to discussion and refinement

### Code Contributions

1. **Fork** the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Write code and tests
4. Ensure all tests pass: `make test`
5. Run linters: `make lint`
6. Commit with clear messages following [Conventional Commits](https://www.conventionalcommits.org/)
7. Push and open a Pull Request

### Development Setup

```bash
git clone https://github.com/mchat-ai/mchat.git
cd mchat
make install
make dev
```

### Code Style

- **Backend (Python)**: Follow PEP 8, formatted with `ruff`
- **Frontend (TypeScript)**: ESLint + Prettier
- **Commit messages**: Conventional Commits format

### Testing

- Write tests for all new features
- Ensure existing tests pass
- Backend: `pytest` with `pytest-asyncio`
- Frontend: `vitest` (coming soon)

### Pull Request Process

1. Update documentation if needed
2. Add CHANGELOG entry
3. Ensure CI passes
4. Request review from maintainers
5. Squash merge when approved

## Project Structure

See [docs/architecture.md](docs/architecture.md) for the full architecture overview.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
